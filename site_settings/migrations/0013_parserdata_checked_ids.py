# Generated by Django 3.2.4 on 2021-08-13 09:20

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('site_settings', '0012_auto_20210812_1300'),
    ]

    operations = [
        migrations.AddField(
            model_name='parserdata',
            name='checked_ids',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, null=True, size=None, verbose_name='Checked ids'),
        ),
    ]
