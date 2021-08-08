from django import template
from workoutnote_django import models

register = template.Library()


@register.simple_tag
def is_favorite_exercise(user, exercise):
    return models.FavoriteExercises.objects.filter(user=user, exercise=exercise).exists()
