from datetime import datetime
from django.utils import timezone
from django.utils import timezone, dateformat
import copy

from users.enums import UserTypes
from main.utils.test import IsAuthClientTestCase, TestDataService
from rest_framework.reverse import reverse
from rest_framework import status
from recipe.enums import RecipeTypes, Cuisines, Diets, CookingMethods, CookingSkills
from recipe.models import Recipe
from stats.models import StatRecord
from recipe.tasks import calculate_views_for_recipes


class StatsTestCase(IsAuthClientTestCase):

    def setUp(self):
        super().setUp()
        self.home_chef_user = self.create_random_user(extra_fields={'is_email_active': True})
        self.home_chef_user.user_type = UserTypes.HOME_CHEF.value
        self.home_chef_user.save()
        self.home_chef_client = self.create_client_with_auth(self.home_chef_user)

        self.BASIC_TEST_DATA = {
            'user': self.home_chef_user,
            'title': 'Grilled Basil Chicken',
            'cooking_time': '00:30',
            'description': 'test',
            'language': 'English',
            'caption': 'Caption',
            "cuisines": [Cuisines.INDONISIAN.value],
            "types": [RecipeTypes.BREAKFAST.value],
            "cooking_methods": [CookingMethods.BAKING.value],
            "cooking_skills": CookingSkills.EASY.value,
            "diet_restrictions": [Diets.GLUTEN_FREE.value],
            "status": Recipe.Status.ACCEPTED,
            "publish_status": Recipe.PublishStatus.PUBLISHED
        }

    def test_stats_increment(self):

        data = copy.deepcopy(self.BASIC_TEST_DATA)
        recipe = Recipe.objects.create(**data)

        for _ in range(3):

            response = self.anonymous_client.post(
                reverse('stats:increment'),
                {
                    "key": "SHARES_COUNTER",
                    "content_type": "recipe",
                    "object_id": recipe.pk
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response = self.anonymous_client.post(
                reverse('stats:increment'),
                {
                    "key": "VIEWS_COUNTER",
                    "content_type": "recipe",
                    "object_id": recipe.pk
                }
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check values

        stat = StatRecord.objects.get(
            content_type__model=recipe.__class__.__name__.lower(),
            object_id=recipe.pk,
            date=dateformat.format(timezone.now(), 'Y-m-d')
        )
        self.assertEqual(stat.shares_counter.count, 3)
        self.assertEqual(stat.views_counter.count, 3)

        # if wrong entity

        response = self.anonymous_client.post(
            reverse('stats:increment'),
            {
                "key": "SHARES_COUNTER",
                "content_type": "recipe",
                "object_id": "2353"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.anonymous_client.post(
            reverse('stats:increment'),
            {
                "key": "SHARES_COUNTER",
                "content_type": "unknown",
                "object_id": "2353"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.anonymous_client.post(
            reverse('stats:increment'),
            {
                "key": "TEST",
                "content_type": "unknown",
                "object_id": "2353"
            }
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_views_count(self):

        data = copy.deepcopy(self.BASIC_TEST_DATA)
        recipe = Recipe.objects.create(**data)

        for i in range(3):

            response = self.anonymous_client.get(
                reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        r = Recipe.objects.get(pk=recipe.pk)
        self.assertEqual(r.views_number, 0)

        calculate_views_for_recipes()

        r = Recipe.objects.get(pk=recipe.pk)
        self.assertEqual(r.views_number, 3)

        response = self.anonymous_client.get(
            reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['views_number'], 4)
