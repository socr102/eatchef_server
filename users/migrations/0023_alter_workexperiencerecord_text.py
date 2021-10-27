# Generated by Django 3.2.4 on 2021-08-17 16:06

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_auto_20210817_1604'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workexperiencerecord',
            name='text',
            field=models.CharField(max_length=255, null=True, validators=[django.core.validators.MinLengthValidator(5)], verbose_name='Text'),
        ),
    ]
