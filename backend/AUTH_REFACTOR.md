# Authentication Refactor Notes

## Folder Structure

Runtime app labels are preserved for backward-compatible migrations:

- `config/settings/base.py`, `development.py`, `production.py`, `testing.py`
- `core/services/email_service.py`
- `core/constants/`
- `core/utilities/responses.py`
- `users/services/auth_service.py`
- `users/services/otp_service.py`
- `users/services/user_service.py`
- `users/services/google_auth_service.py`
- `apps/` contains future domain package placeholders.

## Database Changes

- `CustomUser.is_admin` is removed.
- `CustomUser.role` is added with `ADMIN`, `USER`, and `COACH`.
- Existing `is_admin=True` users are migrated to `role="ADMIN"`.
- `PasswordResetOTP` and `RegistrationOTP` are migrated into the single `OTP` model.
- Signup draft data moves into `PendingRegistration`.
- `SocialAccount.extra_data` is removed. Only `provider`, `provider_id`, `provider_email`, `name`, and `picture_url` are stored.
- Indexes were added for user, OTP, and social account lookup fields.

## API Routes

New versioned routes:

- `POST /api/v1/auth/signup/`
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/verify-otp/`
- `POST /api/v1/auth/resend-otp/`
- `POST /api/v1/auth/google-login/`
- `POST /api/v1/auth/password-reset/`
- `POST /api/v1/auth/password-reset/confirm/`
- `POST /api/v1/auth/token/refresh/`
- `GET /api/v1/auth/profile/`
- `POST /api/v1/auth/logout/`

Backward-compatible `/api/users/auth/...` routes remain available.

## OTP Rules

- Expires after 5 minutes.
- Resend cooldown is 60 seconds.
- Maximum 5 OTP requests per hour per email and purpose.
- Maximum 5 verification attempts per active OTP.
- Resending invalidates previous active OTPs for the same email and purpose.

## Response Format

Success:

```json
{"success": true, "message": "Operation successful", "data": {}}
```

Failure:

```json
{"success": false, "message": "OTP expired", "errors": {}}
```

Legacy top-level fields like `token`, `user`, `requiresVerification`, and `cooldown_seconds` are still returned where useful for compatibility.

## JWT

DRF token authentication has been replaced with SimpleJWT:

- Access tokens are sent as `Authorization: Bearer <access>`.
- Refresh tokens are used at `/api/v1/auth/token/refresh/`.
- Logout blacklists refresh tokens when supplied.

## Migration Notes

Run:

```bash
python manage.py migrate
```

The migration `users.0006_auth_hardening` preserves existing admin roles and OTP data.

