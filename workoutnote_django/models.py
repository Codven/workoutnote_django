from django.contrib.auth.models import User as django_User
from utils.tools import Tools
from django.db import models
from django.utils import timezone


class Preferences(models.Model):
    class Gender:
        MALE = "MALE"
        FEMALE = "FEMALE"
        ALL = [MALE, FEMALE]
        CHOICES = (
            (MALE, 'Male'),
            (FEMALE, 'Female')
        )

    user = models.OneToOneField(to=django_User, on_delete=models.CASCADE, primary_key=True, related_name='preferences')
    name = models.CharField(max_length=128, default=None, null=True)
    gender = models.CharField(max_length=24, default=Gender.MALE, choices=Gender.CHOICES)
    date_of_birth = models.DateTimeField(default=None, null=True)
    shared_profile = models.BooleanField(default=True)

    def gender_str(self):
        return self.gender.__str__()

    def date_of_birth_str(self):
        return Tools.date2str(self.date_of_birth)

    def get_age(self):
        today = timezone.now()
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


class WorkoutSession(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(to=django_User, on_delete=models.CASCADE)
    title = models.CharField(max_length=512, default='[unnamed workout]')
    duration = models.IntegerField(default=0)

    def get_duration_str(self):
        seconds = self.duration % 60
        minutes = (int((self.duration - seconds) / 60)) % 60
        hours = int(((int((self.duration - seconds) / 60)) % 60 - minutes) / 60)
        return f'{hours:02}:{minutes:02}:{seconds:02}'

    def get_day_str(self):
        return timezone.localtime(self.timestamp).strftime('%Y.%m.%d. %a').upper()


class Lift(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    workout_session = models.ForeignKey(to=WorkoutSession, on_delete=models.CASCADE)
    exercise = models.ForeignKey(to=Exercise, on_delete=models.CASCADE)
    lift_mass = models.FloatField()
    repetitions = models.IntegerField()
    one_rep_max = models.FloatField(default=None)
