import django
from django.db.models.signals import post_save
from django.dispatch import receiver

from chef_pencils.models import ChefPencilRecord
from notifications.service import NotifyService
from utils.email import (
    send_chef_pencils_record_created_email,
    send_chef_pencils_record_review_result_email
)

S_new_chef_recipe_record_created = django.dispatch.Signal()


@receiver(post_save, sender=ChefPencilRecord)
def notify_about_chef_pencil_record_change(sender, instance, created, **kwargs):
    if not created:
        if "status" in kwargs.get('update_fields', []) and instance.status in [
            ChefPencilRecord.Status.APPROVED,
            ChefPencilRecord.Status.REJECTED,
        ]:
            NotifyService().create_notify_chef_pencil_record_status_changed(
                user=instance.user,
                chef_pencil_record=instance
            )
            send_chef_pencils_record_review_result_email(
                [instance.user.email],
                user=instance.user,
                chef_pencil_record=instance
            )


@receiver(S_new_chef_recipe_record_created)
def notify_about_chef_pencil_record_creation(sender, instance, **kwargs):
    NotifyService().create_notify_chef_pencil_record_created(
        user=instance.user,
        chef_pencil_record=instance
    )
    send_chef_pencils_record_created_email(
        [instance.user.email],
        user=instance.user,
        chef_pencil_record=instance
    )
