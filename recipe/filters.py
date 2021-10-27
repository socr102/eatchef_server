from django_filters.rest_framework.filters import CharFilter
from django_filters.rest_framework import FilterSet
from rest_framework.filters import OrderingFilter
from datetime import timedelta
from recipe.models import (
    Recipe,
    SavedRecipe
)
from django.db.models import F


class RecipeFilterSet(FilterSet):

    title = CharFilter(method="filter_by_title")
    types = CharFilter(method="filter_by_types")
    cooking_time = CharFilter(method="filter_by_cooking_time")
    cuisines = CharFilter(method='filter_by_cuisines')
    cooking_time = CharFilter(method='filter_by_cooking_time')
    cooking_methods = CharFilter(method="filter_by_cooking_methods")
    cooking_skills = CharFilter(method="filter_by_cooking_skills")
    diet_restrictions = CharFilter(method="filter_by_diet_restrictions")
    class Meta:
        model = Recipe
        fields = []

    def filter_by_title(self, queryset, name, title):
        return queryset.filter(title__search=title)

    def filter_by_types(self, queryset, name, types):
        if types is not None:
            types_params = []
            for recipe_type in types.split(','):
                try:
                    types_params.append(int(recipe_type))
                except ValueError:
                    pass
            queryset = queryset.filter(types__overlap=types_params)
        return queryset.order_by('-id')

    def filter_by_cooking_skills(self, queryset, name, cooking_skills):
        if cooking_skills is not None:
            cooking_skills_params = []
            for cs in cooking_skills.split(','):
                try:
                    cooking_skills_params.append(int(cs))
                except ValueError:
                    pass
            queryset = queryset.filter(cooking_skills__in=cooking_skills_params)
        return queryset.order_by('-id')

    def filter_by_cuisines(self, queryset, name, cuisines):
        if cuisines is not None:
            cuisine_params = []
            for cuisine in cuisines.split(','):
                try:
                    cuisine_params.append(int(cuisine))
                except ValueError:
                    pass
            queryset = queryset.filter(cuisines__overlap=cuisine_params)
        return queryset.order_by('-id')

    def filter_by_diet_restrictions(self, queryset, name, diet_restrictions):
        if diet_restrictions is not None:
            diet_params = []
            for diet in diet_restrictions.split(','):
                try:
                    diet_params.append(int(diet))
                except ValueError:
                    pass
            queryset = queryset.filter(diet_restrictions__overlap=diet_params)
        return queryset.order_by('-id')

    def filter_by_cooking_methods(self, queryset, name, cooking_methods):
        if cooking_methods is not None:
            cooking_method_params = []
            for cm in cooking_methods.split(','):
                try:
                    cooking_method_params.append(int(cm))
                except ValueError:
                    pass
            queryset = queryset.filter(cooking_methods__overlap=cooking_method_params)
        return queryset.order_by('-id')

    def filter_by_cooking_time(self, queryset, name, cooking_time):
        if cooking_time is not None:
            # TODO: improve later
            try:
                hh, mm = int(cooking_time.split(":")[0]), int(cooking_time.split(":")[1])
            except Exception as e:
                return []
            else:
                return queryset.filter(cooking_time=timedelta(hours=hh, minutes=mm))
        return queryset.order_by('-id')


class NullsAlwaysLastOrderingFilter(OrderingFilter):
    """ Use Django 1.11 nulls_last feature to force nulls to bottom in all orderings. """
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            f_ordering = []
            for o in ordering:
                if not o:
                    continue
                if o[0] == '-':
                    f_ordering.append(F(o[1:]).desc(nulls_last=True))
                else:
                    f_ordering.append(F(o).asc(nulls_last=True))

            return queryset.order_by(*f_ordering)

        return queryset


class SavedRecipeFilterSet(FilterSet):

    types = CharFilter(method="filter_by_types")

    class Meta:
        model = SavedRecipe
        fields = []

    def filter_by_types(self, queryset, name, types):
        if types is not None:
            types_params = []
            for recipe_type in types.split(','):
                try:
                    types_params.append(int(recipe_type))
                except ValueError:
                    pass
            queryset = queryset.filter(recipe__types__overlap=types_params)
        return queryset.order_by('-id')