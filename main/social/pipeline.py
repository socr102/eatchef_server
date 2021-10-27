
from django.core.files import File
import os
from urllib.request import urlopen, HTTPError
from django.core.files.temp import NamedTemporaryFile

from users.errors import UserNotCreated
from users.models import User
from users.enums import UserTypes

from users.signals import (
    S_new_password_created,
    S_new_user_email_activated
)


USER_FIELDS = ['email', 'last_name', 'first_name', 'user_type', 'register']


def create_user(strategy, details, backend, user=None, *args, **kwargs):

    if user:
        # user may already be with such email but email still not activated
        # to prevent error during social login we activate it
        user.is_email_active = True
        user.save()
        return {'is_new': False}

    fields = dict((name, kwargs.get(name, details.get(name))) for name in backend.setting('USER_FIELDS', USER_FIELDS))
    if not fields:
        return

    # set fields with necessary values

    fields['full_name'] = fields.get('first_name', '') + fields.get('last_name', '')
    password = User.objects.make_random_password()
    fields = dict(**fields, password=password, is_email_active=True)

    if not fields.get('register'):
        raise UserNotCreated()

    del fields['register']

    if not fields.get('user_type'):
        fields['user_type'] = UserTypes.CUSTOMER.value

    user = User.objects.create_user(**fields)

    S_new_user_email_activated.send(sender=User, instance=user)
    S_new_password_created.send(
        sender=User,
        instance=user,
        new_password=password
    )

    url = None
    if backend.name == 'facebook':
        # url = "http://graph.facebook.com/%s/picture?type=large" % response["id"]
        url = "http://graph.facebook.com/%s/picture?width=150&height=150" % kwargs['response']['id']
    if backend.name == 'google-oauth2':
        url = kwargs['response']['picture']
    if url:
        try:
            img_temp = NamedTemporaryFile(suffix='.png', delete=False)
            img_temp.write(urlopen(url).read())
            img_temp.flush()
        except Exception:
            pass
        else:
            user.avatar = File(img_temp, name=os.path.split(img_temp.name)[-1])
            user.save()
        finally:
            os.remove(img_temp.name)

    return {
        'is_new': True,
        'user': user
    }
