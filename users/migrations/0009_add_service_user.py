# Generated by Django 3.2.4 on 2021-07-09 08:32

from django.db import migrations
from django.conf import settings

from users.enums import UserTypes


def forwards_func(apps, schema_editor):
    """
    This migration will add service User to hold recipes from API
    """

    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    User = apps.get_model("users", "User")
    db_alias = schema_editor.connection.alias

    user = User.objects.using(db_alias).create(
        email='noreply@eatchef.com',
        full_name=settings.EATCHEFS_ACCOUNT_NAME,
        password='12345678',
        is_staff=True,
        user_type=UserTypes.HOME_CHEF.value
    )


def reverse_func(apps, schema_editor):
    """
    Delete service user
    """

    User = apps.get_model("users", "User")
    db_alias = schema_editor.connection.alias

    try:
        user = User.objects.using(db_alias).get(
            full_name=settings.EATCHEFS_ACCOUNT_NAME,
            is_staff=True
        ).delete()
    except Exception:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_alter_user_avatar'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]

