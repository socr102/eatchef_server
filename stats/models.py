from enum import Enum

from django.db import models
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone, dateformat
from django.db import IntegrityError

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class BaseStatCounter(models.Model):

    count = models.IntegerField(verbose_name='Quantity', default=0)

    class Meta:
        abstract = True


class ViewsCounter(BaseStatCounter):

    def __str__(self):
        return f'#{self.pk}: {self.count}'

    class Meta:
        ordering = ['count']


class SharesCounter(BaseStatCounter):

    def __str__(self):
        return f'#{self.pk}: {self.count}'

    class Meta:
        ordering = ['count']


class StatRecordManager(models.Manager):

    def increment(self, content_object, model):
        try:
            stat_record = self.get(
                content_type__model=content_object.__class__.__name__.lower(),
                object_id=content_object.pk,
                date=dateformat.format(timezone.now(), 'Y-m-d')
            )
        except StatRecord.DoesNotExist:
            stat_record = self.create(
                content_object=content_object,
                date=dateformat.format(timezone.now(), 'Y-m-d')
            )
        return model.objects.filter(
            stat_record__id=stat_record.pk,
            stat_record__date=stat_record.date
        ).update(count=F('count') + 1)

    def increment_views(self, content_object):
        return self.increment(content_object, ViewsCounter)

    def increment_shares(self, content_object):
        return self.increment(content_object, SharesCounter)


class StatRecord(models.Model):

    limit = models.Q(app_label='recipe', model='recipe') | models.Q(app_label='chef_pencils', model='chefpencilrecord')
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='stat_records',
        null=False,
        limit_choices_to=limit
    )
    object_id = models.BigIntegerField(null=False)
    content_object = GenericForeignKey('content_type', 'object_id')

    views_counter = models.OneToOneField(
        ViewsCounter,
        on_delete=models.SET_NULL,
        related_name='stat_record',
        null=True,
        default=None,
        verbose_name='Views counter'
    )

    shares_counter = models.OneToOneField(
        SharesCounter,
        on_delete=models.SET_NULL,
        related_name='stat_record',
        null=True,
        default=None,
        verbose_name='Shares counter'
    )

    date = models.DateField(verbose_name='Day')

    objects = StatRecordManager()

    class Meta:
        unique_together = [['date', 'content_type', 'object_id']]

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.views_counter is None:
            self.views_counter = ViewsCounter.objects.create()
        if self.shares_counter is None:
            self.shares_counter = SharesCounter.objects.create()
        super().save(force_insert, force_update, using, update_fields)


class CounterKeys(Enum):

    VIEWS_COUNTER = ViewsCounter
    SHARES_COUNTER = SharesCounter

    @classmethod
    def choices(cls):
        return [key.name for key in cls]


@receiver(post_save, sender='recipe.Recipe')
@receiver(post_save, sender='chef_pencils.ChefPencilRecord')
def create_stat(sender, instance, created, **kwargs):
    if created:
        try:
            stat = StatRecord.objects.create(
                content_object=instance,
                date=dateformat.format(timezone.now(), 'Y-m-d')
            )
        except IntegrityError:
            stat = StatRecord.objects.get(
                content_type__model=instance.__class__.__name__.lower(),
                object_id=instance.pk,
                date=dateformat.format(timezone.now(), 'Y-m-d')
            )
