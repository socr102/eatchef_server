from main.utils.test import IsAuthClientTestCase
from rest_framework.reverse import reverse
from rest_framework import status

from site_settings.models import Support

class SupportTestCase(IsAuthClientTestCase):

    def setUp(self):
        super().setUp()

    def test_create_support(self):

        self.assertEqual(Support.objects.count(), 0)

        response = self.client.post(
            reverse('settings:support_create'),
            {'email': 'test@example.com'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, {'email': 'test@example.com'})

        self.assertEqual(Support.objects.count(), 1)
