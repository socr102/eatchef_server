# Generated by Django 3.2.4 on 2021-09-20 08:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('site_settings', '0016_alter_block_change_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='change_time',
            field=models.PositiveIntegerField(default=5, verbose_name='Change time (sec)'),
        ),
    ]
