from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from backend.users.services.user_service import UserService
from backend.users.models import OTP, SocialAccount, UserProfile


User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthAPITests(APITestCase):
    def setUp(self):
        self.signup_payload = {
            "email": "runner@example.com",
            "username": "runner",
            "first_name": "Road",
            "last_name": "Runner",
            "password": "StrongPass1!",
            "password2": "StrongPass1!",
        }

    def signup(self):
        with patch("core.services.email_service.EmailService.send_otp"):
            return self.client.post("/api/v1/auth/signup/", self.signup_payload, format="json")

    def verified_user(self):
        response = self.signup()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        otp = OTP.objects.get(email=self.signup_payload["email"], purpose=OTP.PURPOSE_REGISTER)
        return self.client.post(
            "/api/v1/auth/verify-otp/",
            {"email": self.signup_payload["email"], "otp_code": otp.otp_code},
            format="json",
        )

    def test_signup_generates_registration_otp(self):
        response = self.signup()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["cooldown_seconds"], 60)
        self.assertTrue(OTP.objects.filter(email="runner@example.com", purpose=OTP.PURPOSE_REGISTER).exists())

    def test_verify_signup_otp_creates_user_and_jwt(self):
        response = self.verified_user()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="runner@example.com", is_email_verified=True)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertIn("access", response.data["data"]["tokens"])
        self.assertIn("refresh", response.data["data"]["tokens"])

    def test_user_create_signal_creates_profile(self):
        user = User.objects.create_user(
            email="signal@example.com",
            username="signal",
            password="StrongPass1!",
        )
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_login_returns_jwt_tokens(self):
        self.verified_user()
        response = self.client.post(
            "/api/v1/auth/login/",
            {"identifier": "runner@example.com", "password": "StrongPass1!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"]["tokens"])

    def test_jwt_authentication_fetches_profile(self):
        verified = self.verified_user()
        access = verified.data["data"]["tokens"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get("/api/v1/auth/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], "runner@example.com")
        self.assertIn("profile", response.data["data"])
        self.assertIn("age", response.data["data"]["profile"])

    def test_profile_patch_updates_user_and_profile_fields(self):
        verified = self.verified_user()
        access = verified.data["data"]["tokens"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        response = self.client.patch(
            "/api/v1/auth/profile/",
            {
                "phone_number": "9876543210",
                "date_of_birth": "2000-01-01",
                "gender": "Male",
                "blood_group": "O+",
                "height_cm": 175,
                "weight_kg": 70,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["phone_number"], "9876543210")
        self.assertEqual(response.data["data"]["profile"]["height_cm"], 175)
        self.assertEqual(response.data["data"]["profile"]["weight_kg"], 70)
        self.assertIsNotNone(response.data["data"]["profile"]["age"])

    def test_resend_otp_respects_cooldown(self):
        self.signup()
        response = self.client.post(
            "/api/v1/auth/resend-otp/",
            {"email": "runner@example.com", "purpose": OTP.PURPOSE_REGISTER},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertGreater(response.data["cooldown_seconds"], 0)

    def test_resend_otp_after_cooldown_invalidates_previous_otp(self):
        self.signup()
        OTP.objects.filter(email="runner@example.com").update(last_sent_at=timezone.now() - timedelta(seconds=61))
        with patch("core.services.email_service.EmailService.send_otp"):
            response = self.client.post(
                "/api/v1/auth/resend-otp/",
                {"email": "runner@example.com", "purpose": OTP.PURPOSE_REGISTER},
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(OTP.objects.filter(email="runner@example.com", is_used=False).count(), 1)
        self.assertEqual(response.data["data"]["cooldown_seconds"], 60)

    def test_otp_max_attempts_invalidates_otp(self):
        self.signup()
        otp = OTP.objects.get(email="runner@example.com", purpose=OTP.PURPOSE_REGISTER)
        for _ in range(5):
            self.client.post(
                "/api/v1/auth/verify-otp/",
                {"email": "runner@example.com", "otp_code": "000000"},
                format="json",
            )
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    def test_password_reset(self):
        self.verified_user()
        with patch("core.services.email_service.EmailService.send_otp"):
            response = self.client.post("/api/v1/auth/password-reset/", {"email": "runner@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["cooldown_seconds"], 60)
        self.assertEqual(response.data["data"]["expires_in_seconds"], 300)
        otp = OTP.objects.filter(email="runner@example.com", purpose=OTP.PURPOSE_PASSWORD_RESET).latest("created_at")
        response = self.client.post(
            "/api/v1/auth/password-reset/confirm/",
            {
                "email": "runner@example.com",
                "otp_code": otp.otp_code,
                "password": "NewStrong1!",
                "password2": "NewStrong1!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.get(email="runner@example.com").check_password("NewStrong1!"))
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    def test_password_reset_resend_respects_cooldown(self):
        self.verified_user()
        with patch("core.services.email_service.EmailService.send_otp"):
            self.client.post("/api/v1/auth/password-reset/", {"email": "runner@example.com"}, format="json")
        response = self.client.post(
            "/api/v1/auth/resend-otp/",
            {"email": "runner@example.com", "purpose": OTP.PURPOSE_PASSWORD_RESET},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertGreater(response.data["cooldown_seconds"], 0)

    def test_password_reset_resend_after_cooldown_invalidates_previous_otp(self):
        self.verified_user()
        with patch("core.services.email_service.EmailService.send_otp"):
            self.client.post("/api/v1/auth/password-reset/", {"email": "runner@example.com"}, format="json")
        OTP.objects.filter(email="runner@example.com", purpose=OTP.PURPOSE_PASSWORD_RESET).update(
            last_sent_at=timezone.now() - timedelta(seconds=61)
        )
        with patch("core.services.email_service.EmailService.send_otp") as send_otp:
            response = self.client.post(
                "/api/v1/auth/resend-otp/",
                {"email": "runner@example.com", "purpose": OTP.PURPOSE_PASSWORD_RESET},
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["cooldown_seconds"], 60)
        self.assertEqual(
            OTP.objects.filter(email="runner@example.com", purpose=OTP.PURPOSE_PASSWORD_RESET, is_used=False).count(),
            1,
        )
        send_otp.assert_called_once()

    def test_password_reset_rate_limit_allows_five_otps_per_hour(self):
        self.verified_user()
        with patch("core.services.email_service.EmailService.send_otp"):
            for _ in range(5):
                response = self.client.post(
                    "/api/v1/auth/password-reset/",
                    {"email": "runner@example.com"},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                OTP.objects.filter(email="runner@example.com", purpose=OTP.PURPOSE_PASSWORD_RESET).update(
                    last_sent_at=timezone.now() - timedelta(seconds=61)
                )

            response = self.client.post(
                "/api/v1/auth/password-reset/",
                {"email": "runner@example.com"},
                format="json",
            )
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.data["max_requests_per_hour"], 5)

    def test_password_reset_max_attempts_invalidates_otp(self):
        self.verified_user()
        with patch("core.services.email_service.EmailService.send_otp"):
            self.client.post("/api/v1/auth/password-reset/", {"email": "runner@example.com"}, format="json")
        otp = OTP.objects.filter(email="runner@example.com", purpose=OTP.PURPOSE_PASSWORD_RESET).latest("created_at")
        for _ in range(5):
            self.client.post(
                "/api/v1/auth/password-reset/confirm/",
                {
                    "email": "runner@example.com",
                    "otp_code": "000000",
                    "password": "NewStrong1!",
                    "password2": "NewStrong1!",
                },
                format="json",
            )
        otp.refresh_from_db()
        self.assertTrue(otp.is_used)

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="test-client")
    @patch("users.services.google_auth_service.id_token.verify_oauth2_token")
    def test_google_login(self, verify_google_token):
        verify_google_token.return_value = {
            "aud": "test-client",
            "email_verified": True,
            "email": "google@example.com",
            "sub": "google-123",
            "given_name": "Google",
            "family_name": "User",
            "name": "Google User",
            "picture": "https://example.com/p.png",
        }
        response = self.client.post("/api/v1/auth/google-login/", {"id_token": "token"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"]["tokens"])
        self.assertTrue(User.objects.get(email="google@example.com").is_email_verified)
        self.assertTrue(SocialAccount.objects.filter(provider="GOOGLE", provider_id="google-123").exists())

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="test-client")
    @patch("users.services.google_auth_service.id_token.verify_oauth2_token")
    def test_google_login_links_existing_local_account(self, verify_google_token):
        user = User.objects.create_user(
            email="local@example.com",
            username="local",
            password="StrongPass1!",
            is_email_verified=False,
        )
        UserProfile.objects.filter(user=user).delete()
        verify_google_token.return_value = {
            "aud": "test-client",
            "email_verified": True,
            "email": "local@example.com",
            "sub": "google-local-123",
            "given_name": "Local",
            "family_name": "User",
            "name": "Local User",
            "picture": "",
        }

        response = self.client.post("/api/v1/auth/google-login/", {"id_token": "token"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.filter(email="local@example.com").count(), 1)
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertTrue(SocialAccount.objects.filter(user=user, provider="GOOGLE", provider_id="google-local-123").exists())

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="test-client")
    @patch("users.services.google_auth_service.id_token.verify_oauth2_token")
    def test_google_login_reuses_legacy_lowercase_social_account(self, verify_google_token):
        user = User.objects.create_user(
            email="legacy@example.com",
            username="legacy",
            password="StrongPass1!",
            is_email_verified=True,
        )
        SocialAccount.objects.create(
            user=user,
            provider="google",
            provider_id="legacy-google-123",
            provider_email="legacy@example.com",
        )
        verify_google_token.return_value = {
            "aud": "test-client",
            "email_verified": True,
            "email": "legacy@example.com",
            "sub": "legacy-google-123",
            "given_name": "Legacy",
            "family_name": "User",
            "name": "Legacy User",
            "picture": "https://example.com/legacy.png",
        }

        response = self.client.post("/api/v1/auth/google-login/", {"id_token": "token"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SocialAccount.objects.filter(user=user).count(), 1)
        social = SocialAccount.objects.get(user=user)
        self.assertEqual(social.provider, "GOOGLE")
        self.assertEqual(social.provider_id, "legacy-google-123")

    def test_google_username_generation_uses_underscore_suffix(self):
        User.objects.create_user(email="john-owner@example.com", username="john", password="StrongPass1!")
        self.assertEqual(UserService.generate_unique_username("john@gmail.com"), "john_1")
