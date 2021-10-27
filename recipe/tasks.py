import sys
import subprocess
from collections import defaultdict
from main.celery_config import app
from django.core.files import File
import os
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger('django')

from recipe.services import (
    RecipeRatingCalculator,
    RecipeLikeCalculator,
    RecipeApiParser,
    RecipeViewsCalculator
)
from chef_pencils.services import (
    ChefPencilRecordLikeCalculator,
    ChefPencilRecordViewsCalculator
)
from social.models import Comment
from recipe.services import LimitsExceededError
from notifications.service import NotifyService

from users.models import User

from utils.email import send_new_comments_for_recipe
from utils.email import send_new_comments_for_chef_pencils_record

from main.watermark_storage import WatermarkStorage
from django.conf import settings
from recipe.services import RecommendedRecipesService

import logging
logger = logging.getLogger('django')


@app.task(acks_late=True)
def calculate_avg_rating_for_recipes():
    calc = RecipeRatingCalculator()
    calc.get_avg_ratings_for_recipes()
    calc.update_records()


@app.task(acks_late=True)
def calculate_likes_for_recipes():
    calc = RecipeLikeCalculator()
    calc.get_total_likes_for_recipes()
    calc.update_records()


@app.task(acks_late=True)
def calculate_views_for_recipes():
    calc = RecipeViewsCalculator()
    calc.get_total_views_for_recipes()
    calc.update_records()


@app.task(acks_late=True)
def download_recipes():
    """
    Download daily recipes from Spoonacular API
    """
    parser = RecipeApiParser(
        requests_per_day=500,
        results_per_day=5000
    )
    try:
        parser.download_recipes()
    except LimitsExceededError:
        logger.info("day limits exceeded")


@app.task()
def create_thumbnail_for_video(tmp_video_path, new_name):

    from recipe.models import RecipeVideo

    logger.info(f'thumbnail creation for {tmp_video_path} started (rename to {new_name})')

    try:
        # 1. create and open png file in an accessible directory inside PROJECT_DIR
        tmp_dir = Path(settings.PROJECT_DIR) / 'tmp'
        tmp_dir.mkdir(exist_ok=True)

        tmp_thumbnail = tempfile.NamedTemporaryFile(
            suffix='.png',
            dir=tmp_dir,
            delete=False
        )
        tmp_thumbnail_path = tmp_thumbnail.name

        # 2. perform command to write frame into that file
        ffmpeg_command = 'ffmpeg -y -i "{}" -ss 00:00:10 -vframes 1 "{}"'.format(
            tmp_video_path,
            tmp_thumbnail_path
        )
        subprocess.call(ffmpeg_command, shell=True)

        # 3. add watermark to it
        WatermarkStorage().add_watermark(tmp_thumbnail_path)
        """
        recipe.video_thumbnail = resize_image(
            instance.video_thumbnail,
            ThumbnailSize.WIDTH.value,
            ThumbnailSize.HEIGHT.value
        )
        """

        # 4. rename to a name like a video
        thumbnail_path = Path(tmp_thumbnail_path).parent / new_name
        os.rename(tmp_thumbnail_path, thumbnail_path)

    except Exception as e:
        logger.exception(e)
        create_thumbnail_for_video.retry(
            [tmp_video_path, new_name],
            exc=e,
            throw=False
        )
    else:
        os.unlink(tmp_video_path)

        try:
            rv = RecipeVideo.objects.get(
                video__endswith=new_name.replace('.png', '.mp4')
            )
        except RecipeVideo.DoesNotExist as e:
            logger.exception(e)
        else:
            f = open(thumbnail_path, 'rb')
            content = File(f)

            rv.video_thumbnail = content
            rv.save()

            thumbnail_path.unlink()


@app.task(acks_late=True)
def check_new_comments_for_recipes():

    comments = Comment.objects.filter(
        notification_sent=False,
        content_type__model='recipe'
    ).order_by('object_id')

    groups = defaultdict(list)
    for comment in comments:
        groups[comment.object_id].append(comment)

    for recipe_id, comments_group in groups.items():

        recipe = comments_group[0].content_object
        user = recipe.user

        comments_not_by_user = [c for c in comments if c.user != user]
        if comments_not_by_user:
            NotifyService().create_notify_new_comments_for_recipe(
                user=user,
                recipe=recipe,
                comments=comments_not_by_user
            )
            send_new_comments_for_recipe(
                [user.email],
                user=user,
                recipe=recipe,
                comments=comments_not_by_user
            )

        for comment in comments_group:
            comment.notification_sent = True

        # update comments
        Comment.objects.bulk_update(
            comments_group,
            ['notification_sent'],
            batch_size=100
        )


@app.task(acks_late=True)
def check_new_comments_for_chef_pencil_records():

    comments = Comment.objects.filter(
        notification_sent=False,
        content_type__model='chefpencilrecord'
    ).order_by('object_id')

    groups = defaultdict(list)
    for comment in comments:
        groups[comment.object_id].append(comment)

    for recipe_id, comments_group in groups.items():

        chef_pencil_record = comments_group[0].content_object
        user = chef_pencil_record.user

        comments_not_by_user = [c for c in comments if c.user != user]
        if comments_not_by_user:
            NotifyService().create_notify_new_comments_for_chef_pencil_record(
                user=user,
                chef_pencil_record=chef_pencil_record,
                comments=comments_not_by_user
            )
            send_new_comments_for_chef_pencils_record(
                [user.email],
                user=user,
                chef_pencil_record=chef_pencil_record,
                comments=comments_not_by_user
            )

        for comment in comments_group:
            comment.notification_sent = True

        # update comments
        Comment.objects.bulk_update(
            comments_group,
            ['notification_sent'],
            batch_size=100
        )


@app.task(acks_late=True)
def update_recommended_recipes():

    rs = RecommendedRecipesService()
    rs.calculate_recipes_data()

    users = User.objects.all().get_active().get_not_banned()

    to_update = []
    for user in users:
        logger.info(f'DEBUG: {user}')

        ur = rs.get_recipes_related_to_user_activity(user=user)
        logger.info(f'DEBUG: {ur}')

        if ur.count() > 0:
            recommended = rs.get_recommended(user_activity_recipes=ur)
            logger.info(f'DEBUG: recommended {recommended}')

            user.recommended_recipes = recommended
            to_update.append(user)

    User.objects.bulk_update(
        to_update,
        ['recommended_recipes'],
        batch_size=100
    )