# Generated by Django 3.2.4 on 2021-10-08 14:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chef_pencils', '0020_alter_chefpencilrecordcategorylink_unique_together'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='chefpencilrecordcategorylink',
            options={'verbose_name': "Chef's Pencil Category Link", 'verbose_name_plural': "Chef's Pencil Category Links"},
        ),
        migrations.AlterModelOptions(
            name='savedchefpencilrecord',
            options={'verbose_name': "Saved Chef's Pencil Record", 'verbose_name_plural': "Saved Chef's Pencil Records"},
        ),
        migrations.AlterUniqueTogether(
            name='chefpencilrecordcategorylink',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='savedchefpencilrecord',
            unique_together=set(),
        ),
    ]
