from django.contrib.auth.models import User as django_User
from django.db import models
import enum


class Preferences(models.Model):
    class Gender:
        MALE = "MALE"
        FEMALE = "FEMALE"
        ALL = [MALE, FEMALE]

    class ProfileSharing:
        SHARED_WITH_PUBLIC = "SHARED_WITH_PUBLIC"
        SHARED_WITH_USERS = "SHARED_WITH_USERS"
        PRIVATE = "PRIVATE"
        ALL = [SHARED_WITH_PUBLIC, SHARED_WITH_USERS, PRIVATE]

    class MeasurementUnit:
        KILOGRAMS = "KG"
        POUNDS = "LB"
        STONE = "ST"
        ALL = [KILOGRAMS, POUNDS, STONE]

    user = models.OneToOneField(to=django_User, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=128, default=None, null=True)
    gender = models.CharField(max_length=16, default=Gender.MALE)
    date_of_birth = models.DateTimeField(default=None, null=True)
    height = models.FloatField(default=None, null=True)
    profile_sharing = models.CharField(max_length=128, default=ProfileSharing.PRIVATE)
    unit_of_measure = models.CharField(max_length=128, default=MeasurementUnit.KILOGRAMS)

    def gender_str(self):
        return self.gender.__str__()

    def profile_sharing_str(self):
        return self.profile_sharing.__str__()

    def unit_of_measure_str(self):
        return self.unit_of_measure.__str__()

    def date_of_birth_str(self):
        return self.date_of_birth.strftime('%m%d%Y') if self.date_of_birth is not None else ''


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
    one_rep_max = models.FloatField(default=None)

    def __str__(self):
        return self.exercise.name
