from django.db import models
from django.utils.translation import gettext_lazy as _


class NotifyQuerySet(models.QuerySet):

    def owner(self, user):
        return self.filter(user=user)


class NotifyManager(models.Manager):

    def get_queryset(self):
        return NotifyQuerySet(self.model, using=self._db).order_by('-created_at')


class Notify(models.Model):

    class Code(models.IntegerChoices):
        NEW_USER_GREETING = 1, _('New user greeting')

        RECIPE_CREATED_AND_AWAITING_APPROVAL = 2, _('Recipe created. Awaiting approval')
        RECIPE_STATUS_CHANGED = 3, _('Recipe status changed')
        NEW_COMMENTS_IN_YOUR_RECIPE = 4, _('New comments in your recipe')

        CHEF_PENCIL_RECORD_CREATED_AND_AWAITING_APPROVAL = 5, _('Chef Pencil Record created. Awaiting approval')
        CHEF_PENCIL_RECORD_STATUS_CHANGED = 6, _('Chef Pencil Record status changed')
        NEW_COMMENTS_IN_YOUR_CHEF_PENCIL_RECORD = 7, _('New comments in your Chef Pencil Record')

    code = models.PositiveSmallIntegerField('code', choices=Code.choices)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='notifies')
    payload = models.JSONField('payload', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = NotifyManager()