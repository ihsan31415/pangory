from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import UserProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler to create a user profile when a user is created or update it when a user is updated
    """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Ensure profile exists even if user was created before this signal was connected
        UserProfile.objects.get_or_create(user=instance) 