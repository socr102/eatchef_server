from rest_framework import serializers

from notifications.models import Notify


class NotifySerializer(serializers.ModelSerializer):
    class Meta:
        model = Notify
        fields = ['id', 'code', 'payload', 'created_at']
        write_only = ['account']
