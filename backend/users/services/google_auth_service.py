from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import status

from backend.core.constants import AuthProvider
from backend.users.models import SocialAccount, UserProfile
from .auth_service import AuthService, AuthServiceError
from .user_service import UserService


User = get_user_model()


class GoogleAuthService:
    @classmethod
    def authenticate(cls, id_token_value):
        try:
            user_info = id_token.verify_oauth2_token(
                id_token_value,
                requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID,
            )
        except Exception as exc:
            raise AuthServiceError(str(exc), status.HTTP_401_UNAUTHORIZED)

        if user_info.get("aud") != settings.GOOGLE_OAUTH_CLIENT_ID:
            raise AuthServiceError("Invalid Google token audience.", status.HTTP_401_UNAUTHORIZED)

        email = (user_info.get("email") or "").strip().lower()
        provider_id = user_info.get("sub")
        if not email or not provider_id:
            raise AuthServiceError("Invalid Google account data.", status.HTTP_401_UNAUTHORIZED)

        if user_info.get("email_verified") is False:
            raise AuthServiceError("Google email is not verified.", status.HTTP_401_UNAUTHORIZED)

        with transaction.atomic():
            user = cls._get_or_create_user(email, user_info)
            cls._ensure_social_account(user, provider_id, email, user_info)
            UserProfile.objects.get_or_create(user=user)

        return AuthService.auth_payload(user)

    @staticmethod
    def _get_or_create_user(email, user_info):
        user = User.objects.filter(email__iexact=email).first()
        if user:
            update_fields = []
            if not user.is_email_verified:
                user.is_email_verified = True
                update_fields.append("is_email_verified")
            if update_fields:
                user.save(update_fields=update_fields)
            return user

        user = User(
            email=email,
            username=UserService.generate_unique_username(email),
            first_name=user_info.get("given_name", ""),
            last_name=user_info.get("family_name", ""),
            is_email_verified=True,
        )
        user.set_unusable_password()
        user.save()
        return user

    @staticmethod
    def _ensure_social_account(user, provider_id, email, user_info):
        defaults = {
            "provider": AuthProvider.GOOGLE,
            "provider_id": provider_id,
            "provider_email": email,
            "name": user_info.get("name", ""),
            "picture_url": user_info.get("picture", ""),
        }

        social = (
            SocialAccount.objects.select_related("user")
            .filter(provider_id=provider_id, provider__iexact=AuthProvider.GOOGLE)
            .first()
        )
        if social and social.user_id != user.id:
            raise AuthServiceError("This Google account is already linked to another user.", status.HTTP_409_CONFLICT)

        if not social:
            social = SocialAccount.objects.filter(user=user).first()

        if social:
            for field, value in defaults.items():
                setattr(social, field, value)
            social.user = user
            social.save(update_fields=[*defaults.keys(), "user"])
            return social

        return SocialAccount.objects.create(user=user, **defaults)
