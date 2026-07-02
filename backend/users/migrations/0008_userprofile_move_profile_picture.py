from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def copy_profile_pictures_to_profiles(apps, schema_editor):
    User = apps.get_model("users", "CustomUser")
    UserProfile = apps.get_model("users", "UserProfile")

    for user in User.objects.all().iterator():
        profile, _ = UserProfile.objects.get_or_create(user_id=user.pk)
        if getattr(user, "profile_picture", None) and not profile.profile_picture:
            profile.profile_picture = user.profile_picture
            profile.save(update_fields=["profile_picture", "updated_at"])


def copy_profile_pictures_to_users(apps, schema_editor):
    User = apps.get_model("users", "CustomUser")
    UserProfile = apps.get_model("users", "UserProfile")

    for profile in UserProfile.objects.exclude(profile_picture="").exclude(profile_picture__isnull=True).iterator():
        User.objects.filter(pk=profile.user_id).update(profile_picture=profile.profile_picture)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0007_alter_otp_purpose_alter_socialaccount_provider"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("profile_picture", models.ImageField(blank=True, null=True, upload_to=settings.USER_PROFILE_PICTURE_UPLOAD_TO)),
                ("date_of_birth", models.DateField(blank=True, null=True)),
                (
                    "gender",
                    models.CharField(
                        blank=True,
                        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")],
                        max_length=10,
                        null=True,
                    ),
                ),
                (
                    "blood_group",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("A+", "A+"),
                            ("A-", "A-"),
                            ("B+", "B+"),
                            ("B-", "B-"),
                            ("AB+", "AB+"),
                            ("AB-", "AB-"),
                            ("O+", "O+"),
                            ("O-", "O-"),
                        ],
                        max_length=3,
                        null=True,
                    ),
                ),
                ("height_cm", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("weight_kg", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.RunPython(copy_profile_pictures_to_profiles, copy_profile_pictures_to_users),
        migrations.RemoveField(
            model_name="customuser",
            name="profile_picture",
        ),
    ]
