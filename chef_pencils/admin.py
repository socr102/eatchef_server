# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from main.admin_utils import get_app_list

admin.AdminSite.get_app_list = get_app_list

from .forms import RejectReasonForm
from .models import (ChefPencilCategory, ChefPencilImage, ChefPencilRecord,
                     ChefPencilRecordCategoryLink, SavedChefPencilRecord)


class ChefPencilImageInline(admin.TabularInline):
    model = ChefPencilImage
    min_num = 1

    fields = ('rendered_image', 'image', 'main_image', 'order_index',)
    readonly_fields = ('rendered_image',)

    def rendered_image(self, obj):
        if obj.image:
            url = obj.image.storage.url(name=obj.image.name)
            return mark_safe(f"""<a href="/admin/chef_pencils/chefpencilimage/{obj.pk}/change/"><img src="{url}" width=320 height=240 /></a>""")
        return ''


@admin.register(ChefPencilRecord)
class ChefPencilRecordAdmin(admin.ModelAdmin):
    admin_priority = 1
    list_display = (
        'id',
        'title',
        'user',
        'cp_actions',
        'main_image',
        'html_content',
        'avg_rating',
        'created_at',
        'updated_at',
    )
    list_filter = ('status', 'created_at',)
    date_hierarchy = 'created_at'
    search_fields = ['title', 'html_content']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            url(
                r'^(?P<chefpencil_record_id>.+)/approve/$',
                self.admin_site.admin_view(self.approve_chefpencil_record),
                name='cp-approve',
            ),
            url(
                r'^(?P<chefpencil_record_id>.+)/reject/$',
                self.admin_site.admin_view(self.reject_chefpencil_record),
                name='cp-reject',
            )
        ]
        return custom_urls + urls

    def main_image(self, obj):
        main_image = obj.images.filter(main_image=True).first()
        if main_image:
            url = main_image.image.storage.url(name=main_image.image.name)
            return mark_safe(f"""<a href="/admin/chef_pencils/chefpencilimage/{main_image.pk}/change/"><img src="{url}" width=160 height=120 /></a>""")
        return ''

    def cp_actions(self, obj):

        btn1 = '<a class="button accept {classname} {clickable}" href="{url}">{text}</a>'.format(
            text='Approved' if obj.status == ChefPencilRecord.Status.APPROVED else 'Approve',
            classname='selected' if obj.status == ChefPencilRecord.Status.APPROVED else '',
            clickable='' if obj.status in [
                ChefPencilRecord.Status.AWAITING_APPROVAL, ChefPencilRecord.Status.REJECTED] else 'non_clickable',
            url=reverse('admin:cp-approve', args=[obj.pk])
        )

        btn2 = '<a class="button reject {classname} {clickable}" href="{url}">{text}</a>'.format(
            text='Rejected' if obj.status == ChefPencilRecord.Status.REJECTED else 'Reject',
            classname='selected' if obj.status == ChefPencilRecord.Status.REJECTED else '',
            clickable='' if obj.status in [
                ChefPencilRecord.Status.AWAITING_APPROVAL, ChefPencilRecord.Status.APPROVED] else 'non_clickable',
            url=reverse('admin:cp-reject', args=[obj.pk])
        )
        return format_html(f'{btn1}&nbsp;{btn2}')

    cp_actions.short_description = 'ChefPencils Actions'
    cp_actions.allow_tags = True

    def approve_chefpencil_record(self, request, chefpencil_record_id, *args, **kwargs):
        cp = self.get_object(request, chefpencil_record_id)
        cp.status = ChefPencilRecord.Status.APPROVED
        cp.save()

        self.message_user(
            request,
            f'Status of Chef\'s Pencil Record #{cp.pk} changed to APPROVED'
        )

        url = reverse(
            'admin:chef_pencils_chefpencilrecord_changelist',
            current_app=self.admin_site.name,
        )
        return HttpResponseRedirect(url)

    def reject_chefpencil_record(self, request, chefpencil_record_id, *args, **kwargs):

        cp = self.get_object(request, chefpencil_record_id)

        if request.method != 'POST':
            form = RejectReasonForm()

        else:
            form = RejectReasonForm(request.POST)
            if form.is_valid():
                try:
                    form.save(cp)
                except Exception as e:
                    self.message_user(request, str(e), messages.ERROR)
                    # If save() raised, the form will a have a non
                    # field error containing an informative message.
                    pass
                else:
                    self.message_user(request, 'Success')
                    url = reverse(
                        'admin:chef_pencils_chefpencilrecord_changelist',
                        current_app=self.admin_site.name,
                    )
                    return HttpResponseRedirect(url)

        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['form'] = form
        context['cp'] = cp
        context['title'] = 'Enter rejection reason'

        return TemplateResponse(
            request,
            'admin/chef_pencils/chef_pencils_action.html',
            context,
        )

    inlines = [
        ChefPencilImageInline,
    ]


@admin.register(ChefPencilImage)
class ChefPencilImageAdmin(admin.ModelAdmin):
    admin_priority = 3
    list_display = (
        'id',
        'rendered_image',
        'chefpencil_record',
        'main_image',
        'order_index',
        'created_at',
        'updated_at'
    )
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

    def rendered_image(self, obj):
        if obj.image:
            url = obj.image.storage.url(name=obj.image.name)
            return mark_safe(f"""<a href="/admin/chef_pencils/chefpencilimage/{obj.pk}/change/"><img src="{url}" width=160 height=120 /></a>""")
        return ''


@admin.register(ChefPencilCategory)
class ChefPencilCategoryAdmin(admin.ModelAdmin):
    admin_priority = 2
    list_display = (
        'id',
        'title',
        'created_at',
        'updated_at'
    )
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
    search_fields = ['title']


@admin.register(SavedChefPencilRecord)
class SavedChefPencilRecordAdmin(admin.ModelAdmin):
    admin_priority = 5
    list_display = ('id', 'user', 'chef_pencil_record', 'created_at')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'
    autocomplete_fields = ['chef_pencil_record']


@admin.register(ChefPencilRecordCategoryLink)
class ChefPencilRecordCategoryLink(admin.ModelAdmin):
    admin_priority = 4
    list_display = ('id', 'chefpencil_record', 'category')
    autocomplete_fields = ['chefpencil_record', 'category']
