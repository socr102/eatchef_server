# Generated by Django 3.2.4 on 2021-07-13 13:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0025_merge_20210713_1200'),
    ]

    operations = [
        migrations.AlterField(
            model_name='savedrecipe',
            name='recipe',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='recipe.recipe'),
        ),
    ]