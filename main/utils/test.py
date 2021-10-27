import random

from rest_framework.test import APITestCase, APIClient

import utils.random
from users.models import User
from utils.test import UserFactoryMixin
from utils.vcr import VCRMixin
from users.enums import UserTypes

from recipe.enums import RecipeTypes, Cuisines, Diets, CookingMethods, CookingSkills, Units
from recipe.models import Recipe


class BaseUserTestCase(VCRMixin, APITestCase, UserFactoryMixin):
    pass


class IsAuthClientTestCase(BaseUserTestCase):
    staff_user: User
    staff_client: APIClient
    anonymous_client: APIClient

    def setUp(self):
        super().setUp()

        self.user = self.create_random_user(extra_fields={'is_email_active': True})
        self.client = self.create_client_with_auth(self.user)
        self.staff_user = self.create_random_user({'is_staff': True, 'is_email_active': True})
        self.staff_client = self.create_client_with_auth(user=self.staff_user)

        self.anonymous_client = self.client_class()

        self.home_chef_user = self.create_random_user(
            extra_fields={'is_email_active': True})
        self.home_chef_user.user_type = UserTypes.HOME_CHEF.value
        self.home_chef_user.save()
        self.home_chef_client = self.create_client_with_auth(self.home_chef_user)


class TestDataService(UserFactoryMixin):
    DEFAULT_ENTITIES_COUNT = 10

    used_users = set([])

    def _get_next_random_user(self) -> User:
        """ Return random user excluding already selected """

        users = set(User.objects.all())
        to_select = users - self.used_users
        if not to_select:
            to_select = users
            self.used_users = set([])
        choice = random.choice(list(to_select))
        self.used_users.add(choice)
        return choice

    def create_users(self, count: int = DEFAULT_ENTITIES_COUNT):
        for i in range(count):
            self.create_random_user()

    def get_random_recipe(self):

        home_chef_user = self.create_random_user(extra_fields={'is_email_active': True})
        home_chef_user.user_type = UserTypes.HOME_CHEF.value
        home_chef_user.save()
        home_chef_client = self.create_client_with_auth(home_chef_user)

        BASIC_TEST_DATA = {
            'user': home_chef_user,
            'title': 'Grilled Basil Chicken',
            'cooking_time': '00:30',
            'description': 'adfslkasjdflkajsdfjaskldfas',
            'language': 'English',
            'caption': 'Caption',
            "cuisines": [Cuisines.INDONISIAN.value],
            "types": [RecipeTypes.BREAKFAST.value],
            "cooking_methods": [CookingMethods.BAKING.value],
            "cooking_skills": CookingSkills.EASY.value,
            "diet_restrictions": [Diets.GLUTEN_FREE.value]
        }
        recipe = Recipe.objects.create(**BASIC_TEST_DATA)
        recipe.status = Recipe.Status.ACCEPTED
        recipe.publish_status = Recipe.PublishStatus.PUBLISHED
        recipe.save()
        return recipe


def create_random_sentence(min_words=5, max_words=10):
    """
    Creates a simple random sentence from English words
    """
    words = [
        'about',
        'after',
        'again',
        'alive',
        'all',
        'alone',
        'also',
        'and',
        'any',
        'as',
        'at',
        'back',
        'bag',
        'bath',
        'be',
        'beat',
        'because',
        'beer',
        'book',
        'boot',
        'bored',
        'brothers',
        'brown',
        'bubble',
        'build',
        'but',
        'by',
        'can',
        'cap',
        'car',
        'care',
        'case',
        'cash',
        'casual',
        'cat',
        'cave',
        'cheese',
        'chew',
        'chill',
        'choose',
        'church',
        'clear',
        'coil',
        'cold',
        'come',
        'cook',
        'could',
        'cow',
        'crazy',
        'cricket',
        'day',
        'delusion',
        'do',
        'don’t',
        'door',
        'down',
        'drive',
        'ear',
        'eight',
        'employ',
        'even',
        'face',
        'fast',
        'fear',
        'feed',
        'few',
        'first',
        'fish',
        'flag',
        'flat',
        'flight',
        'for',
        'friday',
        'from',
        'fruit',
        'full',
        'fun',
        'get',
        'girl',
        'give',
        'gloomy',
        'go',
        'good',
        'grass',
        'green',
        'hair',
        'hand',
        'hard',
        'have',
        'he',
        'heard',
        'hello',
        'help',
        'her',
        'high',
        'him',
        'his',
        'hole',
        'house',
        'how',
        'I',
        'if',
        'in',
        'intend',
        'into',
        'it',
        'its',
        'jaw',
        'joy',
        'juggle',
        'juice',
        'just',
        'kind',
        'king',
        'knew',
        'knife',
        'know',
        'late',
        'law',
        'lazy',
        'leap',
        'letter',
        'like',
        'london',
        'long',
        'look',
        'lose',
        'lots',
        'love',
        'mad',
        'make',
        'me',
        'melt',
        'money',
        'more',
        'most',
        'mother',
        'mouth',
        'my',
        'nap',
        'near',
        'need',
        'new',
        'no',
        'nobody',
        'nose',
        'not',
        'now',
        'nurse',
        'of',
        'on',
        'one',
        'only',
        'or',
        'other',
        'others',
        'our',
        'out',
        'over',
        'oyster',
        'pause',
        'pear',
        'people',
        'pill',
        'pin',
        'pride',
        'purpose',
        'put',
        'quick',
        'rain',
        'ride',
        'ring',
        'river',
        'road',
        'rob',
        'robe',
        'room',
        'roses',
        'rush',
        'sausage',
        'say',
        'see',
        'send',
        'she',
        'shirt',
        'shop',
        'should',
        'sight',
        'so',
        'sock',
        'some',
        'song',
        'space',
        'squat',
        'stage',
        'stairs',
        'stones',
        'swimming',
        'take',
        'talk',
        'team',
        'tear',
        'television',
        'than',
        'that',
        'the',
        'their',
        'them',
        'then',
        'there',
        'these',
        'they',
        'thing',
        'think',
        'third',
        'this',
        'those',
        'thought',
        'time',
        'to',
        'top',
        'tow',
        'toy',
        'train',
        'tune',
        'turn',
        'two',
        'up',
        'us',
        'use',
        'usual',
        'vest',
        'view',
        'village',
        'walk',
        'wall',
        'want',
        'watch',
        'way',
        'we',
        'well',
        'went',
        'what',
        'when',
        'which',
        'who',
        'will',
        'wine',
        'with',
        'work',
        'world',
        'would',
        'yard',
        'yawn',
        'year',
        'yellow',
        'yesterday',
        'you',
        'your',
        'zigzag',
        'zoo',
    ]
    selected = random.sample(words, random.randint(min_words, max_words))
    return ' '.join(selected)

