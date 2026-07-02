import re

from rest_framework import serializers
from django.contrib.auth import get_user_model

from backend.config.settings import base
from backend.core.compatibility.legacy_otp_mapping import accepted_otp_purpose_values, normalize_otp_purpose
from backend.users.models import UserProfile

User = get_user_model()
PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$')
NAME_PATTERN = re.compile(r'^[A-Za-z\s]+$')
PASSWORD_ERROR = (
    'Password must contain:\n'
    '- Minimum 8 characters\n'
    '- One uppercase letter\n'
    '- One lowercase letter\n'
    '- One number\n'
    '- One special character'
)


def validate_password_strength(password):
    if not PASSWORD_PATTERN.match(password):
        raise serializers.ValidationError(PASSWORD_ERROR)
    return password


def validate_name(value, field_name):
    if value and not NAME_PATTERN.match(value):
        raise serializers.ValidationError(f'{field_name} can contain only letters and spaces.')
    return value


class CustomUserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    profile_picture = serializers.ImageField(required=False, allow_null=True, write_only=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True, write_only=True)
    gender = serializers.ChoiceField(choices=UserProfile.Gender.choices, required=False, allow_null=True, allow_blank=True, write_only=True)
    blood_group = serializers.ChoiceField(choices=UserProfile.BloodGroup.choices, required=False, allow_null=True, allow_blank=True, write_only=True)
    height_cm = serializers.IntegerField(required=False, allow_null=True, min_value=0, write_only=True)
    weight_kg = serializers.IntegerField(required=False, allow_null=True, min_value=0, write_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'phone_number',
            'is_email_verified',
            'is_phone_verified',
            'role',
            'created_at',
            'updated_at',
            'profile',
            'profile_picture',
            'date_of_birth',
            'gender',
            'blood_group',
            'height_cm',
            'weight_kg',
        )
        read_only_fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'created_at',
            'updated_at',
            'is_email_verified',
            'is_phone_verified',
            'role',
            'profile',
        )

    def get_profile(self, obj):
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return UserProfileSerializer(profile, context=self.context).data

    def update(self, instance, validated_data):
        profile_fields = {
            field: validated_data.pop(field)
            for field in (
                'profile_picture',
                'date_of_birth',
                'gender',
                'blood_group',
                'height_cm',
                'weight_kg',
            )
            if field in validated_data
        }

        instance = super().update(instance, validated_data)

        if profile_fields:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            for field, value in profile_fields.items():
                setattr(profile, field, value)
            profile.save(update_fields=[*profile_fields.keys(), 'updated_at'])

        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            'profile_picture',
            'date_of_birth',
            'age',
            'gender',
            'blood_group',
            'height_cm',
            'weight_kg',
        )
        read_only_fields = ('age',)


class UserSignUpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)

    def validate_email(self, value):
        domain = value.rsplit('@', 1)[-1].lower()
        if domain not in base.ALLOWED_EMAIL_DOMAINS:
            allowed_domains = ', '.join(base.ALLOWED_EMAIL_DOMAINS)
            raise serializers.ValidationError(
                f'Email domain must be one of: {allowed_domains}.'
            )
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Email is already registered.')
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Username already exists. Please choose another username.')
        return value

    def validate_first_name(self, value):
        return validate_name(value, 'First name')

    def validate_last_name(self, value):
        return validate_name(value, 'Last name')

    def validate_password(self, value):
        return validate_password_strength(value)

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class RegistrationOTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    purpose = serializers.CharField(
        help_text=f"Must be one of: {accepted_otp_purpose_values()}"
    )

    def validate_purpose(self, value):
        purpose = normalize_otp_purpose(value)
        if not purpose:
            raise serializers.ValidationError(
                f"Must be one of: {accepted_otp_purpose_values()}"
            )
        return purpose


class UserSignInSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        identifier = data.get('identifier') or data.get('email') or data.get('username')
        if not identifier:
            raise serializers.ValidationError({'identifier': 'Enter your username or email.'})
        data['identifier'] = identifier.strip()
        return data


class GoogleOAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_password(self, value):
        return validate_password_strength(value)

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return data
