# Generated by Django 3.2.4 on 2021-07-29 14:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0033_merge_20210722_1537'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tagreciperelation',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tag_recipe_relations', to='recipe.recipe'),
        ),
    ]
