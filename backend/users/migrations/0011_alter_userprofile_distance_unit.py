from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0010_userprofile_distance_unit"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="distance_unit",
            field=models.CharField(
                choices=[("km", "Kilometers"),("mile", "Miles")],
                default="km",
                max_length=4,
            ),
        ),
    ]
