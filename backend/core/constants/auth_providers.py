from django.db import models


class AuthProvider(models.TextChoices):
    GOOGLE = "GOOGLE", "Google"

