from django.db import migrations


def normalize_google_provider(apps, schema_editor):
    SocialAccount = apps.get_model("users", "SocialAccount")

    for legacy in SocialAccount.objects.filter(provider__iexact="google").exclude(provider="GOOGLE").iterator():
        canonical = SocialAccount.objects.filter(provider="GOOGLE", provider_id=legacy.provider_id).first()
        if canonical:
            if not canonical.provider_email and legacy.provider_email:
                canonical.provider_email = legacy.provider_email
            if not canonical.name and legacy.name:
                canonical.name = legacy.name
            if not canonical.picture_url and legacy.picture_url:
                canonical.picture_url = legacy.picture_url
            canonical.save()
            legacy.delete()
            continue

        legacy.provider = "GOOGLE"
        legacy.save(update_fields=["provider"])


def restore_google_provider(apps, schema_editor):
    SocialAccount = apps.get_model("users", "SocialAccount")
    SocialAccount.objects.filter(provider="GOOGLE").update(provider="google")


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0008_userprofile_move_profile_picture"),
    ]

    operations = [
        migrations.RunPython(normalize_google_provider, restore_google_provider),
    ]
