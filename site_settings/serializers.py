from rest_framework import serializers

from site_settings.models import (
    Banner,
    Support,
    Block
)


class BannerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Banner
        fields = ['image']
        read_only_fields = []


class SupportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Support
        fields = ['email']
        read_only_fields = ['pk', 'user']

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        return super().validate(attrs)


class BlockSerializer(serializers.ModelSerializer):

    class Meta:
        model = Block
        fields = [
            'image',
            'title',
            'text',
            'change_time',
            'button',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'image',
            'title',
            'text',
            'change_time',
            'button',
            'is_active',
            'created_at',
            'updated_at'
        ]
