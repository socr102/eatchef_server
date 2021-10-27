from django.urls import path
from rest_framework import routers

from site_settings.views import (
    SupportCreateView,
    BlocksListView
)

app_name = 'Settings api'

router = routers.SimpleRouter()

urlpatterns = [
    path('', SupportCreateView.as_view(), name='support_create'),
    path('blocks', BlocksListView.as_view(), name='blocks'),
]

urlpatterns += router.urls
