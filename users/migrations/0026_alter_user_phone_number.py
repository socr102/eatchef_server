# Generated by Django 3.2.4 on 2021-08-27 11:18

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0025_user_email_activation_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=18, null=True, validators=[django.core.validators.RegexValidator(message='Enter the correct phone number', regex='^\\+([0-9]+)$')], verbose_name='Phone number'),
        ),
    ]