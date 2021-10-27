from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from users.serializers import UserCardSerializer

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from social.models import Comment, Rating, Like, CommentLike


class RatingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Rating
        fields = ['user', 'content_type', 'object_id', 'rating', 'created_at']
        read_only_fields = ['user', 'content_type', 'object_id', 'created_at']

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        attrs['content_type'] = self.initial_data['content_type']

        ct = ContentType.objects.get(model=attrs['content_type'])
        ct_class = ct.model_class()
        try:
            content_object = ct_class.objects.get(pk=self.context["view"].kwargs["pk"])
        except Exception:
            raise ValidationError({attrs['content_type']: "Object does not exists"})
        attrs['content_object'] = content_object
        return super().validate(attrs)

    def create(self, validated_data):
        try:
            rating = Rating.objects.create(
                user=validated_data['user'],
                content_object=validated_data['content_object'],
                rating=validated_data['rating']
            )
        except IntegrityError:
            rating = Rating.objects.get(
                user=validated_data['user'],
                content_type__model=validated_data['content_type'],
                object_id=validated_data['content_object'].pk
            )
        return rating


class LikeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Like
        fields = ['user', 'content_type', 'object_id', 'created_at']
        read_only_fields = ['user', 'content_type', 'object_id', 'created_at']

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        attrs['content_type'] = self.initial_data['content_type']

        ct = ContentType.objects.get(model=attrs['content_type'])
        ct_class = ct.model_class()
        try:
            content_object = ct_class.objects.get(
                pk=self.context["view"].kwargs["pk"])
        except Exception:
            raise ValidationError(
                {attrs['content_type']: "Object does not exists"})
        attrs['content_object'] = content_object
        return super().validate(attrs)

    def create(self, validated_data):
        try:
            like = Like.objects.get(
                user=validated_data['user'],
                content_type__model=validated_data['content_type'],
                object_id=validated_data['content_object'].pk
            )
            like.delete()
            self.context['like_status'] = 'deleted'
        except Like.DoesNotExist:
            like = Like.objects.create(
                user=validated_data['user'],
                content_object=validated_data['content_object'],
            )
            self.context['like_status'] = 'created'
        return like

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['like_status'] = self.context.get('like_status', '')
        return ret


class CommentSerializer(serializers.ModelSerializer):

    user = UserCardSerializer(read_only=True)

    text = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        min_length=5,
        max_length=3000
    )

    class Meta:
        model = Comment
        fields = ['pk', 'user', 'content_type', 'object_id', 'text', 'created_at']
        read_only_fields = ['pk', 'user', 'content_type', 'object_id', 'created_at']

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        attrs['content_type'] = self.initial_data['content_type']

        ct = ContentType.objects.get(model=attrs['content_type'])
        ct_class = ct.model_class()
        try:
            content_object = ct_class.objects.get(
                pk=self.context["view"].kwargs["pk"])
        except Exception:
            raise ValidationError(
                {attrs['content_type']: "Object does not exists"})
        attrs['content_object'] = content_object
        return super().validate(attrs)

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        # if pre-calculated in 'annotate'
        if hasattr(instance, 'likes_number'):
            ret['likes_number'] = instance.likes_number
        else:
            ret['likes_number'] = CommentLike.objects.filter(comment=instance, is_dislike=False).count()

        if hasattr(instance, 'dislikes_number'):
            ret['dislikes_number'] = instance.dislikes_number
        else:
            ret['dislikes_number'] = CommentLike.objects.filter(comment=instance, is_dislike=True).count()

        return ret

    def create(self, validated_data):
        try:
            comment = Comment.objects.create(
                user=validated_data['user'],
                content_object=validated_data['content_object'],
                text=validated_data['text']
            )
        except IntegrityError:
            comment = Comment.objects.get(
                user=validated_data['user'],
                content_type__model=validated_data['content_type'],
                object_id=validated_data['content_object'].pk
            )
        return comment


class CommentLikeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CommentLike
        fields = ['user', 'comment', 'created_at']
        read_only_fields = ['user', 'comment', 'created_at']

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        try:
            comment = Comment.objects.get(pk=self.context["view"].kwargs["pk"])
        except Exception:
            raise ValidationError({'comment': "Comment does not exists"})
        attrs['comment'] = comment
        if 'dislike' in self.initial_data:
            attrs['dislike'] = True
        return super().validate(attrs)

    def create(self, validated_data):
        try:
            cl = CommentLike.objects.get(
                user=validated_data['user'],
                comment=validated_data['comment']
            )
        except CommentLike.DoesNotExist:
            like = CommentLike.objects.create(
                user=validated_data['user'],
                comment=validated_data['comment'],
                is_dislike='dislike' in validated_data
            )
            if 'dislike' in validated_data:
                self.context['dislike_status'] = 'created'
            else:
                self.context['like_status'] = 'created'
            return like
        else:

            if cl.is_dislike and 'dislike' in validated_data:
                cl.delete()
                self.context['dislike_status'] = 'deleted'
                return cl

            if not cl.is_dislike and 'dislike' not in validated_data:
                cl.delete()
                self.context['like_status'] = 'deleted'
                return cl

            if cl.is_dislike and 'dislike' not in validated_data:
                cl.delete()
                self.context['dislike_status'] = 'deleted'
                like = CommentLike.objects.create(
                    user=validated_data['user'],
                    comment=validated_data['comment'],
                )
                self.context['like_status'] = 'created'
                return like

            if not cl.is_dislike and 'dislike' in validated_data:
                cl.delete()
                self.context['like_status'] = 'deleted'
                like = CommentLike.objects.create(
                    user=validated_data['user'],
                    comment=validated_data['comment'],
                    is_dislike=True
                )
                self.context['dislike_status'] = 'created'
                return like

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['like_status'] = self.context.get('like_status', '')
        ret['dislike_status'] = self.context.get('dislike_status', '')
        return ret
