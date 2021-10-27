# Generated by Django 3.2.4 on 2021-07-01 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cooking_method',
            field=models.IntegerField(choices=[(1, 'Broiling'), (2, 'Grilling'), (3, 'Roasting'), (4, 'Baking'), (5, 'Sauteing'), (6, 'Poaching'), (7, 'Simmering'), (8, 'Boiling'), (9, 'Steaming'), (10, 'Braising'), (11, 'Stewing')], verbose_name='cooking method'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='cooking_skills',
            field=models.IntegerField(choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Complex')], verbose_name='cooking skills'),
        ),
    ]
