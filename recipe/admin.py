# -*- coding: utf-8 -*-
from datetime import date

from django import forms
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from main.admin_utils import get_app_list
from users.models import User
from utils.admin import DateFilter, DropdownFilter

from recipe.enums import CookingMethods, Cuisines, Diets, RecipeTypes
from recipe.forms import RejectReasonForm
from recipe.models import (Ingredient, Recipe, RecipeImage, RecipeStep,
                           RecipeVideo, SavedRecipe, Tag, TagRecipeRelation)

admin.AdminSite.get_app_list = get_app_list


class RecipeCreationFormAdmin(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.all().get_home_chef_accounts()|User.objects.filter(is_staff=True))

    cuisines = forms.MultipleChoiceField(
        choices=Cuisines.choices, required=True)

    types = forms.MultipleChoiceField(
        choices=RecipeTypes.choices, required=True)

    cooking_methods = forms.MultipleChoiceField(
        choices=CookingMethods.choices, required=True)

    diet_restrictions = forms.MultipleChoiceField(
        choices=Diets.choices, required=True)

    class Meta:
        model = Recipe
        fields = '__all__'

    def clean_cuisines(self):
        return list(map(int, self.cleaned_data['cuisines']))

    def clean_types(self):
        return list(map(int, self.cleaned_data['types']))

    def clean_cooking_methods(self):
        return list(map(int, self.cleaned_data['cooking_methods']))

    def clean_diet_restrictions(self):
        return list(map(int, self.cleaned_data['diet_restrictions']))


def accept_recipe(modeladmin, request, queryset):
    recipes = []
    for recipe in queryset:
        recipe.status = Recipe.Status.ACCEPTED
        recipe.save()


def reject_recipe(modeladmin, request, queryset):
    recipes = []
    for recipe in queryset:
        recipe.status = Recipe.Status.REJECTED
        recipe.save()


accept_recipe.short_description = "Accept recipe"
reject_recipe.short_description = "Reject recipe"


class IngredientInline(admin.TabularInline):
    model = Ingredient


class RecipeStepInline(admin.TabularInline):
    model = RecipeStep


class RecipeImageInline(admin.TabularInline):
    model = RecipeImage
    min_num = 1

    fields = ('rendered_image', 'file', 'main_image', 'order_index',)
    readonly_fields = ('rendered_image',)

    def rendered_image(self, obj):
        if obj.file:
            url = obj.file.storage.url(name=obj.file.name)
            return mark_safe(f"""<a href="/admin/recipe/recipeimage/{obj.pk}/change/"><img src="{url}" width=320 height=240 /></a>""")
        return ''

class RecipeVideoInline(admin.TabularInline):
    model = RecipeVideo
    min_num = 1

    fields = ('rendered_video_thumbnail', 'video',)
    readonly_fields = ('rendered_video_thumbnail', 'video',)

    def rendered_video_thumbnail(self, obj):
        if obj.video_thumbnail:
            url = obj.video_thumbnail.storage.url(
                name=obj.video_thumbnail.name)
            return mark_safe(f"""<a href="/admin/recipe/recipevideo/{obj.pk}/change/"><img src="{url}" width=320 height=240 /></a>""")
        return ''


class TagRecipeRelationInline(admin.TabularInline):
    model = TagRecipeRelation


class PublishStatusFilter(SimpleListFilter):
    title = _('publish status')

    parameter_name = 'publish_status__exact'

    def lookups(self, request, model_admin):
        return (
            (0, _('All')),
            (1, Recipe.PublishStatus.NOT_PUBLISHED.label),
            (2, Recipe.PublishStatus.PUBLISHED.label),
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:

            if self.value() is None:
                is_selected = True if lookup == Recipe.PublishStatus.PUBLISHED else False  # PUBLISHED by default
            else:
                is_selected = self.value() == str(lookup)

            yield {
                'selected': is_selected,
                'query_string': cl.get_query_string({self.parameter_name: lookup,}, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() in [str(Recipe.PublishStatus.PUBLISHED), str(Recipe.PublishStatus.NOT_PUBLISHED)]:
            return queryset.filter(publish_status=self.value())
        elif self.value() == '0':
            return queryset.all()
        else:
            return queryset.filter(publish_status=Recipe.PublishStatus.PUBLISHED)


class RecipeFilter(SimpleListFilter):
    title = _('author')

    parameter_name = 'author_type'

    def lookups(self, request, model_admin):
        return (
            (0, _('All')),
            (1, 'From API'),
            (2, 'By users'),
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == str(lookup),
                'query_string': cl.get_query_string({self.parameter_name: lookup, }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.all()

        elif self.value() == '1':
            return queryset.filter(is_parsed=True)

        elif self.value() == '2':
            return queryset.exclude(is_parsed=True)

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    admin_priority = 1
    form = RecipeCreationFormAdmin
    actions = []
    fields = [
        'title',
        'user',
        'status',
        'rejection_reason',
        'publish_status',
        'cooking_time',
        'cuisines',
        'types',
        'cooking_methods',
        'diet_restrictions',
        'cooking_skills',
        'description',
        'proteins',
        'fats',
        'carbohydrates',
        'calories',
        # 'avg_rating',
        'likes_number',
        'views_number',
        'source_id',
        'source_url'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'recipe_actions'
    ]
    list_display = (
        'id',
        'recipe_title',
        'user',
        'recipe_actions',
        'publish_status',
        'cooking_time',
        'cuisines_info',
        'types_info',
        'cooking_methods_info',
        'diet_restrictions_info',
        'cooking_skills',
        'description',
        'language',
        'caption',
        'video_thumbnail_link',
        'video_link',
        # 'avg_rating',
        'likes_number',
        'views_number',
        'source_id',
        'source',
        'is_parsed',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'status',
        PublishStatusFilter,
        RecipeFilter,
        ('created_at', DateFilter),
        ('updated_at', DateFilter),
    )
    date_hierarchy = 'created_at'
    search_fields = ['title', 'pk', 'source_id', 'source_url', 'user__full_name', 'user__email']

    def cuisines_info(self, obj):
        return [Cuisines(v).label for v in obj.cuisines]

    def types_info(self, obj):
        return [RecipeTypes(v).label for v in obj.types]

    def cooking_methods_info(self, obj):
        return [CookingMethods(v).label for v in obj.cooking_methods]

    def diet_restrictions_info(self, obj):
        return [Diets(v).label for v in obj.diet_restrictions]

    def video_thumbnail_link(self, obj):
        if not obj.video:
            return '-'
        url = obj.video.video_thumbnail.storage.url(name=obj.video.video_thumbnail.name)
        return mark_safe(f'<a href="{url}" target="_blank" rel="nofollow"><img src="{url}" width=160 height=120 /></a>')

    def video_link(self, obj):
        if not obj.video:
            return '-'
        url = obj.video.video.storage.url(name=obj.video.video.name)
        return mark_safe(f'<a href="{url}" target="_blank" rel="nofollow">MP4</a>')

    def source(self, obj):
        if not obj.source_url:
            return '-'
        return mark_safe(f'<a href="{obj.source_url}" target="_blank" rel="nofollow">{obj.source_url}</a>')

    def recipe_title(self, obj):
        url = settings.BASE_CLIENT_URL + f'/recipe/{obj.pk}'
        return mark_safe(f'<a href="{url}" target="_blank" rel="nofollow">{obj.title}</a>')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(
                r'^(?P<recipe_id>.+)/accept/$',
                self.admin_site.admin_view(self.accept_recipe),
                name='recipe-accept',
            ),
            url(
                r'^(?P<recipe_id>.+)/reject/$',
                self.admin_site.admin_view(self.reject_recipe),
                name='recipe-reject',
            )
        ]
        return custom_urls + urls

    def recipe_actions(self, obj):

        btn1 = '<a class="button accept {classname} {clickable}" href="{url}">{text}</a>'.format(
            text='Accepted' if obj.status == Recipe.Status.ACCEPTED else 'Accept',
            classname='selected' if obj.status == Recipe.Status.ACCEPTED else '',
            clickable='' if obj.status in [Recipe.Status.AWAITING_ACCEPTANCE, Recipe.Status.REJECTED] else 'non_clickable',
            url=reverse('admin:recipe-accept', args=[obj.pk])
        )

        btn2 = '<a class="button reject {classname} {clickable}" href="{url}">{text}</a>'.format(
            text='Rejected' if obj.status == Recipe.Status.REJECTED else 'Reject',
            classname='selected' if obj.status == Recipe.Status.REJECTED else '',
            clickable='' if obj.status in [Recipe.Status.AWAITING_ACCEPTANCE, Recipe.Status.ACCEPTED] else 'non_clickable',
            url=reverse('admin:recipe-reject', args=[obj.pk])
        )
        return format_html(f'{btn1}&nbsp;{btn2}')

    recipe_actions.short_description = 'Recipe Actions'
    recipe_actions.allow_tags = True

    def accept_recipe(self, request, recipe_id, *args, **kwargs):
        recipe = self.get_object(request, recipe_id)
        recipe.status = Recipe.Status.ACCEPTED
        recipe.save()

        self.message_user(
            request,
            f'Status of recipe #{recipe.pk} changed to ACCEPTED'
        )

        url = reverse(
            'admin:recipe_recipe_changelist',
            current_app=self.admin_site.name,
        )
        return HttpResponseRedirect(url)

    def reject_recipe(self, request, recipe_id, *args, **kwargs):

        recipe = self.get_object(request, recipe_id)

        if request.method != 'POST':
            form = RejectReasonForm()

        else:
            form = RejectReasonForm(request.POST)
            if form.is_valid():
                try:
                    form.save(recipe)
                except Exception as e:
                    self.message_user(request, str(e), messages.ERROR)
                    # If save() raised, the form will a have a non
                    # field error containing an informative message.
                    pass
                else:
                    self.message_user(request, 'Success')
                    url = reverse(
                        'admin:recipe_recipe_changelist',
                        current_app=self.admin_site.name,
                    )
                    return HttpResponseRedirect(url)

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['recipe'] = recipe
        context['title'] = 'Enter rejection reason'

        return TemplateResponse(
            request,
            'admin/recipe/recipe_action.html',
            context,
        )

    inlines = [
        IngredientInline,
        RecipeStepInline,
        RecipeVideoInline,
        RecipeImageInline,
        TagRecipeRelationInline
    ]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    admin_priority = 4
    list_display = (
        'id',
        'quantity',
        'unit',
        'title',
        'recipe',
        'created_at',
    )
    list_filter = ('unit', 'created_at')
    date_hierarchy = 'created_at'
    autocomplete_fields = ['recipe']
    search_fields = ['recipe__pk', 'recipe__title']


@admin.register(RecipeImage)
class RecipeImageAdmin(admin.ModelAdmin):
    admin_priority = 3
    list_display = ('id', 'recipe', 'file', 'main_image', 'order_index',)
    autocomplete_fields = ['recipe']
    search_fields = ['recipe__pk', 'recipe__title']


@admin.register(RecipeStep)
class RecipeStepAdmin(admin.ModelAdmin):
    admin_priority = 5
    list_display = (
        'id',
        'num',
        'title',
        'description',
        'recipe',
        'created_at',
    )
    list_filter = ()
    date_hierarchy = 'created_at'
    autocomplete_fields = ['recipe']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    admin_priority = 6
    list_display = ('id', 'text', 'created_at')
    list_filter = ('created_at',)
    raw_id_fields = ('recipes',)
    date_hierarchy = 'created_at'


@admin.register(SavedRecipe)
class SavedRecipeAdmin(admin.ModelAdmin):
    admin_priority = 7
    list_display = ('id', 'user', 'recipe', 'created_at')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
    autocomplete_fields = ['recipe']


@admin.register(RecipeVideo)
class RecipeVideoAdmin(admin.ModelAdmin):
    admin_priority = 2
    list_display = ('id', 'user', 'video', 'video_thumbnail', 'recipe', 'created_at')
    list_filter = ('user', 'created_at')
    date_hierarchy = 'created_at'
    autocomplete_fields = ['recipe', 'user']
