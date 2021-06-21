from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from workoutnote_django import models
from utils.tools import Tools
from datetime import datetime
import re


@login_required
def handle_init_exercises(request):
    if request.user.is_superuser:
        models.Exercise.init_from_csv()
    return redirect(to='index')


# region authentication
@require_http_methods(['GET', 'POST'])
def handle_login(request):
    if request.user.is_authenticated:
        return redirect(to='index')
    elif request.method == 'GET':
        return render(request=request, template_name='index/auth login.html')
    else:
        if 'email' in request.POST and 'password' in request.POST:
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(username=email, password=password)
            if user and user.is_authenticated:
                login(request=request, user=user)
                if 'next' in request.POST and len(request.POST['next']) > 0:
                    return redirect(to=request.POST['next'])
                else:
                    return redirect(to='profile main')
            else:
                return redirect(to='login')
    return redirect(to='index')


@require_http_methods(['GET', 'POST'])
def handle_register(request):
    if request.user.is_authenticated:
        return redirect(to='profile main')
    elif request.method == 'GET':
        return render(request=request, template_name='index/auth register.html')
    elif 'email' in request.POST and 'password' in request.POST:
        email = request.POST['email']
        password = request.POST['password']
        if User.objects.filter(username=email).exists() or len(password) < 4:
            return redirect(to='register')
        else:
            User.objects.create_user(username=email, password=password).save()
            user = authenticate(request, username=email, password=password)
            if user:
                models.Preferences.objects.create(user=user)
                login(request=request, user=user)
                if 'next' in request.POST and len(request.POST['next']) > 0:
                    return redirect(to=request.POST['next'])
                else:
                    return redirect(to='profile main')
            else:
                return redirect(to='register')  # whatever the reason could be
    else:
        return redirect(to='index')


@login_required
@require_http_methods(['GET'])
def handle_logout(request):
    logout(request=request)
    return redirect(to='index')


# endregion


def handle_faq(request):
    # models.Exercise.init_from_csv()
    return render(request=request, template_name='index/faq.html')


def handle_about(request):
    return render(request=request, template_name='index/about.html')


@require_http_methods(['GET', 'POST'])
def handle_index(request):
    data = {
        'lvl_txt': None,
        'lvl_stars_number': None,
        'one_rep_max': None,
        'lvl_percentage': None,
        'body_weight': None,
        'gender': None,
        'lift_mass': None,
        'body_weight_ratio': None,
        'lvl_boundaries': None,
        'selected_exercise': models.Exercise.objects.all(),
        'exercises': models.Exercise.objects.all()
    }
    if request.method == 'POST':
        gender = request.POST['gender']
        body_weight = float(request.POST['bodymass'])
        exercise = request.POST['exercise']
        lift_mass = float(request.POST['liftmass'])
        repetitions = int(request.POST['repetitions'])
        avg_age = float(request.POST['age'])
        # TODO: check the following data filtering
        age_range = Tools.get_age_range(avg_age)
        filtered_prefs = models.Preferences.objects.filter(
            date_of_birth__range=Tools.get_date_of_birth_range(age_range),
            gender=str(gender).upper())
        user_ids = filtered_prefs.values_list('user', flat=True)

        filtered_lifts = models.Lift.objects.filter(
            body_weight=body_weight,
            exercise__name=exercise,
            user_id__in=user_ids
        )
        sorted_1rms_for_given_bw = list(filtered_lifts.order_by('one_rep_max').values_list('one_rep_max', flat=True))

        one_rep_max = Tools.calculate_one_rep_max(lift_mass, repetitions)

        lvl_in_percentage = Tools.get_level_in_percentage(sorted_1rms_for_given_bw, one_rep_max)
        lvl_boundaries = Tools.get_level_boundaries_for_bodyweight(sorted_1rms_for_given_bw)
        lvl_in_text = Tools.get_string_level(lvl_boundaries, one_rep_max)

        # Construct the resulting data
        data['lvl_txt'] = lvl_in_text
        data['lvl_stars_number'] = None  # TODO: make a function to calculate number of stars
        data['one_rep_max'] = one_rep_max
        data['lvl_percentage'] = round(lvl_in_percentage, 1)
        data['body_weight'] = body_weight
        data['gender'] = gender
        data['lift_mass'] = lift_mass
        data['body_weight_ratio'] = round(Tools.calculate_body_weight_ratio(lift_mass, body_weight), 2)
        data['lvl_boundaries'] = lvl_boundaries
        data['selected_exercise'] = exercise

    return render(request=request, template_name='index/index.html', context=data)


def handle_calculators(request):
    return render(request=request, template_name='index/calculators.html')


def handle_strength_standards(request):
    return render(
        request=request,
        template_name='index/strength standards.html',
        context={'exercises': models.Exercise.objects.all()}
    )


def handle_training_log_tutorial(request):
    return render(request=request, template_name='index/training log tutorial.html')


@require_http_methods(['GET', 'POST'])
def handle_one_rep_max_calculator(request):
    data = {
        'result_number': None,
        'result_table_1': [],
        'result_table_2': []
    }
    table_1_reps = [1, 2, 4, 6, 8, 10, 12, 16, 20, 24, 30]
    table_2_percentages = [
        100, 97, 94, 92, 89, 86, 83, 81, 78, 75, 73, 71, 70, 68, 67, 65, 64, 63, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50
    ]
    if request.method == 'GET':
        for index, item in enumerate(table_2_percentages):
            data['result_table_2'].append(
                {'percentage': item, 'reps_of_1rm': index + 1}
            )

        return render(request=request, template_name='index/one rep max calculator.html', context=data)
    elif request.method == 'POST':
        result = Tools.calculate_one_rep_max(
            float(request.POST['liftmass']),
            int((request.POST['repetitions']))
        )
        max_percentage = 100
        data['result_number'] = result

        # Populate Table 1 with content
        for item in table_1_reps:
            data['result_table_1'].append(
                {'percentage': max_percentage, 'liftmass': round(result * max_percentage / 100, 1), 'reps_of_1rm': item}
            )
            max_percentage -= 5

        # Populate Table 2 with content
        for index, item in enumerate(table_2_percentages):
            data['result_table_2'].append(
                {'percentage': item, 'liftmass': round(result * item / 100, 1), 'reps_of_1rm': index + 1}
            )
        return render(request=request, template_name='index/one rep max calculator.html', context=data)


def handle_plate_barbell_racking_calculator(request):
    return render(request=request, template_name='index/plate barbell racking calculator.html')


@require_http_methods(['GET', 'POST'])
def handle_powerlifting_calculator(request):
    data = {
        'lvl_txt': None,
        'lvl_stars_number': None,
        'lvl_percentage': None,
        'gender': None,
        'body_weight': None,
        'total_lift_mass': None,
        'wilks_score': None,
        'lvl_boundaries': None
    }
    if request.method == 'POST':
        gender = request.POST['gender']
        body_weight = float(request.POST['bodymass'])
        # TODO: check following data filtering
        filtered_prefs = models.Preferences.objects.filter(gender=str(gender).upper())
        user_ids = filtered_prefs.values_list('user', flat=True)
        filtered_lifts = models.Lift.objects.filter(body_weight=body_weight, user_id__in=user_ids)
        sorted_1rms_for_given_bw = list(filtered_lifts.order_by('one_rep_max').values_list('one_rep_max', flat=True))
        if request.POST['method'] == 'total':
            total_lift_mass = float(request.POST['totalliftmass'])
        else:
            bench_1rm = Tools.calculate_one_rep_max(
                float(request.POST['benchliftmass']),
                int(request.POST['benchrepetitions'])
            )
            squat_1rm = Tools.calculate_one_rep_max(
                float(request.POST['squatliftmass']),
                int(request.POST['squatrepetitions'])
            )
            deadlift_1rm = Tools.calculate_one_rep_max(
                float(request.POST['deadliftliftmass']),
                int(request.POST['deadliftrepetitions'])
            )
            total_lift_mass = bench_1rm + squat_1rm + deadlift_1rm

        lvl_in_percentage = Tools.get_level_in_percentage(sorted_1rms_for_given_bw, total_lift_mass)
        lvl_boundaries = Tools.get_level_boundaries_for_bodyweight(sorted_1rms_for_given_bw)
        lvl_in_text = Tools.get_string_level(lvl_boundaries, total_lift_mass)

        # Construct the resulting data
        data['lvl_txt'] = lvl_in_text
        data['lvl_stars_number'] = None  # TODO: make a function to calculate number of stars
        data['lvl_percentage'] = round(lvl_in_percentage, 1)
        data['body_weight'] = body_weight
        data['gender'] = gender
        data['total_lift_mass'] = total_lift_mass
        data['wilks_score'] = Tools.calculate_wilks_score(total_lift_mass)
        data['lvl_boundaries'] = lvl_boundaries

    return render(request=request, template_name='index/powerlifting calculator.html', context=data)


@require_http_methods(['GET', 'POST'])
def handle_wilks_calculator(request):
    data = {
        'wilks_score': None,
        'gender': None,
        'body_weight': None,
        'total_lift_mass': None,
        'wilks_score_boundaries': None
    }
    if request.method == 'POST':
        gender = request.POST['gender']
        body_weight = float(request.POST['bodymass'])
        if request.POST['method'] == 'total':
            total_lift_mass = float(request.POST['totalliftmass'])
        else:
            bench_1rm = Tools.calculate_one_rep_max(
                float(request.POST['benchliftmass']),
                int(request.POST['benchrepetitions'])
            )
            squat_1rm = Tools.calculate_one_rep_max(
                float(request.POST['squatliftmass']),
                int(request.POST['squatrepetitions'])
            )
            deadlift_1rm = Tools.calculate_one_rep_max(
                float(request.POST['deadliftliftmass']),
                int(request.POST['deadliftrepetitions'])
            )
            total_lift_mass = bench_1rm + squat_1rm + deadlift_1rm

        wilks_score = Tools.calculate_wilks_score(total_lift_mass)
        wilks_score_boundaries = Tools.get_wilks_score_boundaries()

        # Construct the resulting data
        data['wilks_score'] = wilks_score
        data['body_weight'] = body_weight
        data['gender'] = gender
        data['total_lift_mass'] = total_lift_mass
        data['wilks_score_boundaries'] = wilks_score_boundaries

    return render(request=request, template_name='index/wilks calculator.html', context=data)


def handle_powerlifting_standards(request):
    return render(request=request, template_name='index/powerlifting standards.html')


@login_required
def handle_profile_main(request):
    return render(
        request=request,
        template_name='profile/main.html',
        context={'preferences': models.Preferences.objects.get(user=request.user)}
    )


@login_required
@require_http_methods(['GET', 'POST'])
def handle_settings(request):
    preferences = models.Preferences.objects.get(user=request.user)
    if request.method == 'POST':
        print(request.POST)
        # personal data
        if 'name' in request.POST:
            preferences.name = request.POST['name']
        if 'gender' in request.POST and request.POST['gender'] in models.Preferences.Gender.ALL:
            preferences.gender = request.POST['gender']
        if 'birthday' in request.POST and re.match(r'^\d{8}$', request.POST['birthday']):
            year = int(request.POST['birthday'][:4])
            month = int(request.POST['birthday'][4:6])
            day = int(request.POST['birthday'][6:])
            if 1930 < year < datetime.now().year and 0 < month < 13 and 0 < day < 32:
                preferences.date_of_birth = request.POST['birthday']
        if 'height' in request.POST and 30 < int(request.POST['height']) < 300:
            preferences.height = int(request.POST['height'])
        if 'measurement_unit' in request.POST and request.POST['measurement_unit'] in models.Preferences.MeasurementUnit.ALL:
            preferences.unit_of_measure = request.POST['measurement_unit']
        if 'profile_sharing' in request.POST and request.POST['profile_sharing'] in models.Preferences.ProfileSharing.ALL:
            preferences.profile_sharing = request.POST['profile_sharing']
        if 'oldpassword' in request.POST and 'newpassword' in request.POST and 'repeatpassword' in request.POST and request.POST['newpassword'] == request.POST['repeatpassword']:
            if request.user.check_password(raw_password=request.POST['oldpassword']):
                request.user.set_password(request.POST['newpassword'])
                request.user.save()
        preferences.save()

    return render(
        request=request,
        template_name='profile/settings.html',
        context={
            'preferences': preferences,
            'gender': models.Preferences.Gender,
            'sharing': models.Preferences.ProfileSharing,
            'unit': models.Preferences.MeasurementUnit,
        }
    )


def handle_analyse_lift(request):
    return render(request=request, template_name='profile/analyse lift.html')


def handle_bodyweight(request):
    return render(request=request, template_name='profile/bodyweight.html')


def handle_find_lifters(request):
    return render(request=request, template_name='profile/find lifters.html')


@login_required
@require_http_methods(['GET'])
def handle_workouts(request):
    return render(
        request=request,
        template_name='profile/workouts.html',
        context={
            'lifts': models.Lift.objects.filter(user=request.user)
        }
    )


@login_required
@require_http_methods(['GET'])
def handle_lifts(request):
    return render(
        request=request,
        template_name='profile/lifts.html',
        context={
            'exercises': models.Exercise.objects.all(),
            'lifts': models.Lift.objects.filter(user=request.user)
        }
    )


@login_required
@require_http_methods(['POST'])
def handle_add_lift(request):
    exercise = models.Exercise.objects.get(name=request.POST['exercise']) if models.Exercise.objects.filter(name=request.POST['exercise']).exists() else None
    lift_mass = float(request.POST['liftmass'])
    repetitions = int(request.POST['repetitions'])
    sets = int(request.POST['sets'])
    if exercise is not None:
        for _ in range(sets):
            models.Lift.objects.create(
                user=request.user,
                exercise=exercise,
                body_weight=70,
                lift_mass=lift_mass,
                repetitions=repetitions,
                one_rep_max=Tools.calculate_one_rep_max(lift_mass, repetitions)
            )
    return redirect(to='lifts')


def handle_exercises(request):
    return render(request=request, template_name='profile/exercises.html')
