# Generated by Django 3.2.4 on 2021-08-27 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0045_auto_20210827_1016'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='caption',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='caption'),
        ),
        migrations.AddField(
            model_name='recipe',
            name='language',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='language'),
        ),
    ]