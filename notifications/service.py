from redis import Redis

from notifications.models import Notify
from utils.patterns import SingletonMeta
from datetime import datetime
from utils.redis import get_redis_instance


class NotifyService(metaclass=SingletonMeta):
    DAY_IN_SECONDS = 86400
    SUCCESS_REDIS_SET_VALUE = 'yes'
    DENIED_REDIS_SET_VALUE = 'no'
    redis: Redis

    def __init__(self):
        self.redis = get_redis_instance()

    def _check_redis_value(self, redis_key: str) -> bool:
        redis_value = self.redis.get(redis_key)
        return redis_value is None or redis_value.decode('utf-8') == self.DENIED_REDIS_SET_VALUE

    def _check_save_notify_and_set_redis_value(self, notify: Notify, redis_key: str):
        if notify.pk is not None:
            self.redis.set(name=redis_key, value=self.SUCCESS_REDIS_SET_VALUE, ex=self.DAY_IN_SECONDS)
        else:
            self.redis.set(name=redis_key, value=self.DENIED_REDIS_SET_VALUE, ex=self.DAY_IN_SECONDS)

    def _create_notify(self, redis_key: str, notify: Notify) -> bool:
        if not self._check_redis_value(redis_key=redis_key):
            return False
        notify.save()
        self._check_save_notify_and_set_redis_value(notify=notify, redis_key=redis_key)
        return True

    def create_notify_new_user_greeting(self, user):
        self._create_notify(
            redis_key=f'notify_new_user_{user.pk}_greeting',
            notify=Notify(
                code=Notify.Code.NEW_USER_GREETING,
                user=user,
                payload=dict(
                    user_type=user.user_type
                )
            )
        )

    # recipe

    def create_notify_recipe_created(self, user, recipe):
        self._create_notify(
            redis_key=f'notify_recipe_{recipe.pk}_created_by_{user.pk}',
            notify=Notify(
                code=Notify.Code.RECIPE_CREATED_AND_AWAITING_APPROVAL,
                user=user,
                payload=dict(
                    id=recipe.pk,
                    title=recipe.title
                )
            )
        )

    def create_notify_recipe_status_changed(self, user, recipe):
        self._create_notify(
            redis_key=f'notify_recipe_{recipe.pk}_status_changed_{datetime.now()}',
            notify=Notify(
                code=Notify.Code.RECIPE_STATUS_CHANGED,
                user=user,
                payload=dict(
                    id=recipe.pk,
                    title=recipe.title,
                    status=recipe.status,
                    rejection_reason=recipe.rejection_reason
                )
            )
        )

    def create_notify_new_comments_for_recipe(self, user, recipe, comments):
        comments_ids = ','.join([str(c.pk) for c in comments])
        self._create_notify(
            redis_key=f'notify_new_comments_for_recipe_{recipe.pk}_{comments_ids}',
            notify=Notify(
                code=Notify.Code.NEW_COMMENTS_IN_YOUR_RECIPE,
                user=user,
                payload=dict(
                    id=recipe.pk,
                    title=recipe.title,
                    count=len(comments)
                )
            )
        )

    # chef pencil record

    def create_notify_chef_pencil_record_created(self, user, chef_pencil_record):
        self._create_notify(
            redis_key=f'notify_chef_pencil_record_{chef_pencil_record.pk}_created_by_{user.pk}',
            notify=Notify(
                code=Notify.Code.CHEF_PENCIL_RECORD_CREATED_AND_AWAITING_APPROVAL,
                user=user,
                payload=dict(
                    id=chef_pencil_record.pk,
                    title=chef_pencil_record.title
                )
            )
        )

    def create_notify_chef_pencil_record_status_changed(self, user, chef_pencil_record):
        self._create_notify(
            redis_key=f'notify_chef_pencil_record_{chef_pencil_record.pk}_status_changed_{datetime.now()}',
            notify=Notify(
                code=Notify.Code.CHEF_PENCIL_RECORD_STATUS_CHANGED,
                user=user,
                payload=dict(
                    id=chef_pencil_record.pk,
                    title=chef_pencil_record.title,
                    status=chef_pencil_record.status,
                    rejection_reason=chef_pencil_record.rejection_reason
                )
            )
        )

    def create_notify_new_comments_for_chef_pencil_record(self, user, chef_pencil_record, comments):
        comments_ids = ','.join([str(c.pk) for c in comments])
        self._create_notify(
            redis_key=f'notify_new_comments_for_chef_pencil_record_{chef_pencil_record.pk}_{comments_ids}',
            notify=Notify(
                code=Notify.Code.NEW_COMMENTS_IN_YOUR_CHEF_PENCIL_RECORD,
                user=user,
                payload=dict(
                    id=chef_pencil_record.pk,
                    title=chef_pencil_record.title,
                    count=len(comments)
                )
            )
        )