from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def migrate_auth_data(apps, schema_editor):
    User = apps.get_model("users", "CustomUser")
    OTP = apps.get_model("users", "OTP")
    PendingRegistration = apps.get_model("users", "PendingRegistration")
    PasswordResetOTP = apps.get_model("users", "PasswordResetOTP")
    RegistrationOTP = apps.get_model("users", "RegistrationOTP")

    User.objects.filter(is_admin=True).update(role="ADMIN")

    for old in PasswordResetOTP.objects.all().iterator():
        new_otp = OTP.objects.create(
            email=old.email,
            otp_code=old.otp_code,
            purpose="PASSWORD_RESET",
            is_used=old.is_used,
            expires_at=old.expires_at,
            attempt_count=0,
            last_sent_at=old.created_at,
        )
        OTP.objects.filter(pk=new_otp.pk).update(created_at=old.created_at)

    for old in RegistrationOTP.objects.all().iterator():
        PendingRegistration.objects.update_or_create(
            email=old.email,
            defaults={
                "username": old.username,
                "password_hash": old.password_hash,
                "first_name": old.first_name,
                "last_name": old.last_name,
            },
        )
        new_otp = OTP.objects.create(
            email=old.email,
            otp_code=old.otp_code,
            purpose="REGISTER",
            is_used=old.is_used,
            expires_at=old.expires_at,
            attempt_count=0,
            last_sent_at=old.created_at,
        )
        OTP.objects.filter(pk=new_otp.pk).update(created_at=old.created_at)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_customuser_is_admin"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="role",
            field=models.CharField(
                choices=[("ADMIN", "Admin"), ("USER", "User"), ("COACH", "Coach")],
                db_index=True,
                default="USER",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="OTP",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254)),
                ("otp_code", models.CharField(max_length=6)),
                (
                    "purpose",
                    models.CharField(
                        choices=[
                            ("REGISTER", "Register"),
                            ("PASSWORD_RESET", "Password reset"),
                            ("EMAIL_CHANGE", "Email change"),
                            ("LOGIN", "Login"),
                        ],
                        max_length=20,
                    ),
                ),
                ("is_used", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
                ("attempt_count", models.PositiveSmallIntegerField(default=0)),
                ("last_sent_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PendingRegistration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("username", models.CharField(max_length=150)),
                ("password_hash", models.CharField(max_length=128)),
                ("first_name", models.CharField(blank=True, max_length=150)),
                ("last_name", models.CharField(blank=True, max_length=150)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddField(
            model_name="socialaccount",
            name="name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="socialaccount",
            name="picture_url",
            field=models.URLField(blank=True),
        ),
        migrations.RunPython(migrate_auth_data, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="customuser",
            name="is_admin",
        ),
        migrations.RemoveField(
            model_name="socialaccount",
            name="extra_data",
        ),
        migrations.DeleteModel(
            name="PasswordResetOTP",
        ),
        migrations.DeleteModel(
            name="RegistrationOTP",
        ),
        migrations.AddIndex(
            model_name="customuser",
            index=models.Index(fields=["email"], name="users_custo_email_c80f75_idx"),
        ),
        migrations.AddIndex(
            model_name="customuser",
            index=models.Index(fields=["username"], name="users_custo_usernam_a8ad03_idx"),
        ),
        migrations.AddIndex(
            model_name="customuser",
            index=models.Index(fields=["role"], name="users_custo_role_6a37b1_idx"),
        ),
        migrations.AddIndex(
            model_name="otp",
            index=models.Index(fields=["email"], name="users_otp_email_fb3550_idx"),
        ),
        migrations.AddIndex(
            model_name="otp",
            index=models.Index(fields=["otp_code"], name="users_otp_otp_cod_06fd51_idx"),
        ),
        migrations.AddIndex(
            model_name="otp",
            index=models.Index(fields=["purpose"], name="users_otp_purpose_1a0278_idx"),
        ),
        migrations.AddIndex(
            model_name="otp",
            index=models.Index(fields=["expires_at"], name="users_otp_expires_8f43b7_idx"),
        ),
        migrations.AddIndex(
            model_name="otp",
            index=models.Index(fields=["email", "purpose", "is_used"], name="users_otp_email_a5d88f_idx"),
        ),
        migrations.AddIndex(
            model_name="socialaccount",
            index=models.Index(fields=["provider_id"], name="users_socia_provide_7c3bbf_idx"),
        ),
        migrations.AddIndex(
            model_name="socialaccount",
            index=models.Index(fields=["provider_email"], name="users_socia_provide_8bdcc5_idx"),
        ),
    ]
