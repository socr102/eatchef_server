# -*- coding: utf-8 -*-

from .models import ViewsCounter, SharesCounter, StatRecord
from django.contrib import admin


@admin.register(ViewsCounter)
class ViewsCounterAdmin(admin.ModelAdmin):
    list_display = ('id', 'count')


@admin.register(SharesCounter)
class SharesCounterAdmin(admin.ModelAdmin):
    list_display = ('id', 'count')


@admin.register(StatRecord)
class StatRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'content_type',
        'object_id',
        'date',
        'views_counter',
        'shares_counter',
    )
    list_filter = ('content_type', 'date')
    search_fields = ['object_id']
