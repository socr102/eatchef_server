from .models import Rating, Like, Comment, CommentLike
from django.contrib import admin

from social.models import Comment, Rating, Like, CommentLike


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'rating',
        'content_type',
        'object_id',
        'created_at',
    )
    list_filter = ('content_type', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'content_type', 'object_id', 'created_at')
    list_filter = ('content_type', 'created_at')
    date_hierarchy = 'created_at'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'content_type',
        'object_id',
        'text',
        'notification_sent',
        'created_at',
        'likes_number',
        'dislikes_number',
    )
    list_filter = ('content_type', 'notification_sent', 'created_at')
    date_hierarchy = 'created_at'

    def likes_number(self, obj):
        # TODO: for now, simply count like that
        return CommentLike.objects.filter(comment=obj, is_dislike=False).count()

    def dislikes_number(self, obj):
        return CommentLike.objects.filter(comment=obj, is_dislike=True).count()

@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'comment', 'is_dislike', 'created_at')
    list_filter = ('created_at', 'is_dislike',)
    date_hierarchy = 'created_at'
