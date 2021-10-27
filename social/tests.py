from utils.email import SEND_NEW_COMMENTS_IN_RECIPE
from main.utils.test import IsAuthClientTestCase

from recipe.tasks import check_new_comments_for_recipes
from django.core import mail
from rest_framework.reverse import reverse
from rest_framework import status
from datetime import timedelta

from chef_pencils.models import ChefPencilRecord

import copy
from recipe.models import Recipe
from recipe.enums import (
    Cuisines,
    RecipeTypes,
    CookingMethods,
    CookingSkills,
    Diets
)
from social.models import Comment
from django.conf import settings

DESCRIPTION = """
Wash hands with soap and water.
After washing basil and tomatoes, blot them dry with clean paper towel.
Using a clean cutting board, cut tomatoes into quarters.
For marinade, place first six ingredients in a blender. Cover and process until well blended.
Place chicken breasts in a shallow dish; orange quote icon do not rinse raw poultry.
Cover with marinade. Cover dish. Refrigerate about 1 hour, turning occasionally.
Wash dish after touching raw poultry.
Wash hands with soap and water after handling uncooked chicken.
Place chicken on an oiled grill rack over medium heat.
Do not reuse marinades used on raw foods. Grill chicken 4-6 minutes per side.
Cook until internal temperature reaches 165 °F as measured with a food thermometer.
"""

class CommentTestCase(IsAuthClientTestCase):

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

    def test_notify_about_comments(self):

        # 1. create recipe

        data = copy.deepcopy(self.BASIC_TEST_DATA)
        data.update({
            'status': Recipe.Status.ACCEPTED,
            'publish_status': Recipe.PublishStatus.PUBLISHED
        })
        recipe = Recipe.objects.create(**data)

        # 2. create 3 comments

        user = self.create_random_user(extra_fields={'is_email_active': True})

        comment = Comment.objects.create(user=user, content_object=recipe, text='comment1')
        comment = Comment.objects.create(user=user, content_object=recipe, text='comment2')
        comment = Comment.objects.create(user=self.home_chef_user, content_object=recipe, text='comment3')

        mail.outbox = []

        check_new_comments_for_recipes()

        outbox = mail.outbox
        self.assertEqual(len(outbox), 1, "Inbox is not empty")
        self.assertEqual(outbox[0].subject, SEND_NEW_COMMENTS_IN_RECIPE)
        self.assertEqual(outbox[0].from_email, settings.EMAIL_FROM)
        self.assertEqual(outbox[0].to, [self.home_chef_user.email])
        self.assertTrue('2 new comment' in str(outbox[0].message()))

    def test_dont_notify_about_own_comments(self):

        # 1. create recipe

        data = copy.deepcopy(self.BASIC_TEST_DATA)
        data.update({
            'status': Recipe.Status.ACCEPTED,
            'publish_status': Recipe.PublishStatus.PUBLISHED
        })
        recipe = Recipe.objects.create(**data)

        # 2. create 3 comments

        user = self.create_random_user(extra_fields={'is_email_active': True})

        comment = Comment.objects.create(
            user=self.home_chef_user, content_object=recipe, text='comment3')

        mail.outbox = []

        check_new_comments_for_recipes()

        outbox = mail.outbox
        self.assertEqual(len(outbox), 0)

    def test_delete_own_recipe_comment(self):

        # 1. create recipe

        data = copy.deepcopy(self.BASIC_TEST_DATA)
        data.update({
            'status': Recipe.Status.ACCEPTED,
            'publish_status': Recipe.PublishStatus.PUBLISHED
        })
        recipe = Recipe.objects.create(**data)

        # 2. create 3 comments

        user = self.create_random_user(extra_fields={'is_email_active': True})
        self.client = self.create_client_with_auth(user)

        comment1 = Comment.objects.create(user=user, content_object=recipe, text='comment1')
        comment2 = Comment.objects.create(user=self.home_chef_user, content_object=recipe, text='comment2')
        comment3 = Comment.objects.create(user=user, content_object=recipe, text='comment1')

        response = self.client.delete(reverse('recipe:recipe_comment_delete', args=[comment1.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=comment1.pk).exists())

        response = self.home_chef_client.delete(reverse('recipe:recipe_comment_delete', args=[comment1.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Comment.objects.filter(pk=comment2.pk).exists())

        # after 2 hours

        comment3.created_at = comment3.created_at - timedelta(hours=2, seconds=1)
        comment3.save()

        response = self.client.delete(reverse('recipe:recipe_comment_delete', args=[comment3.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Comment.objects.filter(pk=comment3.pk).exists())

    def test_delete_own_chef_pencil_comment(self):

        # 1. create chef pencil record

        data = {
            'user': self.home_chef_user,
            'title': 'updated',
            'html_content': 'updated content'
        }
        cp = ChefPencilRecord.objects.create(**data)

        # 2. create 3 comments

        user = self.create_random_user(extra_fields={'is_email_active': True})
        self.client = self.create_client_with_auth(user)

        comment1 = Comment.objects.create(user=user, content_object=cp, text='comment1')
        comment2 = Comment.objects.create(user=self.home_chef_user, content_object=cp, text='comment2')
        comment3 = Comment.objects.create(user=user, content_object=cp, text='comment1')

        response = self.client.delete(reverse('chef_pencil:chef_pencil_comment_delete', args=[comment1.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=comment1.pk).exists())

        response = self.home_chef_client.delete(reverse('chef_pencil:chef_pencil_comment_delete', args=[comment1.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Comment.objects.filter(pk=comment2.pk).exists())

        # after 2 hours

        comment3.created_at = comment3.created_at - timedelta(hours=2, seconds=1)
        comment3.save()

        response = self.client.delete(reverse('chef_pencil:chef_pencil_comment_delete', args=[comment3.pk]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Comment.objects.filter(pk=comment3.pk).exists())
