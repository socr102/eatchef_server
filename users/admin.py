from utils.admin import DateFilter, DropdownFilter
from django.contrib.admin.filters import (
    SimpleListFilter,
    AllValuesFieldListFilter,
    ChoicesFieldListFilter,
    RelatedFieldListFilter,
    RelatedOnlyFieldListFilter
)

from django.contrib.admin.views.main import ChangeList
from django.contrib.auth.models import Group
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from users.services.user import UserService
from users.serializers import UserStatSerializer
from django.contrib.admin.options import (IncorrectLookupParameters)
from django.core.paginator import InvalidPage
from operator import attrgetter

from users.models import (
    FavoriteRecipe,
    User,
    RoleModel,
    UserViewHistoryRecord,
    WorkExperienceRecord
)
from users.forms import CustomUserCreationForm, CustomUserChangeForm, GroupAdminForm


class FavoriteRecipeInline(admin.TabularInline):
    model = FavoriteRecipe
    autocomplete_fields = ['recipe']


class WorkExperienceRecordInline(admin.TabularInline):
    model = WorkExperienceRecord
    autocomplete_fields = ['user']


class RoleModelInline(admin.TabularInline):
    model = RoleModel
    autocomplete_fields = ['user']

    fields = ('pk', 'name', 'file', 'rendered_image',)
    readonly_fields = ('pk', 'rendered_image',)

    def rendered_image(self, obj):
        if obj.file:
            url = obj.file.storage.url(name=obj.file.name)
            return mark_safe(f"""<a href="/admin/users/rolemodels/{obj.pk}/change/"><img src="{url}" width=320 height=240 /></a>""")
        return ''


def resend_verification_email(modeladmin, request, queryset):
    for user in queryset:
        if not user.is_email_active:
            UserService().send_email_activation_code(user)


resend_verification_email.short_description = "Resend verification email to user"


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    model = User
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    list_display = (
        'pk',
        'full_name',
        'city',
        'registration_date',
        'phone_number',
        'email',
        'user_type',
        'is_email_active',
        'is_superuser',
        'is_staff',
    )
    list_filter = (
        'user_type', # ChoicesFieldListFilter,),
        ('city', DropdownFilter),
        ('created_at', DateFilter),
        'is_email_active',
        'is_staff',
        'is_superuser',
    )

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Information', {'fields': (
            'avatar',
            'full_name',
            'bio',
            'phone_number',
            'city',
            'language',
            'cooking_philosophy_0',
            'cooking_philosophy_1',
            'cooking_philosophy_2',
            'personal_cooking_mission_0',
            'personal_cooking_mission_1',
            'personal_cooking_mission_2',
            'source_of_inspiration_0',
            'source_of_inspiration_1',
            'source_of_inspiration_2',
            'recommended_recipes'
        )}),
        ('Permissions', {
         'fields': ('is_staff', 'is_active', 'is_email_active')}),
        ('Status', {'fields': ('status', 'user_type',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')},
         ),
        ('Information', {'fields': ('full_name', 'city',
         'language', 'phone_number', 'avatar',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active',)}),
        ('Status', {'fields': ('status', 'user_type',)}),
    )
    search_fields = ('first_name', 'last_name', 'full_name', 'email')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)
    readonly_fields = ["recommended_recipes"]
    actions = [resend_verification_email]

    def registration_date(self, obj):
        return obj.created_at.strftime("%d.%m.%Y")

    inlines = [
        RoleModelInline,
        FavoriteRecipeInline,
        WorkExperienceRecordInline
    ]


class CustomStatsChangeList(ChangeList):
    """
    This class is used to set additional calculated attributes to the queryset,
    so they are available in the admin section after filtering
    """

    def multisort(self, xs, ordering):
        specs = [(key[1:] if key.startswith('-') else key, True if key.startswith('-') else False) for key in ordering]
        for key, reverse in reversed(specs):
            xs.sort(key=attrgetter(key), reverse=reverse)
        return xs

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        result = UserStatSerializer.retrieve_stats(users=queryset)
        return result

    def get_results(self, request):
        paginator = self.model_admin.get_paginator(
            request, self.queryset, self.list_per_page)
        # Get the number of objects, with admin filters applied.
        result_count = paginator.count

        # Get the total number of objects, with no admin filters applied.
        if self.model_admin.show_full_result_count:
            full_result_count = self.root_queryset.count()
        else:
            full_result_count = None
        can_show_all = result_count <= self.list_max_show_all
        multi_page = result_count > self.list_per_page

        # Get the list of objects to display on this page.
        if (self.show_all and can_show_all) or not multi_page:
            result_list = self.multisort(
                list(UserStatSerializer.retrieve_stats(users=self.queryset)),
                self.get_ordering(request, self.queryset)
            )
        else:
            try:
                result_list = paginator.page(self.page_num).object_list

                result_list = self.multisort(
                    paginator.page(self.page_num).object_list,
                    self.get_ordering(request, self.queryset)
                )

            except InvalidPage:
                raise IncorrectLookupParameters

        self.result_count = result_count
        self.show_full_result_count = self.model_admin.show_full_result_count
        # Admin actions are shown if there is at least one entry
        # or if entries are not counted because show_full_result_count is disabled
        self.show_admin_actions = not self.show_full_result_count or bool(
            full_result_count)
        self.full_result_count = full_result_count
        self.result_list = result_list
        self.can_show_all = can_show_all
        self.multi_page = multi_page
        self.paginator = paginator


class UserInfo(User):
    class Meta:
        proxy = True
        verbose_name = 'Users Statistics'
        app_label = 'users'  # or another app to put your custom view


@admin.register(UserInfo)
class UserStatisticsAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    model = UserInfo
    show_admin_actions = False
    search_fields = (
        "full_name",
        "email"
    )

    list_display = (
        "uid",
        "user_name",
        "total",
        "accepted",
        "awaiting",
        "rejected",
        "published",
        "in_recommendations",
        "views_total",
        "shares_total",
        "user_liked",
        "user_commented",
        "user_saved"
    )

    def get_changelist(self, request, **kwargs):
        return CustomStatsChangeList

    def get_queryset(self, request):

        queryset = super().get_queryset(request) \
            .get_home_chef_accounts() \
            .get_not_banned() \
            .get_active() \
            .get_with_email_confirmed() \
            .order_by('pk')

        return UserStatSerializer.retrieve_stats(users=queryset)

    def uid(self, obj):
        return mark_safe(f"""<a href="/admin/users/user/{obj.pk}/change/">{obj.pk}</a>""")

    def user_name(self, obj):
        return mark_safe(f"""<a href="/admin/users/user/{obj.pk}/change/">{obj.full_name}</a>""")

    def total(self, obj):
        return obj.total

    def accepted(self, obj):
        return obj.accepted

    def awaiting(self, obj):
        return obj.awaiting_acceptance

    def rejected(self, obj):
        return obj.rejected

    def published(self, obj):
        return obj.published

    def in_recommendations(self, obj):
        return obj.in_recommendations

    def views_total(self, obj):
        return obj.total_views

    def shares_total(self, obj):
        return obj.total_shares

    def user_liked(self, obj):
        return obj.likes_count

    def user_commented(self, obj):
        return obj.comments_count

    def user_saved(self, obj):
        return obj.saved_recipes_count

    uid.admin_order_field = 'pk'
    user_name.admin_order_field = 'full_name'
    total.admin_order_field = 'total'
    accepted.admin_order_field = 'accepted'
    awaiting.admin_order_field = 'awaiting_acceptance'
    rejected.admin_order_field = 'rejected'
    published.admin_order_field = 'published'
    in_recommendations.admin_order_field = 'in_recommendations'
    views_total.admin_order_field = 'total_views'
    shares_total.admin_order_field = 'total_shares'
    user_liked.admin_order_field = 'likes_count'
    user_commented.admin_order_field = 'comments_count'
    user_saved.admin_order_field = 'saved_recipes_count'


admin.site.unregister(Group)


class GroupAdmin(admin.ModelAdmin):
    form = GroupAdminForm
    filter_horizontal = ['permissions']


admin.site.register(Group, GroupAdmin)


@admin.register(RoleModel)
class RoleModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'name', 'file')
    list_filter = ('user',)
    search_fields = ('name',)
    autocomplete_fields = ['user']


@admin.register(UserViewHistoryRecord)
class UserViewHistoryRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', 'count',
                    'created_at', 'updated_at')
    list_filter = ('user',)
    search_fields = ('user__full_name', 'recipe__title',)
    autocomplete_fields = ['user', 'recipe']
