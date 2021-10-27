from calendar import monthrange
from datetime import timedelta, datetime

from django.db import IntegrityError
from django.db.models import Sum
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAdminUser

from stats.models import StatRecord, CounterKeys
from stats.serializers import StatSerializer, StatsIncrementViewSerializer
from utils.helper import remove_keys_with_none
from rest_framework.response import Response

from main.pagination import StandardResultsSetPagination

from users.models import User
from users.serializers import UserStatSerializer


class StatsView(generics.ListAPIView):
    # TODO: finalize when necessary

    serializer_class = StatSerializer
    queryset = StatRecord.objects.all()
    WEEKS = 'weeks'
    MONTHS = 'months'

    def get_queryset(self):
        qs = StatRecord.objects.all() \
            .select_related('views_counter', 'shares_counter') \
            .filter(
                # TODO: content_type__model='content_type',
                object_id=self.kwargs.get('id')
            )
        filter_args = dict(
            date__gte=self.request.query_params.get('start_date', None),
            date__lte=self.request.query_params.get('end_date', None),
        )
        qs = qs.filter(**remove_keys_with_none(filter_args))
        return qs

    class StatsViewQueryRequest(serializers.Serializer):
        start_date = serializers.DateField(write_only=True, required=False)
        end_date = serializers.DateField(write_only=True, required=False)

    @swagger_auto_schema(
        query_serializer=StatsViewQueryRequest(),
        responses={status.HTTP_200_OK: StatSerializer(many=False)})
    def get(self, request, *args, **kwargs):
        group_by = self.request.query_params.get('group_by')
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        if group_by == self.WEEKS:
            data = self._get_stats_by_weeks()
            return Response(data)

        if group_by == self.MONTHS:
            data = self._get_stats_by_months()
            return Response(data)

        return Response(serializer.data)

    def _get_stats_by_months(self):
        data = []
        months = self.filter_queryset(
            self.get_queryset()).dates('date', 'month')
        for first_date in months:
            end_day_of_month = monthrange(first_date.year, first_date.month)[1]
            end_date = datetime(
                year=first_date.year, month=first_date.month, day=end_day_of_month).date()
            item = {'date': first_date.strftime("%B")}
            item.update(self._get_aggregate_period(first_date, end_date))
            data.append(item)
        return data

    def _get_stats_by_weeks(self):
        data = []
        weeks = self.filter_queryset(self.get_queryset()).dates('date', 'week')
        for monday in weeks:
            sunday = monday + timedelta(days=6)
            item = {'date': f"{monday} - {sunday}"}
            item.update(self._get_aggregate_period(monday, sunday))
            data.append(item)
        return data

    def _get_aggregate_period(self, start_day, end_day):
        queryset = self.filter_queryset(self.get_queryset())
        return queryset.filter(date__gte=start_day, date__lte=end_day) \
            .aggregate(views_counter=Sum('views_counter__count'),
                       shares_counter=Sum('shars_counter__count'))


class StatsIncrementView(generics.CreateAPIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=StatsIncrementViewSerializer(),
        responses={status.HTTP_200_OK: ''})
    def post(self, request, *args, **kwargs):
        serializer = StatsIncrementViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            StatRecord.objects.increment(
                serializer.validated_data['content_object'],
                eval(f"CounterKeys.{serializer.validated_data['key']}.value")
            )
        except IntegrityError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StatsAdminView(generics.ListAPIView):

    permission_classes = [IsAdminUser]
    serializer_class = UserStatSerializer
    queryset = User.objects.all() \
        .get_home_chef_accounts() \
        .get_not_banned() \
        .get_active() \
        .order_by('pk')

    pagination_class = StandardResultsSetPagination

    def list(self, request, *args, **kwargs):
        page = self.paginate_queryset(self.queryset)

        if page is not None:
            serializer = self.get_serializer(
                UserStatSerializer.retrieve_stats(users=page),
                many=True
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            UserStatSerializer.retrieve_stats(users=self.queryset),
            many=True
        )
        return Response(serializer.data)



