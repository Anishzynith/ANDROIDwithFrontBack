OTP_EXPIRY_SECONDS = 300
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_REQUESTS_PER_HOUR = 5
OTP_MAX_VERIFY_ATTEMPTS = 5

from .auth_providers import AuthProvider
from .otp_purposes import OTPPurpose
from .user_roles import UserRole

__all__ = [
    "AuthProvider",
    "OTPPurpose",
    "UserRole",
    "OTP_EXPIRY_SECONDS",
    "OTP_MAX_REQUESTS_PER_HOUR",
    "OTP_MAX_VERIFY_ATTEMPTS",
    "OTP_RESEND_COOLDOWN_SECONDS",
]
