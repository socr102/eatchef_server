"""
All notifications and messages to the mail are called through signals
"""

from django.dispatch import receiver
import django.dispatch
from notifications.service import NotifyService

from utils import email

S_password_reset_code_created = django.dispatch.Signal()
S_new_password_created = django.dispatch.Signal()
S_email_activation_code_created = django.dispatch.Signal()
S_new_email_activation_code_created = django.dispatch.Signal()
S_new_user_email_activated = django.dispatch.Signal()


@receiver(S_new_user_email_activated)
def notify_new_user_greeting(sender, instance, **kwargs):
    NotifyService().create_notify_new_user_greeting(
        user=instance
    )
    email.send_new_user_greeting(
        [instance.email],
        user=instance
    )


@receiver(S_new_password_created)
def send_new_password(sender, instance, **kwargs):
    email.send_reset_password_message(
        [instance.email],
        new_password=kwargs['new_password']
    )


@receiver(S_password_reset_code_created)
def send_reset_password_code(sender, instance, **kwargs):
    # not used anymore
    email.send_reset_password_message(
        [instance.email],
        code=instance.reset_password_code
    )


@receiver(S_email_activation_code_created)
def send_email_activation_code(sender, instance, **kwargs):
    email.send_confirm_email(emails=[instance.email], code=instance.activation_email_code, user=instance)


@receiver(S_new_email_activation_code_created)
def send_new_email_activation_code(sender, instance, new_email, **kwargs):
    email.send_confirm_new_email(emails=[new_email], code=instance.activation_email_code)
