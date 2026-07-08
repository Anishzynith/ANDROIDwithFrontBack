from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0009_normalize_google_social_provider"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="distance_unit",
            field=models.CharField(
                choices=[("km", "Kilometers"), ("mile", "Miles")],
                default="km",
                max_length=4,
            ),
        ),
    ]
