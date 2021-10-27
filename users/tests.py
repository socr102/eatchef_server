import json
import shutil
from pathlib import Path

from django.core import mail
from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework_simplejwt.exceptions import InvalidToken

from main.utils.test import BaseUserTestCase, IsAuthClientTestCase, TestDataService
from utils.email import SEND_CONFIRM_EMAIL_SUBJECT

from users.enums import UserStatuses, UserTypes
from users.errors import UserIsHardBanned
from users.models import RoleModel, User, WorkExperienceRecord

from utils.test import get_test_avatar_file, get_test_files, get_alt_test_files

class TokenTestCase(IsAuthClientTestCase):
    credentials: dict

    def setUp(self) -> None:
        super().setUp()
        self.user = self.create_random_user(extra_fields={'is_email_active': True})

        self.credentials = {
            'email': self.user.email,
            'password': self.USER_PASSWORD,
        }
        self.client = self.create_client_with_auth(self.user)
        mail.outbox = []

    def test_get_token(self):
        response = self.client.post(reverse('token_obtain_pair'), self.credentials)
        tokens = response.data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(tokens['access'])
        self.assertTrue(tokens['refresh'])
        response = self.client.post(reverse('token_verify'), {'token': tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % tokens['access'])
        auth_client = self.client_class()
        auth_client.credentials(HTTP_AUTHORIZATION='Bearer %s' % tokens['access'])
        response = auth_client.post(reverse('token_check_auth'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_fail_token_verify(self):
        access = 'eyJ0eXAiOiJKV1p2LCJhbGciOiJIUzI1NiJ9.' \
                 'eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwI' \
                 'joxNTg0Nzg1NDkxLCJqdGkiOiI3NDkyNzdlOG' \
                 'E0MzU0NDk5OTY2ZjFjZWI2ZDhlNGRmNSIsInV' \
                 'zZXJfaWQiOjV9.EDuzYiPjtyn9WrMcrueZC9IV0BTmWciq9U2TBFMIpw0'
        response = self.client.post(reverse('token_verify'), {'token': access})
        self.assertEqual(response.status_code, InvalidToken.status_code)
        self.assertEqual(response.data['detail'], InvalidToken.default_detail)
        self.assertEqual(response.data['code'], InvalidToken.default_code)

    def test_fail_email_get_token(self):
        data = self.credentials
        data['email'] = 'te3st23@exam22ple.ru'
        response = self.client.post(reverse('token_obtain_pair'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fail_password_get_token(self):
        data = self.credentials
        data['password'] = 'te3stasdasd'
        response = self.client.post(reverse('token_obtain_pair'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fail_password_and_email_get_token(self):
        data = self.credentials
        data['email'] = 'te3s45t23@exam2d2ple.ru'
        data['password'] = 'te3stas4332dasd'
        response = self.client.post(reverse('token_obtain_pair'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_token_for_admin_access_user(self):
        anonymous_client = self.client_class()
        credentials = {
            'email': self.staff_user.email,
            'password': self.USER_PASSWORD,
        }
        response = anonymous_client.post(
            reverse('token_obtain_pair'), credentials)
        tokens = response.data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(tokens['access'])
        self.assertTrue(tokens['refresh'])
        response = anonymous_client.post(reverse('token_verify'), {
                                    'token': tokens['access']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        anonymous_client.credentials(
            HTTP_AUTHORIZATION='Bearer %s' % tokens['access'])
        response = anonymous_client.post(
            reverse('token_check_auth'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestClassIsAuthClientTestCase(BaseUserTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.user = self.create_random_user(extra_fields={'is_email_active': True})
        self.client = self.create_client_with_auth(self.user)
        mail.outbox = []

    def test_is_authenticated_client(self):
        response = self.client.post(reverse('token_check_auth'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.hard_ban_user()
        self.user.save()
        response = self.client.post(reverse('token_check_auth'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'User is hard banned')
        self.assertEqual(response.data['code'], 'user_hard_banned')


class TestChangePassword(BaseUserTestCase):
    data = {
        'new_password': 'new_password',
    }

    def setUp(self):
        super().setUp()
        self.user = self.create_random_user(extra_fields={'is_email_active': True})
        self.client = self.create_client_with_auth(self.user)
        mail.outbox = []
        self.data['password'] = self.USER_PASSWORD

    def _get_change_password_response(self):
        return self.client.post(reverse('users:change_password'), data=self.data)

    def test_change_password(self):
        response = self._get_change_password_response()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data)

    def test_change_password_with_invalid_password(self):
        self.data['password'] = 'invalid_password'
        response = self._get_change_password_response()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['password'][0], 'Wrong password')


class UserRegistrationsTestCase(BaseUserTestCase):

    def test_registration_without_full_name(self):
        credentials = {
            'email': 'test@test.ru',
            'full_name': '',
            'password': self.USER_PASSWORD
        }
        mail.outbox = []
        response = self.client.post(reverse('users:register'), data=credentials)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_as_customer_by_default(self):
        credentials = {
            'email': 'test@test.ru',
            'full_name': 'Test Testov',
            'password': self.USER_PASSWORD
        }
        mail.outbox = []
        response = self.client.post(reverse('users:register'), data=credentials)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        credentials['user_id'] = str(response.data['pk'])
        user = User.objects.get(email=credentials.get('email'))
        self.assertEqual(user.user_type, UserTypes.CUSTOMER.value)
        self.assertEqual(user.full_name, 'Test Testov')

        if settings.SEND_ACTIVATION_EMAIL:

            # can't authorize until email is confirmed
            response = self.client.post(reverse('token_obtain_pair'), credentials)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

            outbox = mail.outbox
            self.assertEqual(len(outbox), 1, "Inbox is not empty")
            self.assertEqual(outbox[0].subject, SEND_CONFIRM_EMAIL_SUBJECT)
            self.assertEqual(outbox[0].from_email, settings.EMAIL_FROM)
            self.assertEqual(outbox[0].to, [credentials.get('email')])
            user = User.objects.get(email=credentials.get('email'))
            response = self.client.post(
                reverse('users:confirm_email'),
                data={'code': user.activation_email_code}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            user = User.objects.get(email=credentials.get('email'))
            self.assertEqual(user.is_active, True)
            self.assertEqual(user.is_email_active, True)
            self.assertEqual(user.activation_email_code, None)

            # now authorization is possible
            response = self.client.post(reverse('token_obtain_pair'), credentials)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        else:
            self.assertEqual(user.is_active, True)
            self.assertEqual(user.is_email_active, True)
            self.assertEqual(user.activation_email_code, None)

    def test_registration_as_home_chef(self):
        credentials = {
            'email': 'test@test.ru',
            'password': self.USER_PASSWORD,
            'full_name': 'Test Testov',
            'user_type': UserTypes.HOME_CHEF.value
        }
        mail.outbox = []
        response = self.client.post(
            reverse('users:register'), data=credentials)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(pk=response.data['pk'])
        self.assertEqual(user.user_type, UserTypes.HOME_CHEF.value)
        self.assertEqual(user.full_name, 'Test Testov')

    def test_google_social_auth_user_creation(self):
        """
        Test that user is created after access_token is received

        Also avatar is retrieved
        """

        self.assertEqual(User.objects.count(), 1)

        response = self.client.get(
            reverse('token_obtain_pair_by_social'),
            data={
                'access_token': 'ya29.a0ARrdaM_KU5JXkFqvVB8XD_TmjcU5Au2jbbVWggi0xcEXYYBW1Xyi6UojY2JXrV1CE5Lc6s2WZj0hEcX79UVL91JD892Kg3BaJ6lXI9vNwLZ4OaD-jdTW0YFzVdl1hhHqplnH5RlveVb1Hq98cpqVFiNznZUHYQ',
                'account_type': 0,
                'backend': 'google-oauth2',
                'register': 'true',
                'redirect_uri': 'http:%2F%2Flocalhost:8030%2Flogin%2Fsocial%2F'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(User.objects.count(), 2)
        self.assertTrue(str(User.objects.last().avatar).endswith('.png'))

class TestHardBanUser(BaseUserTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.user = self.create_random_user(extra_fields={'is_email_active': True})
        self.client = self.create_client_with_auth(self.user)
        self.second_user = self.create_random_user(extra_fields={'is_email_active': True})
        self.second_client = self.create_client_with_auth(self.user)
        mail.outbox = []

    def test_hard_ban_user(self):
        self.second_user.status = UserStatuses.HARD_BANNED.value
        self.second_user.save()
        credentials = {
            'email': self.second_user.email,
            'password': self.USER_PASSWORD
        }
        response = self.client.post(reverse('token_obtain_pair'), credentials)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], UserIsHardBanned.default_detail)
        self.assertEqual(response.data['code'], UserIsHardBanned.default_code)


class NewConfirmEmailTestCase(IsAuthClientTestCase):
    def test_send_confirm_email(self):
        mail.outbox = []
        response = self.client.post(reverse("users:send_confirm_email"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(mail.outbox), 0)
        self.assertEqual(self.user.email, mail.outbox[0].to[0])
        self.assertIsNotNone(mail.outbox[0].body)


class ResetPasswordTestCase(IsAuthClientTestCase):
    def test_request_reset_password(self):
        user = self.create_random_user(extra_fields={'is_email_active': True})
        password_hash1 = user.password
        self.assertIsNone(user.reset_password_code)
        response = self.client.post(reverse("users:request_reset_password"), data={'email': user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(pk=user.pk)
        self.assertNotEqual(password_hash1, user.password)

    def test_send_request_reset_password_email(self):
        mail.outbox.clear()
        response = self.client.post(reverse("users:request_reset_password"), data={'email': self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(mail.outbox), 0)
        self.assertEqual(self.user.email, mail.outbox[0].to[0])
        self.assertIsNotNone(mail.outbox[0].body)


class UserTestCase(IsAuthClientTestCase):

    test_data_service = TestDataService()

    def setUp(self):
        super().setUp()
        self.user.full_name = 'John Johnson'
        self.user.user_type = UserTypes.CUSTOMER.value
        self.user.phone_number = '1111111115'
        self.user.email = 'test@example.com'
        self.user.city = 'New York City'
        self.user.language = 'English'
        self.user.save()

    def test_user_retrieve(self):
        response = self.client.get(reverse("users:me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pk'], self.user.pk)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['full_name'], 'John Johnson')
        self.assertEqual(response.data['phone_number'], '1111111115')
        self.assertEqual(response.data['user_type'], UserTypes.CUSTOMER.value)
        self.assertEqual(response.data['city'], 'New York City')
        self.assertEqual(response.data['language'], 'English')

    def test_user_homechef_profile_view(self):

        # incorrect users
        # 1. customer
        self.user.user_type = UserTypes.CUSTOMER.value
        self.user.save()
        response = self.anonymous_client.get(reverse("users:user_view", args=[self.user.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 2. banned
        self.user.user_type = UserTypes.HOME_CHEF.value
        self.user.status = UserStatuses.HARD_BANNED.value
        self.user.save()
        response = self.anonymous_client.get(reverse("users:user_view", args=[self.user.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # 3. not-active (=deleted)
        self.user.user_type = UserTypes.HOME_CHEF.value
        self.user.status = UserStatuses.ACTIVE.value
        self.user.is_active = False
        self.user.save()
        response = self.anonymous_client.get(reverse("users:user_view", args=[self.user.pk]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # correct user home-chef
        self.user.user_type = UserTypes.HOME_CHEF.value
        self.user.status = UserStatuses.ACTIVE.value
        self.user.is_active = True
        self.user.save()
        response = self.anonymous_client.get(reverse("users:user_view", args=[self.user.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_homechef_request(self):

        self.user.user_type = UserTypes.CUSTOMER.value
        self.user.save()

        recipe_ids = []
        for i in range(3):

            # recipes
            recipe = self.test_data_service.get_random_recipe()
            recipe_ids.append(recipe.pk)

        data = {
            'email': 'test2@example.com',
            'full_name': 'Ivan Ivanov',
            'phone_number': '2222222225',
            'city': 'London',
            'language': 'German',
            'bio': "some biography",
            'experience': [
                "experience 1",
                "experience 2",
                "experience 3",
            ],
            'cooking_philosophy': [
                'cooking philosophy #1',
                'cooking philosophy #2',
                'cooking philosophy #3',
            ],
            'personal_cooking_mission': [
                'personal_cooking_mission #1',
                'personal_cooking_mission #2',
                'personal_cooking_mission #3',
            ],
            'source_of_inspiration': [
                'source_of_inspiration #1',
                'source_of_inspiration #2',
                'source_of_inspiration #3',
            ],
            "favorite_recipes": recipe_ids,
            "role_models": [
                "John Johnson",
                "Mary Johnson"
            ]
        }
        payload = {
            'data': json.dumps(data),
            'avatar':  get_test_avatar_file('avatar_img.png'),
        }

        for i, file in enumerate(get_alt_test_files()):
            payload[f'role_model_images[{i}]'] = file

        response = self.client.post(
            reverse("users:homechef_request"),
            payload,
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pk'], self.user.pk)

        # check

        user = User.objects.get(pk=self.user.pk)
        self.assertEqual(user.user_type, UserTypes.HOME_CHEF.value)  # became HOME_CHEF

        self.assertEqual(user.email, 'test2@example.com')
        self.assertEqual(user.full_name, 'Ivan Ivanov')
        self.assertEqual(user.phone_number, '2222222225')
        self.assertEqual(user.city, 'London')
        self.assertEqual(user.language, 'German')
        self.assertEqual(user.bio, 'some biography')
        self.assertEqual(
            WorkExperienceRecord.objects.count(),
            3
        )
        self.assertEqual(
            user.cooking_philosophy,
            [
                'cooking philosophy #1',
                'cooking philosophy #2',
                'cooking philosophy #3',
            ]
        )
        self.assertEqual(
            user.personal_cooking_mission,
            [
                'personal_cooking_mission #1',
                'personal_cooking_mission #2',
                'personal_cooking_mission #3',
            ]
        )
        self.assertEqual(
            user.source_of_inspiration,
            [
                'source_of_inspiration #1',
                'source_of_inspiration #2',
                'source_of_inspiration #3',
            ]
        )
        self.assertTrue(str(user.avatar).endswith('.png'))
        self.assertListEqual(
            [fr.recipe.pk for fr in user.favorite_recipes.all()],
            recipe_ids
        )
        self.assertEqual(RoleModel.objects.filter(user=self.user).count(), 2)

        # response check

        response = self.client.get(reverse("users:me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'Ivan Ivanov')
        self.assertEqual(response.data['bio'], 'some biography')
        self.assertEqual(
            response.data['experience'],
            ['experience 1', 'experience 2', 'experience 3']
        )
        self.assertEqual(
            response.data['cooking_philosophy'],
            [
                'cooking philosophy #1',
                'cooking philosophy #2',
                'cooking philosophy #3',
            ]
        )
        self.assertEqual(
            response.data['personal_cooking_mission'],
            [
                'personal_cooking_mission #1',
                'personal_cooking_mission #2',
                'personal_cooking_mission #3',
            ]
        )
        self.assertEqual(
            response.data['source_of_inspiration'],
            [
                'source_of_inspiration #1',
                'source_of_inspiration #2',
                'source_of_inspiration #3',
            ]
        )
        self.assertEqual(len(response.data['favorite_recipes']), 3)

        # role models
        self.assertEqual(len(response.data['role_models']), 2)
        self.assertEqual(response.data['role_models'][0]['name'], 'John Johnson')
        self.assertTrue(response.data['role_models'][0]['file'].endswith('.jpg'))

        self.assertEqual(response.data['role_models'][1]['name'], 'Mary Johnson')
        self.assertTrue(response.data['role_models'][1]['file'].endswith('.jpg'))

    def test_user_homechef_full_update(self):

        # make homechef
        self.user.user_type = UserTypes.HOME_CHEF.value
        self.user.save()

        recipe_ids = []
        for i in range(3):
            recipe = self.test_data_service.get_random_recipe()
            recipe_ids.append(recipe.pk)

            RoleModel.objects.create(
                user=self.user,
                name=f'John Johnson {i}',
                file=get_test_files()[0]
            )

        self.assertEqual(self.user.city, 'New York City')
        self.assertEqual(str(self.user.avatar), '')
        self.assertEqual(RoleModel.objects.count(), 3)

        # update

        data = {
            'email': 'test2@example.com',
            'full_name': 'Jack Jackson',
            'phone_number': '2222222225',
            'city': 'London',
            'language': 'German',
            'bio': "some biography",
            'experience': [
                "experience update 1",
                "experience update 2",
                "experience update 3"
            ],
            'cooking_philosophy': [
                'cooking philosophy #1',
                'cooking philosophy #2',
                'cooking philosophy #3',
            ],
            'personal_cooking_mission': [
                'personal_cooking_mission #1',
                'personal_cooking_mission #2',
                'personal_cooking_mission #3',
            ],
            'source_of_inspiration': [
                'source_of_inspiration #1',
                'source_of_inspiration #2',
                'source_of_inspiration #3',
            ],
            "favorite_recipes": recipe_ids,
            "role_models": [
                "Test Testov1",
                "Test Testov2"
            ],
            "role_models_to_delete": [
                RoleModel.objects.all().order_by('pk')[0].pk,
                RoleModel.objects.all().order_by('pk')[1].pk,
            ]
        }
        payload = {
            'data': json.dumps(data),
            'avatar':  get_test_avatar_file('avatar_img.png'),
        }

        for i, file in enumerate(get_alt_test_files()):
            payload[f'role_model_images[{i}]'] = file

        response = self.client.put(reverse("users:me"), payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pk'], self.user.pk)

        # check

        user = User.objects.get(pk=self.user.pk)
        self.assertEqual(user.email, 'test2@example.com')
        self.assertEqual(user.full_name, 'Jack Jackson')
        self.assertEqual(user.phone_number, '2222222225')
        self.assertEqual(user.user_type, UserTypes.HOME_CHEF.value)
        self.assertEqual(user.city, 'London')
        self.assertEqual(user.language, 'German')
        self.assertEqual(user.bio, 'some biography')
        self.assertEqual(
            WorkExperienceRecord.objects.count(),
            3
        )
        self.assertEqual(
            user.cooking_philosophy,
            [
                'cooking philosophy #1',
                'cooking philosophy #2',
                'cooking philosophy #3',
            ]
        )
        self.assertEqual(
            user.personal_cooking_mission,
            [
                'personal_cooking_mission #1',
                'personal_cooking_mission #2',
                'personal_cooking_mission #3',
            ]
        )
        self.assertEqual(
            user.source_of_inspiration,
            [
                'source_of_inspiration #1',
                'source_of_inspiration #2',
                'source_of_inspiration #3',
            ]
        )
        self.assertTrue(str(user.avatar).endswith('.png'))
        self.assertListEqual(
            [fr.recipe.pk for fr in user.favorite_recipes.all()],
            recipe_ids
        )
        self.assertEqual(RoleModel.objects.all().count(), 3)
        self.assertEqual(RoleModel.objects.all().order_by('pk')[0].name, 'John Johnson 2')
        self.assertEqual(RoleModel.objects.all().order_by('pk')[1].name, 'Test Testov1')
        self.assertEqual(RoleModel.objects.all().order_by('pk')[2].name, 'Test Testov2')

        # response check
        response = self.client.get(reverse("users:me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], 'some biography')
        self.assertEqual(
            response.data['experience'],
            [
                'experience update 1',
                'experience update 2',
                'experience update 3'
            ]
        )
        self.assertEqual(
            response.data['cooking_philosophy'],
            [
                'cooking philosophy #1',
                'cooking philosophy #2',
                'cooking philosophy #3',
            ]
        )
        self.assertEqual(
            response.data['personal_cooking_mission'],
            [
                'personal_cooking_mission #1',
                'personal_cooking_mission #2',
                'personal_cooking_mission #3',
            ]
        )
        self.assertEqual(
            response.data['source_of_inspiration'],
            [
                'source_of_inspiration #1',
                'source_of_inspiration #2',
                'source_of_inspiration #3',
            ]
        )
        self.assertListEqual(
            [fr.recipe.pk for fr in user.favorite_recipes.all()],
            recipe_ids
        )

    def test_user_partial_update_avatar(self):
        self.assertEqual(self.user.city, 'New York City')
        self.assertEqual(str(self.user.avatar), '')
        data = {
            'user_type': self.user.user_type,
            'full_name': 'New Name',
            'email': self.user.email,
            'phone_number': None,
            'city': None,
            'language': None
        }
        payload = {
            'data': json.dumps(data),
            'avatar':  get_test_avatar_file('avatar_img.png'),
        }
        response = self.client.patch(reverse("users:me"), payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pk'], self.user.pk)

        user = User.objects.get(pk=self.user.pk)
        self.assertTrue(str(user.avatar).endswith('.png'))

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            shutil.rmtree(Path(settings.MEDIA_ROOT) / 'role_model_files')
            shutil.rmtree(Path(settings.MEDIA_ROOT) / 'avatars')
        except OSError as e:
            print(e)
        return super().tearDownClass()