from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from main.mixins import UpdatedFieldsMixin
from main.validators import (validate_decimals, validate_images_file_max_size,
                             validate_video_ext, validate_video_file_max_size)
from social.models import Comment, Like, Rating
from stats.models import StatRecord
from users.models import User
from utils.file_storage import (recipe_image_file_path,
                                recipe_new_image_file_path,
                                recipe_thumbnail_file_path,
                                recipe_video_file_path)

from recipe.enums import (CookingMethods, CookingSkills, Cuisines, Diets,
                          RecipeTypes, Units)


class RecipeQuerySet(models.QuerySet):

    def get_published(self):
        return self.filter(publish_status=Recipe.PublishStatus.PUBLISHED)

    def get_published_and_accepted(self):
        return self.filter(
            publish_status=Recipe.PublishStatus.PUBLISHED,
            status=Recipe.Status.ACCEPTED
        )

    def get_filtered_by_source(self, only_eatchefs_recipes):
        try:
            user = User.objects.get(
                full_name=settings.EATCHEFS_ACCOUNT_NAME,
                is_staff=True
            )
        except User.DoesNotExist:
            pass
        else:
            if only_eatchefs_recipes is not None:
                return self.filter(user=user)
        return self


class RecipeManager(models.Manager):

    def get_queryset(self):
        return RecipeQuerySet(self.model, using=self._db)


class Recipe(UpdatedFieldsMixin, models.Model):

    class PublishStatus(models.IntegerChoices):
        NOT_PUBLISHED = 1, _('Not published')
        PUBLISHED = 2, _('Published')

    class Status(models.IntegerChoices):
        AWAITING_ACCEPTANCE = 1, _('Awaiting acceptance')
        ACCEPTED = 2, _('Accepted')
        REJECTED = 3, _('Rejected')

    title = models.CharField('title', max_length=255)
    cooking_time = models.DurationField('cooking time')
    cuisines = ArrayField(
        base_field=models.IntegerField(choices=Cuisines.choices),
        size=None,
        verbose_name='Cuisines',
        null=True,
        blank=True
    )
    types = ArrayField(
        base_field=models.IntegerField(choices=RecipeTypes.choices),
        size=None,
        verbose_name='Types',
        null=True,
        blank=True
    )
    cooking_methods = ArrayField(
        base_field=models.IntegerField(choices=CookingMethods.choices),
        size=None,
        verbose_name='Cooking methods',
        null=True,
        blank=True
    )
    cooking_skills = models.IntegerField(
        'Cooking skills',
        choices=CookingSkills.choices,
        null=True,
        blank=True
    )
    diet_restrictions = ArrayField(
        base_field=models.IntegerField(choices=Diets.choices),
        size=None,
        verbose_name='Diet restrictions',
        null=True,
        blank=True
    )

    description = models.TextField(max_length=4000)

    language = models.CharField('language', null=True, blank=True, max_length=255)
    caption = models.CharField('caption', null=True, blank=True, max_length=255)

    publish_status = models.IntegerField(
        'publish status',
        choices=PublishStatus.choices,
        default=PublishStatus.NOT_PUBLISHED
    )
    status = models.IntegerField(
        'status',
        choices=Status.choices,
        default=Status.AWAITING_ACCEPTANCE
    )

    avg_rating = models.FloatField(
        'Rating',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    likes_number = models.PositiveSmallIntegerField(
        'Likes',
        null=True,
        blank=False,
        default=0
    )
    views_number = models.PositiveSmallIntegerField(
        'Views',
        null=True,
        blank=False,
        default=0
    )

    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='recipes')

    # info
    proteins = models.FloatField(
        _('Proteins'),
        null=True,
        blank=True,
        validators=[MaxValueValidator(100)]
    )
    fats = models.FloatField(
        _('Fats'),
        null=True,
        blank=True,
        validators=[MaxValueValidator(100)]
    )
    carbohydrates = models.FloatField(
        _('Carbohydrates'),
        null=True,
        blank=True,
        validators=[MaxValueValidator(100)]
    )
    calories = models.FloatField(
        _('Calories'),
        null=True,
        blank=True,
        validators=[MaxValueValidator(99999)]
    )

    rejection_reason = models.TextField(
        null=True,
        blank=True,
        default=''
    )

    # import-related fields
    source_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    source_url = models.URLField(unique=True, null=True, blank=True)
    is_parsed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    objects = RecipeManager()

    ratings = GenericRelation(Rating, related_query_name='recipe')
    comments = GenericRelation(Comment, related_query_name='recipe')
    likes = GenericRelation(Like, related_query_name='recipe')

    stat_records = GenericRelation(StatRecord, related_query_name='recipe')

    class Meta:
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'

    def __str__(self):
        rating = self.avg_rating if self.avg_rating else '-'
        likes = self.likes_number if self.likes_number else '-'
        return f'#{self.pk} - {self.title[0:50]} (by {self.user}) rating: {rating}, likes: {likes}'

    @property
    def video_url(self):
        if self.video:
            return self.video.video.storage.url(name=self.video.video.name)
        return None

    @property
    def video_thumbnail_url(self):
        if self.video:
            return self.video.video_thumbnail.storage.url(name=self.video.video_thumbnail.name)
        return None


class RecipeImage(models.Model):

    recipe = models.ForeignKey(
        'Recipe',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='images'
    )
    file = models.ImageField(
        'file',
        null=True,
        blank=True,
        upload_to=recipe_new_image_file_path,
        validators=[validate_images_file_max_size]
    )
    user = models.ForeignKey(
        'users.User',
        null=True,
        blank=False,
        on_delete=models.CASCADE,
        related_name='recipe_images'
    )
    main_image = models.BooleanField(default=False)
    order_index = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f'#{self.pk} by User: {self.user} File: {self.file} [{self.created_at}]'


class RecipeVideo(models.Model):

    user = models.ForeignKey(
        'users.User',
        null=True,
        blank=False,
        on_delete=models.CASCADE,
        related_name='recipe_videos'
    )
    recipe = models.OneToOneField(
        'recipe.Recipe',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='video'
    )
    video = models.FileField(
        'Video',
        upload_to=recipe_video_file_path,
        null=True,
        blank=False,
        validators=[validate_video_file_max_size, validate_video_ext],
    )
    video_thumbnail = models.ImageField(
        'Thumbnail',
        upload_to=recipe_thumbnail_file_path,
        validators=[validate_images_file_max_size],
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f'#{self.pk} by User: {self.user} File: {self.video} [{self.created_at}]'


class Ingredient(models.Model):

    title = models.CharField('Title', max_length=255)
    quantity = models.FloatField(
        validators=[validate_decimals]
    )
    unit = models.CharField(
        max_length=25,
        choices=Units.choices,
        default="",
        null=True,
        blank=True
    )
    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='ingredients'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False
    )

    def __str__(self):
        return f'#{self.pk}: {self.title} ({self.quantity} {self.unit}) for [{self.recipe}]'


class RecipeStep(models.Model):

    num = models.PositiveSmallIntegerField(_('Number'))
    title = models.CharField('title', max_length=50)
    description = models.TextField(max_length=200)
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE, related_name='steps')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)


class Tag(models.Model):
    text = models.CharField(max_length=255, unique=True)
    recipes = models.ManyToManyField(
        'Recipe',
        through='TagRecipeRelation',
        related_name='tags',
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f'#{self.pk} "{self.text}" {self.created_at}'


class TagRecipeRelation(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='tag_recipe_relations')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:

        unique_together = ['tag', 'recipe']


class SavedRecipe(models.Model):

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='saved_recipes'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='saved_recipes'
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:

        unique_together = ['user', 'recipe']
