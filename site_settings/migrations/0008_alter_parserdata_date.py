# Generated by Django 3.2.4 on 2021-07-22 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('site_settings', '0007_parserdata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parserdata',
            name='date',
            field=models.DateField(unique=True),
        ),
    ]
