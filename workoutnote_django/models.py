from django.contrib.auth.models import User as django_User
from utils.tools import Tools
from django.db import models


class Preferences(models.Model):
    class Gender:
        MALE = "MALE"
        FEMALE = "FEMALE"
        ALL = [MALE, FEMALE]
        CHOICES = (
            (MALE, 'Male'),
            (FEMALE, 'Female')
        )

    class ProfileSharing:
        SHARED_WITH_PUBLIC = "SHARED_WITH_PUBLIC"
        SHARED_WITH_USERS = "SHARED_WITH_USERS"
        PRIVATE = "PRIVATE"
        ALL = [SHARED_WITH_PUBLIC, SHARED_WITH_USERS, PRIVATE]
        CHOICES = (
            (SHARED_WITH_PUBLIC, 'Shared with people'),
            (SHARED_WITH_USERS, 'Shared with users'),
            (PRIVATE, 'Private'),
        )

    class MeasurementUnit:
        KILOGRAMS = "KG"
        POUNDS = "LB"
        STONE = "ST"
        ALL = [KILOGRAMS, POUNDS, STONE]
        CHOICES = (
            (KILOGRAMS, 'kg'),
            (POUNDS, 'lb'),
            (STONE, 'st'),
        )

    user = models.OneToOneField(to=django_User, on_delete=models.CASCADE, primary_key=True, related_name='preferences')
    name = models.CharField(max_length=128, default=None, null=True)
    gender = models.CharField(max_length=24, default=Gender.MALE, choices=Gender.CHOICES)
    date_of_birth = models.DateTimeField(default=None, null=True)
    height = models.FloatField(default=None, null=True)
    body_weight = models.FloatField(default=None, null=True)
    profile_sharing = models.CharField(max_length=128, default=ProfileSharing.PRIVATE, choices=ProfileSharing.CHOICES)
    unit_of_measure = models.CharField(max_length=128, default=MeasurementUnit.KILOGRAMS, choices=MeasurementUnit.CHOICES)

    def gender_str(self):
        return self.gender.__str__()

    def profile_sharing_str(self):
        return self.profile_sharing.__str__()

    def unit_of_measure_str(self):
        return self.unit_of_measure.__str__()

    def date_of_birth_str(self):
        return Tools.date2str(self.date_of_birth)

    def get_age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))


class EmailConfirmationCodes(models.Model):
    email = models.CharField(max_length=128, primary_key=True)
    verification_code = models.CharField(max_length=16)


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
    body_weight = models.FloatField(default=None, null=True)
    lift_mass = models.FloatField()
    repetitions = models.IntegerField()
    created_at = models.DateField(auto_now_add=True)
    one_rep_max = models.FloatField(default=None)

    def __str__(self):
        return self.exercise.name

    class Meta:
        ordering = ['user', '-created_at']
