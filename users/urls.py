from users.models import UserViewHistoryRecord
from django.urls import path
from rest_framework import routers

from users.views import (
    ChangePasswordView,
    CheckResetCodeView,
    ConfirmEmailView, ConfirmNewEmailView,
    RequestChangeEmailView,
    RequestResetPasswordView,
    ResetPasswordView,
    ResendConfirmEmailView,
    UserCreateView,
    UserMeRetrieveUpdateView,
    UserView,
    HomeChefRequestCreateView,
    UserViewHistoryRecordView
)


app_name = 'Users api'

router = routers.SimpleRouter()

urlpatterns = [
    path('register', UserCreateView.as_view(), name='register'),
    path('me', UserMeRetrieveUpdateView.as_view(), name='me'),
    path('<int:pk>', UserView.as_view(), name='user_view'),
    path('homechef_request', HomeChefRequestCreateView.as_view(), name='homechef_request'),
    path('email/confirm', ConfirmEmailView.as_view(), name='confirm_email'),
    path('email/confirm/resend', ResendConfirmEmailView.as_view(), name='send_confirm_email'),
    path('email/change', RequestChangeEmailView.as_view(), name='change_email'),
    path('new-email/confirm/<str:code>', ConfirmNewEmailView.as_view(), name='confirm_new_email'),
    path('password/change', ChangePasswordView.as_view(), name='change_password'),
    path('password/reset', RequestResetPasswordView.as_view(), name='request_reset_password'),
    path('password/reset/check', CheckResetCodeView.as_view(), name='check_password_reset_code'),
    path('password/new', ResetPasswordView.as_view(), name='reset_password'),
    path('view_history', UserViewHistoryRecordView.as_view(), name='view_history'),
]

urlpatterns += router.urls
