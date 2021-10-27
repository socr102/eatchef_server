# -*- coding: utf-8 -*-

from chef_pencils.models import ChefPencilRecord
from main.utils.db import Round1
from social.models import Rating, Like
from django.db.models import Sum
from django.db.models.aggregates import Avg, Count


class ChefPencilRatingCalculator:

    def get_avg_ratings_for_chef_pencils(self):
        ratings = Rating.objects.filter(content_type__model='chefpencilrecord').values_list(
            'object_id'
        ).annotate(
            rounded_avg_rating=Round1(Avg('rating'))
        )
        self.ratings = {p[0]: p[1] for p in ratings}

    def update_records(self):
        to_update = []
        for r in ChefPencilRecord.objects.filter(pk__in=self.ratings.keys()).only('pk'):
            r.avg_rating = self.ratings[r.pk]
            to_update.append(r)
        ChefPencilRecord.objects.bulk_update(to_update, ['avg_rating'], batch_size=100)


class ChefPencilRecordLikeCalculator:

    def get_total_likes_for_chef_pencil_records(self):
        likes = Like.objects.filter(content_type__model='chefpencilrecord').values_list(
            'object_id'
        ).annotate(
            Count('pk')
        )
        self.ratings = {p[0]: p[1] for p in likes}

    def update_records(self):
        to_update = []
        for r in ChefPencilRecord.objects.filter(pk__in=self.ratings.keys()).only('pk'):
            r.likes_number = self.ratings[r.pk]
            to_update.append(r)
        ChefPencilRecord.objects.bulk_update(to_update, ['likes_number'], batch_size=100)


class ChefPencilRecordViewsCalculator:

    def get_total_views_for_chef_pencil_records(self):

        rr = ChefPencilRecord.objects.all().select_related('user').annotate(
            views_number_calculated=Sum('stat_records__views_counter__count')
        )
        self.ratings = {r.pk: r.views_number_calculated for r in rr}

    def update_records(self):
        to_update = []
        for r in ChefPencilRecord.objects.filter(pk__in=self.ratings.keys()).only('pk'):
            r.views_number = self.ratings[r.pk]
            to_update.append(r)
        ChefPencilRecord.objects.bulk_update(to_update, ['views_number'], batch_size=100)