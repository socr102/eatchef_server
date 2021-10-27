# Generated by Django 3.2.4 on 2021-07-22 13:59

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0031_auto_20210722_0939'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cuisines',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(1, 'American'), (2, 'Chinese'), (3, 'Continental'), (4, 'Cuban'), (5, 'French'), (6, 'Greek'), (7, 'Indian'), (8, 'Indonisian'), (9, 'Italian'), (10, 'Japanese'), (11, 'Korean'), (12, 'Libanese'), (13, 'Malyasian'), (14, 'Mexican'), (15, 'Spanish'), (16, 'Thai'), (17, 'Moracon'), (18, 'Turkish'), (19, 'African'), (20, 'Vietnamese'), (21, 'British'), (22, 'Irish'), (23, 'Middle eastern'), (24, 'Jewish'), (25, 'Cajun'), (26, 'Southern'), (27, 'German'), (28, 'Nordic'), (29, 'Eastern european'), (30, 'Caribbean'), (31, 'Latin American')]), blank=True, null=True, size=None, verbose_name='Cuisines'),
        ),
    ]
