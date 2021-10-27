import os

from django.dispatch import receiver
from django.db.models.signals import post_save
import django

from notifications.service import NotifyService

from recipe.models import Recipe

from utils.email import send_recipe_review_result_email, send_recipe_created_email

S_new_recipe_created = django.dispatch.Signal()


@receiver(post_save, sender=Recipe)
def notify_about_recipe_change(sender, instance, created, **kwargs):
    if not created:
        if "status" in kwargs["update_fields"] and instance.status in [
            Recipe.Status.ACCEPTED,
            Recipe.Status.REJECTED,
        ]:
            NotifyService().create_notify_recipe_status_changed(
                user=instance.user, recipe=instance
            )
            send_recipe_review_result_email(
                [instance.user.email], user=instance.user, recipe=instance
            )


@receiver(S_new_recipe_created)
def notify_about_recipe_creation(sender, instance, **kwargs):
    NotifyService().create_notify_recipe_created(user=instance.user, recipe=instance)
    send_recipe_created_email(
        [instance.user.email], user=instance.user, recipe=instance
    )
