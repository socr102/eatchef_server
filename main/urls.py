"""main URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLConf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.conf.urls.static import static
from django.urls import include, path
from django.contrib import admin
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.views import get_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenVerifyView

from main import settings

from users.tokens.views import LoginCheckView, TokenObtainPairView, TokenRefreshView
from users.views import OAuthRegistrationView

schema_view = get_schema_view(
    openapi.Info(
        title="Eatchef",
        default_version='v1',
        description="Test description",
        terms_of_service="#",
        contact=openapi.Contact(email="info@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(),
)


class HealthCheckView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(responses={200: ''})
    def get(self, request):
        return Response(data='OK', status=status.HTTP_200_OK)


urlpatterns = \
    [
        # Admin panel
        path('admin/', admin.site.urls),
        # Health check http server
        url('health', HealthCheckView.as_view(), name='health_check'),
        # Health check http server
        url('health', HealthCheckView.as_view(), name='health_check'),
        # Web API automatic documentation
        url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        # Web API Authentication
        path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
        path('token/check/', LoginCheckView.as_view(), name='token_check_auth'),
        path('token/social', OAuthRegistrationView.as_view(), name='token_obtain_pair_by_social'),
        path('social/', include('social_django.urls', namespace='social')),
        # Web API
        path('account/', include('users.urls', namespace='users')),
        path('recipe/', include('recipe.urls', namespace='recipe')),
        path('settings/', include('site_settings.urls', namespace='settings')),
        path('chef_pencil/', include('chef_pencils.urls', namespace='chef_pencil')),
        path('stats/', include('stats.urls', namespace='stats')),
        path('notifications/', include('notifications.urls', namespace='notifications')),
    ] + static(settings.MEDIA_PATH, document_root=settings.MEDIA_ROOT)
