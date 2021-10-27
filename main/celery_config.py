from __future__ import absolute_import, unicode_literals

import os
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab
# set the default Django settings module for the 'celery' program.
from django.conf import settings
from utils.helper import is_prod

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings.prod')
os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

app = Celery('tasks')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Conf
app.conf.broker_transport_options = {'visibility_timeout': 3600, 'max_retries': 5}
app.conf.worker_max_memory_per_child = 12000


app.conf.beat_schedule = {
    'calculate_avg_rating_for_recipes': {
        'task': 'recipe.tasks.calculate_avg_rating_for_recipes',
        'schedule': crontab(minute='*/1')  # every minute
    },
    'calculate_likes_for_recipes': {
        'task': 'recipe.tasks.calculate_likes_for_recipes',
        'schedule': crontab(minute='*/1')  # every minute
    },
    'calculate_views_for_recipes': {
        'task': 'recipe.tasks.calculate_views_for_recipes',
        'schedule': crontab(minute='*/1')  # every minute
    },
    'calculate_avg_rating_for_chef_pencils': {
        'task': 'chef_pencils.tasks.calculate_avg_rating_for_chef_pencils',
        'schedule': crontab(minute='*/1')  # every minute
    },
    'check_new_comments_for_recipes': {
        'task': 'recipe.tasks.check_new_comments_for_recipes',
        'schedule': crontab(minute='*/60')  # every hour
    },
    'check_new_comments_for_chef_pencil_records': {
        'task': 'recipe.tasks.check_new_comments_for_chef_pencil_records',
        'schedule': crontab(minute='*/60')  # every hour
    },
    'update_recommended_recipes': {
        'task': 'recipe.tasks.update_recommended_recipes',
        'schedule': crontab(minute='*/1')
    }
}

if is_prod():

    app.conf.beat_schedule['download_recipes'] = {
        'task': 'recipe.tasks.download_recipes',
        'schedule': crontab(minute=45, hour=6)
    }