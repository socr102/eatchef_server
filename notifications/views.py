from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework import mixins, status
from rest_framework.generics import DestroyAPIView
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from notifications.models import Notify
from notifications.serializers import NotifySerializer
from utils.websocket import send_new_notification


@receiver(post_save, sender=Notify)
def receive_new_notification(sender, instance: Notify, created, **kwargs):
    if created:
        send_new_notification(instance)


class RetrieveDestroyNotificationsViewSet(
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    serializer_class = NotifySerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Notify.objects.all().owner(user=self.request.user)


class DeleteAccountNotifications(DestroyAPIView):
    serializer_class = NotifySerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Notify.objects.all().owner(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        self.get_queryset().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
