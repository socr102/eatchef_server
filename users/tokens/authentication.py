from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken

from users.enums import UserStatuses
from users.models import User


class JWTAuthentication(BaseJWTAuthentication):

    @staticmethod
    def _is_user_hard_banned(user: User) -> bool:
        return user.status == UserStatuses.HARD_BANNED.value

    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        user_id, email = None, None
        user = None

        try:
            user_id = validated_token['user_id']
        except KeyError:
            try:
                email = validated_token['email']
            except KeyError:
                raise InvalidToken(_('Token contained no recognizable user identification'))

        if user_id is not None:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise AuthenticationFailed(_('User not found'), code='user_not_found')
        elif email is not None:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise AuthenticationFailed(
                    _('User not found'), code='user_not_found')

        if not user.is_active:
            raise AuthenticationFailed(_('User is inactive'), code='user_inactive')

        if self._is_user_hard_banned(user):
            raise AuthenticationFailed(detail='User is hard banned', code='user_hard_banned')

        return user
