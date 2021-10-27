# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Notify


@admin.register(Notify)
class NotifyAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'user', 'payload', 'created_at')
    list_filter = ('code',)
    raw_id_fields = ('user',)
    date_hierarchy = 'created_at'
    search_fields = ['user__email', 'user__full_name']
    autocomplete_fields = ['user']
