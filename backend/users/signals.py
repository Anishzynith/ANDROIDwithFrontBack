from django.conf import settings
from django.db.models.signals import post_save
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import UserProfile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


def _delete_profile_picture(file_field):
    if file_field and file_field.name and file_field.storage.exists(file_field.name):
        file_field.storage.delete(file_field.name)


@receiver(pre_save, sender=UserProfile)
def remember_replaced_profile_picture(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_profile_picture_name = None
        return

    try:
        old_picture = sender.objects.only("profile_picture").get(pk=instance.pk).profile_picture
    except sender.DoesNotExist:
        instance._old_profile_picture_name = None
        return

    old_name = old_picture.name
    new_name = instance.profile_picture.name
    instance._old_profile_picture_name = old_name if old_name and old_name != new_name else None


@receiver(post_save, sender=UserProfile)
def delete_replaced_profile_picture(sender, instance, **kwargs):
    old_name = getattr(instance, "_old_profile_picture_name", None)
    if old_name:
        instance.profile_picture.storage.delete(old_name)
        instance._old_profile_picture_name = None


@receiver(post_delete, sender=UserProfile)
def delete_profile_picture_on_profile_delete(sender, instance, **kwargs):
    _delete_profile_picture(instance.profile_picture)
