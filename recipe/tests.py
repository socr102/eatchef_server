import copy
import json
import random
import re
import shutil
from pathlib import Path
from pprint import pprint

from celery.utils.functional import first
from django.conf import settings
from django.core import mail
from django.core.files import File
from main.utils.test import IsAuthClientTestCase, TestDataService
from rest_framework import status
from rest_framework.reverse import reverse
from site_settings.models import (Banner, FeaturedRecipe, HomepagePinnedRecipe,
                                  MealOfTheWeekRecipe, ParserData,
                                  TopRatedRecipe)
from social.models import Comment, CommentLike, Like, Rating
from users.enums import UserTypes
from users.models import User
from utils.helper import strip_links
from utils.test import get_alt_test_files, get_test_files, get_test_video_file

from recipe.enums import (CookingMethods, CookingSkills, Cuisines, Diets,
                          RecipeTypes, Units)
from recipe.management.commands.add_recipes import RecipeCreator
from recipe.models import (Ingredient, Recipe, RecipeImage, RecipeStep,
                           RecipeVideo, SavedRecipe, Tag, TagRecipeRelation)
from recipe.services import LimitsExceededError, RecipeApiParser
from recipe.tasks import (calculate_avg_rating_for_recipes,
                          calculate_likes_for_recipes)

DESCRIPTION = """
Wash hands with soap and water.
After washing basil and tomatoes, blot them dry with clean paper towel.
For marinade, place first six ingredients in a blender. Cover and process until well blended.
"""


class RecipeTestCase(IsAuthClientTestCase):
    test_data_service = TestDataService()

    def setUp(self):
        super().setUp()

        self.BASIC_TEST_DATA = {
            'user': self.home_chef_user,
            'title': 'Grilled Basil Chicken',
            'cooking_time': '00:30',
            'description': DESCRIPTION,
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

    def _create_recipe(self, data, images=None, main_image=None):

        if images is not None:
            images_ids = []
            for f in images:
                ri = RecipeImage.objects.create(
                    user=self.home_chef_user,
                    file=f
                )
                if Path(f.name).name == main_image:
                    data['main_image'] = ri.pk
                images_ids.append(ri.pk)
            data['images'] = images_ids

        payload = {
            'data': json.dumps(data),
        }
        return self.home_chef_client.post(
            reverse('recipe:recipe_list_create'),
            data=payload,
            format='multipart'
        )

    def _update_recipe(self, recipe_id, data, images=None, main_image=None):

        if str(main_image).isdigit():
            data['main_image'] = main_image

        if images is not None:
            images_ids = []
            for f in images:
                ri = RecipeImage.objects.create(
                    user=self.home_chef_user,
                    file=f
                )

                if Path(f.name).name == main_image:
                    data['main_image'] = ri.pk

                images_ids.append(ri.pk)
            data['images'] = images_ids

        payload = {
            'data': json.dumps(data)
        }
        return self.home_chef_client.patch(
            reverse('recipe:recipe_retrieve_update_destroy', args=[recipe_id]),
            payload,
            format='multipart'
        )

    def test_create_by_customer(self):
        user = self.create_random_user(extra_fields={'is_email_active': True})
        user.user_type = UserTypes.CUSTOMER.value
        user.save()
        self.customer_client = self.create_client_with_auth(user)
        response = self.customer_client.post(
            reverse('recipe:recipe_list_create'), data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_by_home_chef(self):

        # 1. video upload to another endpoint

        rv = RecipeVideo.objects.create(
            user=self.home_chef_user,
            video=get_test_video_file()
        )

        # 2.

        data = {
            'user': self.home_chef_user.pk,
            'title': 'Grilled Basil Chicken',
            'cooking_time': '00:30',
            'description': DESCRIPTION,
            'language': 'English',
            'caption': 'Caption',
            "cuisines": [
                Cuisines.INDIAN.value,
                Cuisines.ITALIAN.value,
                Cuisines.AMERICAN.value
            ],
            "types": [
                RecipeTypes.BREAKFAST.value
            ],
            "cooking_methods": [
                CookingMethods.BAKING.value
            ],
            "cooking_skills": CookingSkills.EASY.value,
            "diet_restrictions": [
                Diets.DAIRY_FREE.value,
                Diets.GLUTEN_FREE.value
            ],
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ],
            "steps": [
                {
                    "num": 1,
                    "title": "First step for the recipe",
                    "description": DESCRIPTION
                },
                {
                    "num": 2,
                    "title": "Second step for the recipe",
                    "description": DESCRIPTION
                },
                {
                    "num": 3,
                    "title": "Third step for the recipe",
                    "description": DESCRIPTION
                }
            ],
            "tags": [
                "тест 1",
                "тест тэга 2",
                "тест 1",
                "длинный тэг для рецепта"
            ],
            "video": rv.pk
        }

        response = self._create_recipe(data, images=get_test_files())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['images']), 2)
        self.assertTrue('url' in response.data['images'][0])
        Recipe.objects.all().update(publish_status=Recipe.PublishStatus.PUBLISHED)

        recipe = Recipe.objects.get(pk=response.data['pk'])
        self.assertEqual(recipe.title, 'Grilled Basil Chicken')

        ingredients = Ingredient.objects.filter(recipe=recipe)
        self.assertEqual(ingredients.count(), 2)

        # self.assertEqual(recipe)

        images = RecipeImage.objects.filter(recipe=recipe)
        self.assertEqual(images.count(), 2)

        steps = RecipeStep.objects.filter(recipe=recipe)
        self.assertEqual(steps.count(), 3)

        self.assertEqual(Tag.objects.all().count(), 3)
        self.assertEqual(recipe.tags.count(), 3)
        # self.assertTrue('text' in response.data['tags'][0])

        self.assertEqual(len(mail.outbox), 1, "Inbox is not empty")

    def test_create_by_home_chef_without_video(self):

        mail.outbox = []
        data = {
            'user': self.home_chef_user.pk,
            'title': 'Grilled Basil Chicken',
            'cooking_time': '00:30',
            'description': DESCRIPTION,
            "cuisines": [
                Cuisines.INDIAN.value,
                Cuisines.ITALIAN.value,
                Cuisines.AMERICAN.value
            ],
            "types": [
                RecipeTypes.BREAKFAST.value
            ],
            "cooking_methods": [
                CookingMethods.BAKING.value
            ],
            "cooking_skills": CookingSkills.EASY.value,
            "diet_restrictions": [
                Diets.DAIRY_FREE.value,
                Diets.GLUTEN_FREE.value
            ],
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ],
            "steps": [
                {
                    "num": 1,
                    "title": "First step for the recipe",
                    "description": DESCRIPTION[0:200]
                },
                {
                    "num": 2,
                    "title": "Second step for the recipe",
                    "description": DESCRIPTION[0:200]
                },
                {
                    "num": 3,
                    "title": "Third step for the recipe",
                    "description": DESCRIPTION[0:200]
                }
            ],
            "video": "",
            "tags": [
                "тест 1",
                "тест тэга 2",
                "тест 1",
                "длинный тэг для рецепта"
            ],
            "proteins": "40.5",
            "fats": "10.5",
            "carbohydrates": "10.5",
            "calories": "300"
        }
        response = self._create_recipe(data, images=get_test_files(), main_image="test_image2.jpg")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('url' in response.data['images'][0])

    def test_update_video(self):

        rv1 = RecipeVideo.objects.create(
            user=self.home_chef_user,
            video=get_test_video_file()
        )

        rv2 = RecipeVideo.objects.create(
            user=self.home_chef_user,
            video=get_test_video_file()
        )

        # 2.

        mail.outbox = []
        data = {
            'user': self.home_chef_user.pk,
            'title': 'Grilled Basil Chicken',
            'cooking_time': '00:30',
            'description': DESCRIPTION,
            "cuisines": [
                Cuisines.INDIAN.value,
                Cuisines.ITALIAN.value,
                Cuisines.AMERICAN.value
            ],
            "types": [
                RecipeTypes.BREAKFAST.value
            ],
            "cooking_methods": [
                CookingMethods.BAKING.value
            ],
            "cooking_skills": CookingSkills.EASY.value,
            "diet_restrictions": [
                Diets.DAIRY_FREE.value,
                Diets.GLUTEN_FREE.value
            ],
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ],
            "steps": [
                {
                    "num": 1,
                    "title": "First step for the recipe",
                    "description": DESCRIPTION[0:200]
                },
                {
                    "num": 2,
                    "title": "Second step for the recipe",
                    "description": DESCRIPTION[0:200]
                },
                {
                    "num": 3,
                    "title": "Third step for the recipe",
                    "description": DESCRIPTION[0:200]
                }
            ],
            "tags": [
                "тест 1",
                "тест тэга 2",
                "тест 1",
                "длинный тэг для рецепта"
            ],
            "video": rv1.pk,
            "proteins": "40.5",
            "fats": "10.5",
            "carbohydrates": "10.5",
            "calories": "300"
        }
        response = self._create_recipe(data, images=get_test_files(), main_image="test_image2.jpg")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['video'], rv1.pk)

        self.assertEqual(RecipeVideo.objects.all().count(), 2)

        # update with another video

        update_data = {
            "steps": [
                {
                    "num": 1,
                    "title": "update1",
                    "description": "description"
                },
                {
                    "num": 2,
                    "title": "update2",
                    "description": "description"
                }
            ],
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ],
            "video": rv2.pk
        }
        response = self._update_recipe(response.data['pk'], update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['video'], rv2.pk)
        self.assertEqual(RecipeVideo.objects.all().count(), 1)

        # update with another video

        update_data = {
            "steps": [
                {
                    "num": 1,
                    "title": "update1",
                    "description": "description"
                },
                {
                    "num": 2,
                    "title": "update2",
                    "description": "description"
                }
            ],
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ],
        }
        response = self._update_recipe(response.data['pk'], update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['video'], None)
        self.assertEqual(RecipeVideo.objects.all().count(), 0)

    def test_update_recipe(self):
        data = copy.deepcopy(self.BASIC_TEST_DATA)
        data.update({
            "user": self.BASIC_TEST_DATA['user'].pk,
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ],
            "steps": [
                {
                    "num": 1,
                    "title": "First step for the recipe",
                    "description": DESCRIPTION[0:200]
                },
                {
                    "num": 2,
                    "title": "Second step for the recipe",
                    "description": DESCRIPTION[0:200]
                },
                {
                    "num": 3,
                    "title": "Third step for the recipe",
                    "description": DESCRIPTION[0:200]
                }
            ],
            "tags": [
                "тест 1",
                "тест тэга 2",
                "тест 1",
                "длинный тэг для рецепта"
            ]
        })
        response = self._create_recipe(data, images=get_test_files())
        self.assertEqual(RecipeStep.objects.count(), 3)
        Recipe.objects.all().update(publish_status=Recipe.PublishStatus.PUBLISHED)

        self.assertEqual(Tag.objects.all().count(), 3)
        self.assertEqual(TagRecipeRelation.objects.all().count(), 3)

        # to update
        recipe = Recipe.objects.first()

        self.anonymous_client.get(
            reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        update_data = {
            "steps": [
                {
                    "num": 1,
                    "title": "update1",
                    "description": "description"
                },
                {
                    "num": 2,
                    "title": "update2",
                    "description": "description"
                }
            ],
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ],
            "tags": [
                "тест 3",
                "тест 4",
            ]
        }
        response = self._update_recipe(
            recipe.pk,
            update_data,
            images=get_alt_test_files(),
            main_image="test_image4.jpg"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(response.data['steps']), 2)
        self.assertEqual(response.data['steps'][0]['title'], 'update1')
        self.assertEqual(RecipeStep.objects.all().count(), 2)

        self.assertEqual(Tag.objects.all().count(), 5)
        self.assertEqual(TagRecipeRelation.objects.all().count(), 2)

        images = RecipeImage.objects.filter(recipe=recipe)
        self.assertEqual(images.count(), 2)
        self.assertTrue(images.last().main_image)

    def test_update_recipe_new_main_image_by_id(self):
        data = copy.deepcopy(self.BASIC_TEST_DATA)
        data.update({
            "user": self.BASIC_TEST_DATA['user'].pk,
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ]
        })
        response = self._create_recipe(
            data,
            images=get_test_files(),
            main_image="test_image1.jpg"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        Recipe.objects.all().update(publish_status=Recipe.PublishStatus.PUBLISHED)

        recipe = Recipe.objects.first()

        self.anonymous_client.get(
            reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # TO UPDATE
        update_data = {
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ]
        }
        response = self._update_recipe(
            recipe.pk,
            update_data,
            images=get_alt_test_files()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_main_image_id = RecipeImage.objects.first().pk

        response = self._update_recipe(
            recipe.pk,
            {},
            main_image=RecipeImage.objects.first().pk
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        images = RecipeImage.objects.filter(recipe=recipe)
        self.assertEqual(images.count(), 2)
        self.assertTrue(images.get(pk=new_main_image_id).main_image)

    def test_recipe_create_image_limit(self):
        data = copy.deepcopy(self.BASIC_TEST_DATA)
        data.update({
            "user": self.BASIC_TEST_DATA['user'].pk,
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ]
        })
        images = [File(open(f"{settings.TEST_FILES_ROOT}/test_image1.jpg", mode='rb')) for i in range(21)]
        response = self._create_recipe(data, images=images, main_image="test_image1.jpg")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recipe_update_image_limit(self):

        data = copy.deepcopy(self.BASIC_TEST_DATA)
        data.update({
            "user": self.BASIC_TEST_DATA['user'].pk,
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ],
            "main_image": "test_image1.jpg"
        })
        response = self._create_recipe(data, images=get_test_files())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        Recipe.objects.all().update(publish_status=Recipe.PublishStatus.PUBLISHED)

        recipe = Recipe.objects.first()

        self.anonymous_client.get(
            reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # TO UPDATE
        images = [get_alt_test_files()[0] for i in range(21)]
        response = self._update_recipe(recipe.pk, {}, images=images)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('images' in response.data)

    def test_update_recipe_delete_steps(self):

        data = copy.deepcopy(self.BASIC_TEST_DATA)
        data.update({
            "user": self.BASIC_TEST_DATA['user'].pk,
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ],
            "steps": [
                {
                    "num": 1,
                    "title": "First step for the recipe",
                    "description": DESCRIPTION[0:200]
                },
                {
                    "num": 2,
                    "title": "Second step for the recipe",
                    "description": DESCRIPTION[0:200]
                },
                {
                    "num": 3,
                    "title": "Third step for the recipe",
                    "description": DESCRIPTION[0:200]
                }
            ],
            "tags": [
                "тест 1",
                "тест тэга 2",
                "тест 1",
                "длинный тэг для рецепта"
            ]
        })
        response = self._create_recipe(data, images=get_test_files())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(RecipeStep.objects.count(), 3)
        Recipe.objects.all().update(publish_status=Recipe.PublishStatus.PUBLISHED)

        # to update
        recipe = Recipe.objects.first()

        update_data = {
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "12",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "25",
                    "unit": Units.TABLESPOON
                }
            ],
        }
        response = self._update_recipe(recipe.pk, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Ingredient.objects.first().quantity, 12)

    def test_update_recipe_make_awaiting_approval(self):
        data = {
            'user': self.home_chef_user,
            'title': 'Grilled Basil Chicken',
            'cooking_time': '00:30',
            'description': DESCRIPTION,
            "cuisines": [
                Cuisines.INDONISIAN.value,
                Cuisines.ITALIAN.value,
                Cuisines.AMERICAN.value
            ],
            "types": [
                RecipeTypes.BREAKFAST.value,
                RecipeTypes.DINNER.value
            ],
            "cooking_methods": [
                CookingMethods.BAKING.value,
                CookingMethods.BOILING.value
            ],
            "cooking_skills": CookingSkills.EASY.value,
            "diet_restrictions": [
                Diets.DAIRY_FREE.value,
                Diets.GLUTEN_FREE.value
            ],
            "status": Recipe.Status.ACCEPTED
        }
        Recipe.objects.create(**data)
        self.assertEqual(Recipe.objects.first().status, Recipe.Status.ACCEPTED)

        recipe = Recipe.objects.first()

        data = {
            "description": "test",
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ],
        }
        response = self._update_recipe(recipe.pk, data, images=get_alt_test_files())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Recipe.objects.first().status, Recipe.Status.AWAITING_ACCEPTANCE)

    def test_list_and_filter_recipes(self):
        data = {
            'user': self.home_chef_user,
            'title': 'Grilled Basil Chicken',
            'cooking_time': '00:30',
            'description': DESCRIPTION,
            'language': 'English',
            'caption': 'Caption',
            "cuisines": [
                Cuisines.INDONISIAN.value,
                Cuisines.ITALIAN.value,
                Cuisines.AMERICAN.value
            ],
            "types": [
                RecipeTypes.BREAKFAST.value,
                RecipeTypes.DINNER.value
            ],
            "cooking_methods": [
                CookingMethods.BAKING.value,
                CookingMethods.BOILING.value
            ],
            "cooking_skills": CookingSkills.EASY.value,
            "diet_restrictions": [
                Diets.DAIRY_FREE.value,
                Diets.GLUTEN_FREE.value
            ],
            "status": Recipe.Status.ACCEPTED
        }
        Recipe.objects.create(**data)
        data['cuisines'] = [Cuisines.FRENCH.value, Cuisines.TURKISH.value]
        data['types'] = [RecipeTypes.SALAD.value]
        data['cooking_methods'] = [CookingMethods.BOILING.value]
        data['diet_restrictions'] = [Diets.DAIRY_FREE.value]
        Recipe.objects.create(**data)
        data['cuisines'] = [Cuisines.FRENCH.value, Cuisines.THAI.value]
        data['types'] = [RecipeTypes.SALAD.value]
        data['cooking_methods'] = [CookingMethods.BAKING.value]
        data['diet_restrictions'] = [Diets.DAIRY_FREE.value]
        Recipe.objects.create(**data)
        data['cuisines'] = [Cuisines.INDONISIAN.value]
        data['types'] = [RecipeTypes.SALAD.value]
        data['cooking_methods'] = [CookingMethods.BOILING.value]
        data['diet_restrictions'] = [Diets.DAIRY_FREE.value]
        Recipe.objects.create(**data)
        data['cuisines'] = [Cuisines.INDONISIAN.value]
        data['types'] = [RecipeTypes.SALAD.value, RecipeTypes.DINNER.value]
        data['cooking_methods'] = [CookingMethods.BOILING.value]
        data['diet_restrictions'] = [Diets.DAIRY_FREE.value]
        data['cooking_skills'] = CookingSkills.COMPLEX.value
        data['cooking_time'] = '00:45'
        Recipe.objects.create(**data)
        Recipe.objects.all().update(publish_status=Recipe.PublishStatus.PUBLISHED)

        response = self.client.get(reverse('recipe:recipe_list_create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)

        # cuisines filter
        response = self.client.get(reverse('recipe:recipe_list_create'), {'cuisines': f'{Cuisines.FRENCH.value},{Cuisines.THAI.value}'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        response = self.client.get(reverse('recipe:recipe_list_create'), {'cuisines': Cuisines.FRENCH.value})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        response = self.client.get(reverse('recipe:recipe_list_create'), {'cuisines': Cuisines.TURKISH.value})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        response = self.client.get(reverse('recipe:recipe_list_create'), {'cuisines': Cuisines.INDONISIAN.value})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        # types filter
        response = self.client.get(reverse('recipe:recipe_list_create'), {'types': f'{RecipeTypes.SALAD.value},{RecipeTypes.DINNER.value}'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)
        response = self.client.get(reverse('recipe:recipe_list_create'), {'types': RecipeTypes.DINNER.value})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

        # cooking methods filter
        response = self.client.get(reverse('recipe:recipe_list_create'), {'cooking_methods': f'{CookingMethods.BOILING.value},{CookingMethods.BAKING.value}'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)
        response = self.client.get(reverse('recipe:recipe_list_create'), {'cooking_methods': CookingMethods.BOILING.value})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)

        # diet restrictions filter
        response = self.client.get(reverse('recipe:recipe_list_create'), {'diet_restrictions': f'{Diets.DAIRY_FREE.value},{Diets.GLUTEN_FREE.value}'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)
        response = self.client.get(reverse('recipe:recipe_list_create'), {'diet_restrictions': Diets.GLUTEN_FREE.value})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # cooking skills
        response = self.client.get(reverse('recipe:recipe_list_create'), {'cooking_skills': CookingSkills.COMPLEX.value})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        # cooking time
        response = self.client.get(reverse('recipe:recipe_list_create'), {'cooking_time': '00:45'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_retrieve_recipe(self):

        # 1. unpublished
        data = copy.deepcopy(self.BASIC_TEST_DATA)
        data.update({'status': Recipe.Status.AWAITING_ACCEPTANCE, 'publish_status': Recipe.PublishStatus.NOT_PUBLISHED})
        Recipe.objects.create(**data)

        recipe = Recipe.objects.first()

        response = self.client.get(reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.home_chef_client.get(reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. published
        recipe.status = Recipe.Status.ACCEPTED
        recipe.publish_status = Recipe.PublishStatus.PUBLISHED
        recipe.save()

        response = self.client.get(reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_recipe(self):

        data = copy.deepcopy(self.BASIC_TEST_DATA)
        Recipe.objects.create(**data)

        recipe = Recipe.objects.first()

        response = self.anonymous_client.delete(reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.delete(reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.home_chef_client.delete(reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_create_ratings(self):
        Recipe.objects.create(**self.BASIC_TEST_DATA)
        Recipe.objects.create(**self.BASIC_TEST_DATA)
        recipe1 = Recipe.objects.all().order_by('pk')[0]
        recipe2 = Recipe.objects.all().order_by('pk')[1]

        ratings1 = [3,4,3]
        ratings2 = [5,5,4]
        for i in range(3):

            user = self.create_random_user(extra_fields={'is_email_active': True})
            client = self.create_client_with_auth(user)

            response = client.post(
                reverse('recipe:recipe_rate', args=[recipe1.pk]),
                data={'rating': ratings1[i]}
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            response = client.post(
                reverse('recipe:recipe_rate', args=[recipe2.pk]),
                data={'rating': ratings2[i]}
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Rating.objects.filter(content_type__model='recipe').count(), 6)

        calculate_avg_rating_for_recipes()

        recipe = Recipe.objects.get(pk=recipe1.pk)
        self.assertEqual(recipe.avg_rating, 3.3)

        recipe = Recipe.objects.get(pk=recipe2.pk)
        self.assertEqual(recipe.avg_rating, 4.7)

    def test_create_likes(self):
        Recipe.objects.create(**self.BASIC_TEST_DATA)
        Recipe.objects.create(**self.BASIC_TEST_DATA)
        recipe1 = Recipe.objects.all().order_by('pk')[0]
        recipe2 = Recipe.objects.all().order_by('pk')[1]

        for i in range(3):

            user = self.create_random_user(extra_fields={'is_email_active': True})
            client = self.create_client_with_auth(user)

            # like #1

            response = client.get(reverse('recipe:recipe_retrieve_update_destroy', args=[recipe1.pk]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.data['user_liked'])

            response = client.post(
                reverse('recipe:recipe_like', args=[recipe1.pk])
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['like_status'], 'created')

            response = client.get(reverse('recipe:recipe_retrieve_update_destroy', args=[recipe1.pk]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['user_liked'])

            # anonymous client has no likes

            response = self.anonymous_client.get(reverse('recipe:recipe_retrieve_update_destroy', args=[recipe1.pk]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.data['user_liked'])

            # like #2

            response = client.post(
                reverse('recipe:recipe_like', args=[recipe2.pk])
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Like.objects.count(), 6)

        calculate_likes_for_recipes()

        recipe = Recipe.objects.get(pk=recipe1.pk)
        self.assertEqual(recipe.likes_number, 3)

        recipe = Recipe.objects.get(pk=recipe2.pk)
        self.assertEqual(recipe.likes_number, 3)

    def test_unlike_recipe(self):

        user = self.create_random_user(extra_fields={'is_email_active': True})
        client = self.create_client_with_auth(user)

        Recipe.objects.create(**self.BASIC_TEST_DATA)
        recipe1 = Recipe.objects.all().order_by('pk')[0]

        Like.objects.create(
            user=user,
            content_object=recipe1
        )

        response = client.post(
            reverse('recipe:recipe_like', args=[recipe1.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['like_status'], 'deleted')

    def test_favorite_cuisines(self):
        # 1. setup

        cuisine = random.choice([c.value for c in Cuisines])
        recipes = []
        for i in range(3):
            data = copy.deepcopy(self.BASIC_TEST_DATA)
            data.update({'cuisines': [cuisine]})
            recipes.append(Recipe.objects.create(**data))

        ratings = [3, 3, 3, 4, 4, 4, 5, 5, 5]
        for i in range(9):

            user = self.create_random_user(extra_fields={'is_email_active': True})
            client = self.create_client_with_auth(user)

            response = client.post(
                reverse('recipe:recipe_rate', args=[recipes[int(i / 3)].pk]),
                data={'rating': ratings[i]}
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Rating.objects.count(), 9)

        calculate_avg_rating_for_recipes()

        # 2. test

        response = self.client.get(
            reverse('recipe:recipe_favorite_cuisines'),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        response = self.client.get(
            reverse('recipe:recipe_favorite_cuisines'),
            {'cuisine': cuisine}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # related to avg_rating, not used anymore
        """
        self.assertEqual(response.data[0]['pk'], recipes[2].pk)
        self.assertEqual(response.data[1]['pk'], recipes[1].pk)
        self.assertEqual(response.data[2]['pk'], recipes[0].pk)
        """

    def test_homepage_banners(self):

        files = get_test_files()
        for f in files:
            Banner.objects.create(image=f)

        response = self.anonymous_client.get(
            reverse('recipe:recipe_homepage_banners'),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_pinned_meals(self):
        for _ in range(5):
            data = copy.deepcopy(self.BASIC_TEST_DATA)
            recipe = Recipe.objects.create(**data)
            HomepagePinnedRecipe.objects.create(recipe=recipe)

        self.assertEqual(HomepagePinnedRecipe.objects.count(), 5)

        response = self.client.get(
            reverse('recipe:recipe_pinned'),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_meal_of_the_weak(self):
        for _ in range(5):
            data = copy.deepcopy(self.BASIC_TEST_DATA)
            recipe = Recipe.objects.create(**data)
            MealOfTheWeekRecipe.objects.create(recipe=recipe)

        self.assertEqual(MealOfTheWeekRecipe.objects.count(), 5)

        response = self.client.get(
            reverse('recipe:meal_of_the_week'),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_top_rated_meals(self):

        for _ in range(5):
            data = copy.deepcopy(self.BASIC_TEST_DATA)
            recipe = Recipe.objects.create(**data)
            TopRatedRecipe.objects.create(recipe=recipe)

        self.assertEqual(TopRatedRecipe.objects.count(), 5)

        response = self.client.get(
            reverse('recipe:recipe_top_rated'),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_featured_meals(self):

        response = self.client.get(
            reverse('recipe:recipe_featured'),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        for _ in range(3):
            data = copy.deepcopy(self.BASIC_TEST_DATA)
            recipe = Recipe.objects.create(**data)
            FeaturedRecipe.objects.create(recipe=recipe)

        self.assertEqual(FeaturedRecipe.objects.count(), 3)

        response = self.client.get(
            reverse('recipe:recipe_featured'),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # random

        for _ in range(3):
            data = copy.deepcopy(self.BASIC_TEST_DATA)
            recipe = Recipe.objects.create(**data)
            FeaturedRecipe.objects.create(recipe=recipe)

        response = self.client.get(
            reverse('recipe:recipe_featured'),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)  # random

    def test_create_comments_and_comment_likes(self):
        Recipe.objects.create(**self.BASIC_TEST_DATA)
        recipe1 = Recipe.objects.all().order_by('pk')[0]

        # comment for non-existing recipe
        response = self.anonymous_client.get(
            reverse('recipe:recipe_comment_list_create', args=[153])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        # create 5 comments
        for i in range(5):
            response = self.home_chef_client.post(
                reverse('recipe:recipe_comment_list_create', args=[recipe1.pk]),
                {'text': f'comment #{i}: {DESCRIPTION}'}
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Comment.objects.count(), 5)

        recipe_comment_1 = Comment.objects.first()

        # 5 comment likes
        for i in range(5):
            user = self.create_random_user(extra_fields={'is_email_active': True})
            client = self.create_client_with_auth(user)

            response = client.post(
                reverse('recipe:recipe_comment_like', args=[recipe_comment_1.pk]),
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # this last like will be auto-deleted
        response = client.post(
            reverse('recipe:recipe_comment_like', args=[recipe_comment_1.pk]),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 5 comment dis-likes
        for i in range(5):
            user = self.create_random_user(extra_fields={'is_email_active': True})
            client = self.create_client_with_auth(user)

            response = client.post(
                reverse('recipe:recipe_comment_like', args=[recipe_comment_1.pk]),
                {'dislike': 'Y'}
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # get comments
        response = self.anonymous_client.get(
            reverse('recipe:recipe_comment_list_create', args=[recipe1.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)
        self.assertEqual(response.data['results'][-1]['likes_number'], 4)
        self.assertEqual(response.data['results'][-1]['dislikes_number'], 5)
        self.assertTrue(response.data['results'][-1]['text'].startswith('comment #0'))  # means: first comment at the top

    def test_comment_like_after_dislike(self):
        Recipe.objects.create(**self.BASIC_TEST_DATA)
        recipe1 = Recipe.objects.all().order_by('pk')[0]

        response = self.home_chef_client.post(
            reverse('recipe:recipe_comment_list_create',
                    args=[recipe1.pk]),
            {'text': f'comment #0: {DESCRIPTION}'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)

        recipe_comment_1 = Comment.objects.first()

        user = self.create_random_user(extra_fields={'is_email_active': True})
        client = self.create_client_with_auth(user)

        response = client.post(
            reverse('recipe:recipe_comment_like',
                    args=[recipe_comment_1.pk]),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CommentLike.objects.filter(is_dislike=False).count(), 1)

        response = client.post(
            reverse('recipe:recipe_comment_like',
                    args=[recipe_comment_1.pk]),
            {'dislike': 'Y'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # get comments
        response = self.anonymous_client.get(
            reverse('recipe:recipe_comment_list_create', args=[recipe1.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['likes_number'], 0)
        self.assertEqual(response.data['results'][0]['dislikes_number'], 1)
        self.assertEqual(CommentLike.objects.filter(is_dislike=True).count(), 1)

    def test_search_suggestions(self):

        titles = [
            ('Thai Coconut Curry Soup', 3,),
            ('Thai Coconut Curry Lentil Soup', 5,),
            ('Green Thai Curry with Beef', 4,),
            ('Italian tomato and mozzarella caprese', 4)
        ]

        recipes = []
        for info in titles:
            data = copy.deepcopy(self.BASIC_TEST_DATA)
            data.update({'title': [info[0]], 'avg_rating': info[1]})
            recipes.append(Recipe.objects.create(**data))

        response = self.anonymous_client.get(
            reverse('recipe:search_suggestions'),
            {'search': 'curry'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]['result'], 'curry lentil')
        self.assertEqual(response.data[1]['result'], 'curry soup')
        self.assertEqual(response.data[2]['result'], 'curry with')

        response = self.anonymous_client.get(
            reverse('recipe:search_suggestions'),
            {'search': 'mozza'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['result'], 'mozzarella caprese')

        # search with suggested string
        response = self.anonymous_client.get(
            reverse('recipe:recipe_list_create'),
            {'title': 'curry soup'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_popular_recipes(self):
        recipes = []

        response = self.client.get(
            reverse('recipe:recipe_popular'),
            {'cuisines': Cuisines.INDONISIAN.value, 'types': RecipeTypes.BREAKFAST.value}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # after recipes added

        for i in range(7):
            data = copy.deepcopy(self.BASIC_TEST_DATA)
            data.update({
                'avg_rating': 4 + i / 10
            })
            recipes.append(Recipe.objects.create(**data))

        response = self.client.get(
            reverse('recipe:recipe_popular'),
            # {'cuisines': Cuisines.INDONISIAN.value, 'types': RecipeTypes.BREAKFAST.value}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
        """
        # initially proposed filtering is disabled for now
        self.assertEqual(response.data[0]['pk'], recipes[-1].pk)
        self.assertEqual(response.data[1]['pk'], recipes[-2].pk)
        self.assertEqual(response.data[2]['pk'], recipes[-3].pk)
        self.assertEqual(response.data[3]['pk'], recipes[-4].pk)
        """

    def test_latest_recipes_by_user(self):

        response = self.client.get(reverse('recipe:recipe_latest'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        data = copy.deepcopy(self.BASIC_TEST_DATA)
        Recipe.objects.create(**data)

        response = self.client.get(reverse('recipe:recipe_latest'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        recipes = []
        for i in range(7):
            data = copy.deepcopy(self.BASIC_TEST_DATA)
            recipes.append(Recipe.objects.create(**data))

        response = self.client.get(reverse('recipe:recipe_latest'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_user_recipes_list(self):

        recipes = []
        for i in range(7):
            data = copy.deepcopy(self.BASIC_TEST_DATA)
            recipes.append(Recipe.objects.create(**data))

        self.assertEqual(Recipe.objects.all().count(), 7)
        self.assertEqual(Recipe.objects.all().filter(user=self.home_chef_user).count(), 7)

        response = self.anonymous_client.get(
            reverse('recipe:recipe_user_list', args=(self.home_chef_user.pk,)),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 7)

    def test_upload_video(self):

        # is not used if googlecloud is enabled
        if settings.DEFAULT_FILE_STORAGE.endswith('FileSystemStorage'):

            response = self.home_chef_client.post(
                reverse('recipe:upload_video'),
                data={
                    'video': get_test_video_file()
                },
                format='multipart'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_upload_image(self):

        # is not used if googlecloud is enabled
        if settings.DEFAULT_FILE_STORAGE.endswith('FileSystemStorage'):

            response = self.home_chef_client.post(
                reverse('recipe:upload_image'),
                data={
                    'file': get_test_files()[0]
                },
                format='multipart'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_reorder_images(self):

        data = {
            'user': self.home_chef_user.pk,
            'title': 'Grilled Basil Chicken',
            'description': DESCRIPTION,
            'language': 'English',
            'caption': 'Caption',
            "cuisines": [
                Cuisines.INDIAN.value,
                Cuisines.ITALIAN.value,
                Cuisines.AMERICAN.value
            ],
            "types": [
                RecipeTypes.BREAKFAST.value
            ],
            "cooking_time": "00:00",
            "cooking_methods": [
                CookingMethods.BAKING.value
            ],
            "cooking_skills": CookingSkills.EASY.value,
            "diet_restrictions": [
                Diets.DAIRY_FREE.value,
                Diets.GLUTEN_FREE.value
            ],
            "ingredients": [
                {
                    "title": "First",
                    "quantity": "10",
                    "unit": Units.OUNCE
                },
                {
                    "title": "Second",
                    "quantity": "2.5",
                    "unit": Units.TABLESPOON
                }
            ]
        }

        images_ids = []
        for f in get_test_files():
            ri = RecipeImage.objects.create(
                user=self.home_chef_user,
                file=f
            )
            if Path(f.name).name == "test_image1.jpg":
                data['main_image'] = ri.pk
            images_ids.append(ri.pk)
        data['images'] = images_ids  # 1,2
        payload = {
            'data': json.dumps(data),
        }
        response = self.home_chef_client.post(
            reverse('recipe:recipe_list_create'),
            data=payload,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['images']), 2)
        Recipe.objects.all().update(publish_status=Recipe.PublishStatus.PUBLISHED)

        first_id = response.data['images'][0]['id']
        second_id = response.data['images'][1]['id']

        indexes = []
        indexes.append(second_id)
        indexes.append(first_id)  # 2,1

        response = self.home_chef_client.patch(
            reverse('recipe:recipe_retrieve_update_destroy', args=[response.data['pk']]),
            {'data': json.dumps({'images': indexes})},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['images'][0]['id'], second_id)

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            shutil.rmtree(Path(settings.MEDIA_ROOT) / 'recipe_video')
            shutil.rmtree(Path(settings.MEDIA_ROOT) / 'recipe_image_files')
            shutil.rmtree(Path(settings.MEDIA_ROOT) / 'b_images')
        except OSError as e:
            print(e)
        return super().tearDownClass()


class SavedRecipeTestCase(IsAuthClientTestCase):

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
            'description': DESCRIPTION,
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

    def test_list_saved_recipes(self):

        for i in range(3):
            data = copy.deepcopy(self.BASIC_TEST_DATA)
            data['types'] = [i+1, i+2]  # 1,2; 2,3; 3,4
            recipe = Recipe.objects.create(**data)
            saved_recipe = SavedRecipe.objects.create(recipe=recipe, user=self.home_chef_user)

        self.assertEqual(SavedRecipe.objects.count(), 3)

        response = self.anonymous_client.get(
            reverse('recipe:recipe_saved_recipe')
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.home_chef_client.get(
            reverse('recipe:recipe_saved_recipe')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

        response = self.home_chef_client.get(
            reverse('recipe:recipe_saved_recipe'),
            {'types': "1,4"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_create_saved_recipe(self):

        data = copy.deepcopy(self.BASIC_TEST_DATA)
        recipe = Recipe.objects.create(**data)

        response = self.anonymous_client.get(reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['user_saved_recipe'])

        response = self.home_chef_client.get(reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['user_saved_recipe'])

        response = self.home_chef_client.post(
            reverse('recipe:recipe_saved_recipe'),
            {'recipe': recipe.pk}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data['recipe']['user_saved_recipe'], False)
        self.assertEqual(SavedRecipe.objects.count(), 1)

        response = self.home_chef_client.get(reverse('recipe:recipe_retrieve_update_destroy', args=[recipe.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['user_saved_recipe'], 0)

    def test_delete_saved_recipe(self):

        data = copy.deepcopy(self.BASIC_TEST_DATA)
        recipe = Recipe.objects.create(**data)

        saved_recipe = SavedRecipe.objects.create(
            recipe=recipe,
            user=self.home_chef_user
        )
        self.assertEqual(SavedRecipe.objects.count(), 1)

        response = self.client.delete(
            reverse('recipe:recipe_saved_recipe_retrieve_destroy', args=(saved_recipe.pk,))
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.home_chef_client.delete(
            reverse('recipe:recipe_saved_recipe_retrieve_destroy', args=(saved_recipe.pk,))
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(SavedRecipe.objects.count(), 0)


class RecipeParserTestCase(IsAuthClientTestCase):

    def setUp(self):
        super().setUp()

    def test_A_add_recipe_from_json(self):

        user = self.create_random_user(extra_fields={'is_email_active': True})

        with open('test_files/test_recipe_data.json', 'r') as f:
            recipe_data = json.load(f)

        rc = RecipeCreator(recipe_data=recipe_data, user=user)
        recipe = rc.add_recipe()
        self.assertEqual(Ingredient.objects.count(), 22)

    def test_B_parser_settings(self):

        parser = RecipeApiParser(
            requests_per_day=10,
            results_per_day=40
        )
        parser.save_settings()

        parser.today_results += 1
        parser.today_requests += 1
        parser.save_settings()
        self.assertEqual(parser.settings.today_results, 1)
        self.assertEqual(parser.settings.today_requests, 1)

        # check limits
        parser.today_results += 39
        parser.save_settings()
        with self.assertRaises(LimitsExceededError):
            parser.check_limits()

        parser.today_results -= 1
        parser.save_settings()
        parser.check_limits()

        parser.today_requests += 9
        parser.save_settings()
        with self.assertRaises(LimitsExceededError):
            parser.check_limits()

    def test_C_parser_download(self):

        self.assertEqual(Recipe.objects.all().count(), 0)

        parser = RecipeApiParser(
            requests_per_day=30,
            results_per_day=50
        )
        try:
            parser.download_recipes()
        except LimitsExceededError:
            self.assertEqual(parser.today_requests, 26)
            self.assertEqual(parser.today_results, 50)

        self.assertEqual(Recipe.objects.all().count(), 21)

    def test_prepare_descripton(self):

        text = """The recipe Tofu with Thai Curry Sauce is ready <b>in roughly 20 minutes</b> and is definitely a spectacular <b>gluten free,
        fodmap friendly, and vegan</b> option for lovers of Asian food. For <b>$1.49 per serving</b>,
        this recipe <b>covers 21%</b> of your daily requirements of vitamins and minerals.
        This recipe makes 4 servings with <b>108 calories</b>, <b>9g of protein</b>,
        and <b>5g of fat</b> each. 698 people have made this recipe and would make it again.
        It works well as a side dish. A mixture of cilantro, olive oil, salt, and a handful of other ingredients are all
        it takes to make this recipe so scrumptious. All things considered, we decided this recipe
        <b>deserves a spoonacular score of 100%</b>. This score is tremendous.
        Try <a href="https://spoonacular.com/recipes/noodles-in-thai-curry-sauce-with-tofu-37080">Noodles In Thai Curry Sauce With Tofu</a>,
        <a href="https://spoonacular.com/recipes/thai-tofu-w-red-curry-sauce-over-coconut-scallion-rice-110536">Thai Tofu W/Red Curry Sauce
        over Coconut Scallion Rice</a>, and <a href="https://spoonacular.com/recipes/thai-curry-tofu-471423">Thai Curry Tofu</a> for similar recipes."""

        text_without_links = """The recipe Tofu with Thai Curry Sauce is ready <b>in roughly 20 minutes</b> and is definitely a spectacular <b>gluten free,
        fodmap friendly, and vegan</b> option for lovers of Asian food. For <b>$1.49 per serving</b>,
        this recipe <b>covers 21%</b> of your daily requirements of vitamins and minerals.
        This recipe makes 4 servings with <b>108 calories</b>, <b>9g of protein</b>,
        and <b>5g of fat</b> each. 698 people have made this recipe and would make it again.
        It works well as a side dish. A mixture of cilantro, olive oil, salt, and a handful of other ingredients are all
        it takes to make this recipe so scrumptious. All things considered, we decided this recipe
        <b>deserves a spoonacular score of 100%</b>. This score is tremendous.
        Try Noodles In Thai Curry Sauce With Tofu,
        Thai Tofu W/Red Curry Sauce over Coconut Scallion Rice, and Thai Curry Tofu for similar recipes."""

        result = strip_links(text)

        self.assertEqual(
            re.sub('(\s)+', ' ', result.replace('\n', '')),
            re.sub('(\s)+', ' ', text_without_links.replace('\n', '')),
        )