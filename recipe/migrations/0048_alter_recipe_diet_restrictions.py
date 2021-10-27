# Generated by Django 3.2.4 on 2021-08-30 08:41

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0047_auto_20210830_0820'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='diet_restrictions',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(0, 'None'), (1, 'Vegan'), (2, 'Vegetarian'), (3, 'Pescetarian'), (4, 'Gluten Free'), (5, 'Grain Free'), (6, 'Dairy Free'), (7, 'High Protein'), (8, 'Low Sodium'), (9, 'Low Carb'), (10, 'Paleo'), (11, 'Primal'), (12, 'Ketogenic'), (13, 'FODMAP'), (14, 'Whole 30'), (15, 'Low FODMAP'), (16, 'High FODMAP')]), blank=True, null=True, size=None, verbose_name='Diet restrictions'),
        ),
    ]
