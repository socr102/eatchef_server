# Generated by Django 3.2.4 on 2021-07-08 08:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0018_merge_0014_auto_20210707_1440_0017_auto_20210707_1114'),
        ('site_settings', '0002_banner_filename'),
    ]

    operations = [
        migrations.CreateModel(
            name='HomepagePinnedRecipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('recipe', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='pinned_recipe', to='recipe.recipe')),
            ],
        ),
    ]
