from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from backend.users.models import CustomUser, OTP, PendingRegistration
from .otp_service import OTPService, OTPServiceError
from .user_service import UserService


User = get_user_model()


class AuthServiceError(Exception):
    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST, metadata=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.metadata = metadata or {}


class AuthService:
    @staticmethod
    def token_payload(user):
        refresh = RefreshToken.for_user(user)
        return {"access": str(refresh.access_token), "refresh": str(refresh)}

    @classmethod
    def auth_payload(cls, user):
        from backend.users.serializers import CustomUserSerializer

        tokens = cls.token_payload(user)
        return {"user": CustomUserSerializer(user).data, "tokens": tokens, "token": tokens["access"]}

    @classmethod
    def register_user(cls, data):
        PendingRegistration.objects.update_or_create(
            email=data["email"],
            defaults={
                "username": data["username"],
                "password_hash": make_password(data["password"]),
                "first_name": data.get("first_name", ""),
                "last_name": data.get("last_name", ""),
            },
        )
        otp, metadata = OTPService.send_otp(data["email"], OTP.PURPOSE_REGISTER)
        return {
            "email": otp.email,
            "otpRequired": True,
            "verificationPending": True,
            "requiresVerification": True,
            "isOtpSent": True,
            "cooldown_seconds": metadata["cooldown_seconds"],
            "expires_in_seconds": metadata["expires_in_seconds"],
        }

    @classmethod
    def verify_registration(cls, email, otp_code):
        otp = OTPService.verify_otp(email, otp_code, OTP.PURPOSE_REGISTER)
        try:
            pending = PendingRegistration.objects.get(email__iexact=email)
        except PendingRegistration.DoesNotExist:
            raise AuthServiceError("Registration session expired. Please sign up again.")

        if User.objects.filter(email__iexact=email).exists():
            raise AuthServiceError("Email is already registered.")
        if User.objects.filter(username__iexact=pending.username).exists():
            raise AuthServiceError("Username already exists. Please choose another username.")

        user = User(
            email=pending.email,
            username=pending.username,
            first_name=pending.first_name,
            last_name=pending.last_name,
            is_email_verified=True,
        )
        user.password = pending.password_hash
        user.save()
        OTPService.mark_used(otp)
        pending.delete()
        return cls.auth_payload(user)

    @classmethod
    def login(cls, identifier, password, admin=False):
        user = UserService.find_by_identifier(identifier)
        if not user or not user.check_password(password):
            raise AuthServiceError("Invalid username/email or password", status.HTTP_401_UNAUTHORIZED)

        is_admin = user.role == CustomUser.ROLE_ADMIN or user.is_staff or user.is_superuser
        if admin and not is_admin:
            raise AuthServiceError("You do not have admin access.", status.HTTP_403_FORBIDDEN)
        if not admin and is_admin:
            raise AuthServiceError("Admins must use admin login.", status.HTTP_403_FORBIDDEN)
        if not user.is_email_verified:
            raise AuthServiceError(
                "Please verify your email before signing in.",
                status.HTTP_403_FORBIDDEN,
                {"requiresVerification": True, "email": user.email},
            )
        return cls.auth_payload(user)

    @classmethod
    def request_password_reset(cls, email):
        if not User.objects.filter(email__iexact=email).exists():
            raise AuthServiceError("You have not registered yet.")
        _, metadata = OTPService.send_otp(email, OTP.PURPOSE_PASSWORD_RESET)
        return metadata

    @classmethod
    def confirm_password_reset(cls, email, otp_code, password):
        otp = OTPService.verify_otp(email, otp_code, OTP.PURPOSE_PASSWORD_RESET)
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise AuthServiceError("Invalid email or OTP.")
        user.set_password(password)
        user.save(update_fields=["password"])
        OTPService.mark_used(otp)
        return {}
