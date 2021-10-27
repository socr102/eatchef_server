from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Rating(models.Model):

    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='ratings')
    rating = models.PositiveSmallIntegerField(
        'rating', validators=[MinValueValidator(1), MaxValueValidator(5)])

    limit = models.Q(app_label='recipe', model='recipe') | models.Q(app_label='chef_pencils', model='chefpencilrecord')
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='ratings',
        null=False,
        limit_choices_to=limit
    )
    object_id = models.BigIntegerField(null=False)
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:

        unique_together = ['user', 'content_type', 'object_id']

    def __str__(self):
        return f'#{self.pk} for [{self.content_object}] rating: {self.rating} by {self.user}'


class Like(models.Model):

    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='likes')

    limit = models.Q(app_label='recipe', model='recipe')
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='likes',
        null=False,
        limit_choices_to=limit
    )
    object_id = models.BigIntegerField(null=False)
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:

        unique_together = ['user', 'content_type', 'object_id']

    def __str__(self):
        return f'#{self.pk} for [{self.content_object}] by {self.user}'


class Comment(models.Model):

    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='comments')

    limit=models.Q(app_label = 'recipe', model = 'recipe') | models.Q(app_label = 'chef_pencils', model = 'chefpencilrecord')
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='comments',
        null=False,
        limit_choices_to = limit
    )
    object_id = models.BigIntegerField(null=False)
    content_object = GenericForeignKey('content_type', 'object_id')

    text = models.TextField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    notification_sent = models.BooleanField(default=False)

    def __str__(self):
        return f'#{self.pk} for [{self.content_object}] text: {self.text[0:20]} by {self.user}'


class CommentLike(models.Model):

    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='comment_likes')
    comment = models.ForeignKey(
        'Comment', on_delete=models.CASCADE, related_name='comment_likes')
    is_dislike = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:

        unique_together = ['user', 'comment']

    def __str__(self):
        return f'#{self.pk} for [{self.comment}] by {self.user}'
