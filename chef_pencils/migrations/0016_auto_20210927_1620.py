# Generated by Django 3.2.4 on 2021-09-27 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chef_pencils', '0015_savedchefpencilrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='chefpencilrecord',
            name='likes_number',
            field=models.PositiveSmallIntegerField(default=0, null=True, verbose_name='Likes'),
        ),
        migrations.AddField(
            model_name='chefpencilrecord',
            name='views_number',
            field=models.PositiveSmallIntegerField(default=0, null=True, verbose_name='Views'),
        ),
    ]
