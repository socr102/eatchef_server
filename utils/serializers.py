from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import empty

from users.models import User


class IncludeUserMixin:
    _user: User or None = None

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)
        if 'request' in self.context:
            self._user = self.context['request'].user
        else:
            self.user = None

    def get_user(self) -> User:
        if self._user is None:
            raise PermissionDenied()
        return self._user