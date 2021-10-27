# Generated by Django 3.2.4 on 2021-08-02 12:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipe', '0039_alter_recipevideo_recipe'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipeimage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recipeimage',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='recipe_images', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='recipeimage',
            name='recipe',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='images', to='recipe.recipe'),
        ),
    ]
