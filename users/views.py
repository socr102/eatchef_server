from users.enums import UserTypes
from django.http import Http404
import json
import requests
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.db import models, transaction
from rest_framework.reverse import reverse
from social_core.exceptions import MissingBackend
from social_django.utils import load_backend, load_strategy
from main.permissions import IsOwner
from main.pagination import StandardResultsSetPagination

from users.models import User, UserViewHistoryRecord
from users.serializers import (
    ChangePasswordSerializer,
    CheckResetCodeSerializer,
    ConfirmEmailSerializer,
    ConfirmNewEmailSerializer,
    RequestChangeEmailSerializer,
    RequestResetPasswordSerializer,
    ResetPasswordSerializer,
    ResendConfirmEmailSerializer,
    RoleModelSerializer,
    UserCustomerSerializer,
    UserHomeChefSerializer,
    UserRegisterSerializer,
    UserViewHistoryRecordSerializer
)
from users.tokens.serializers import TokenObtainPairSerializer


class OAuthRegistrationView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]

    class OAuthLoginRequestSerializer(serializers.Serializer):
        backend = serializers.ChoiceField(
            required=True,
            write_only=True,
            choices=('google-oauth2', 'facebook')
        )
        access_token = serializers.CharField(
            required=True,
            write_only=True,
            allow_blank=True,
            allow_null=True,
            help_text='access_token from service like google, twitter etc.'
        )
        register = serializers.BooleanField(
            write_only=True,
            default=False,
            help_text="Enable new user registration"
        )
    class OAuthLoginResponseSerializer(serializers.Serializer):
        refresh = serializers.CharField(required=True)
        access = serializers.CharField(required=True)

    @swagger_auto_schema(
        query_serializer=OAuthLoginRequestSerializer(),
        responses={
            status.HTTP_200_OK: OAuthLoginResponseSerializer(),
            status.HTTP_403_FORBIDDEN: '',
        }
    )
    def get(self, request, *args, **kwargs):
        redirect_uri = 'social:complete'
        uri = redirect_uri
        serializer = OAuthRegistrationView.OAuthLoginRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        backend = serializer.validated_data.get('backend')
        token = serializer.validated_data.get('access_token')

        register = serializer.validated_data.get('register')
        if uri and not uri.startswith('/'):
            uri = reverse(redirect_uri, args=(backend,))
        request.social_strategy = load_strategy(request)
        # backward compatibility in attribute name, only if not already
        # defined
        if not hasattr(request, 'strategy'):
            request.strategy = request.social_strategy

        try:
            request.backend = load_backend(request.social_strategy, backend, uri)
        except MissingBackend:
            raise Http404('Backend not found')
        # This view expects an access_token GET parameter, if it's needed,
        # request.backend and request.strategy will be loaded with the current
        # backend and strategy.
        user = request.backend.do_auth(token, response=None, register=register)
        if user:
            refresh = TokenObtainPairSerializer.get_token(user)
            data = {'refresh': str(refresh), 'access': str(refresh.access_token)}
            return Response(data=data, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


class UserCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer


class UserView(generics.RetrieveAPIView):

    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all().get_home_chef_accounts().get_active().get_not_banned()

    def get_serializer_class(self):
        if self.get_object().user_type == UserTypes.HOME_CHEF.value:
            return UserHomeChefSerializer
        return UserCustomerSerializer

    def get_object(self):
        user_id = self.kwargs.get('pk')
        try:
            obj = self.queryset.get(pk=user_id)
        except User.DoesNotExist:
            raise Http404
        return obj


class UserMeRetrieveUpdateView(generics.RetrieveUpdateAPIView):

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.get_object().user_type == UserTypes.HOME_CHEF.value:
            return UserHomeChefSerializer
        return UserCustomerSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        role_model_images = [request.FILES[k] for k in request.FILES.keys() if k.startswith('role_model_images[')]

        if request.data.get('data'):
            data = dict(**json.loads(request.data.get('data')))
            if 'avatar' in request.data:
                data.update(dict(avatar=request.data.get('avatar')))
        else:
            data = request.data

        role_model_names = data.get('role_models')

        serializer = self.get_serializer(instance, data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # role models creation
        if role_model_names is not None:
            for i, role_model_name in enumerate(role_model_names):

                role_model = {}
                role_model['user'] = self.request.user.pk
                role_model['name'] = role_model_name
                role_model['file'] = role_model_images[i]

                rm_serializer = RoleModelSerializer(data=role_model)
                rm_serializer.is_valid(raise_exception=True)
                rm_serializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class HomeChefRequestCreateView(generics.UpdateAPIView):

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserHomeChefSerializer

    def get_queryset(self):
        return [self.request.user]

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(
        responses={200: ''},
        request_body=UserHomeChefSerializer(),
    )
    def post(self, request, *args, **kwargs):
        # Here we basically perform an update of the existing user
        # Although it looks like a 'homechef request' creation
        return super().put(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        role_model_images = [request.FILES[k] for k in request.FILES.keys() if k.startswith('role_model_images[')]

        if request.data.get('data'):
            data = dict(**json.loads(request.data.get('data')))
            if 'avatar' in request.data:
                data.update(dict(avatar=request.data.get('avatar')))
        else:
            data = request.data

        role_model_names = data.get('role_models')

        serializer = self.get_serializer(instance, data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # role models creation
        if role_model_names is not None:
            for i, role_model_name in enumerate(role_model_names):

                role_model = {}
                role_model['user'] = self.request.user.pk
                role_model['name'] = role_model_name
                role_model['file'] = role_model_images[i]

                rm_serializer = RoleModelSerializer(data=role_model)
                rm_serializer.is_valid(raise_exception=True)
                rm_serializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data, status=status.HTTP_200_OK)


class ConfirmEmailView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ConfirmEmailSerializer

    @swagger_auto_schema(responses={200: ''})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.confirm_email()
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class RequestChangeEmailView(generics.GenericAPIView):
    serializer_class = RequestChangeEmailSerializer

    @swagger_auto_schema(responses={200: ''})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.send_confirm_new_email(request.data)
        data = dict(code=self.request.user.activation_email_code)
        return Response(data=data, status=status.HTTP_200_OK)


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer

    @swagger_auto_schema(responses={200: ''})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.set_password()
        return Response(status=status.HTTP_200_OK)


class ConfirmNewEmailView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ConfirmNewEmailSerializer

    @swagger_auto_schema(responses={200: ''})
    def post(self, request):
        serializer = self.get_serializer(data={'code': self.kwargs['code']})
        serializer.is_valid(raise_exception=True)
        serializer.confirm_new_email()
        return Response({}, status=status.HTTP_200_OK)


class RequestResetPasswordView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RequestResetPasswordSerializer

    @swagger_auto_schema(responses={200: ''})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.send_make_new_password()
        return Response(data=None, status=status.HTTP_200_OK)


class CheckResetCodeView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CheckResetCodeSerializer

    @swagger_auto_schema(responses={200: ''})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_200_OK)


class ResetPasswordView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPasswordSerializer

    @swagger_auto_schema(responses={200: ''})
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.reset_password()
        return Response(status=status.HTTP_200_OK)


class ResendConfirmEmailView(generics.GenericAPIView):
    serializer_class = ResendConfirmEmailSerializer

    @swagger_auto_schema(responses={200: ""})
    def post(self, request):
        serializer = self.get_serializer(request.user)
        serializer.send_confirm_email()
        return Response(data=None, status=status.HTTP_200_OK)


class UserViewHistoryRecordView(generics.ListAPIView):

    queryset = UserViewHistoryRecord.objects.all() \
        .select_related('recipe') \
        .order_by("-updated_at")
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserViewHistoryRecordSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
