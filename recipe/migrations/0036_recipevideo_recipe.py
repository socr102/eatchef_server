# Generated by Django 3.2.4 on 2021-07-28 14:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0035_auto_20210727_1610'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipevideo',
            name='recipe',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='recipe.recipe'),
        ),
    ]
