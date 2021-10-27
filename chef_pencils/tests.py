import copy
import json
import shutil
from pathlib import Path
from pprint import pprint

from django.conf import settings
from main.utils.test import (IsAuthClientTestCase, TestDataService,
                             create_random_sentence)
from rest_framework import status
from rest_framework.reverse import reverse
from social.models import Comment, CommentLike, Like, Rating
from users.enums import UserTypes
from utils.test import get_alt_test_files, get_test_files

from chef_pencils.models import (ChefPencilCategory, ChefPencilImage,
                                 ChefPencilRecord, SavedChefPencilRecord)
from chef_pencils.tasks import (calculate_avg_rating_for_chef_pencils,
                                calculate_likes_for_chef_pencil_records)

TEXT = """Maecenas enim lacus, rhoncus eu sagittis ut, tincidunt eu magna.
Proin sit amet mollis eros. Suspendisse id tellus odio. Cras in nisl quis elit
convallis semper pulvinar eu turpis. Pellentesque habitant morbi tristique senectus
et netus et malesuada fames ac turpis egestas. Quisque vestibulum nulla lorem,
vel mollis mi semper nec. Proin id massa dapibus, fermentum nunc id, condimentum
lorem. Fusce eget dapibus metus. Proin luctus, augue sed feugiat hendrerit,
ipsum nisi tristique elit, lobortis tristique tellus ipsum varius justo."""

class ChefPencilTestCase(IsAuthClientTestCase):
    test_data_service = TestDataService()

    def setUp(self):
        super().setUp()
        self.home_chef_user = self.create_random_user(extra_fields={'is_email_active': True})
        self.home_chef_user.user_type = UserTypes.HOME_CHEF.value
        self.home_chef_user.save()
        self.home_chef_client = self.create_client_with_auth(
            self.home_chef_user)

    def test_create_by_customer(self):
        user = self.create_random_user(extra_fields={'is_email_active': True})
        user.user_type = UserTypes.CUSTOMER.value
        user.save()
        self.customer_client = self.create_client_with_auth(user)
        response = self.customer_client.post(
            reverse('chef_pencil:chef_pencil_list_create'), data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _create_chefpencil_record(self, title='Grilled Basil Chicken information', html_content=TEXT, categories=None):
        """
        Create ChefPencilRecord with
        """

        if categories is None:
            categories = []

        data = {
            'user': self.home_chef_user.pk,
            'title': title,
            'html_content': html_content,
            'categories': categories
        }
        payload = {
            'data': json.dumps(data),
        }

        for i, file in enumerate(get_test_files()):
            payload[f'images[{i}]'] = file

        response = self.home_chef_client.post(
            reverse('chef_pencil:chef_pencil_list_create'),
            data=payload,
            format='multipart'
        )
        return response

    def test_create_by_home_chef(self):

        c1 = ChefPencilCategory.objects.create(title='category1')
        c2 = ChefPencilCategory.objects.create(title='category2')

        response = self._create_chefpencil_record(categories=[c1.pk, c2.pk])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cpr = ChefPencilRecord.objects.get(pk=response.data['pk'])
        self.assertEqual(cpr.title, 'Grilled Basil Chicken information')
        self.assertEqual(cpr.images.all().count(), 2)
        self.assertEqual(cpr.chefpencilcategory_set.all().count(), 2)

    def test_chef_pencil_update_and_retrieve(self):

        response = self._create_chefpencil_record()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # retrieve
        cr = ChefPencilRecord.objects.first()
        prev_image_name = str(cr.images.all()[0].image.name)

        self.anonymous_client.get(
            reverse('chef_pencil:retrieve_update_destroy', args=[cr.pk]),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        images_to_delete = [i['id'] for i in response.data['images']]

        # update
        data = {
            'user': self.home_chef_user.pk,
            'title': 'updated',
            'html_content': 'updated content',
            'images_to_delete': images_to_delete
        }
        payload = {
            'data': json.dumps(data),
            'images[0]': get_alt_test_files()[1]
        }
        response = self.home_chef_client.patch(
            reverse('chef_pencil:retrieve_update_destroy',
                    args=[cr.pk]),
            payload,
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'updated')
        self.assertEqual(response.data['html_content'], 'updated content')

        self.assertEqual(ChefPencilImage.objects.all().count(), 1)

        updated_cr = ChefPencilRecord.objects.first()
        self.assertNotEqual(
            prev_image_name,
            str(updated_cr.images.all()[0].image.name)
        )

    def test_chef_pencil_update_categories(self):

        c1 = ChefPencilCategory.objects.create(title='category1')
        c2 = ChefPencilCategory.objects.create(title='category2')
        c3 = ChefPencilCategory.objects.create(title='category3')
        c4 = ChefPencilCategory.objects.create(title='category4')

        response = self._create_chefpencil_record(categories=[c1.pk, c2.pk])
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cpr = ChefPencilRecord.objects.get(pk=response.data['pk'])
        self.assertEqual(cpr.title, 'Grilled Basil Chicken information')
        self.assertEqual(cpr.images.all().count(), 2)
        self.assertEqual(cpr.chefpencilcategory_set.all().count(), 2)

        # update
        data = {
            'categories': [c3.pk, c4.pk]
        }
        payload = {
            'data': json.dumps(data),
        }
        response = self.home_chef_client.patch(
            reverse('chef_pencil:retrieve_update_destroy', args=[cpr.pk]),
            payload,
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['categories'], [{'pk': c3.pk, 'title': 'category3'}, {'pk': c4.pk, 'title': 'category4'}])

    def test_chef_pencil_images_reorder(self):

        response = self._create_chefpencil_record()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # retrieve
        cr = ChefPencilRecord.objects.first()

        self.anonymous_client.get(reverse('chef_pencil:retrieve_update_destroy', args=[cr.pk]))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        images = [
            {
                'id': 1,
                'main_image': True,
                'order_index': 0,
                'url': 'http://localhost:4096/media/chef_pencils/295bcd6b8668ef4a6a63f79aca93615d.jpg'
            },
            {
                'id': 2,
                 'main_image': False,
                 'order_index': 1,
                 'url': 'http://localhost:4096/media/chef_pencils/4af3007143286f5d83141d1022290f06.jpg'
            }
        ]
        self.assertEqual(response.data['images'], images)

        # update
        images = [
            {
                'id': 2,
                'url': 'http://localhost:4096/media/chef_pencils/4af3007143286f5d83141d1022290f06.jpg'
            },
            {
                'id': 1,
                'url': 'http://localhost:4096/media/chef_pencils/295bcd6b8668ef4a6a63f79aca93615d.jpg'
            }
        ]
        payload = {
            'data': json.dumps({'images': images}),
            'images[0]': get_alt_test_files()[0],  # will be always added as last (at first)
            'images[1]': get_alt_test_files()[1]
        }
        response = self.home_chef_client.patch(
            reverse('chef_pencil:retrieve_update_destroy', args=[cr.pk]),
            payload,
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['images'], [
                {
                    'id': 2,
                    'main_image': False,
                    'order_index': 0,
                    'url': 'http://localhost:4096/media/chef_pencils/4af3007143286f5d83141d1022290f06.jpg'
                },
                {
                    'id': 1,
                    'main_image': True,
                    'order_index': 1,
                    'url': 'http://localhost:4096/media/chef_pencils/295bcd6b8668ef4a6a63f79aca93615d.jpg'
                },
                {
                    'id': 3,
                    'main_image': False,
                    'order_index': 2,
                    'url': 'http://localhost:4096/media/chef_pencils/106c05b9bb3c4edecd0bcfc70054095e.jpg'
                },
                {
                    'id': 4,
                    'main_image': False,
                    'order_index': 3,
                    'url': 'http://localhost:4096/media/chef_pencils/1afd5aefe14f52ffb7d9a7941ae759b1.jpg'
                }
            ]
        )
        self.assertEqual(ChefPencilImage.objects.all().count(), 4)

        # update 2
        images = [
            {
                'id': 4,
                'main_image': False,
                'order_index': 3,
                'url': 'http://localhost:4096/media/chef_pencils/1afd5aefe14f52ffb7d9a7941ae759b1.jpg'
            },
            {
                'id': 3,
                'main_image': False,
                'order_index': 2,
                'url': 'http://localhost:4096/media/chef_pencils/106c05b9bb3c4edecd0bcfc70054095e.jpg'
            },
            {
                'id': 2,
                'main_image': False,
                'order_index': 0,
                'url': 'http://localhost:4096/media/chef_pencils/4af3007143286f5d83141d1022290f06.jpg'
            },
            {
                'id': 1,
                'main_image': True,
                'order_index': 1,
                'url': 'http://localhost:4096/media/chef_pencils/295bcd6b8668ef4a6a63f79aca93615d.jpg'
            }
        ]
        payload = {
            'data': json.dumps({'images': images}),
        }
        response = self.home_chef_client.patch(
            reverse('chef_pencil:retrieve_update_destroy', args=[cr.pk]),
            payload,
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['images'], [
                {
                    'id': 4,
                    'main_image': False,
                    'order_index': 0,
                    'url': 'http://localhost:4096/media/chef_pencils/1afd5aefe14f52ffb7d9a7941ae759b1.jpg'
                },
                {
                    'id': 3,
                    'main_image': False,
                    'order_index': 1,
                    'url': 'http://localhost:4096/media/chef_pencils/106c05b9bb3c4edecd0bcfc70054095e.jpg'
                },
                {
                    'id': 2,
                    'main_image': False,
                    'order_index': 2,
                    'url': 'http://localhost:4096/media/chef_pencils/4af3007143286f5d83141d1022290f06.jpg'
                },
                {
                    'id': 1,
                    'main_image': True,
                    'order_index': 3,
                    'url': 'http://localhost:4096/media/chef_pencils/295bcd6b8668ef4a6a63f79aca93615d.jpg'
                }
            ]
        )

    def test_chef_pencil_update_without_image(self):

        response = self._create_chefpencil_record()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # retrieve
        cr = ChefPencilRecord.objects.first()
        prev_image_name = cr.images.all()[0].image.name

        # update without image

        data = {
            'user': self.home_chef_user.pk,
            'title': 'updated',
            'html_content': 'updated content'
        }
        payload = {
            'data': json.dumps(data),
        }
        response = self.home_chef_client.patch(
            reverse('chef_pencil:retrieve_update_destroy',
                    args=[response.data['pk']]),
            payload,
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'updated')
        self.assertEqual(response.data['html_content'], 'updated content')

        updated_cr = ChefPencilRecord.objects.first()
        self.assertEqual(
            prev_image_name,
            updated_cr.images.all()[0].image.name
        )

    def test_list_chef_pencils(self):

        for i in range(5):
            response = self._create_chefpencil_record()
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ChefPencilRecord.objects.update(status=ChefPencilRecord.Status.APPROVED)

        response = self.client.get(reverse('chef_pencil:chef_pencil_list_create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)

    def test_search_chef_pencils(self):

        for i in range(5):
            title = create_random_sentence() + ' test' if i == 0 else create_random_sentence()
            html_content = '. '.join([create_random_sentence() for i in range(5)])
            if i == 2:
                html_content += '. test to search.'

            response = self._create_chefpencil_record(title, html_content)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ChefPencilRecord.objects.update(status=ChefPencilRecord.Status.APPROVED)

        response = self.client.get(
            reverse('chef_pencil:chef_pencil_list_create'),
            {'search': 'test'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_create_ratings(self):

        for i in range(2):
            response = self._create_chefpencil_record()
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        cpr1 = ChefPencilRecord.objects.all().order_by('pk')[0]
        cpr2 = ChefPencilRecord.objects.all().order_by('pk')[1]

        ratings1 = [3, 4, 3]
        ratings2 = [5, 5, 4]
        for i in range(3):

            user = self.create_random_user(extra_fields={'is_email_active': True})
            client = self.create_client_with_auth(user)

            response = client.post(
                reverse('chef_pencil:chef_pencil_rate', args=[cpr1.pk]),
                data={'rating': ratings1[i]}
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

            response = client.post(
                reverse('chef_pencil:chef_pencil_rate', args=[cpr2.pk]),
                data={'rating': ratings2[i]}
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Rating.objects.filter(
            content_type__model='chefpencilrecord').count(), 6)

        calculate_avg_rating_for_chef_pencils()

        cpr = ChefPencilRecord.objects.get(pk=cpr1.pk)
        self.assertEqual(cpr.avg_rating, 3.3)

        cpr = ChefPencilRecord.objects.get(pk=cpr2.pk)
        self.assertEqual(cpr.avg_rating, 4.7)

    def test_create_comments_and_comment_likes(self):

        response = self._create_chefpencil_record()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cpr1 = ChefPencilRecord.objects.all().order_by('pk')[0]

        for i in range(5):
            response = self.home_chef_client.post(
                reverse('chef_pencil:chef_pencil_comment_list_create',
                        args=[cpr1.pk]),
                {'text': f'comment #{i}: {TEXT}'}
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Comment.objects.count(), 5)

        comment_1 = Comment.objects.first()

        for i in range(5):
            user = self.create_random_user(extra_fields={'is_email_active': True})
            client = self.create_client_with_auth(user)
            response = client.post(
                reverse('chef_pencil:chef_pencil_comment_like',
                        args=[comment_1.pk]),
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # list comments
        response = self.anonymous_client.get(
            reverse('chef_pencil:chef_pencil_comment_list_create', args=[cpr1.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 5)
        self.assertEqual(response.data['results'][0]['likes_number'], 5)
        self.assertTrue(response.data['results'][0]['text'].startswith(
            'comment #0'))  # means: first comment at the top

    def test_latest_chef_pencils_records(self):

        response = self.client.get(reverse('chef_pencil:latest_chef_pencils'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # add more

        response = self._create_chefpencil_record()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(reverse('chef_pencil:latest_chef_pencils'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_search_suggestions_for_chef_pencils(self):

        titles = [
            ('We have a new Coconut Curry Soup', 3,),
            ('Top 10 coconut dishes', 5,),
            ('My favorite cookies', 4,),
            ('Italian cookies', 4)
        ]

        chef_records = []
        for info in titles:
            data = {
                'user': self.home_chef_user,
                'html_content': TEXT
            }
            data.update({'title': [info[0]], 'avg_rating': info[1]})
            chef_records.append(ChefPencilRecord.objects.create(**data))

        ChefPencilRecord.objects.update(status=ChefPencilRecord.Status.APPROVED)

        response = self.anonymous_client.get(
            reverse('chef_pencil:search_suggestions'),
            {'search': 'coconut'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['result'], 'coconut curry')
        self.assertEqual(response.data[1]['result'], 'coconut dishes')

        # search with suggested string
        response = self.client.get(
            reverse('chef_pencil:chef_pencil_list_create'),
            {'search': 'coconut'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_chef_pencils_category_view(self):

        for i in range(3):
            cpc = ChefPencilCategory(title=f'category {i}')
            cpc.save()

        response = self.client.get(reverse('chef_pencil:categories'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 4)

    def test_create_likes_for_chef_pencils(self):

        response1 = self._create_chefpencil_record()
        response2 = self._create_chefpencil_record()

        for i in range(3):

            user = self.create_random_user(extra_fields={'is_email_active': True})
            client = self.create_client_with_auth(user)

            # like #1

            response = client.get(reverse('chef_pencil:retrieve_update_destroy', args=[response1.data['pk']]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.data['user_liked'])

            response = client.post(
                reverse('chef_pencil:chef_pencil_like', args=[response1.data['pk']])
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['like_status'], 'created')

            response = client.get(reverse('chef_pencil:retrieve_update_destroy', args=[response1.data['pk']]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['user_liked'])

            # anonymous client has no likes

            response = self.anonymous_client.get(reverse('chef_pencil:retrieve_update_destroy', args=[response1.data['pk']]))
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertFalse(response.data['user_liked'])

            # like #2

            response = client.post(
                reverse('chef_pencil:chef_pencil_like', args=[response2.data['pk']])
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Like.objects.count(), 6)

        calculate_likes_for_chef_pencil_records()

        cp = ChefPencilRecord.objects.get(pk=response1.data['pk'])
        self.assertEqual(cp.likes_number, 3)

        cp = ChefPencilRecord.objects.get(pk=response2.data['pk'])
        self.assertEqual(cp.likes_number, 3)

    def test_unlike_recipe(self):

        user = self.create_random_user(extra_fields={'is_email_active': True})
        client = self.create_client_with_auth(user)

        response1 = self._create_chefpencil_record()

        cp1 = ChefPencilRecord.objects.get(pk=response1.data['pk'])

        Like.objects.create(
            user=user,
            content_object=cp1
        )

        response = client.post(
            reverse('chef_pencil:chef_pencil_like', args=[response1.data['pk']])
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['like_status'], 'deleted')

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            shutil.rmtree(Path(settings.MEDIA_ROOT) / 'chef_pencils')
        except OSError as e:
            print(e)
        return super().tearDownClass()


class SavedChefPencilRecordTestCase(IsAuthClientTestCase):

    def setUp(self):
        super().setUp()
        self.home_chef_user = self.create_random_user(extra_fields={'is_email_active': True})
        self.home_chef_user.user_type = UserTypes.HOME_CHEF.value
        self.home_chef_user.save()
        self.home_chef_client = self.create_client_with_auth(self.home_chef_user)

    def test_list_saved_recipes(self):

        for i in range(3):
            chef_pencil_record = ChefPencilRecord(
                title='123',
                html_content='345345',
                user=self.home_chef_user
            )
            chef_pencil_record.save()
            saved_chef_pencil_record = SavedChefPencilRecord.objects.create(
                chef_pencil_record=chef_pencil_record,
                user=self.home_chef_user
            )

        self.assertEqual(SavedChefPencilRecord.objects.count(), 3)

        response = self.anonymous_client.get(
            reverse('chef_pencil:saved_chef_pencil_record')
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.home_chef_client.get(
            reverse('chef_pencil:saved_chef_pencil_record')
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_create_saved_recipe(self):

        chef_pencil_record = ChefPencilRecord(
            title='123',
            html_content='345345',
            user=self.home_chef_user
        )
        chef_pencil_record.save()

        response = self.anonymous_client.get(reverse('chef_pencil:retrieve_update_destroy', args=[chef_pencil_record.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['user_saved_chef_pencil_record'])

        response = self.home_chef_client.post(
            reverse('chef_pencil:saved_chef_pencil_record'),
            {'chef_pencil_record': chef_pencil_record.pk}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(response.data['chef_pencil_record']['user_saved_chef_pencil_record'], False)
        self.assertEqual(SavedChefPencilRecord.objects.count(), 1)

        response = self.home_chef_client.get(reverse('chef_pencil:retrieve_update_destroy', args=[chef_pencil_record.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data['user_saved_chef_pencil_record'], 0)

    def test_delete_saved_recipe(self):

        chef_pencil_record = ChefPencilRecord(
            title='123',
            html_content='345345',
            user=self.home_chef_user
        )
        chef_pencil_record.save()
        saved_chef_pencil_record = SavedChefPencilRecord.objects.create(
            chef_pencil_record=chef_pencil_record,
            user=self.home_chef_user
        )
        self.assertEqual(SavedChefPencilRecord.objects.count(), 1)

        response = self.client.delete(
            reverse('chef_pencil:saved_chef_pencil_record_retrieve_destroy', args=(saved_chef_pencil_record.pk,))
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.home_chef_client.delete(
            reverse('chef_pencil:saved_chef_pencil_record_retrieve_destroy', args=(saved_chef_pencil_record.pk,))
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(SavedChefPencilRecord.objects.count(), 0)
