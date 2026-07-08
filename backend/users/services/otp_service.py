import logging
import secrets
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import status

from core.compatibility.legacy_otp_mapping import accepted_otp_purpose_values, normalize_otp_purpose
from core.constants import (
    OTPPurpose,
    OTP_EXPIRY_SECONDS,
    OTP_MAX_REQUESTS_PER_HOUR,
    OTP_MAX_VERIFY_ATTEMPTS,
    OTP_RESEND_COOLDOWN_SECONDS,
)
from core.services.email_service import EmailService
from .user_service import UserService
from users.models import OTP


logger = logging.getLogger(__name__)


class OTPServiceError(Exception):
    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST, metadata=None, errors=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.metadata = metadata or {}
        if errors is not None:
            self.metadata["errors"] = errors


class OTPService:
    @staticmethod
    def normalize_purpose(purpose):
        normalized = normalize_otp_purpose(purpose)
        if not normalized:
            raise OTPServiceError(
                "Invalid OTP purpose",
                errors={"purpose": [f"Must be one of: {accepted_otp_purpose_values()}"]},
            )
        return normalized

    @staticmethod
    def generate_code():
        return f"{secrets.randbelow(900000) + 100000}"

    @classmethod
    def _cooldown_remaining(cls, email, purpose):
        latest = OTP.objects.filter(email__iexact=email, purpose=purpose).order_by("-last_sent_at", "-created_at").first()
        if not latest:
            return 0
        reference = latest.last_sent_at or latest.created_at
        elapsed = (timezone.now() - reference).total_seconds()
        return max(0, OTP_RESEND_COOLDOWN_SECONDS - int(elapsed))

    @classmethod
    def _enforce_request_limits(cls, email, purpose):
        remaining = cls._cooldown_remaining(email, purpose)
        if remaining > 0:
            raise OTPServiceError(
                "Please wait before requesting another OTP.",
                status.HTTP_429_TOO_MANY_REQUESTS,
                {"cooldown_seconds": remaining},
            )

        hourly_count = OTP.objects.filter(
            email__iexact=email,
            purpose=purpose,
            created_at__gte=timezone.now() - timedelta(hours=1),
        ).aggregate(total=Count("id"))["total"]
        if hourly_count >= OTP_MAX_REQUESTS_PER_HOUR:
            raise OTPServiceError(
                "Too many OTP requests. Please try again later.",
                status.HTTP_429_TOO_MANY_REQUESTS,
                {"max_requests_per_hour": OTP_MAX_REQUESTS_PER_HOUR},
            )

    @classmethod
    def send_otp(cls, email, purpose, enforce_limits=True):
        purpose = cls.normalize_purpose(purpose)
        if enforce_limits:
            cls._enforce_request_limits(email, purpose)

        OTP.objects.filter(email__iexact=email, purpose=purpose, is_used=False).update(is_used=True)
        otp = OTP.objects.create(
            email=email,
            otp_code=cls.generate_code(),
            purpose=purpose,
            expires_at=timezone.now() + timedelta(seconds=OTP_EXPIRY_SECONDS),
            last_sent_at=timezone.now(),
        )
        try:
            EmailService.send_otp(email, otp.otp_code, purpose)
        except Exception:
            logger.exception("Failed to send OTP email to %s", email)
            otp.delete()
            raise OTPServiceError(
                "Email delivery failed. Please try again.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return otp, {"cooldown_seconds": OTP_RESEND_COOLDOWN_SECONDS, "expires_in_seconds": OTP_EXPIRY_SECONDS}

    @classmethod
    def resend_otp(cls, email, purpose):
        purpose = cls.normalize_purpose(purpose)
        if purpose == OTPPurpose.REGISTER and UserService.find_by_identifier(email):
            raise OTPServiceError("Email is already registered.")
        return cls.send_otp(email, purpose, enforce_limits=True)

    @classmethod
    def verify_otp(cls, email, otp_code, purpose):
        purpose = cls.normalize_purpose(purpose)
        otp = OTP.objects.filter(
            email__iexact=email,
            otp_code=otp_code,
            purpose=purpose,
            is_used=False,
        ).order_by("-created_at").first()

        if not otp:
            active_otp = OTP.objects.filter(
                email__iexact=email,
                purpose=purpose,
                is_used=False,
            ).order_by("-created_at").first()
            if active_otp:
                active_otp.attempt_count += 1
                if active_otp.attempt_count >= OTP_MAX_VERIFY_ATTEMPTS:
                    active_otp.is_used = True
                    active_otp.save(update_fields=["attempt_count", "is_used"])
                else:
                    active_otp.save(update_fields=["attempt_count"])
            raise OTPServiceError("Invalid OTP.")

        if otp.expires_at < timezone.now():
            otp.is_used = True
            otp.save(update_fields=["is_used"])
            raise OTPServiceError("OTP expired.", metadata={"otpExpired": True, "requiresVerification": True, "email": email})

        otp.attempt_count = 0
        otp.save(update_fields=["attempt_count"])

        return otp

    @staticmethod
    def mark_used(otp):
        otp.is_used = True
        otp.save(update_fields=["is_used"])
