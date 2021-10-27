# Generated by Django 3.2.4 on 2021-08-04 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0036_alter_savedrecipe_recipe'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='likes_number',
            field=models.PositiveSmallIntegerField(default=0, null=True, verbose_name='Likes'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='views_number',
            field=models.PositiveSmallIntegerField(default=0, null=True, verbose_name='Views'),
        ),
    ]