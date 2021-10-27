from django.urls import path
from rest_framework import routers

from stats.views import (
    StatsAdminView,
    StatsIncrementView
)


app_name = 'Stats api'

router = routers.SimpleRouter()

urlpatterns = [
    path('increment', StatsIncrementView.as_view(), name='increment'),
    # path('admin/users_stats', StatsAdminView.as_view(), name='stats_admin_view'),
]

urlpatterns += router.urls
