from django.db import models
from utils.file_storage import (
    banner_image_file_path,
    block_image_file_path
)
from main.validators import validate_images_file_max_size
from django.contrib.postgres.fields import ArrayField


class Banner(models.Model):

    image = models.ImageField(
        'Image',
        upload_to=banner_image_file_path,
        validators=[validate_images_file_max_size]
    )

    def __str__(self):
        return f'Banner #{self.pk}: {self.image}'

class HomepagePinnedRecipe(models.Model):

    recipe = models.OneToOneField('recipe.Recipe', on_delete=models.CASCADE, related_name='pinned_recipe')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return f'HomepagePinnedRecipe #{self.pk}: {self.recipe}'


class MealOfTheWeekRecipe(models.Model):

    recipe = models.OneToOneField(
        'recipe.Recipe', on_delete=models.CASCADE, related_name='meal_of_the_week')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return f'MealOfTheWeekRecipe #{self.pk}: {self.recipe}'


class TopRatedRecipe(models.Model):

    recipe = models.OneToOneField(
        'recipe.Recipe', on_delete=models.CASCADE, related_name='top_rated_recipe')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return f'TopRatedRecipe #{self.pk}: {self.recipe}'


class FeaturedRecipe(models.Model):

    recipe = models.OneToOneField(
        'recipe.Recipe', on_delete=models.CASCADE, related_name='featured_recipe')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return f'FeaturedRecipe #{self.pk}: {self.recipe}'


class Support(models.Model):

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='supports',
        null=True,
        blank=True
    )
    email = models.EmailField(blank=False, null=False)

    def __str__(self):
        return f'Support #{self.pk} {self.email} ({self.user})'


class ParserData(models.Model):

    date = models.DateField(unique=True)

    today_requests = models.PositiveIntegerField(default=0)
    today_results = models.PositiveIntegerField(default=0)

    checked_ids = ArrayField(
        base_field=models.IntegerField(),
        size=None,
        verbose_name='Checked ids',
        null=True,
        blank=True
    )
    added_recipes = models.TextField(default='', null=True, blank=True)
    not_added_recipes = models.TextField(default='', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return f'ParserData #{self.pk}'


class Block(models.Model):

    class Buttons(models.TextChoices):
        EMPTY = ""
        CHEF = "chef"
        FOODIE = "foodie"

    image = models.ImageField(
        'Image',
        upload_to=block_image_file_path,
        validators=[validate_images_file_max_size]
    )

    title = models.CharField(max_length=255)

    text = models.TextField(max_length=1000)

    change_time = models.PositiveIntegerField('Change time (sec)', default=5)

    button = models.CharField(
        'Button',
        max_length=25,
        choices=Buttons.choices,
        default=Buttons.EMPTY,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    def __str__(self):
        return f'Block #{self.pk}: {self.image}'
