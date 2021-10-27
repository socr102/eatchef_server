# Generated by Django 3.2.4 on 2021-09-27 08:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chef_pencils', '0011_chefpencilcategory'),
    ]

    operations = [
        migrations.AddField(
            model_name='chefpencilrecord',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chefpencil_records', to='chef_pencils.chefpencilcategory'),
        ),
    ]