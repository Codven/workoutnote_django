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
    date_of_birth = models.DateField(default=None, null=True)
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


class BodyPart(models.Model):
    name = models.CharField(max_length=16)

    @staticmethod
    def init_body_parts():
        BodyPart.objects.all().delete()
        for body_part in ['등', '이두근', '가슴', '핵심', '숲', '다리', '어깨', '삼두근', '전체']:
            BodyPart.objects.create(name=body_part)


class Category(models.Model):
    name = models.CharField(max_length=16)

    @staticmethod
    def init_categories():
        Category.objects.all().delete()
        for category in ['무슨', '바벨', '체중', '굵은', '밧줄', '아령', '기계', '올림픽', '대회의']:
            Category.objects.create(name=category)


class Exercise(models.Model):
    name = models.CharField(max_length=64, unique=True)
    icon = models.ImageField(upload_to='exercise_icons', default='default_icon.svg')
    body_part = models.ForeignKey(to=BodyPart, null=True, on_delete=models.SET_NULL)
    category = models.ForeignKey(to=Category, null=True, on_delete=models.SET_NULL)

    @staticmethod
    def init_from_csv():
        Exercise.objects.all().delete()
        with open('static/exercises-kr.csv', 'r', encoding='utf-8') as r:
            for line in r.readlines()[1:]:
                exercise_name, body_part_str = line[:-1].split(',')
                if BodyPart.objects.filter(name=body_part_str).exists() and Category.objects.filter(name='무슨'):
                    Exercise.objects.create(
                        name=exercise_name,
                        body_part=BodyPart.objects.get(name=body_part_str),
                        category=Category.objects.get(name='무슨')
                    )


class WorkoutSession(models.Model):
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
    timestamp = models.DateTimeField(auto_now_add=True)
    workout_session = models.ForeignKey(to=WorkoutSession, null=True, on_delete=models.SET_NULL)
    exercise = models.ForeignKey(to=Exercise, null=True, on_delete=models.SET_NULL)
    lift_mass = models.FloatField()
    repetitions = models.IntegerField()
    one_rep_max = models.FloatField(default=None)
