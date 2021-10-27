# Generated by Django 3.2.4 on 2021-07-15 10:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0027_auto_20210714_1436'),
        ('site_settings', '0005_support'),
    ]

    operations = [
        migrations.CreateModel(
            name='TopRatedRecipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('recipe', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='top_rated_recipe', to='recipe.recipe')),
            ],
        ),
        migrations.CreateModel(
            name='MealOfTheWeekRecipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('recipe', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='meal_of_the_week', to='recipe.recipe')),
            ],
        ),
    ]
