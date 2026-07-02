from core.constants import OTPPurpose


LEGACY_OTP_PURPOSE_MAP = {
    "registration": OTPPurpose.REGISTER,
    "register": OTPPurpose.REGISTER,
    "password_reset": OTPPurpose.PASSWORD_RESET,
}


def normalize_otp_purpose(value):
    purpose = str(value or "").strip()
    if purpose in OTPPurpose.values:
        return purpose
    return LEGACY_OTP_PURPOSE_MAP.get(purpose.lower())


def accepted_otp_purpose_values():
    return ", ".join(OTPPurpose.values)
