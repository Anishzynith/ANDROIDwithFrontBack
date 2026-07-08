from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0014_remove_userprofile_height_unit_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="pendingregistration",
            name="height_cm",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name="pendingregistration",
            name="weight_kg",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name="pendingregistration",
            name="distance_unit",
            field=models.CharField(
                blank=True,
                choices=[("km", "Kilometers"), ("mile", "Miles")],
                default="km",
                max_length=4,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="userprofile",
            name="distance_unit",
            field=models.CharField(
                blank=True,
                choices=[("km", "Kilometers"), ("mile", "Miles")],
                default="km",
                max_length=4,
                null=True,
            ),
        ),
    ]
