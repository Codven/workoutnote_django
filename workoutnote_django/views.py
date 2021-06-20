from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.template.response import TemplateResponse
from django.contrib.auth.models import User
from workoutnote_django import models
from utils.tools import Tools


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


def handle_index(request):
    return render(request=request, template_name='index/index.html')


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

        return TemplateResponse(request=request, template='index/one rep max calculator.html', context=data)
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
        return TemplateResponse(request=request, template='index/one rep max calculator.html', context=data)


def handle_plate_barbell_racking_calculator(request):
    return render(request=request, template_name='index/plate barbell racking calculator.html')


@require_http_methods(['GET', 'POST'])
def handle_powerlifting_calculator(request):
    # TODO: remove following fake data after model for lifts is set
    TMP_POWERLIFTING_FAKE_DATA = [
        {'body_weight': 70, 'reps': 10, "lift_mass": 30},
        {'body_weight': 70, 'reps': 10, "lift_mass": 20},
        {'body_weight': 70, 'reps': 10, "lift_mass": 50},
        {'body_weight': 70, 'reps': 10, "lift_mass": 41},
        {'body_weight': 70, 'reps': 10, "lift_mass": 32},
        {'body_weight': 70, 'reps': 10, "lift_mass": 35},
        {'body_weight': 70, 'reps': 10, "lift_mass": 16},
        {'body_weight': 70, 'reps': 10, "lift_mass": 105},
        {'body_weight': 70, 'reps': 10, "lift_mass": 85},
        {'body_weight': 70, 'reps': 10, "lift_mass": 102},
        {'body_weight': 70, 'reps': 10, "lift_mass": 50},
        {'body_weight': 70, 'reps': 10, "lift_mass": 58},
        {'body_weight': 70, 'reps': 10, "lift_mass": 25},
    ]

    data = {
        'lvl_txt': None,
        'lvl_stars_number': None,
        'lvl_percentage': None,
        'gender': None,
        'body_weight': None,
        'total_lift': None,
        'wilks_score': None,
        'lvl_boundaries': None
    }
    if request.method == 'POST':
        gender = request.POST['gender']
        body_weight = float(request.POST['bodymass'])
        # TODO: instead of following fake data get real data from db for given bodyweight and gender
        sorted_fake_lift_mass = sorted([i['lift_mass'] for i in TMP_POWERLIFTING_FAKE_DATA])
        total_lift_mass = float(request.POST['totalliftmass'])
        if request.POST['method'] == 'split':
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

        lvl_in_percentage = Tools.get_power_level_in_percentage(sorted_fake_lift_mass, total_lift_mass)
        lvl_in_text = Tools.get_string_power_level(lvl_in_percentage)
        lvl_boundaries = Tools.get_level_boundaries_for_bodyweight(sorted_fake_lift_mass)

        # Construct the resulting data
        data['lvl_txt'] = lvl_in_text
        data['lvl_stars_number'] = None  # TODO: make a function to calculate number of stars
        data['lvl_percentage'] = round(lvl_in_percentage, 1)
        data['body_weight'] = body_weight
        data['gender'] = gender
        data['total_lift'] = total_lift_mass
        data['wilks_score'] = None  # TODO: make a function to calculate Wilks Score
        data['lvl_boundaries'] = lvl_boundaries

    return TemplateResponse(request=request, template='index/powerlifting calculator.html', context=data)


def handle_wilks_calculator(request):
    return render(request=request, template_name='index/wilks calculator.html')


def handle_powerlifting_standards(request):
    return render(request=request, template_name='index/powerlifting standards.html')


def handle_profile_main(request):
    return render(request=request, template_name='profile/main.html')


def handle_settings(request):
    return render(request=request, template_name='profile/settings.html')


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
                repetitions=repetitions
            )
    return redirect(to='lifts')


def handle_exercises(request):
    return render(request=request, template_name='profile/exercises.html')
