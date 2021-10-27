from rest_framework import status
from rest_framework.reverse import reverse

from notifications.models import Notify
from main.utils.test import IsAuthClientTestCase, TestDataService

from datetime import datetime


# class NotifyTestCase(IsAuthClientTestCase):
#
#     def test_model_notify(self):
#         notify = Notify.objects.create(code=SystemNotifyCodeEnum.success_registration.value, payload=None,
#                                        account=self.user.get_account())
#         self.assertEqual(notify is not None, True)
#         self.assertEqual(notify.code, SystemNotifyCodeEnum.success_registration.value)
#
#     def test_success_registration(self):
#         notify = Notify.objects.get(account=self.user.get_account(),
#                                     code=SystemNotifyCodeEnum.success_registration.value)
#         self.assertEqual(notify is not None, True)
#         self.assertEqual(notify.code, SystemNotifyCodeEnum.success_registration.value)
#
#     def test_notifications_list_api(self):
#         response = self.client.get(reverse('notifications:notify-list'))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data) > 0, True)
#
#     def test_notifications_destroy_api(self):
#         notify = Notify.objects.get(account=self.user.get_account(),
#                                     code=SystemNotifyCodeEnum.success_registration.value)
#         response = self.client.delete(reverse('notifications:notify-detail', args=[notify.pk]))
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
#         with self.assertRaises(Exception):
#             Notify.objects.get(pk=notify.pk)
#
#     def test_delete_account_notifications(self, count: int = 10):
#         account = self.user.get_account()
#         for i in range(count):
#             Notify.objects.create(
#                 code=SystemNotifyCodeEnum.success_registration.value,
#                 payload=None,
#                 account=account
#             )
#         self.assertTrue(account.notifies.exists())
#         response = self.client.delete(reverse('notifications:delete-account-notifications'))
#         self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
#         self.assertFalse(account.notifies.exists())


class NotifyTestCase(IsAuthClientTestCase):
    test_data_service = TestDataService()
