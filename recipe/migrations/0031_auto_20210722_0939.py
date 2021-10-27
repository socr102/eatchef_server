# Generated by Django 3.2.4 on 2021-07-22 09:39

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipe', '0030_alter_ingredient_quantity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredient',
            name='unit',
            field=models.CharField(blank=True, choices=[('', 'Empty'), ('bag(s)', 'Bag'), ('bottle', 'Bottle'), ('box(es)', 'Box'), ('bunch', 'Bunch'), ('can', 'Can'), ('chunks', 'Chunk'), ('clove(s)', 'Clove'), ('container', 'Container'), ('cube', 'Cube'), ('cup(s)', 'Cup'), ('dash(es)', 'Dash'), ('gram(s)', 'Gram'), ('halves', 'Halves'), ('handful', 'Handful'), ('head', 'Head'), ('inch(es)', 'Inch'), ('jar', 'Jar'), ('kg', 'Kg'), ('large bag', 'Large Bag'), ('large can', 'Large Can'), ('large clove(s)', 'Large Clove'), ('large handful', 'Large Handful'), ('large head', 'Large Head'), ('large leaves', 'Large Leaves'), ('large slices', 'Large Slices'), ('lb(s)', 'Lbs'), ('leaves', 'Leaves'), ('liter(s)', 'Liters'), ('loaf', 'Loaf'), ('medium head', 'Medium Head'), ('milliliters', 'Milliliters'), ('ounce(s)', 'Ounce'), ('package', 'Package'), ('packet', 'Packet'), ('piece(s)', 'Piece'), ('pinch', 'Pinch'), ('pint', 'Pint'), ('pound(s)', 'Pound'), ('quart', 'Quart'), ('serving(s)', 'Serving'), ('sheet(s)', 'Sheets'), ('slice(s)', 'Slice'), ('small can', 'Small Can'), ('small head', 'Small Head'), ('small pinch', 'Small Pinch'), ('sprig(s)', 'Sprig'), ('stalk(s)', 'Stalk'), ('tablespoon(s)', 'Tablespoon'), ('teaspoon(s)', 'Teaspoon')], default='', max_length=25, null=True),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='cooking_methods',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(1, 'Broiling'), (2, 'Grilling'), (3, 'Roasting'), (4, 'Baking'), (5, 'Sauteing'), (6, 'Poaching'), (7, 'Simmering'), (8, 'Boiling'), (9, 'Steaming'), (10, 'Braising'), (11, 'Stewing')]), blank=True, null=True, size=None, verbose_name='Cooking methods'),
        ),
        migrations.AlterField(
            model_name='recipe',
            name='types',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(choices=[(1, 'Breakfast'), (2, 'Lunch'), (3, 'Dinner'), (4, 'Dessert'), (5, 'Beverage'), (6, 'Appetizer'), (7, 'Salad'), (8, 'Bread')]), blank=True, null=True, size=None, verbose_name='Types'),
        ),
    ]