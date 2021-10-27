import json
import logging
import random
from datetime import datetime

from django.conf import settings
from django.db import transaction
from django.db.models import Case, Count, F, IntegerField, When
from django.http.response import Http404
from drf_yasg.openapi import IN_QUERY, Parameter
from drf_yasg.utils import swagger_auto_schema
from main.pagination import StandardResultsSetPagination
from main.permissions import IsHomeChef, IsOwner
from rest_framework import generics, permissions, serializers, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from site_settings.models import (Banner, FeaturedRecipe, HomepagePinnedRecipe,
                                  MealOfTheWeekRecipe, TopRatedRecipe)
from site_settings.serializers import BannerSerializer
from social.models import Comment
from social.serializers import (CommentLikeSerializer, CommentSerializer,
                                LikeSerializer, RatingSerializer)
from stats.models import StatRecord
from users.models import User, UserViewHistoryRecord

from recipe.enums import Cuisines
from recipe.filters import (NullsAlwaysLastOrderingFilter, RecipeFilterSet,
                            SavedRecipeFilterSet)
from recipe.models import Recipe, RecipeVideo, SavedRecipe
from recipe.serializers import (IngredientSerializer, QuerySerializer,
                                RecipeCardSerializer, RecipeImageSerializer,
                                RecipeSavedRecipeSerializer, RecipeSerializer,
                                RecipeStepSerializer, RecipeVideoSerializer,
                                SavedRecipeSerializer)
from recipe.signals import S_new_recipe_created

logger = logging.getLogger('django')


class RecipeListCreateView(generics.ListCreateAPIView):

    queryset = Recipe.objects.all() \
        .select_related('user') \
        .prefetch_related('images') \
        .get_published_and_accepted() \
        .order_by('-likes_number')

    pagination_class = StandardResultsSetPagination
    filterset_class = RecipeFilterSet
    filter_backends = [NullsAlwaysLastOrderingFilter]
    ordering_fields = [
        'likes_number',
        'views_number',
        'created_at'
    ]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeCardSerializer
        return RecipeSerializer

    def get_permissions(self):
        method = self.request.method
        if method == 'POST':
            return [IsHomeChef()]
        return [AllowAny()]

    def get_queryset(self):
        try:
            user = User.objects.get(
                full_name=settings.EATCHEFS_ACCOUNT_NAME,
                is_staff=True
            )
        except User.DoesNotExist:
            queryset = self.queryset
        else:
            queryset_from_api = self.queryset.filter(user=user)

            if self.request.query_params.get('only_eatchefs_recipes', None) is None:

                queryset_by_users = self.filterset_class(
                    self.request.GET,
                    queryset=self.queryset.exclude(user=user)
                ).qs

                queryset_from_api = self.filterset_class(
                    self.request.GET,
                    queryset=self.queryset.filter(user=user)
                ).qs

                return queryset_by_users.union(queryset_from_api, all=True)
            else:
                queryset = queryset_from_api
                return self.filterset_class(self.request.GET, queryset=queryset_from_api).qs

    @swagger_auto_schema(
        manual_parameters=[
            Parameter('title', IN_QUERY, type='str'),
            Parameter('types', IN_QUERY, type='list'),
            Parameter('cooking_time', IN_QUERY, type='str'),
            Parameter('cooking_skills', IN_QUERY, type='list'),
            Parameter('cuisines', IN_QUERY, type='list'),
            Parameter('diet_restrictions', IN_QUERY, type='list'),
            Parameter('cooking_methods', IN_QUERY, type='list'),
            Parameter('only_eatchefs_recipes', IN_QUERY, type='str'),
        ]
    )
    def get(self, request, *args, **kwargs):
        """ Get list of recipes"""
        return super().get(request, *args, **kwargs)

    @transaction.atomic
    def create(self, request, *args, **kwargs):

        if request.data.get('data'):
            data = dict(**json.loads(request.data.get('data')))
        else:
            data = request.data

        recipe_serializer = self.get_serializer(data=data)
        recipe_serializer.is_valid(raise_exception=True)
        recipe = recipe_serializer.save()

        return Response(recipe_serializer.data, status=status.HTTP_201_CREATED)


class RecipeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):

    queryset = Recipe.objects.select_related(
        'user',
    ).all()
    serializer_class = RecipeSerializer

    def get_permissions(self):
        method = self.request.method
        if method in ['PUT', 'PATCH', 'DELETE']:
            return [IsOwner()]
        return [AllowAny()]

    def get_object(self):
        try:
            obj = self.queryset.get(id=self.kwargs['pk'])
        except Recipe.DoesNotExist:
            raise Http404

        if obj.user == self.request.user:
            return obj
        elif (obj.status != Recipe.Status.ACCEPTED or obj.publish_status != Recipe.PublishStatus.PUBLISHED):
            raise Http404

        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        obj = self.get_object()

        # if public view, not editing
        # (although some editing also will be tracked, we can't separate them now)
        if obj.status == Recipe.Status.ACCEPTED and obj.publish_status == Recipe.PublishStatus.PUBLISHED:
            StatRecord.objects.increment_views(obj)
            if self.request.user.is_authenticated:
                try:
                    uv = UserViewHistoryRecord.objects.get(
                        user=self.request.user,
                        recipe=obj
                    )
                    uv.count += 1
                    uv.save()
                except UserViewHistoryRecord.DoesNotExist:
                    UserViewHistoryRecord.objects.create(
                        user=self.request.user,
                        recipe=obj,
                        count=1
                    )
        return super().get(self, request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):

        if request.data.get('data'):
            data = dict(**json.loads(request.data.get('data')))
        else:
            data = request.data

        recipe_serializer = self.get_serializer(self.get_object(), data=data, partial=True)
        recipe_serializer.is_valid(raise_exception=True)
        recipe_serializer.save()

        return Response(recipe_serializer.data, status=status.HTTP_200_OK)


class UserRecipeListView(generics.ListAPIView):

    queryset = Recipe.objects.all() \
        .get_published_and_accepted() \
        .select_related('user') \
        .prefetch_related('images') \
        .order_by("-id")
    serializer_class = RecipeCardSerializer
    pagination_class = StandardResultsSetPagination
    filterset_class = RecipeFilterSet
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise Http404
        queryset = super().get_queryset().filter(user=user)
        return self.filterset_class(self.request.GET, queryset=queryset).qs

    @swagger_auto_schema(
        manual_parameters=[
            Parameter('types', IN_QUERY, type='list'),
            Parameter('cooking_time', IN_QUERY, type='str'),
            Parameter('cuisines', IN_QUERY, type='list'),
            Parameter('diet_restrictions', IN_QUERY, type='list'),
            Parameter('cooking_methods', IN_QUERY, type='list')
        ]
    )
    def get(self, request, *args, **kwargs):
        """ Get list of recipes"""
        return super().get(request, *args, **kwargs)


class MyRecipeListView(generics.ListAPIView):

    queryset = Recipe.objects.all() \
        .select_related('user') \
        .prefetch_related('images') \
        .order_by("-id")
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RecipeCardSerializer
    pagination_class = StandardResultsSetPagination
    filterset_class = RecipeFilterSet

    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)
        return self.filterset_class(self.request.GET, queryset=queryset).qs

    @swagger_auto_schema(
        manual_parameters=[
            Parameter('types', IN_QUERY, type='list'),
            Parameter('cooking_time', IN_QUERY, type='str'),
            Parameter('cuisines', IN_QUERY, type='list'),
            Parameter('diet_restrictions', IN_QUERY, type='list'),
            Parameter('cooking_methods', IN_QUERY, type='list')
        ]
    )
    def get(self, request, *args, **kwargs):
        """ Get list of recipes"""
        return super().get(request, *args, **kwargs)


class RecipeRatingView(generics.CreateAPIView):
    serializer_class = RatingSerializer

    def create(self, request, *args, **kwargs):
        new_data = {
            'rating': request.data['rating'],
            'content_type': 'recipe',
            'object_id': kwargs['pk']
        }
        serializer = self.get_serializer(data=new_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipeLikeView(generics.CreateAPIView):
    serializer_class = LikeSerializer

    def create(self, request, *args, **kwargs):
        new_data = {
            'content_type': 'recipe',
            'object_id': kwargs['pk']
        }
        serializer = self.get_serializer(data=new_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipeCommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        method = self.request.method
        if method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        try:
            recipe = Recipe.objects.get(pk=self.kwargs['pk'])
        except Recipe.DoesNotExist:
            return []
        return Comment.objects.filter(
                recipe=recipe
            ) \
            .annotate(
                likes_number=Count(Case(
                    When(comment_likes__is_dislike=False, then=1),
                    output_field=IntegerField(),
                )),
                dislikes_number=Count(Case(
                    When(comment_likes__is_dislike=True, then=1),
                    output_field=IntegerField(),
                ))
            ) \
            .select_related('user') \
            .order_by("-created_at")

    def create(self, request, *args, **kwargs):
        new_data = {
            'content_type': 'recipe',
            'object_id': kwargs['pk'],
            'text': request.data['text']
        }
        serializer = self.get_serializer(data=new_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipeCommentDeleteView(generics.DestroyAPIView):
    serializer_class = CommentSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        return [IsOwner()]

    def get_queryset(self):
        return Comment.objects.all()

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])

    def destroy(self, request, *args, **kwargs):
        timedelta = datetime.now() - self.get_object().created_at
        if timedelta.total_seconds() <= 2 * 3600:
            return super().destroy(self, request, *args, **kwargs)
        return Response(status=status.HTTP_403_FORBIDDEN)


class RecipeCommentLikeView(generics.CreateAPIView):
    serializer_class = CommentLikeSerializer

    def create(self, request, *args, **kwargs):
        new_data = {
            'content_type': 'recipe',
            'object_id': kwargs['pk']
        }
        if request.data.get('dislike') or request.query_params.get('dislike'):
            new_data['dislike'] = True
        serializer = self.get_serializer(data=new_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipeFavoriteCuisinesView(generics.ListAPIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = RecipeCardSerializer

    def get_queryset(self):
        cuisine = self.request.query_params.get('cuisine')
        try:
            cuisine = int(cuisine)
        except (ValueError, TypeError):
            return []
        if cuisine not in [c.value for c in Cuisines]:
            return []
        return Recipe.objects.all().get_published() \
            .select_related('user') \
            .prefetch_related('images') \
            .filter(cuisines__contains=[cuisine]) \
            .order_by(F('likes_number').desc(nulls_last=True))[0:3]

    @swagger_auto_schema(
        manual_parameters=[
            Parameter('cuisine', IN_QUERY, type='int'),
        ],
        responses={200: ""}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SearchSuggestionsView(APIView):

    permission_classes = [permissions.AllowAny]

    class ResponseSerializer(serializers.Serializer):

        class Meta:
            ref_name = "RecipeResponse"

        result = serializers.CharField(read_only=True)

    @swagger_auto_schema(
        manual_parameters=[
            Parameter('search', IN_QUERY, type='str'),
            Parameter('only_eatchefs_recipes', IN_QUERY, type='str'),
        ],
        responses={status.HTTP_200_OK: ResponseSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        serializer = QuerySerializer(
            data=request.query_params,
            context={
                'request': request
            }
        )
        serializer.is_valid(raise_exception=True)
        res = serializer.get_suggestions()
        res_serializer = SearchSuggestionsView.ResponseSerializer(
            res, many=True)
        return Response(res_serializer.data, status=status.HTTP_200_OK)


class HomepageBannersView(generics.ListAPIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = BannerSerializer

    def get_queryset(self):
        # should not be too many (5 max)
        return Banner.objects.all()[:5]


class PinnedRecipeView(generics.ListAPIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = RecipeCardSerializer

    def get_queryset(self):
        return Recipe.objects.filter(
            pk__in=HomepagePinnedRecipe.objects.all().values_list('recipe', flat=True)
        ) \
        .select_related('user') \
        .prefetch_related('images') \
        .get_published_and_accepted() \
        .distinct() \
        .order_by(F('likes_number').desc(nulls_last=True))[0:3]


class MealOfTheWeekView(generics.ListAPIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = RecipeSerializer

    def get_queryset(self):
        mealoftheweek = MealOfTheWeekRecipe.objects.first()
        if mealoftheweek:
            return [mealoftheweek.recipe]
        return []


class TopRatedRecipeView(generics.ListAPIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = RecipeCardSerializer

    def get_queryset(self):
        return Recipe.objects.filter(
            pk__in=TopRatedRecipe.objects.all().values_list('recipe', flat=True)
        ) \
        .select_related('user') \
        .prefetch_related('images') \
        .get_published_and_accepted() \
        .distinct() \
        .order_by(F('likes_number').desc(nulls_last=True))[0:18]


class FeaturedRecipeView(generics.ListAPIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = RecipeCardSerializer

    def get_queryset(self):
        frs = FeaturedRecipe.objects.all()
        select_num = frs.count() if frs.count() < 5 else 5
        recipe_ids = [f.recipe.pk for f in random.sample(list(frs), select_num)]
        return Recipe.objects.filter(pk__in=recipe_ids) \
            .select_related('user') \
            .prefetch_related('images') \
            .get_published_and_accepted() \
            .distinct() \
            .order_by(F('likes_number').desc(nulls_last=True))[0:18]


class SavedRecipeListCreateView(generics.ListCreateAPIView):

    serializer_class = SavedRecipeSerializer
    pagination_class = StandardResultsSetPagination
    filterset_class = SavedRecipeFilterSet

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = SavedRecipe.objects.filter(
            user=self.request.user
        ) \
        .select_related('recipe', 'user') \
        .order_by('pk')
        return self.filterset_class(self.request.GET, queryset=queryset).qs

    @swagger_auto_schema(
        manual_parameters=[
            Parameter('types', IN_QUERY, type='list'),
        ]
    )
    def get(self, request, *args, **kwargs):
        """ Get list of recipes"""
        return super().get(request, *args, **kwargs)


class SavedRecipeRetrieveDestroyView(generics.RetrieveDestroyAPIView):

    serializer_class = SavedRecipeSerializer

    def get_permissions(self):
        return [IsOwner()]

    def get_queryset(self):
        return SavedRecipe.objects.filter(user=self.request.user).order_by('pk')

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])


class PopularRecipesView(generics.ListAPIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = RecipeCardSerializer
    # filterset_class = RecipeFilterSet

    def get_queryset(self):

        if not self.request.user.is_authenticated:
            return Recipe.objects.all() \
                            .select_related('user') \
                            .prefetch_related('images') \
                            .get_published_and_accepted() \
                            .order_by('-likes_number')[0:4]

        elif self.request.user.recommended_recipes:
            queryset = Recipe.objects.filter(
                pk__in=self.request.user.recommended_recipes
            ) \
            .select_related('user') \
            .prefetch_related('images')

        else:
            queryset = Recipe.objects.all() \
                            .select_related('user') \
                            .prefetch_related('images') \
                            .get_published_and_accepted() \
                            .order_by('-likes_number')[0:4]

        return queryset

    """
    @swagger_auto_schema(
        manual_parameters=[
            Parameter('types', IN_QUERY, type='list'),
            Parameter('cuisines', IN_QUERY, type='list'),
        ]
    )
    """
    def get(self, request, *args, **kwargs):
        # queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)


class LatestRecipesView(generics.ListAPIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = RecipeSavedRecipeSerializer
    queryset = Recipe.objects.all() \
        .get_published_and_accepted() \
        .order_by('-created_at')

    @swagger_auto_schema(responses={200: ''})
    def get(self, request, *args, **kwargs):
        ids = list(self.get_queryset().values_list('pk', flat=True)[0:100])
        number_of_items = 2 if len(ids) >= 2 else len(ids)

        items = Recipe.objects \
            .select_related('user') \
            .prefetch_related('images') \
            .filter(pk__in=random.sample(ids, number_of_items))

        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)

class UploadVideoView(generics.CreateAPIView):

    serializer_class = RecipeVideoSerializer
    permission_classes = [IsAuthenticated, IsHomeChef]

class UploadImageView(generics.CreateAPIView):

    serializer_class = RecipeImageSerializer
    permission_classes = [IsAuthenticated, IsHomeChef]

class RetrieveRecipeVideoView(generics.RetrieveAPIView):

    serializer_class = RecipeVideoSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = RecipeVideo.objects.all()

    def get_object(self):
        try:
            obj = self.queryset.get(id=self.kwargs['pk'])
        except RecipeVideo.DoesNotExist:
            raise Http404
        self.check_object_permissions(self.request, obj)
        return obj
