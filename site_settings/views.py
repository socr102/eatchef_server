from django.shortcuts import render
from rest_framework import generics, permissions

from site_settings.serializers import (
    SupportSerializer,
    BlockSerializer
)

from site_settings.models import Block


class SupportCreateView(generics.CreateAPIView):
    serializer_class = SupportSerializer


class BlocksListView(generics.ListAPIView):
    serializer_class = BlockSerializer
    queryset = Block.objects.filter(is_active=True)
    permission_classes = [permissions.AllowAny]
