from django.contrib.auth.models import User as django_User
from datetime import date, timedelta, datetime
from typing import Tuple
from math import pow
import random
import math


class Levels:
    BEGINNER = 'Beginner'
    NOVICE = 'Novice'
    INTERMEDIATE = 'Intermediate'
    ADVANCED = 'Advanced'
    ELITE = 'Elite'

    LIMITS = {
        BEGINNER: 0.05,
        NOVICE: 0.2,
        INTERMEDIATE: 0.5,
        ADVANCED: 0.8,
        ELITE: 0.95
    }


class Tools:
    AGE_RANGES = {
        '14-17': (14, 17),
        '18-23': (18, 23),
        '24-39': (24, 39),
        '40-49': (40, 49),
        '50-59': (50, 59),
        '60-69': (60, 69),
        '70-79': (70, 79),
        '80-89': (80, 89)
    }
    POWERLIFTING_EXERCISE_NAMES = ['Bench Press', 'Deadlift', 'Squat']

    @staticmethod
    def calculate_one_rep_max(lift_mass: float, repetitions: int) -> float:
        return round(lift_mass / (1.0278 - 0.0278 * repetitions), 1)

    @staticmethod
    def get_level_in_percentage(sorted_lifts_for_body_weight: list, total_lift_mass: float) -> float:
        list_copy = sorted_lifts_for_body_weight[:]
        data_length = len(list_copy)
        list_copy.append(total_lift_mass)
        list_copy.sort()
        return (list_copy.index(total_lift_mass)) / data_length * 100

    @staticmethod
    def get_level_boundaries_for_bodyweight(sorted_lifts_for_body_weight: list) -> dict:
        return {
            Levels.BEGINNER: sorted_lifts_for_body_weight[int(Levels.LIMITS[Levels.BEGINNER] * len(sorted_lifts_for_body_weight))],
            Levels.NOVICE: sorted_lifts_for_body_weight[int(Levels.LIMITS[Levels.NOVICE] * len(sorted_lifts_for_body_weight))],
            Levels.INTERMEDIATE: sorted_lifts_for_body_weight[int(Levels.LIMITS[Levels.INTERMEDIATE] * len(sorted_lifts_for_body_weight))],
            Levels.ADVANCED: sorted_lifts_for_body_weight[int(Levels.LIMITS[Levels.ADVANCED] * len(sorted_lifts_for_body_weight))],
            Levels.ELITE: sorted_lifts_for_body_weight[int(Levels.LIMITS[Levels.ELITE] * len(sorted_lifts_for_body_weight))]
        }

    @staticmethod
    def get_string_level(boundaries: dict, total_lift_mass: float) -> str:
        level = Levels.BEGINNER  # let the default be a Beginner level
        if total_lift_mass > boundaries[Levels.BEGINNER]:
            level = Levels.BEGINNER
        if total_lift_mass > boundaries[Levels.NOVICE]:
            level = Levels.NOVICE
        if total_lift_mass > boundaries[Levels.INTERMEDIATE]:
            level = Levels.INTERMEDIATE
        if total_lift_mass > boundaries[Levels.ADVANCED]:
            level = Levels.ADVANCED
        if total_lift_mass > boundaries[Levels.ELITE]:
            level = Levels.ELITE
        return level

    @staticmethod
    def calculate_wilks_score(gender: str, body_weight: float, lift_mass: float) -> float:
        '''
        Wilks score formula:
        Wilks coefficient = W * 500 / (a + bx +cx² +dx³ +ex⁴ +fx⁵)
        W - the maximum weight lifted
        x - body weight
        letters denote coefficients from coeff  array
        '''
        coeff = []
        from workoutnote_django.models import Preferences
        if gender == Preferences.Gender.MALE:
            coeff = [-216.0475144, 16.2606339, -0.002388645, -0.00113732, 7.01863E-06, -1.291E-08]
        elif gender == Preferences.Gender.FEMALE:
            coeff = [594.31747775582, -27.23842536447, 0.82112226871, -0.00930733913, 4.731582E-05, -9.054E-08]

        denominator = 0
        for i in range(0, 6):
            denominator += coeff[i] * pow(body_weight, i)

        result = lift_mass * 500 / denominator

        return round(result, 2)

    @staticmethod
    def calculate_body_weight_ratio(lift_mass: float, body_weight: float):
        return lift_mass / body_weight

    @staticmethod
    def get_age_range(avg_age: float) -> Tuple[int, int]:
        for key, value in Tools.AGE_RANGES.items():
            if avg_age >= value[0] and avg_age <= value[1]:
                return value

    @staticmethod
    def get_date_of_birth_range(age_range: Tuple[int, int]) -> Tuple[date, date]:
        today = date.today()
        start_date = (today - timedelta(days=365 * age_range[0])).replace(month=1, day=1)
        end_date = (today - timedelta(days=365 * age_range[1])).replace(month=1, day=1)
        return (start_date, end_date)

    @staticmethod
    def generate_dummy_data():
        print('working on dummy data')
        from workoutnote_django.models import Exercise, Preferences, Lift
        from django.utils import timezone
        exercises = Exercise.objects.all()
        # create dummy accounts
        for weight in range(50, 141):
            username = f'male_{weight}kg@workoutnote.com'
            if django_User.objects.filter(username=username).exists():
                user = django_User.objects.get(username=username)
                update_timestamps = True
            else:
                user = django_User.objects.create_user(username=username, email=username, password=username)
                user.save()
                Preferences.objects.create(user=user, gender=Preferences.Gender.MALE).save()
                update_timestamps = False
            print(f'\rWorking on dummy data of {username}')
            # generate dummy lifts for the user
            timestamp = (timezone.now() - timedelta(days=len(exercises))).replace(hour=0, minute=0, microsecond=0)
            for exercise in exercises:
                if update_timestamps:
                    lifts = Lift.objects.filter(user=user, exercise=exercise)
                    for lift in lifts:
                        lift.created_at = timestamp
                        lift.save()
                else:
                    number_of_sets = random.randint(2, 10)
                    number_of_reps = random.randint(2, 7)
                    lift_mass = random.randint(math.floor(weight * .5), math.ceil(weight * 1.8))
                    one_rep_max = lift_mass + lift_mass * number_of_reps * 0.025
                    for _ in range(number_of_sets):
                        lift = Lift.objects.create(
                            user=user,
                            exercise=exercise,
                            body_weight=weight,
                            lift_mass=lift_mass,
                            repetitions=number_of_reps,
                            created_at=timestamp,
                            one_rep_max=one_rep_max
                        )
                        lift.created_at = timestamp
                        lift.save()
                timestamp += timedelta(days=1)
                print(f'\r{exercise}', end='', flush=True)

        for weight in range(40, 121):
            username = f'female_{weight}kg@workoutnote.com'
            if django_User.objects.filter(username=username).exists():
                user = django_User.objects.get(username=username)
                update_timestamps = True
            else:
                user = django_User.objects.create_user(username=username, email=username, password=username)
                user.save()
                Preferences.objects.create(user=user, gender=Preferences.Gender.FEMALE).save()
                update_timestamps = False
            print(f'\rWorking on dummy data of {username}')
            # generate dummy lifts for the user
            timestamp = (timezone.now() - timedelta(days=len(exercises))).replace(hour=0, minute=0, microsecond=0)
            for exercise in exercises:
                if update_timestamps:
                    lifts = Lift.objects.filter(user=user, exercise=exercise)
                    for lift in lifts:
                        lift.created_at = timestamp
                        lift.save()
                else:
                    number_of_sets = random.randint(1, 6)
                    number_of_reps = random.randint(1, 5)
                    lift_mass = random.randint(math.floor(weight * .3), math.ceil(weight * 1.4))
                    one_rep_max = lift_mass + lift_mass * number_of_reps * 0.025
                    for _ in range(number_of_sets):
                        lift = Lift.objects.create(
                            user=user,
                            exercise=exercise,
                            body_weight=weight,
                            lift_mass=lift_mass,
                            repetitions=number_of_reps,
                            one_rep_max=one_rep_max
                        )
                        lift.created_at = timestamp
                        lift.save()
                timestamp += timedelta(days=1)
                print(f'\r{exercise}', end='', flush=True)

    @staticmethod
    def date2str(_date, readable=False):
        if readable:
            return _date.strftime("%d %B %Y")
        else:
            return _date.strftime('%d%m%Y')
