# Generated by Django 3.2.4 on 2021-09-16 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chef_pencils', '0008_auto_20210916_1603'),
    ]

    operations = [
        migrations.AddField(
            model_name='chefpencilrecord',
            name='status',
            field=models.IntegerField(choices=[(1, 'Awaiting approval'), (2, 'Approved'), (3, 'Rejected')], default=1, verbose_name='status'),
        ),
    ]
