from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework_simplejwt.exceptions import DetailDictMixin


class ResetCodeOrEmailInvalid(ValidationError):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Код или email не валиден.'


class EmailDoesNotExist(ValidationError):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'There is no such email address.'


class PasswordsDoNotMatch(ValidationError):
    default_detail = 'Password mismatch.'


class UserIsHardBanned(DetailDictMixin, PermissionDenied):
    default_detail = 'Your account has been blocked due to violations of the rules of using the portal.'
    default_code = 'user_is_hard_banned'


class InsufficientFunds(ValidationError):
    default_detail = 'Insufficient funds.'
    default_code = 'insufficient_funds'


class MailAlreadyExists(ValidationError):
    default_detail = 'New mail is already in use on the portal'


class UserNotCreated(ValidationError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'User has not been created.'


class EmailNotActivated(ValidationError):
    default_detail = {'email': 'Email is not activated. Please follow the link in the sent email to confirm.'}
