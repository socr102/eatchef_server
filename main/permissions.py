from django.conf import settings
from rest_framework.permissions import BasePermission, SAFE_METHODS

from users.enums import UserTypes


class IsEmailConfirmed(BasePermission):
    message = 'Your mail has not been verified. Access limited'

    def has_permission(self, request, view):
        if not settings.CHECK_EMAIL_ACTIVATION:
            return True
        user = request.user
        if user.is_authenticated:
            return user.is_email_active


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class IsHomeChef(BasePermission):
    def has_permission(self, request, view):
        return request.user.get_type() == UserTypes.HOME_CHEF.value

class IsOwner(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
