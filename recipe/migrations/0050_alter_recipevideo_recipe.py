# Generated by Django 3.2.4 on 2021-09-08 11:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0049_merge_20210901_1546'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipevideo',
            name='recipe',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='video', to='recipe.recipe'),
        ),
    ]
