from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt import exceptions
from rest_framework_simplejwt.settings import api_settings

from users.enums import UserStatuses
from users.errors import (
    EmailNotActivated,
    UserIsHardBanned
)
from users.models import User
from users.tokens.tokens import RefreshToken, SlidingToken


def _add_custom_token_claims(token, user: User):
    token['email'] = user.email
    return token


class PasswordField(serializers.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault('style', {})

        kwargs['style']['input_type'] = 'password'
        kwargs['write_only'] = True

        super().__init__(**kwargs)


class EmailField(serializers.EmailField):
    def __init__(self, **kwargs):
        kwargs.setdefault('style', {})

        kwargs['style']['input_type'] = 'email'
        kwargs['write_only'] = True

        super().__init__(**kwargs)


class TokenObtainSerializer(serializers.Serializer):
    user: User
    default_error_messages = {
        'no_active_account': _('Wrong login or password')
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'] = EmailField()
        self.fields['password'] = PasswordField()

        self.fields['access'] = serializers.CharField(read_only=True)
        self.fields['refresh'] = serializers.CharField(read_only=True)

    def validate(self, attrs):
        authenticate_kwargs = {
            'email': attrs['email'].lower(),
            'password': attrs['password'],
        }
        try:
            authenticate_kwargs['request'] = self.context['request']
        except KeyError:
            pass

        self.user = authenticate(**authenticate_kwargs)

        if self.user is None or self.user is None or not self.user.is_active:
            raise exceptions.AuthenticationFailed(
                self.error_messages['no_active_account'],
                'no_active_account',
            )

        return {}

    @classmethod
    def get_token(cls, user):
        raise NotImplementedError('Must implement `get_token` method for `TokenObtainSerializer` subclasses')


class TokenObtainPairSerializer(TokenObtainSerializer):

    @classmethod
    def get_token(cls, user) -> RefreshToken:

        if user.status == UserStatuses.HARD_BANNED.value:
            raise UserIsHardBanned()

        if not user.is_email_active:
            raise EmailNotActivated()

        token = RefreshToken.for_user(user)
        return _add_custom_token_claims(token, user)

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)

        return data


class TokenObtainSlidingSerializer(TokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        token = SlidingToken.for_user(user)
        return _add_custom_token_claims(token, user)

    def validate(self, attrs):
        data = super().validate(attrs)

        token = self.get_token(self.user)
        data['token'] = str(token)
        return data


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        refresh = RefreshToken(attrs['refresh'])

        data = {'access': str(refresh.access_token)}

        if api_settings.ROTATE_REFRESH_TOKENS:
            if api_settings.BLACKLIST_AFTER_ROTATION:
                try:
                    # Attempt to blacklist the given refresh token
                    refresh.blacklist()
                except AttributeError:
                    # If blacklist app not installed, `blacklist` method will
                    # not be present
                    pass

            refresh.set_jti()
            refresh.set_exp()

            data['refresh'] = str(refresh)

        return data


class TokenRefreshSlidingSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):
        token = SlidingToken(attrs['token'])

        # Check that the timestamp in the "refresh_exp" claim has not
        # passed
        token.check_exp(api_settings.SLIDING_TOKEN_REFRESH_EXP_CLAIM)

        # Update the "exp" claim
        token.set_exp()

        return {'token': str(token)}
