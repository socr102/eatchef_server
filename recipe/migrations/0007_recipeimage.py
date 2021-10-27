# Generated by Django 3.2.4 on 2021-07-02 11:14

from django.db import migrations, models
import django.db.models.deletion
import main.validators
import utils.file_storage


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0006_auto_20210702_0925'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecipeImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.ImageField(upload_to=utils.file_storage.recipe_image_file_path, validators=[main.validators.validate_images_file_max_size], verbose_name='file')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='recipe.recipe')),
            ],
        ),
    ]
