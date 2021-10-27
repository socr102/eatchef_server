from rest_framework.test import APIClient

from django.core.files import File

from random import choice
from utils import random
from django.conf import settings
from utils.random import random_us_international_phone_number

from users.models import User
from users.enums import UserTypes
from users.tokens.serializers import TokenObtainPairSerializer


class UserFactoryMixin:
    USER_PASSWORD = 'sdw332!4TdSD'

    @staticmethod
    def __random_char(length=10, repeat=1):
        return ''.join(random.random_simple_string(length) for _ in range(repeat))

    def create_user(self,
                    email: str,
                    first_name: str,
                    last_name: str,
                    phone_number: str,
                    extra_fields: dict
                    ) -> 'User':
        if len(first_name) == 0:
            first_name = 'None'
        if len(last_name) == 0:
            last_name = 'None'
        user = User.objects._create_user(
            email=email,
            password=self.USER_PASSWORD,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            **extra_fields
        )
        user.save()
        return user

    def create_random_user(self, extra_fields={}) -> 'User':
        extra_fields.update({
            'user_type': choice(
                [UserTypes.CUSTOMER.value, UserTypes.HOME_CHEF.value]
            )
        })
        return self.create_user(
            email=self.__random_char() + "@gmail.com",
            first_name=self.__random_char(),
            last_name=self.__random_char(),
            phone_number=random_us_international_phone_number(),
            extra_fields=extra_fields
        )

    @staticmethod
    def create_client_with_auth(user: 'User') -> APIClient:
        token = TokenObtainPairSerializer.get_token(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer %s' % token.access_token)
        return client


def get_test_avatar_file(filename='avatar_img.png') -> File:
    return File(open(f"{settings.TEST_FILES_ROOT}/{filename}", mode='rb'))


def get_test_files() -> list:
    return [
        File(open(f"{settings.TEST_FILES_ROOT}/test_image1.jpg", mode='rb')),
        File(open(f"{settings.TEST_FILES_ROOT}/test_image2.jpg", mode='rb')),
    ]


def get_alt_test_files() -> list:
    return [
        File(open(f"{settings.TEST_FILES_ROOT}/test_image3.jpg", mode='rb')),
        File(open(f"{settings.TEST_FILES_ROOT}/test_image4.jpg", mode='rb')),
    ]


def get_test_video_file() -> File:
    return File(open(f"{settings.TEST_FILES_ROOT}/file.mp4", mode='rb'))
