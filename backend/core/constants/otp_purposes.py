from django.db import models


class OTPPurpose(models.TextChoices):
    REGISTER = "REGISTER", "Register"
    PASSWORD_RESET = "PASSWORD_RESET", "Password Reset"
    EMAIL_CHANGE = "EMAIL_CHANGE", "Email Change"
    LOGIN = "LOGIN", "Login"

