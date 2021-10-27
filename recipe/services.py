# -*- coding: utf-8 -*-

from site_settings.models import ParserData
import requests

import datetime
from main.settings.common import RAPID_API_KEY
from django.db.models import Sum
from django.db import transaction
from recipe.models import Recipe
from social.models import Rating, Like
from django.db.models.aggregates import Avg, Count
from main.utils.db import Round1

from recipe.management.commands.add_recipes import RecipeCreator
from django.conf import settings

from utils.loggers import current_func_name
from users.models import User
from django.conf import settings

import numpy as np

from users.models import User
from social.models import Like
from recipe.models import Recipe

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from recipe.errors import (
    LimitsExceededError,
    RecipeAlreadyExists,
    RequestError,
    UnexpectedResponse
)


import logging
logger = logging.getLogger('django')


class RecipeRatingCalculator:

    def get_avg_ratings_for_recipes(self):
        ratings = Rating.objects.filter(content_type__model='recipe').values_list(
            'object_id'
        ).annotate(
            rounded_avg_rating=Round1(Avg('rating'))
        )
        self.ratings = {p[0]: p[1] for p in ratings}

    def update_records(self):
        to_update = []
        for r in Recipe.objects.filter(pk__in=self.ratings.keys()).only('pk'):
            r.avg_rating = self.ratings[r.pk]
            to_update.append(r)
        Recipe.objects.bulk_update(to_update, ['avg_rating'], batch_size=100)


class RecipeLikeCalculator:

    def get_total_likes_for_recipes(self):
        likes = Like.objects.filter(content_type__model='recipe').values_list(
            'object_id'
        ).annotate(
            Count('pk')
        )
        self.ratings = {p[0]: p[1] for p in likes}

    def update_records(self):
        to_update = []
        for r in Recipe.objects.filter(pk__in=self.ratings.keys()).only('pk'):
            r.likes_number = self.ratings[r.pk]
            to_update.append(r)
        Recipe.objects.bulk_update(to_update, ['likes_number'], batch_size=100)


class RecipeViewsCalculator:

    def get_total_views_for_recipes(self):

        rr = Recipe.objects.all().select_related('user').annotate(
            views_number_calculated=Sum('stat_records__views_counter__count')
        )
        self.ratings = {r.pk: r.views_number_calculated for r in rr}

    def update_records(self):
        to_update = []
        for r in Recipe.objects.filter(pk__in=self.ratings.keys()).only('pk'):
            r.views_number = self.ratings[r.pk]
            to_update.append(r)
        Recipe.objects.bulk_update(to_update, ['views_number'], batch_size=100)


class RecipeApiParser:

    def __init__(self, requests_per_day=500, results_per_day=5000):

        self.REQUESTS_PER_DAY = requests_per_day
        self.RESULTS_PER_DAY = results_per_day

        self.headers = {
            'content-type': 'application/json',
            'x-rapidapi-key': RAPID_API_KEY,
            'x-rapidapi-host': 'spoonacular-recipe-food-nutrition-v1.p.rapidapi.com'
        }

        self.user = User.objects.get(
            full_name=settings.EATCHEFS_ACCOUNT_NAME,
            is_staff=True
        )

        self.today_requests = self.settings.today_requests
        self.today_results = self.settings.today_results
        self.added_recipes = self.settings.added_recipes.split('\n')
        self.not_added_recipes = self.settings.not_added_recipes.split('\n')
        self.checked_ids = self.settings.checked_ids or []

        self.check_limits()

    def download_recipes(self):

        max_values = [max(a) for a in ParserData.objects.all().values_list('checked_ids', flat=True) if a]
        recipe_id = max(max_values) + 1 if max_values else 1

        while True:

            recipe_results = self.get_similar_recipes_ids_from_api(
                recipe_id=recipe_id
            )
            self.save_settings()

            """
            try:
                recipe_results
            except TypeError:
                logger.info(f"{__class__.__name__}.{current_func_name()}: response from API {recipe_results}")
                raise UnexpectedResponse()
            """

            for r_id, r_url in recipe_results.items():
                try:
                    self.check_recipe(r_url, r_id)
                except RecipeAlreadyExists as e:
                    logger.exception(e)
                    self.save_settings()
                else:
                    try:
                        res = self.get_full_recipe(r_url)
                    except RequestError as e:
                        logger.exception(e)
                    else:
                        self.add_recipe_to_database(res, url=r_url)
                        self.save_settings()

                    self.check_limits()

            self.check_limits()

            recipe_id += 1

    def get_similar_recipes_ids_from_api(self, recipe_id):

        logger.info(f'get_similar_recipes_ids_from_api: {recipe_id}')

        try:
            response = requests.request(
                "GET",
                f"https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/{recipe_id}/similar",
                headers=self.headers,
                params={},
                timeout=25
            )
        except requests.exceptions.Timeout as e:
            logger.exception(e)
            return {}

        logger.info(f"received {len(response.json())}")

        self.today_requests += 1
        self.today_results += len(response.json())
        self.checked_ids.append(recipe_id)

        logger.info(f'today requests {self.today_requests}/{self.REQUESTS_PER_DAY}')
        logger.info(f'today results {self.today_results}/{self.RESULTS_PER_DAY}')
        return {i['id']:i['sourceUrl'] for i in response.json()}

    def get_full_recipe(self, url: str):

        logger.info(f'get_full_recipe: {url}')

        try:
            response = requests.request(
                "GET",
                "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/extract",
                headers=self.headers,
                params={"url": url}
            )
        except requests.exceptions.Timeout:
            raise RequestError

        self.today_requests += 1
        logger.info(f'today requests {self.today_requests}/{self.REQUESTS_PER_DAY}')
        self.today_results += 1
        logger.info(f'today results {self.today_results}/{self.RESULTS_PER_DAY}')

        """
        with open(f'recipe_data/{response.json()["id"]}.json', 'w') as f:
            f.write(json.dumps(response.json(), indent=4, sort_keys=True))
        """

        return response.json()

    def check_recipe(self, url: str, id:int):
        try:
            Recipe.objects.get(source_url=url)
        except Recipe.DoesNotExist:
            pass
        else:
            self.not_added_recipes.append(f"{id};{url}")
            raise RecipeAlreadyExists(f'Recipe with {id} url "{url}" already exists')

    @transaction.atomic
    def add_recipe_to_database(self, recipe_data, url):
        try:
            r = RecipeCreator(recipe_data=recipe_data, user=self.user)
            recipe = r.add_recipe()
        except Exception as e:
            logger.exception(e)
            logger.info(recipe_data)
            self.not_added_recipes.append(f"{recipe_data.get('id', '<no id>')};{url}")
        else:
            logger.info(f"{__class__.__name__}.{current_func_name()}: Recipe #{recipe.pk} with source_id {recipe_data['id']} added")
            self.added_recipes.append(f"{recipe_data['id']};{recipe.pk}")
            return recipe

    def save_settings(self):
        settings = self.settings
        settings.today_results = self.today_results
        settings.today_requests = self.today_requests
        settings.added_recipes = '\n'.join([i for i in self.added_recipes if i.strip()])
        settings.not_added_recipes = '\n'.join([i for i in self.not_added_recipes if i.strip()])
        settings.checked_ids = self.checked_ids
        settings.save()

    @property
    def settings(self):
        parser_data, created = ParserData.objects.get_or_create(
            date=datetime.date.today()
        )
        return parser_data

    def check_limits(self):
        if self.today_requests >= self.REQUESTS_PER_DAY or self.today_results >= self.RESULTS_PER_DAY:
            logger.info(f"{__class__.__name__}.{current_func_name()}: day limit exceeded: {self.today_requests} requests, {self.today_results} results")
            raise LimitsExceededError


class RecommendedRecipesService:

    def get_recipes_related_to_user_activity(self, user):

        viewed_recipes = Recipe.objects \
            .filter(recipe_views__user=user) \
            .order_by('-recipe_views__updated_at')[0:3]

        liked_recipes_ids = Like.objects \
            .filter(
                user=user,
                content_type__model='recipe'
            ) \
            .values_list('object_id', flat=True) \
            .order_by('-created_at')[0:3]
        liked_recipes = Recipe.objects.filter(pk__in=liked_recipes_ids)

        """
        saved_recipes = Recipe.objects
            .filter(saved_recipes__user=user) \
            .order_by('-saved_recipes__created_at')[0:3]
        """

        user_activity_recipes = liked_recipes | viewed_recipes # | saved_recipes

        return user_activity_recipes  # no duplicated here

    def calculate_recipes_data(self):

        recipes = Recipe.objects.all() \
            .get_published_and_accepted() \
            .prefetch_related('ingredients') \
            .order_by('pk')

        recipes_ingredients = {}
        for r in recipes:
            ingredients = ''
            for ing in r.ingredients.all():
                ingredients += ' ' + ing.title.lower()
            recipes_ingredients[r.pk] = ingredients

        tf = TfidfVectorizer(analyzer='word',
                             ngram_range=(1, 3),
                             min_df=0,
                             sublinear_tf=True,
                             stop_words='english')

        tfidf_matrix = tf.fit_transform(recipes_ingredients.values())

        self.recipe_vectors = {}
        for i, r in enumerate(recipes):
            self.recipe_vectors[r.pk] = tfidf_matrix[i]

        self.cosine_similarities = linear_kernel(tfidf_matrix, tfidf_matrix)

    def get_recommended(self, user_activity_recipes):
        """
        1. SIMILAR BY INGREDIENTS
        """

        top = []
        for user_recipe in user_activity_recipes:
            index = list(self.recipe_vectors.keys()).index(user_recipe.pk)  # index of cosine_similarity vector in recipe_vectors for current user recipe
            second_max_value = np.partition(self.cosine_similarities[index], -2)[-2]
            second_max_index_in_vector = list(self.cosine_similarities[index]).index(second_max_value)

            similar_recipe_id = list(self.recipe_vectors.keys())[second_max_index_in_vector]

            top.append((
                similar_recipe_id,
                second_max_value,
                user_recipe.pk,
            ))

        top.sort(key=lambda x:x[1], reverse=True)

        # debug info
        for ur in user_activity_recipes:
            logger.info(f'DEBUG: {ur}')
        logger.info('-----------------')
        for top_item in top[0:10]:
            logger.info(f'DEBUG: {top_item}')

        res = []
        for r in top:
            if r[0] not in res:
                res.append(r[0])

        return res[0:4]

    def _prepare_ingredient_name(self, title):

        SKIP_WORDS = [
            'boneless',
            'for',
            'diced',
            '1/2',
            '1/3',
            '1/4',
            'lb',
            'segments',
            'sweet',
            'to',
            'tablespoon',
            'cup',
            '8s',
            'of',
            'to',
            'packages',
            'a',
            'crusty'
            'good',
            'about',
            'cups',
            'tsp',
            'teaspoon',
            'toasted',
            'crushed',
            '¼',
            '½',
            '-',
            '–',
            '1kg'
        ]

        if ',' in title:
            title = title.split(',')[0]
        if '(' in title:
            title = title.split('(')[0].strip()

        if ' or ' in title:
            candidates = [t.lower() for t in title.split(' or ')]
        else:
            candidates = [title.lower()]

        res = []
        for c in candidates:
            words = [w.strip() for w in c.split() if w not in SKIP_WORDS]
            words = [w for w in words if not w.isdigit()]
            words = [w for w in words if len(w) > 0]
            res.append(' '.join(words))
        if res == ['']:
            return []
        return res
