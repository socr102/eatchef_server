from main.celery_config import app

from chef_pencils.services import (
    ChefPencilRatingCalculator,
    ChefPencilRecordLikeCalculator,
    ChefPencilRecordViewsCalculator
)


@app.task(acks_late=True)
def calculate_avg_rating_for_chef_pencils():
    calc = ChefPencilRatingCalculator()
    calc.get_avg_ratings_for_chef_pencils()
    calc.update_records()


@app.task(acks_late=True)
def calculate_likes_for_chef_pencil_records():
    calc = ChefPencilRecordLikeCalculator()
    calc.get_total_likes_for_chef_pencil_records()
    calc.update_records()


@app.task(acks_late=True)
def calculate_views_for_chef_pencil_records():
    calc = ChefPencilRecordViewsCalculator()
    calc.get_total_views_for_chef_pencil_records()
    calc.update_records()