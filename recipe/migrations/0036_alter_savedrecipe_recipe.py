# Generated by Django 3.2.4 on 2021-08-03 09:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0035_recipe_views_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='savedrecipe',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_recipes', to='recipe.recipe'),
        ),
    ]
