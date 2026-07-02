from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from backend.core.utilities.responses import error_response, success_response
from .serializers import (
    CustomUserSerializer,
    GoogleOAuthSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegistrationOTPVerifySerializer,
    ResendOTPSerializer,
    UserSignInSerializer,
    UserSignUpSerializer,
)
from .services.auth_service import AuthService, AuthServiceError
from .services.google_auth_service import GoogleAuthService
from .services.otp_service import OTPService, OTPServiceError


def _serializer_errors(serializer):
    return error_response("Validation failed", serializer.errors, status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def signup(self, request):
        serializer = UserSignUpSerializer(data=request.data)
        if not serializer.is_valid():
            return _serializer_errors(serializer)
        try:
            data = AuthService.register_user(serializer.validated_data)
            return success_response(
                "OTP sent to your email. Please verify to complete registration.",
                data,
                status.HTTP_200_OK,
            )
        except (AuthServiceError, OTPServiceError) as exc:
            return error_response(exc.message, status_code=exc.status_code, **exc.metadata)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def signin(self, request):
        return self.login(request)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        serializer = UserSignInSerializer(data=request.data)
        if not serializer.is_valid():
            return _serializer_errors(serializer)
        try:
            data = AuthService.login(
                serializer.validated_data["identifier"],
                serializer.validated_data["password"],
            )
            return success_response("Login successful.", data, status.HTTP_200_OK, **data)
        except AuthServiceError as exc:
            return error_response(exc.message, status_code=exc.status_code, **exc.metadata)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def verify_signup_otp(self, request):
        return self.verify_otp(request)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def verify_otp(self, request):
        serializer = RegistrationOTPVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return _serializer_errors(serializer)
        try:
            data = AuthService.verify_registration(
                serializer.validated_data["email"],
                serializer.validated_data["otp_code"],
            )
            return success_response("Registration complete.", data, status.HTTP_201_CREATED, **data)
        except (AuthServiceError, OTPServiceError) as exc:
            return error_response(exc.message, status_code=exc.status_code, **exc.metadata)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def resend_otp(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return _serializer_errors(serializer)
        try:
            _, metadata = OTPService.resend_otp(
                serializer.validated_data["email"],
                serializer.validated_data["purpose"],
            )
            return success_response("OTP sent successfully", metadata, status.HTTP_200_OK)
        except OTPServiceError as exc:
            return error_response(exc.message, status_code=exc.status_code, **exc.metadata)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def google_signin(self, request):
        return self.google_login(request)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def google_login(self, request):
        serializer = GoogleOAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return _serializer_errors(serializer)
        try:
            data = GoogleAuthService.authenticate(serializer.validated_data["id_token"])
            return success_response("Google login successful.", data, status.HTTP_200_OK, **data)
        except AuthServiceError as exc:
            return error_response(exc.message, status_code=exc.status_code)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def password_reset_request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return _serializer_errors(serializer)
        try:
            data = AuthService.request_password_reset(serializer.validated_data["email"])
            return success_response(
                "OTP sent to your email. Please verify to continue password reset.",
                data,
                status.HTTP_200_OK,
            )
        except (AuthServiceError, OTPServiceError) as exc:
            return error_response(exc.message, status_code=exc.status_code, **exc.metadata)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def password_reset_confirm(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return _serializer_errors(serializer)
        try:
            AuthService.confirm_password_reset(
                serializer.validated_data["email"],
                serializer.validated_data["otp_code"],
                serializer.validated_data["password"],
            )
            return success_response("Password reset successful.")
        except (AuthServiceError, OTPServiceError) as exc:
            return error_response(exc.message, status_code=exc.status_code, **exc.metadata)

    @action(detail=False, methods=["get", "patch"], permission_classes=[IsAuthenticated])
    def profile(self, request):
        if request.method == "PATCH":
            serializer = CustomUserSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            if not serializer.is_valid():
                return _serializer_errors(serializer)
            serializer.save()
            return success_response("Profile updated successfully.", serializer.data)

        serializer = CustomUserSerializer(request.user, context={"request": request})
        return success_response("Profile fetched successfully.", serializer.data)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def logout(self, request):
        refresh_token = request.data.get("refresh") or request.data.get("refresh_token")
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass
        return success_response("Successfully logged out")

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def admin_login(self, request):
        serializer = UserSignInSerializer(data=request.data)
        if not serializer.is_valid():
            return _serializer_errors(serializer)
        try:
            data = AuthService.login(
                serializer.validated_data["identifier"],
                serializer.validated_data["password"],
                admin=True,
            )
            return success_response("Admin login successful.", data, status.HTTP_200_OK, is_admin=True, **data)
        except AuthServiceError as exc:
            return error_response(exc.message, status_code=exc.status_code, **exc.metadata)
