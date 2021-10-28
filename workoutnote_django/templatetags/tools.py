import datetime
from django import template
from workoutnote_django import models

register = template.Library()


@register.simple_tag
def is_favorite_exercise(user, exercise):
    return models.FavoriteExercise.objects.filter(user=user, exercise=exercise).exists()


@register.simple_tag
def is_favorite_workout(user, workout_session):
    return models.FavoriteWorkout.objects.filter(user=user, workout_session=workout_session).exists()

@register.simple_tag
def current_time(format_string):
    return datetime.datetime.now().strftime(format_string)