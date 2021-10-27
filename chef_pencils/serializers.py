from main.validators import validate_images_file_max_size
from recipe.serializers import QuerySerializer
from rest_framework import serializers
from social.models import Like
from users.serializers import UserCardSerializer, UserSerializer

from chef_pencils.models import (ChefPencilCategory, ChefPencilImage,
                                 ChefPencilRecord,
                                 ChefPencilRecordCategoryLink,
                                 SavedChefPencilRecord)
from chef_pencils.signals import S_new_chef_recipe_record_created


class ChefPencilQuerySerializer(QuerySerializer):
    """
    A serializer to provide suggestions for ChefPencil blog posts

    Based on and similar to Recipe search suggestions query serializer
    """

    def get_results(self):

        results = ChefPencilRecord.objects.filter(
            title__icontains=self.validated_data['search']
        ).order_by('-created_at')[0:30]

        return results


class ChefPencilRecordSerializer(serializers.ModelSerializer):

    user = UserSerializer(read_only=True)

    images_to_delete = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    categories = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )

    class Meta:
        model = ChefPencilRecord
        fields = [
            'pk',
            'user',
            'title',
            'html_content',
            'images_to_delete',
            'avg_rating',
            'status',
            'likes_number',
            'views_number',
            'categories',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'pk',
            'user',
            'status',
            'avg_rating',
            'created_at',
            'updated_at'
        ]

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        return super().validate(attrs)

    def create(self, validated_data):

        categories = []
        if 'categories' in validated_data:
            categories = validated_data['categories']
            del validated_data['categories']

        instance = super().create(validated_data)

        if categories:
            for cpc_id in categories:
                try:
                    cpc = ChefPencilCategory.objects.get(pk=int(cpc_id))
                except Exception:
                    pass
                else:
                    ChefPencilRecordCategoryLink.objects.get_or_create(
                        chefpencil_record=instance,
                        category=cpc
                    )

        S_new_chef_recipe_record_created.send(
            sender=self.__class__,
            instance=instance
        )

        return instance

    def update(self, instance, validated_data):

        if instance.status == ChefPencilRecord.Status.APPROVED:
            instance.status = ChefPencilRecord.Status.AWAITING_APPROVAL

        if 'images_to_delete' in validated_data:
            ChefPencilImage.objects.filter(
                chefpencil_record=instance,
                pk__in=self.validated_data['images_to_delete']
            ).delete()

        categories = []
        if 'categories' in validated_data:
            categories = validated_data['categories']
            del validated_data['categories']

        if categories:

            ChefPencilRecordCategoryLink.objects.filter(
                chefpencil_record=instance
            ).delete()

            for cpc_id in categories:
                try:
                    cpc = ChefPencilCategory.objects.get(pk=int(cpc_id))
                except Exception:
                    pass
                else:
                    ChefPencilRecordCategoryLink.objects.get_or_create(
                        chefpencil_record=instance,
                        category=cpc
                    )

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        images = []
        image_url = None
        for i in instance.images.all():
            if i.main_image:
                image_url = i.image.storage.url(name=i.image.name)
            images.append({
                'id': i.pk,
                'url': i.image.storage.url(name=i.image.name),
                'main_image': i.main_image,
                "order_index": i.order_index
            })
            ret['images'] = sorted(images, key=lambda x: x['order_index'])

        ret['image'] = image_url

        ret['categories'] = [{'pk': i.pk, 'title': i.title} for i in instance.chefpencilcategory_set.all()]

        try:
            user = self.context['request'].user
        except KeyError:
            ret['user_liked'] = False
            ret['user_saved_chef_pencil_record'] = False
        else:
            if not user.is_authenticated:
                ret['user_liked'] = False
                ret['user_saved_chef_pencil_record'] = False
            else:
                try:
                    Like.objects.get(
                        user=self.context['request'].user,
                        content_type__model=instance.__class__.__name__.lower(),
                        object_id=instance.pk
                    )
                except Like.DoesNotExist:
                    ret['user_liked'] = False
                else:
                    ret['user_liked'] = True

                try:
                    sr = SavedChefPencilRecord.objects.get(
                        user=self.context['request'].user,
                        chef_pencil_record=instance
                    )
                except SavedChefPencilRecord.DoesNotExist:
                    ret['user_saved_chef_pencil_record'] = False
                else:
                    ret['user_saved_chef_pencil_record'] = sr.pk

        return ret


class ChefPencilImageSerializer(serializers.ModelSerializer):

    image = serializers.FileField(
        allow_null=False,
        allow_empty_file=False,
        validators=[
            validate_images_file_max_size,
        ],
        required=True
    )

    class Meta:
        model = ChefPencilImage
        fields = [
            'pk',
            'user',
            'image',
        ]
        read_only_fields = [
            'pk',
            'user',
        ]

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        return super().validate(attrs)


class ChefPencilCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ChefPencilCategory
        fields = [
            'pk',
            'title',
        ]
        read_only_fields = [
            'pk',
            'title',
        ]


class SavedChefPencilRecordSerializer(serializers.ModelSerializer):

    user = UserCardSerializer(read_only=True)

    class Meta:
        model = SavedChefPencilRecord
        fields = ['pk', 'user', 'chef_pencil_record', 'created_at']
        read_only_fields = ['pk', 'user', 'created_at']

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        return super().validate(attrs)

    def create(self, validated_data):
        saved, created = SavedChefPencilRecord.objects.get_or_create(
            user=validated_data['user'],
            chef_pencil_record=validated_data['chef_pencil_record']
        )
        return saved

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['chef_pencil_record'] = ChefPencilRecordSerializer(
            instance=instance.chef_pencil_record,
            context={'request': self.context['request']}
        ).data
        return ret
