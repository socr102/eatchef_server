# Generated by Django 3.2.4 on 2021-10-05 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chef_pencils', '0016_auto_20210927_1620'),
    ]

    operations = [
        migrations.AddField(
            model_name='chefpencilimage',
            name='order_index',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
