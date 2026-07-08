from django.contrib import admin
from .models import CustomUser, OTP, PendingRegistration, SocialAccount, UserProfile


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'phone_number', 'role', 'is_email_verified', 'created_at')
    list_filter = ('role', 'is_email_verified', 'is_phone_verified', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone_number')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'blood_group', 'height_cm','weight_kg','distance_unit', 'updated_at')
    list_filter = ('gender', 'blood_group', 'created_at')
    search_fields = ('user__email', 'user__username', 'user__phone_number')


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'purpose', 'is_used', 'attempt_count', 'expires_at', 'created_at')
    list_filter = ('purpose', 'is_used', 'created_at')
    search_fields = ('email', 'otp_code')


@admin.register(PendingRegistration)
class PendingRegistrationAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'phone_number', 'created_at', 'updated_at')
    search_fields = ('email', 'username', 'phone_number')


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'provider_email', 'created_at')
    list_filter = ('provider', 'created_at')
    search_fields = ('user__email', 'provider_email')
