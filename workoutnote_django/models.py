from django.contrib.auth.models import User as django_User
from django.db import models


class Exercise(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64)
    icon = models.CharField(max_length=128)
    body_part = models.CharField(max_length=16)
    category = models.CharField(max_length=16)

    @staticmethod
    def init_from_csv():
        Exercise.objects.all().delete()
        with open('/Users/kevin/PycharmProjects/workoutnote_django/static/exercises.csv', 'r') as r:
            for line in r.readlines()[1:]:
                exercise_name, icon, body_part, category = line[:-1].split(',')
                Exercise.objects.create(name=exercise_name, icon=icon, body_part=body_part, category=category).save()


class Lift(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(django_User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    body_weight = models.FloatField()
    lift_mass = models.FloatField()
    repetitions = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.exercise.name
