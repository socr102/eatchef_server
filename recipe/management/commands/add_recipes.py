# -*- coding: utf-8 -*-
import json
import recipe
import requests
from datetime import timedelta
from django.db import IntegrityError

from django.db.models import Q
from django.core.files import File
from os.path import basename
from tempfile import TemporaryFile
from urllib.parse import urlsplit

from pathlib import Path

from users.models import User

from recipe.models import Ingredient, Recipe, RecipeImage
from recipe.enums import Cuisines, Diets, RecipeTypes, \
    Units, UNITS_KEYS
from utils.helper import strip_links

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Add recipes from json files in the data directory"

    def add_arguments(self, parser):
        parser.add_argument("--user-id", type=int, help="User ID to assign recipes", required=True)
        parser.add_argument("--data-dir", type=str, help="Data directory")

    def handle(self, *args, **options):

        DIR = options.get('data_dir') or 'recipe_data'

        try:
            user = User.objects.get(pk=options.get('user_id'))
        except User.DoesNotExist as e:
            raise Exception(f"User with id {options['user_id']} not found") from e

        files = [f for f in Path.cwd().joinpath(DIR).iterdir() if f.suffix == '.json']

        for f in files:
            self.stdout.write(str(f))
            try:
                with open(f, 'r') as jf:
                    recipe_data = json.load(jf)

                rc = RecipeCreator(recipe_data=recipe_data, user=user)
                recipe = rc.add_recipe()
            except IntegrityError:
                self.stdout.write(self.style.WARNING(f"Recipe already exists"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {e}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Recipe #{recipe.pk} added"))


class RecipeCreator:
    """
    Created Recipe models from necessary API by matching params
    """

    def __init__(self, recipe_data: dict, user: User):
        self.recipe_data = recipe_data
        self.user = user

    def add_recipe(self):

        description = self.recipe_data.get('instructions') or self.recipe_data.get('summary', '-')

        recipe = Recipe.objects.create(
            title=self.recipe_data['title'],
            description=strip_links(description),
            user=self.user,
            cooking_time=timedelta(minutes=self.recipe_data['readyInMinutes']),
            cuisines=self._get_valid_cuisines(self.recipe_data['cuisines']),
            cooking_methods=self._get_valid_cooking_methods(),
            types=self._get_valid_types(self.recipe_data['dishTypes']),
            diet_restrictions=self._get_diet_restrictions(self.recipe_data),
            language='English',
            caption='unknown',
            status=Recipe.Status.ACCEPTED,
            publish_status=Recipe.PublishStatus.PUBLISHED,
            source_id=int(self.recipe_data['id']),
            source_url=self.recipe_data['sourceUrl'],
            is_parsed=True
        )

        if self.recipe_data.get('image'):
            self.download_to_recipe_image(recipe, self.recipe_data['image'])

        self.add_ingredients(
            recipe,
            self.recipe_data.get('extendedIngredients', [])
        )

        return recipe

    def download_to_recipe_image(self, recipe, url):
        """
        https://goodcode.io/articles/django-download-url-to-file-field/
        """
        ri = RecipeImage()
        ri.recipe = recipe
        ri.user = self.user
        with TemporaryFile() as tf:
            r = requests.get(url, stream=True)
            for chunk in r.iter_content(chunk_size=4096):
                tf.write(chunk)
            tf.seek(0)
            ri.file = File(tf, name=basename(urlsplit(url).path))
            ri.save()

    def add_ingredients(self, recipe, ingredients_list: list):

        def _get_unit(unit: str):
            for keys, unit_value in UNITS_KEYS.items():
                if unit in keys:
                    return unit_value
            for choice in Units.choices:
                if unit == choice[0]:
                    return unit
            return Units.EMPTY

        for ingredient_data in ingredients_list:
            Ingredient.objects.create(
                recipe=recipe,
                title=ingredient_data['originalName'],
                quantity=round(ingredient_data['amount'], 3),
                unit=_get_unit(ingredient_data['unit'])
            )

    def _get_valid_cuisines(self, cuisines_to_load: list) -> list:
        res = [v for v in Cuisines if v.label in cuisines_to_load]
        return res

    def _get_valid_cooking_methods(self) -> list:
        return []

    def _get_valid_types(self, dish_types:list) -> list:
        """
        can have 'main course', 'main dish' values
        """
        return [v for v in RecipeTypes if v.label.lower() in dish_types]

    def _get_diet_restrictions(self, recipe_data: dict) -> int:
        """
        can have 'lacto ovo vegetarian'
        """
        res = []
        if recipe_data.get('dairyFree'):
            res.append(Diets.DAIRY_FREE)
        if recipe_data.get('glutenFree'):
            res.append(Diets.GLUTEN_FREE)
        if recipe_data.get('lowFodmap'):
            res.append(Diets.FODMAP)
        if recipe_data.get('vegan'):
            res.append(Diets.VEGAN)
        if recipe_data.get('vegetarian'):
            res.append(Diets.VEGETARIAN)
        if 'pescatarian' in recipe_data['diets']:
            res.append(Diets.PESCETARIAN)
        if 'paleolitic' in recipe_data['diets']:
            res.append(Diets.PALEO)
        if 'primal' in recipe_data['diets']:
            res.append(Diets.PRIMAL)
        return res

