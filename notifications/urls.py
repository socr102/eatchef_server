from django.urls import path
from rest_framework import routers

from notifications.views import DeleteAccountNotifications, RetrieveDestroyNotificationsViewSet

app_name = 'Notifications api'

router = routers.SimpleRouter()
router.register('', RetrieveDestroyNotificationsViewSet, basename='notify')
urlpatterns = [
    path('delete_all', DeleteAccountNotifications.as_view(), name='delete-account-notifications')
]
urlpatterns += router.urls
