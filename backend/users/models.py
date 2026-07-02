from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from backend.core.constants import AuthProvider, OTPPurpose, UserRole


# ---------------------- Base User ----------------------
class CustomUser(AbstractUser):
    ROLE_ADMIN = UserRole.ADMIN
    ROLE_USER = UserRole.USER
    ROLE_COACH = UserRole.COACH

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=settings.USER_PHONE_MAX_LENGTH, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.USER, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    class Meta:
        ordering = settings.USER_DEFAULT_ORDERING
        verbose_name_plural = settings.USER_VERBOSE_NAME_PLURAL
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["username"]),
            models.Index(fields=["role"]),
        ]


# ---------------------- User Profile ----------------------
class UserProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = "Male", "Male"
        FEMALE = "Female", "Female"
        OTHER = "Other", "Other"

    class BloodGroup(models.TextChoices):
        A_POSITIVE = "A+", "A+"
        A_NEGATIVE = "A-", "A-"
        B_POSITIVE = "B+", "B+"
        B_NEGATIVE = "B-", "B-"
        AB_POSITIVE = "AB+", "AB+"
        AB_NEGATIVE = "AB-", "AB-"
        O_POSITIVE = "O+", "O+"
        O_NEGATIVE = "O-", "O-"

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    profile_picture = models.ImageField(upload_to=settings.USER_PROFILE_PICTURE_UPLOAD_TO, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, null=True)
    blood_group = models.CharField(max_length=3, choices=BloodGroup.choices, blank=True, null=True)
    height_cm = models.PositiveSmallIntegerField(blank=True, null=True)
    weight_kg = models.PositiveSmallIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        from django.utils import timezone

        today = timezone.localdate()
        years = today.year - self.date_of_birth.year
        birthday_passed = (today.month, today.day) >= (self.date_of_birth.month, self.date_of_birth.day)
        return years if birthday_passed else years - 1

    def __str__(self):
        return f"{self.user.email} profile"

    class Meta:
        ordering = settings.USER_DEFAULT_ORDERING


# ---------------------- OTP ----------------------
class OTP(models.Model):
    PURPOSE_REGISTER = OTPPurpose.REGISTER
    PURPOSE_PASSWORD_RESET = OTPPurpose.PASSWORD_RESET
    PURPOSE_EMAIL_CHANGE = OTPPurpose.EMAIL_CHANGE
    PURPOSE_LOGIN = OTPPurpose.LOGIN

    email = models.EmailField()
    otp_code = models.CharField(max_length=settings.OTP_CODE_LENGTH)
    purpose = models.CharField(
        max_length=20,
        choices=OTPPurpose.choices,
    )
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempt_count = models.PositiveSmallIntegerField(default=0)
    last_sent_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f'{self.email} - {self.purpose} - {self.otp_code} ({"used" if self.is_used else "pending"})'

    class Meta:
        ordering = settings.USER_DEFAULT_ORDERING
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["otp_code"]),
            models.Index(fields=["purpose"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["email", "purpose", "is_used"]),
        ]


class PendingRegistration(models.Model):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=settings.USER_NAME_MAX_LENGTH)
    password_hash = models.CharField(max_length=settings.USER_PASSWORD_HASH_MAX_LENGTH)
    first_name = models.CharField(max_length=settings.USER_NAME_MAX_LENGTH, blank=True)
    last_name = models.CharField(max_length=settings.USER_NAME_MAX_LENGTH, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = settings.USER_DEFAULT_ORDERING


# ---------------------- Social Account ----------------------
class SocialAccount(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='social_account')
    provider = models.CharField(max_length=settings.SOCIAL_PROVIDER_MAX_LENGTH, choices=AuthProvider.choices)
    provider_id = models.CharField(max_length=settings.SOCIAL_PROVIDER_ID_MAX_LENGTH)
    provider_email = models.EmailField()
    name = models.CharField(max_length=settings.USER_NAME_MAX_LENGTH, blank=True)
    picture_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.user.email} - {self.provider}'
    
    class Meta:
        unique_together = ('provider', 'provider_id')
        indexes = [
            models.Index(fields=["provider_id"]),
            models.Index(fields=["provider_email"]),
        ]
