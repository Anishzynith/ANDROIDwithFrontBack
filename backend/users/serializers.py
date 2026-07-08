import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from config.settings import base
from core.compatibility.legacy_otp_mapping import accepted_otp_purpose_values, normalize_otp_purpose
from users.models import UserProfile
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

User = get_user_model()
PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{6,14}$')
PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$')
NAME_PATTERN = re.compile(r'^[A-Za-z]+(?: [A-Za-z]+)*$')
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
    value = value.strip()
    if value and not NAME_PATTERN.match(value):
        raise serializers.ValidationError(f'{field_name} can contain only letters.')
    return value


def validate_profile_picture_file(value):
    if value.size > 2 * 1024 * 1024:   # 2 MB
        raise serializers.ValidationError("Image size exceeds 2 MB.")
    ext = value.name.split('.')[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'gif']:
        raise serializers.ValidationError("Only JPG, PNG, and GIF are allowed.")
    return value


class CustomUserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    auth_provider = serializers.SerializerMethodField()
    password_setup_required = serializers.SerializerMethodField()
    profile_picture = serializers.ImageField(required=False, allow_null=True, write_only=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True, write_only=True)
    gender = serializers.ChoiceField(choices=UserProfile.Gender.choices, required=False, allow_null=True, allow_blank=True, write_only=True)
    blood_group = serializers.ChoiceField(choices=UserProfile.BloodGroup.choices, required=False, allow_null=True, allow_blank=True, write_only=True)
    height_cm = serializers.DecimalField(
        required=False,
        allow_null=True,
        min_value=0,
        max_value=250,
        max_digits=5,
        decimal_places=2,
        coerce_to_string=False,
        write_only=True,
    )
    weight_kg = serializers.DecimalField(
        required=False,
        allow_null=True,
        min_value=0,
        max_value=300,
        max_digits=5,
        decimal_places=2,
        coerce_to_string=False,
        write_only=True,
    )
    distance_unit = serializers.ChoiceField(choices=UserProfile.DistanceUnit.choices, required=False, write_only=True)

    def _normalize_decimal(self, value, places=2):
        if value is None:
            return None
        # Convert floats to Decimal safely via string to avoid binary float issues
        if isinstance(value, float):
            value = str(value)
        d = Decimal(value)
        quant = Decimal('1.' + '0' * places) if places == 0 else Decimal((0, (1,), -places))
        # Use ROUND_HALF_UP for more intuitive rounding
        return d.quantize(Decimal('0.' + '0'*(places-1) + '1') if places > 0 else Decimal('1'), rounding=ROUND_HALF_UP)

    def validate_height_cm(self, value):
        return self._normalize_decimal(value, places=2)

    def validate_weight_kg(self, value):
        return self._normalize_decimal(value, places=2)

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
            'auth_provider',
            'password_setup_required',
            'created_at',
            'updated_at',
            'profile',
            'profile_picture',
            'date_of_birth',
            'gender',
            'blood_group',
            'height_cm',
            'weight_kg',
            'distance_unit',
        )
        read_only_fields = (
            'id',
            'email',
            'created_at',
            'updated_at',
            'is_email_verified',
            'is_phone_verified',
            'role',
            'auth_provider',
            'password_setup_required',
            'profile',
        )
    def validate_date_of_birth(self, value):
        if value and value > date.today():
            raise serializers.ValidationError(
                "Date of birth cannot be in the future."
            )
        return value
    

    def validate_phone_number(self, value):
        if not value:
            return None

        value = value.strip()

        if not PHONE_PATTERN.match(value):
            raise serializers.ValidationError(
                "Enter a valid phone number."
            )

        return value

    def validate_first_name(self, value):
        return validate_name(value, 'First name')

    def validate_last_name(self, value):
        return validate_name(value, 'Last name')

    def validate_profile_picture(self, value):
        if value is None:
            return value
        return validate_profile_picture_file(value)

    def get_profile(self, obj):
        profile, _ = UserProfile.objects.get_or_create(user=obj)
        return UserProfileSerializer(profile, context=self.context).data

    def get_auth_provider(self, obj):
        social_account = getattr(obj, 'social_account', None)
        return getattr(social_account, 'provider', 'manual')

    def get_password_setup_required(self, obj):
        return not obj.has_usable_password()

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
                'distance_unit',
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
    profile_picture_url = serializers.SerializerMethodField()
    height_cm = serializers.DecimalField(max_digits=5, decimal_places=2, coerce_to_string=False, allow_null=True)
    weight_kg = serializers.DecimalField(max_digits=5, decimal_places=2, coerce_to_string=False, allow_null=True)

    class Meta:
        model = UserProfile
        fields = (
            'profile_picture',
            'profile_picture_url',
            'date_of_birth',
            'age',
            'gender',
            'blood_group',
            'height_cm',
            'weight_kg',
            'distance_unit',
        )
        read_only_fields = ('age',)

    def get_profile_picture_url(self, obj):
        request = self.context.get('request')
        if obj.profile_picture:
            url = obj.profile_picture.url
            return request.build_absolute_uri(url) if request else url

        social_account = getattr(obj.user, 'social_account', None)
        return getattr(social_account, 'picture_url', '') or ''

    def to_internal_value(self, data):
        # Ensure numeric inputs are normalized to avoid float precision issues
        if 'height_cm' in data and data.get('height_cm') is not None:
            try:
                data['height_cm'] = str(data['height_cm']) if isinstance(data['height_cm'], float) else data['height_cm']
            except Exception:
                pass
        if 'weight_kg' in data and data.get('weight_kg') is not None:
            try:
                data['weight_kg'] = str(data['weight_kg']) if isinstance(data['weight_kg'], float) else data['weight_kg']
            except Exception:
                pass
        return super().to_internal_value(data)


class UserSignUpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_email(self, value):
        value = value.strip().lower()
        domain = value.rsplit('@', 1)[-1].lower()

        if not domain:
            raise serializers.ValidationError('Enter a valid email address.')

        allowed_domains = [item.strip().lower() for item in getattr(base, 'ALLOWED_EMAIL_DOMAINS', []) if item.strip()]
        enforce_domain_check = getattr(base, 'ENFORCE_EMAIL_DOMAIN', False)
        if enforce_domain_check and allowed_domains and domain not in allowed_domains:
            allowed_domains_display = ', '.join(allowed_domains)
            raise serializers.ValidationError(
                f'Email domain must be one of: {allowed_domains_display}.'
            )

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Email is already registered.')
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Username already exists. Please choose another username.')
        return value

    def validate_first_name(self, value):
        value = validate_name(value, 'First name')
        if value and len(value) < 2:
            raise serializers.ValidationError(
                'First name must contain at least 2 characters.')
        return value

    def validate_profile_picture(self, value):
        return validate_profile_picture_file(value)

    def validate_last_name(self, value):
        return validate_name(value, 'Last name')

    

    def validate_phone_number(self, value):
        if not value:
            return None

        value = value.strip()

        if not PHONE_PATTERN.match(value):
            raise serializers.ValidationError("Enter a valid phone number.")

        return value

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
    def get_profile(self, obj):
        profile, _ = UserProfile.objects.get_or_create(user=obj)

        print(UserProfileSerializer(profile).data)

        return UserProfileSerializer(profile, context=self.context).data

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
            raise serializers.ValidationError({
                'password': 'Passwords do not match.'
            })
        try:
            user = User.objects.get(email__iexact=data['email'])

            # Prevent using current password
            if check_password(data['password'], user.password):
                raise serializers.ValidationError({
                    'password': 'New password cannot be the same as your current password.'
                })
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'email': 'User not found.'
            })
        return data


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'})
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_password(self, value):
        return validate_password_strength(value)

    def validate(self, data):
        user = self.context['request'].user
        current_password = data.get('current_password', '')

        if data['password'] != data['password2']:
            raise serializers.ValidationError({
                'password': 'Passwords do not match.'
            })

        if user.has_usable_password():
            if not current_password:
                raise serializers.ValidationError({
                    'current_password': 'Current password is required.'
                })
            if not user.check_password(current_password):
                raise serializers.ValidationError({
                    'current_password': 'Current password is incorrect.'
                })
            if check_password(data['password'], user.password):
                raise serializers.ValidationError({
                    'password': 'New password cannot be the same as your current password.'
                })

        return data
