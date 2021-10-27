import json
import random
from datetime import datetime

from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import FilterSet
from django_filters.rest_framework.filters import CharFilter
from drf_yasg.openapi import IN_QUERY, Parameter
from drf_yasg.utils import swagger_auto_schema
from main.pagination import StandardResultsSetPagination
from main.permissions import IsHomeChef, IsOwner
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from social.models import Comment
from social.serializers import (CommentLikeSerializer, CommentSerializer,
                                LikeSerializer, RatingSerializer)

from chef_pencils.models import (ChefPencilCategory, ChefPencilImage,
                                 ChefPencilRecord, SavedChefPencilRecord)
from chef_pencils.serializers import (ChefPencilCategorySerializer,
                                      ChefPencilImageSerializer,
                                      ChefPencilQuerySerializer,
                                      ChefPencilRecordSerializer,
                                      SavedChefPencilRecordSerializer)


class ChefPencilRecordFilterSet(FilterSet):

    search = CharFilter(method="search_filter")

    class Meta:
        model = ChefPencilRecord
        fields = []

    def search_filter(self, queryset, name, search):
        return queryset.filter(
            Q(title__search=search)|Q(html_content__search=search)
        )


class ChefPencilRecordListCreateView(generics.ListCreateAPIView):

    queryset = ChefPencilRecord.objects.all() \
        .get_approved() \
        .order_by('-created_at')
    serializer_class = ChefPencilRecordSerializer
    pagination_class = StandardResultsSetPagination
    filterset_class = ChefPencilRecordFilterSet

    def get_permissions(self):
        method = self.request.method
        if method == 'POST':
            return [IsHomeChef()]
        return [AllowAny()]

    @swagger_auto_schema(
        manual_parameters=[
            Parameter('search', IN_QUERY, type='str'),
        ]
    )
    def get(self, request, *args, **kwargs):
        """ Get list of ChefPencilRecords"""
        return super().get(request, *args, **kwargs)

    @transaction.atomic
    def create(self, request, *args, **kwargs):

        images = [request.FILES[k] for k in request.FILES.keys() if k.startswith('images[')]
        # TODO: move to serializer later
        if not images:
            raise ValidationError({'images': 'Images field is required'})

        MAX_IMAGES_COUNT = 15
        if len(images) > MAX_IMAGES_COUNT:
            raise ValidationError({'images': f'No more than {MAX_IMAGES_COUNT} can be uploaded'})

        if request.data.get('data'):
            data = dict(**json.loads(request.data.get('data')))
        else:
            data = request.data

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        cr = serializer.save()

        images_objs = []
        for i, image in enumerate(images):
            if data.get('main_image') is None:
                is_main = True if i == 0 else False
            else:
                is_main = True if image.name == data.get('main_image', '') else False
            cpi = ChefPencilImage(
                chefpencil_record=cr,
                image=image,
                main_image=is_main,
                order_index=i
            )
            images_objs.append(cpi)
        ChefPencilImage.objects.bulk_create(images_objs)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChefPencilRecordRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ChefPencilRecord.objects.all()
    serializer_class = ChefPencilRecordSerializer

    def get_permissions(self):
        method = self.request.method
        if method in ['PUT', 'PATCH']:
            return [IsOwner()]
        return [AllowAny()]

    @transaction.atomic
    def update(self, request, *args, **kwargs):

        images = [request.FILES[k] for k in request.FILES.keys() if k.startswith('images[')]

        MAX_IMAGES_COUNT = 15

        if len(images) > MAX_IMAGES_COUNT:
            raise ValidationError({'images': f'No more than {MAX_IMAGES_COUNT} can be uploaded'})

        if request.data.get('data'):
            data = dict(**json.loads(request.data.get('data')))
        else:
            data = request.data

        serializer = self.get_serializer(
            self.get_object(),
            data=data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        cp = serializer.save()

        # Images
        # TODO: refactor later

        if data.get('main_image') is not None:
            cpi = ChefPencilImage.objects.filter(chefpencil_record=cp, main_image=True).first()
            if not cpi:
                old_cpi_with_main_image = None
            else:
                old_cpi_with_main_image = cpi.pk
            ChefPencilImage.objects.filter(chefpencil_record=cp).update(main_image=False)

        images_objs = []
        for image in images:
            # 1st case: new image should be main
            is_main = True if image.name == data.get('main_image', '') else False
            cpi = ChefPencilImage(
                chefpencil_record=cp,
                image=image,
                main_image=is_main
            )
            images_objs.append(cpi)
        ChefPencilImage.objects.bulk_create(images_objs)

        # 2nd case: existing image is main
        if str(data.get('main_image', '')).isdigit():
            try:
                cpi = ChefPencilImage.objects.get(pk=data.get('main_image'))
            except ChefPencilImage.DoesNotExist:
                pass
            else:
                cpi.main_image = True
                cpi.save()

        # if incorrect value was set
        if data.get('main_image') is not None:
            if ChefPencilImage.objects.filter(chefpencil_record=cp, main_image=True).count() == 0 and old_cpi_with_main_image:
                cpi = ChefPencilImage.objects.get(pk=old_cpi_with_main_image)
                cpi.main_image = True
                cpi.save()

        data = json.loads(request.data['data'])
        indexes = [i['id'] for i in data.get('images', [])]
        cpis = ChefPencilImage.objects.filter(chefpencil_record=cp).all()
        for cpi in cpis:
            if cpi.pk in indexes:
                cpi.order_index = indexes.index(cpi.pk)
                cpi.save()
            else:
                cpi.order_index = max(ChefPencilImage.objects.filter(chefpencil_record=cp).values_list('order_index', flat=True)) + 1
                cpi.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class ChefPencilRecordRatingView(generics.CreateAPIView):
    serializer_class = RatingSerializer

    def create(self, request, *args, **kwargs):
        new_data = {
            'rating': request.data['rating'],
            'content_type': 'chefpencilrecord',
            'object_id': kwargs['pk']
        }
        serializer = self.get_serializer(data=new_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChefPencilRecordCommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        method = self.request.method
        if method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        cr = ChefPencilRecord.objects.get(pk=self.kwargs['pk'])
        return Comment.objects.filter(chefpencil_record=cr).order_by("created_at")

    def create(self, request, *args, **kwargs):
        new_data = {
            'content_type': 'chefpencilrecord',
            'object_id': kwargs['pk'],
            'text': request.data['text']
        }
        serializer = self.get_serializer(data=new_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChefPencilRecordCommentLikeView(generics.CreateAPIView):
    serializer_class = CommentLikeSerializer

    def create(self, request, *args, **kwargs):
        new_data = {
            'content_type': 'chefpencilrecord',
            'object_id': kwargs['pk']
        }
        if request.data.get('dislike') or request.query_params.get('dislike'):
            new_data['dislike'] = True
        serializer = self.get_serializer(data=new_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LatestChefPencilsView(generics.ListAPIView):

    permission_classes = [permissions.AllowAny]
    serializer_class = ChefPencilRecordSerializer
    queryset = ChefPencilRecord.objects.all() \
        .order_by('-created_at')

    @swagger_auto_schema(responses={200: ''})
    def get(self, request, *args, **kwargs):
        ids = list(self.get_queryset().values_list('pk', flat=True)[0:100])
        number_of_items = 2 if len(ids) >= 2 else len(ids)

        items = ChefPencilRecord.objects \
            .select_related('user') \
            .prefetch_related('images') \
            .filter(pk__in=random.sample(ids, number_of_items))

        serializer = self.get_serializer(items, many=True)
        return Response(serializer.data)


class SearchSuggestionsView(APIView):

    permission_classes = [permissions.AllowAny]
    class ResponseSerializer(serializers.Serializer):

        class Meta:
            ref_name = "ChefPencilsResponse"

        result = serializers.CharField(read_only=True)

    @swagger_auto_schema(
        manual_parameters=[
            Parameter('search', IN_QUERY, type='str'),
        ],
        responses={status.HTTP_200_OK: ResponseSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        serializer = ChefPencilQuerySerializer(
            data=request.query_params,
            context={
                'request': request
            }
        )
        serializer.is_valid(raise_exception=True)
        res = serializer.get_suggestions()
        res_serializer = SearchSuggestionsView.ResponseSerializer(res, many=True)
        return Response(res_serializer.data, status=status.HTTP_200_OK)


class ChefPencilRecordCommentDeleteView(generics.DestroyAPIView):

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


class MyChefPencilRecordListView(generics.ListAPIView):

    queryset = ChefPencilRecord.objects.all() \
        .select_related('user') \
        .prefetch_related('images') \
        .order_by("-id")

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChefPencilRecordSerializer
    pagination_class = StandardResultsSetPagination
    filterset_class = ChefPencilRecordFilterSet

    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)
        return self.filterset_class(self.request.GET, queryset=queryset).qs

    @swagger_auto_schema(
        manual_parameters=[
            Parameter('search', IN_QUERY, type='str'),
        ]
    )
    def get(self, request, *args, **kwargs):
        """ Get list of chef pencil records"""
        return super().get(request, *args, **kwargs)


class ChefPencilCategoryView(generics.ListAPIView):

    queryset = ChefPencilCategory.objects.all() \
        .order_by("-id")

    permission_classes = [permissions.AllowAny]
    serializer_class = ChefPencilCategorySerializer
    pagination_class = StandardResultsSetPagination


class ChefPencilRecordLikeView(generics.CreateAPIView):
    serializer_class = LikeSerializer

    def create(self, request, *args, **kwargs):
        new_data = {
            'content_type': 'chefpencilrecord',
            'object_id': kwargs['pk']
        }
        serializer = self.get_serializer(data=new_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SavedChefPencilRecordListCreateView(generics.ListCreateAPIView):
    serializer_class = SavedChefPencilRecordSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = SavedChefPencilRecord.objects.filter(
            user=self.request.user
        ) \
            .select_related('chef_pencil_record', 'user') \
            .order_by('pk')
        return queryset

    def get(self, request, *args, **kwargs):
        """ Get list of recipes"""
        return super().get(request, *args, **kwargs)


class SavedChefPencilRecordRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    serializer_class = SavedChefPencilRecordSerializer

    def get_permissions(self):
        return [IsOwner()]

    def get_queryset(self):
        return SavedChefPencilRecord.objects.filter(user=self.request.user).order_by('pk')

    def get_object(self):
        return get_object_or_404(self.get_queryset(), pk=self.kwargs['pk'])
