import logging
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Sum
from main.watermark_storage import WatermarkStorage
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from social.models import Like

from recipe.models import (Ingredient, RecipeImage, RecipeStep, Tag,
                           TagRecipeRelation)
from recipe.signals import S_new_recipe_created

logger = logging.getLogger('django')

import sys

from django.core.files.uploadedfile import InMemoryUploadedFile
from users.serializers import UserCardSerializer

from recipe.models import (Ingredient, Recipe, RecipeImage, RecipeStep,
                           RecipeVideo, SavedRecipe)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ['title', 'quantity', 'unit', 'recipe']
        read_only_fields = []


class RecipeStepSerializer(serializers.ModelSerializer):

    class Meta:
        model = RecipeStep
        fields = ['num', 'title', 'description', 'recipe']
        read_only_fields = []


class RecipeImageSerializer(serializers.ModelSerializer):

    file = serializers.FileField(required=True)

    class Meta:
        model = RecipeImage
        fields = ['pk', 'user', 'file']
        read_only_fields = ['pk', 'user']

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        return super().validate(attrs)

    def create(self, validated_data):
        # add watermark
        """
        tmp_dir = Path(settings.PROJECT_DIR) / 'tmp'
        tmp_dir.mkdir(exist_ok=True)

        extension = Path(self.validated_data['file'].name).suffix

        temp_file = tempfile.NamedTemporaryFile(
            suffix=extension,
            dir=tmp_dir,
            delete=False
        )

        with open(temp_file.name, 'wb') as df:
            for chunk in self.validated_data['file'].chunks():
                df.write(chunk)

        WatermarkStorage().add_watermark(temp_file.name)

        new_file = InMemoryUploadedFile(temp_file.file,
                                       'ImageField',
                                       temp_file.name,
                                       extension.upper(),
                                       sys.getsizeof(temp_file.file), None)

        validated_data['file'] = new_file

        res = super().create(validated_data)
        Path(temp_file.name).unlink()
        """
        res = super().create(validated_data)
        return res


class RecipeVideoSerializer(serializers.ModelSerializer):

    video = serializers.FileField(required=True)

    class Meta:
        model = RecipeVideo
        fields = ['pk', 'user', 'video', 'video_thumbnail']
        read_only_fields = ['pk', 'user', 'video_thumbnail']

    def validate(self, attrs):

        if not attrs['video'].name.endswith('.mp4'):
            raise ValidationError(
                {'video': 'Incorrect file type. mp4 is expected'})

        attrs['user'] = self.context['request'].user
        return super().validate(attrs)

    def create(self, validated_data):
        """
        Additional validation inside
        """
        try:
            rv = super().create(validated_data)
        except ValidationError as e:
            raise ValidationError({"video": str(e.detail['video'])}) from e
        return rv


class CustomDurationField(serializers.DurationField):
    """
    A customized DurationField to accept/return 'HH:MM' by default
    """

    def to_internal_value(self, value):
        value = value + ':00'
        return super().to_internal_value(value)

    def to_representation(self, value):
        value = super().to_representation(value)
        value = value.rsplit(':', 1)[0]  # remove seconds
        return value


class RecipeCardSerializer(serializers.ModelSerializer):

    user = UserCardSerializer(read_only=True)
    cooking_time = CustomDurationField()

    class Meta:
        model = Recipe
        fields = [
            'pk',
            'user',
            'title',
            'cooking_time',
            'description',
            'language',
            'caption',
            'cuisines',
            'types',
            'cooking_methods',
            'cooking_skills',
            'diet_restrictions',
            'calories',
            'proteins',
            'carbohydrates',
            'fats',
            'status',
            'is_parsed',
            'publish_status',
            'avg_rating',
            'likes_number',
            'views_number',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'pk',
            'user',  # remove if problems
            'status',
            'is_parsed',
            'avg_rating',
            'likes_number',
            'views_number',
            'created_at',
            'updated_at'
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        images = []
        for r in instance.images.all():
            images.append({'id': r.pk, 'url': r.file.storage.url(name=r.file.name), 'main_image': r.main_image})
        ret['images'] = sorted(images, key=lambda x: x['main_image'], reverse=True)


    def to_representation(self, instance):
        ret = super().to_representation(instance)

        images = []
        for r in instance.images.all():
            images.append({
                'id': r.pk,
                'url': r.file.storage.url(name=r.file.name),
                'main_image': r.main_image
            })
        ret['images'] = sorted(images, key=lambda x: x['main_image'], reverse=True)

        try:
            ret['video'] = instance.video.pk
        except Exception:
            ret['video'] = None

        return ret


class RecipeSavedRecipeSerializer(RecipeCardSerializer):
    """
    This is slightly extended (has 'user_saved_recipe' returned) serializer
    for work with SavedRecipe to reduce number of SQL queries for them
    """

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        try:
            user = self.context['request'].user
        except KeyError:
            ret['user_saved_recipe'] = False
        else:
            if not user.is_authenticated:
                ret['user_saved_recipe'] = False
            else:
                try:
                    sr = SavedRecipe.objects.get(
                        user=self.context['request'].user,
                        recipe=instance
                    )
                except SavedRecipe.DoesNotExist:
                    ret['user_saved_recipe'] = False
                else:
                    ret['user_saved_recipe'] = sr.pk

        return ret


class RecipeSerializer(serializers.ModelSerializer):

    user = UserCardSerializer(read_only=True)

    title = serializers.CharField(required=True)
    description = serializers.CharField(required=True)

    cooking_time = CustomDurationField()
    cooking_skills = serializers.IntegerField(required=True)
    cooking_methods = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False
    )
    cuisines = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False
    )
    diet_restrictions = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        allow_empty=False
    )

    ingredients = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )

    steps = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )

    """
    steps = SerializerMethodField()
    def get_steps(self, instance):
        return RecipeStepSerializer(instance.steps.order_by('num'), many=True).data
    """

    video = serializers.CharField(
        write_only=True,
        required=False,
        allow_null=True,
        allow_blank=True
    )

    images = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True
    )

    main_image = serializers.CharField(
        write_only=True,
        required=False
    )

    tags = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Recipe
        fields = [
            'pk',
            'user',
            'title',
            'cooking_time',
            'description',
            'language',
            'caption',
            'cuisines',
            'types',
            'cooking_methods',
            'cooking_skills',
            'diet_restrictions',
            'ingredients',
            'images',
            'calories',
            'proteins',
            'carbohydrates',
            'fats',
            'steps',
            'status',
            'is_parsed',
            'publish_status',
            'avg_rating',
            'likes_number',
            'views_number',
            'video',
            'video_url',
            'video_thumbnail_url',
            'views_number',
            'main_image',
            'ingredients',
            'tags',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'pk',
            'user',  # remove if problems
            'status',
            'is_parsed',
            'avg_rating',
            'likes_number',
            'views_number',
            'video_url',
            'video_thumbnail_url',
            'created_at',
            'updated_at'
        ]

    def validate(self, attrs):

        MAX_IMAGES_COUNT = 20

        attrs['user'] = self.context['request'].user

        if attrs.get('video') == '':
            del attrs['video']

        if attrs.get('video'):
            try:
                rv = RecipeVideo.objects.get(pk=attrs['video'])
            except RecipeVideo.DoesNotExist:
                raise ValidationError({'video': 'Incorrect video'})
            else:
                attrs['video'] = rv

        if len(attrs.get('images', [])) > MAX_IMAGES_COUNT:
            raise ValidationError({'images': f'No more than {MAX_IMAGES_COUNT} can be uploaded'})

        if 'images' in attrs:
            images = []
            for i in attrs.get('images', []):
                try:
                    ri = RecipeImage.objects.get(pk=i)
                except Exception as e:
                    raise ValidationError({'images': f'Incorrect image: {e}'})
                else:
                    images.append(ri)
            attrs['images'] = images

        # create
        if not self.instance:

            if not attrs.get('images'):
                raise ValidationError({'images': 'Images should not be empty'})

            if len(attrs.get('ingredients', [])) == 0:
                raise ValidationError({'ingredients': 'Ingredients are required'})

        return super().validate(attrs)

    def create(self, validated_data):

        images = validated_data['images']
        del validated_data['images']

        ingredients = validated_data['ingredients']
        del validated_data['ingredients']

        steps = validated_data.get('steps', [])
        if 'steps' in validated_data:
            del validated_data['steps']

        main_image = validated_data.get('main_image', '')
        if 'main_image' in validated_data:
            del validated_data['main_image']

        tags = validated_data.get('tags', [])
        if 'tags' in validated_data:
            del validated_data['tags']

        recipe = super().create(validated_data)

        for ingredient_data in ingredients:
            ingredient_data['recipe'] = recipe.pk
            serializer = IngredientSerializer(data=ingredient_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        for step_data in steps:
            step_data['recipe'] = recipe.pk
            serializer = RecipeStepSerializer(data=step_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        indexes = [i.pk for i in images]
        ris = RecipeImage.objects.filter(pk__in=indexes).all()
        for ri in ris:
            ri.recipe = recipe
            if str(ri.pk) == str(main_image):
                ri.main_image = True
            ri.order_index = indexes.index(ri.pk)
            ri.save()

        for tag_text in tags:
            tag, created = Tag.objects.get_or_create(text=tag_text.strip())
            _, created = TagRecipeRelation.objects.get_or_create(
                recipe=recipe,
                tag=tag
            )

        self._set_recipe_video(validated_data.get('video'), recipe)

        S_new_recipe_created.send(
            sender=self.__class__,
            instance=recipe
        )

        return recipe

    def update(self, instance, validated_data):

        if instance.status == Recipe.Status.ACCEPTED:
            instance.status = Recipe.Status.AWAITING_ACCEPTANCE

        RecipeVideo.objects.filter(recipe=instance).delete()

        self._set_recipe_video(validated_data.get('video'), instance)

        images = validated_data.get('images', [])
        if 'images' in validated_data:
            del validated_data['images']

        ingredients = validated_data.get('ingredients')
        if 'ingredients' in validated_data:
            del validated_data['ingredients']

        steps = validated_data.get('steps', [])
        if 'steps' in validated_data:
            del validated_data['steps']

        main_image = validated_data.get('main_image', '')
        if 'main_image' in validated_data:
            del validated_data['main_image']

        tags = validated_data.get('tags', [])
        if 'tags' in validated_data:
            del validated_data['tags']

        recipe = super().update(instance, validated_data)

        if ingredients is not None:
            Ingredient.objects.filter(recipe=recipe).delete()
            for ingredient_data in ingredients:
                ingredient_data['recipe'] = recipe.pk
                serializer = IngredientSerializer(data=ingredient_data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

        if steps:
            RecipeStep.objects.filter(recipe=recipe).delete()
            for step_data in steps:
                step_data['recipe'] = recipe.pk
                serializer = RecipeStepSerializer(data=step_data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

        # Images
        if images:

            indexes = [i.pk for i in images]
            RecipeImage.objects.filter(recipe=instance).exclude(
                pk__in=indexes
            ).delete()

            ris = RecipeImage.objects.filter(pk__in=indexes).all()
            for ri in ris:
                ri.recipe = recipe
                ri.order_index = indexes.index(ri.pk)
                ri.save()

            # clear images that were uploaded but were not sent
            RecipeImage.objects.filter(user=recipe.user, recipe__isnull=True).delete()

        if main_image:
            ri = RecipeImage.objects.filter(recipe=recipe, main_image=True).first()
            if not ri:
                old_ri_with_main_image = None
            else:
                old_ri_with_main_image = ri.pk
            RecipeImage.objects.filter(recipe=recipe).update(main_image=False)

            try:
                ri = RecipeImage.objects.get(pk=main_image)
            except RecipeImage.DoesNotExist:
                pass
            else:
                ri.main_image = True
                ri.save()

            # if incorrect value was set
            if RecipeImage.objects.filter(recipe=recipe, main_image=True).count() == 0 and old_ri_with_main_image:
                ri = RecipeImage.objects.get(pk=old_ri_with_main_image)
                ri.main_image = True
                ri.save()

        # Tags
        if tags:
            TagRecipeRelation.objects.filter(recipe=recipe).delete()
            for tag_text in tags:
                tag, created = Tag.objects.get_or_create(text=tag_text.strip())
                _, created = TagRecipeRelation.objects.get_or_create(
                    recipe=recipe,
                    tag=tag
                )

        return recipe

    def _set_recipe_video(self, video, instance):
        if video is not None:
            video.recipe = instance
            video.save()

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        images = []
        for r in instance.images.all():
            images.append({
                'id': r.pk,
                'url': r.file.storage.url(name=r.file.name),
                'main_image': r.main_image,
                "order_index": r.order_index
            })
        ret['images'] = sorted(images, key=lambda x: x['order_index'])

        steps = []
        for s in instance.steps.all():
            steps.append({
                'pk': s.pk,
                'num': s.num,
                'title': s.title,
                'description': s.description,
            })
        ret['steps'] = steps

        ingredients = []
        for i in instance.ingredients.all():
            ingredients.append({
                'pk': i.pk,
                'title': i.title,
                'quantity': i.quantity,
                'unit': i.unit
            })
        ret['ingredients'] = ingredients

        try:
            ret['views_number'] = instance.stat_records.aggregate(
                views_counter=Sum('views_counter__count'))['views_counter']
        except Exception:
            ret['views_number'] = 0

        try:
            ret['video'] = instance.video.pk
        except Exception:
            ret['video'] = None

        """
        tags = []
        for t in instance.tag_recipe_relations.all():
             tags.append({'id': t.tag.pk, 'text': t.tag.text})
        ret['tags'] = tags
        """

        try:
            user = self.context['request'].user
        except KeyError:
            ret['user_liked'] = False
            ret['user_saved_recipe'] = False
        else:
            if not user.is_authenticated:
                ret['user_liked'] = False
                ret['user_saved_recipe'] = False
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
                    sr = SavedRecipe.objects.get(
                        user=self.context['request'].user,
                        recipe=instance
                    )
                except SavedRecipe.DoesNotExist:
                    ret['user_saved_recipe'] = False
                else:
                    ret['user_saved_recipe'] = sr.pk

        return ret


class QuerySerializer(serializers.Serializer):
    search = serializers.CharField(write_only=True)

    def get_results(self):

        results = Recipe.objects.filter(
            title__icontains=self.validated_data['search']
        ).get_filtered_by_source(
            only_eatchefs_recipes=self.context['request'].query_params.get(
                'only_eatchefs_recipes', None
            )
        ).order_by('-likes_number')[0:30]

        return results

    def get_suggestions(self):

        titles = []
        for t in self.get_results():
            title = ''.join(list(filter(lambda x: x.isalpha() or x == ' ', t.title.lower().strip())))
            titles.append(title)

        query = self.validated_data['search'].strip().lower()

        res = []
        for title in titles:
            words_after = title.lower().split(query)[-1]
            if words_after:
                space = ' ' if words_after.lstrip() != words_after else ''

                # CASE: searching 'curry', found 'thai curry soup and coconut', return 'curry soup'
                if space:
                    word_to_add = words_after.strip().split()[0]
                    res.append(f'{query} {word_to_add}')

                # CASE: searching 'mozza', found 'italian tomato and mozzarella caprese', return 'mozzarella caprese'
                else:
                    word_to_add = words_after.strip().split()[0:2]
                    word_to_add = ' '.join(word_to_add)
                    res.append(f'{query}{word_to_add}')
            else:
                res.append(query)
        suggestions = [{'result': l} for l in sorted(set(res))[0:8]]
        return suggestions


class SavedRecipeSerializer(serializers.ModelSerializer):

    user = UserCardSerializer(read_only=True)

    class Meta:
        model = SavedRecipe
        fields = ['pk', 'user', 'recipe', 'created_at']
        read_only_fields = ['pk', 'user', 'created_at']

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        return super().validate(attrs)

    def create(self, validated_data):
        saved_recipe, created = SavedRecipe.objects.get_or_create(
            user=validated_data['user'],
            recipe=validated_data['recipe']
        )
        return saved_recipe

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['recipe'] = RecipeSavedRecipeSerializer(
            instance=instance.recipe,
            context={
                'request': self.context['request']
            }
        ).data
        return ret


class RecipeVideoSerializer(serializers.ModelSerializer):

    video = serializers.FileField(required=True)
    class Meta:
        model = RecipeVideo
        fields = ['pk', 'user', 'video', 'video_thumbnail']
        read_only_fields = ['pk', 'user', 'video_thumbnail']

    def validate(self, attrs):

        if not attrs['video'].name.endswith('.mp4'):
            raise ValidationError({'video': 'Incorrect file type. mp4 is expected'})

        attrs['user'] = self.context['request'].user
        return super().validate(attrs)

    def create(self, validated_data):
        try:
            rv = super().create(validated_data)
        except ValidationError as e:
            raise ValidationError({"video": str(e.detail['video'])}) from e
        return rv
