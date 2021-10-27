# Register your models here.
# -*- coding: utf-8 -*-

from .models import (
    Banner,
    HomepagePinnedRecipe,
    MealOfTheWeekRecipe,
    TopRatedRecipe,
    Support,
    ParserData,
    FeaturedRecipe,
    Block
)
from django.contrib import admin
from main.admin_utils import get_app_list


admin.AdminSite.get_app_list = get_app_list

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('id', 'image')
    admin_priority = 1


@admin.register(HomepagePinnedRecipe)
class HomepagePinnedRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'created_at', 'updated_at',)
    list_filter = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    autocomplete_fields = ['recipe']
    admin_priority = 2


@admin.register(MealOfTheWeekRecipe)
class MealOfTheWeekRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    autocomplete_fields = ['recipe']
    admin_priority = 3

@admin.register(TopRatedRecipe)
class TopRatedRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    autocomplete_fields = ['recipe']
    admin_priority = 4


@admin.register(FeaturedRecipe)
class FeaturedRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    autocomplete_fields = ['recipe']
    admin_priority = 5


@admin.register(Support)
class SupportAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'email')
    list_filter = ()
    admin_priority = 6


def run_parser_manually(modeladmin, request, queryset):
    from recipe.tasks import download_recipes
    download_recipes.delay()


run_parser_manually.short_description = "Run parser manually"

@admin.register(ParserData)
class ParserDataAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'today_requests',
        'today_results',
        'date',
        'checked_ids',
        'created_at',
        'updated_at',
    )
    actions = [run_parser_manually]
    admin_priority = 7
    list_filter = ('date', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'image',
        'title',
        'text',
        'change_time',
        'button',
        'is_active',
        'created_at',
        'updated_at',
    )
    list_filter = ('is_active', 'created_at')
    date_hierarchy = 'created_at'
    admin_priority = 8
