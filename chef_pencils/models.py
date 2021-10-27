from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from main.mixins import UpdatedFieldsMixin
from main.validators import validate_images_file_max_size
from social.models import Comment, Like, Rating
from utils.file_storage import chef_pencil_image_file_path


class ChefPencilRecordQuerySet(models.QuerySet):

    def get_approved(self):
        return self.filter(
            status=ChefPencilRecord.Status.APPROVED
        )


class ChefPencilRecordManager(models.Manager):

    def get_queryset(self):
        return ChefPencilRecordQuerySet(self.model, using=self._db)


class ChefPencilRecord(UpdatedFieldsMixin, models.Model):

    class Status(models.IntegerChoices):
        AWAITING_APPROVAL = 1, _('Awaiting approval')
        APPROVED = 2, _('Approved')
        REJECTED = 3, _('Rejected')

    title = models.CharField('title', max_length=255)

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='chefpencil_records'
    )

    html_content = models.TextField()

    status = models.IntegerField(
        'status',
        choices=Status.choices,
        default=Status.AWAITING_APPROVAL
    )

    rejection_reason = models.TextField(
        null=True,
        blank=True,
        default=''
    )

    avg_rating = models.FloatField(
        'Rating',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )

    ratings = GenericRelation(Rating, related_query_name='chefpencil_record')
    comments = GenericRelation(Comment, related_query_name='chefpencil_record')
    likes = GenericRelation(Like, related_query_name='chefpencil_record')

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

    stat_records = GenericRelation(Like, related_query_name='chefpencil_record')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    objects = ChefPencilRecordManager()

    class Meta:
        verbose_name = "Chef's Pencil Record"
        verbose_name_plural = "Chef's Pencil Records"

    def __str__(self):
        return f'#{self.pk} - {self.title[0:50]} (by {self.user}), likes: {self.likes_number}'


class ChefPencilImage(models.Model):

    image = models.FileField(
        'Attachment',
        upload_to=chef_pencil_image_file_path,
        validators=[validate_images_file_max_size]
    )

    chefpencil_record = models.ForeignKey(
        'ChefPencilRecord',
        on_delete=models.CASCADE,
        related_name='images',
        null=True,
        blank=True
    )

    main_image = models.BooleanField(default=False)
    order_index = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        verbose_name = "Chef's Pencil Image"
        verbose_name_plural = "Chef's Pencil Images"


class ChefPencilCategory(models.Model):

    title = models.CharField('Title', max_length=255)

    chefpencil_records = models.ManyToManyField(
        ChefPencilRecord,
        through='ChefPencilRecordCategoryLink'
    )

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        verbose_name = "Chef's Pencil Category"
        verbose_name_plural = "Chef's Pencil Categorys"

    def __str__(self):
        return f'#{self.pk}: {self.title}'


class ChefPencilRecordCategoryLink(models.Model):

    chefpencil_record = models.ForeignKey(
        ChefPencilRecord,
        related_name='records',
        on_delete=models.SET_NULL,
        null=True
    )
    category = models.ForeignKey(
        ChefPencilCategory,
        related_name='categories',
        on_delete=models.SET_NULL,
        null=True
    )
    class Meta:
        unique_together = ['category', 'chefpencil_record']

    class Meta:
        verbose_name = "Chef's Pencil Category Link"
        verbose_name_plural = "Chef's Pencil Category Links"


class SavedChefPencilRecord(models.Model):

    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='saved_chef_pencil_records'
    )
    chef_pencil_record = models.ForeignKey(
        ChefPencilRecord,
        on_delete=models.CASCADE,
        related_name='saved_chef_pencil_records'
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        unique_together = ['user', 'chef_pencil_record']

    class Meta:
        verbose_name = "Saved Chef's Pencil Record"
        verbose_name_plural = "Saved Chef's Pencil Records"
