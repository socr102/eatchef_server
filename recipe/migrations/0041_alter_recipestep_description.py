# Generated by Django 3.2.4 on 2021-08-23 09:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0040_auto_20210820_1422'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipestep',
            name='description',
            field=models.TextField(max_length=300),
        ),
    ]
