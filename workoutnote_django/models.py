from django.contrib.auth.models import User as django_User
from django.db import models
import enum


class Preferences(models.Model):
    class Gender(enum.Enum):
        MALE = "MALE"
        FEMALE = "FEMALE"

    class ProfileSharing(enum.Enum):
        SHARED_WITH_PUBLIC = "SHARED_WITH_PUBLIC"
        SHARED_WITH_USERS = "SHARED_WITH_USERS"
        PRIVATE = "PRIVATE"

    class MeasurementUnit(enum.Enum):
        KILOGRAMS = "KG"
        POUNDS = "LB"
        STONE = "ST"

    user = models.OneToOneField(to=django_User, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=128, default=None, null=True)
    gender = models.CharField(max_length=16, default=Gender.MALE)
    date_of_birth = models.DateField(default=None, null=True)
    height = models.FloatField(default=None, null=True)
    profile_sharing = models.CharField(max_length=128, default=ProfileSharing.PRIVATE)
    unit_of_measure = models.CharField(max_length=128, default=MeasurementUnit.KILOGRAMS)


class Exercise(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
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
    user = models.ForeignKey(to=django_User, on_delete=models.CASCADE)
    exercise = models.ForeignKey(to=Exercise, on_delete=models.CASCADE)
    body_weight = models.FloatField()
    lift_mass = models.FloatField()
    repetitions = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.exercise.name
