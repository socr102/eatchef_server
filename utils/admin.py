from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.safestring import mark_safe

from django.contrib.admin.filters import (
    AllValuesFieldListFilter,
)

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import datetime
from django.contrib.admin import DateFieldListFilter

from django.utils import timezone
from django.db import models


def edit_link(field_name, short_description=None, rel_field_name=None):
    """
    Displays link to change form for foreign key object.
    Use in `readonly_fields` or `list_display`::
        class BookAdmin(admin.ModelAdmin):
            readonly_fields = (edit_link('author', "Edit author"), )
    """

    def display_func(obj):
        obj = getattr(obj, field_name)
        if not obj:
            return ""
        ct = ContentType.objects.get_for_model(obj)
        link = reverse(f'admin:{ct.app_label}_{ct.model}_change', args=(obj.pk,))
        return mark_safe(f'<a href="{link}">{str(obj) if rel_field_name is None else getattr(obj, rel_field_name)}</a>')

    display_func.allow_tags = True
    if short_description:
        display_func.short_description = short_description

    return display_func


class DateFilter(DateFieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        super().__init__(field, request, params, model, model_admin, field_path)

        now = timezone.now()
        if timezone.is_aware(now):
            now = timezone.localtime(now)

        if isinstance(field, models.DateTimeField):
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:       # field is a models.DateField
            today = now.date()

        yesterday = today - datetime.timedelta(days=1)

        links_start = self.links[:2]  # anyday and today
        link_yesterday = (_('Yesterday'), {
                self.lookup_kwarg_since: str(yesterday),
                self.lookup_kwarg_until: str(today),
            })

        self.links = (*links_start, link_yesterday, *self.links[2:])


class DropdownFilter(AllValuesFieldListFilter):
    template = 'admin/dropdown_filter.html'

