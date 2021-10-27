from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from stats.models import StatRecord, CounterKeys
from rest_framework.exceptions import ValidationError


class StatSerializer(serializers.ModelSerializer):

    class Meta:
        model = StatRecord
        fields = [
            'content_type',
            'object_id',
            'date',
            'views_counter',
            'shares_counter'
        ]
        read_only_fields = [
            'pk',
            'content_type',
            'object_id',
            'date',
            'views_counter',
            'shares_counter'
        ]


class StatsIncrementViewSerializer(serializers.Serializer):

    key = serializers.CharField(required=True)
    content_type = serializers.CharField(required=True)
    object_id = serializers.IntegerField(required=True)

    class Meta:
        fields = ['key', 'content_type', 'object_id']

    def validate(self, attrs):

        if attrs['key'] not in CounterKeys.choices():
            raise ValidationError(f'Incorrect statistics metric: {attrs["key"]}')

        try:
            ct = ContentType.objects.get(model=attrs['content_type'])
            ct_class = ct.model_class()
            content_object = ct_class.objects.get(pk=attrs['object_id'])
        except Exception:
            raise ValidationError({attrs['content_type']: "Object does not exists"})
        else:
            attrs['content_object'] = content_object

        return super().validate(attrs)
