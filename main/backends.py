"""
Provides various authentication policies.
"""
from django.contrib.auth.backends import BaseBackend
from rest_framework import exceptions

from users.models import User


class UserAuthenticationBackend(BaseBackend):

    def authenticate(self, request, username: str = None, password: str = None, **kwargs):
        if kwargs.get('email') is None or password is None:
            return
        try:
            user = User.objects.get(email=kwargs.get('email'))
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            User().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
            else:
                exceptions.AuthenticationFailed('There is no account with such data.')

    def user_can_authenticate(self, user: User):
        if user.is_staff or user.is_superuser:
            return True
        """
        Reject users with is_active=False. Custom user models that don't have
        that attribute are allowed.
        """
        is_active = user.is_active
        return is_active or is_active is None
