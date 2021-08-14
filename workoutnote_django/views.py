import json
import random
import re
import time
from datetime import datetime, timedelta

import pytz
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as django_User
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from utils.tools import Tools, Status
from workoutnote_django import models
from api import models as api_models

LIMIT_OF_ACCEPTABLE_DATA_AMOUNT = 5


@login_required
def handle_init_configs(request):
    if request.user.is_superuser:
        models.BodyPart.init_body_parts()
        models.Category.init_categories()
        models.Exercise.init_from_csv()
    return redirect(to='index')


@login_required
def handle_generate_dummy_data(request):
    if request.user.is_superuser:
        Tools.generate_dummy_data()
    return redirect(to='index')


# region authentication
@csrf_exempt
@require_http_methods(['GET', 'POST'])
def handle_login(request, *args, **kwargs):
    if request.user.is_authenticated:
        return redirect(to='index')
    elif request.method == 'GET':
        return render(request=request, template_name='auth.html', context={'title': ''})
    else:
        if 'email' in request.POST and 'password' in request.POST:
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(request, username=email, password=password)
            if user and user.is_authenticated:
                login(request=request, user=user)
                if 'next' in request.POST and len(request.POST['next']) > 0:
                    return redirect(to=request.POST['next'])
                else:
                    return redirect(to='index')
            else:
                return redirect(to='login')
    return redirect(to='index')


@csrf_exempt
@require_http_methods(['POST'])
def handle_register(request):
    if request.user.is_authenticated:
        return redirect(to='index')
    elif 'name' in request.POST and 'email' in request.POST and 'password' in request.POST:
        name = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']
        if django_User.objects.filter(username=email).exists() or len(password) < 4:
            return redirect(to='login')
        elif 'verification_code' in request.POST and models.EmailConfirmationCode.objects.filter(email=email).exists():
            expected_code = models.EmailConfirmationCode.objects.get(email=email).verification_code
            provided_code = request.POST['verification_code']
            if provided_code == expected_code:
                models.EmailConfirmationCode.objects.filter(email=email).delete()
                django_User.objects.create_user(username=email, password=password)
                user = authenticate(request, username=email, password=password)
                if user:
                    models.Preferences.objects.create(user=user, name=name)
                    login(request=request, user=user)
                    if 'next' in request.POST and len(request.POST['next']) > 0:
                        return redirect(to=request.POST['next'])
                    else:
                        return redirect(to='index')
                else:
                    return redirect(to='register')  # whatever the reason could be
            return redirect(to='login')
        else:
            if not models.EmailConfirmationCode.objects.filter(email=email).exists():
                verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                email_message = EmailMessage(
                    'Workoutnote.com email verification',
                    f'Email verification code is : {verification_code}',
                    settings.EMAIL_HOST_USER,
                    [email],
                )
                email_message.fail_silently = False
                email_message.send()
                models.EmailConfirmationCode.objects.create(email=email, verification_code=verification_code)
            return render(request=request, template_name='auth.html', context={
                'verify_now': True,
                'name': name,
                'email': email,
                'password': password
            })
    else:
        return redirect(to='index')


@csrf_exempt
@login_required
@require_http_methods(['GET'])
def handle_logout(request):
    logout(request=request)
    return redirect(to='index')


# endregion

@login_required
def handle_index(request):
    name = models.Preferences.objects.get(user=request.user).name
    db_workout_sessions = models.WorkoutSession.objects.filter(user=request.user).order_by('-timestamp')
    workouts_by_days = {}
    for db_workout_session in db_workout_sessions:
        db_lifts = models.Lift.objects.filter(workout_session=db_workout_session).order_by('id')
        day_str = db_workout_session.get_day_str()
        for db_lift in db_lifts:
            if day_str in workouts_by_days:
                if db_workout_session in workouts_by_days[day_str]:
                    workouts_by_days[day_str][db_workout_session] += [db_lift]
                else:
                    workouts_by_days[day_str][db_workout_session] = [db_lift]
            else:
                workouts_by_days[day_str] = {db_workout_session: [db_lift]}
    if not api_models.SessionKey.objects.filter(user=request.user).exists():
        session_key = api_models.SessionKey.generate_key(email=request.user.email)
        while api_models.SessionKey.objects.filter(key=session_key).exists():
            time.sleep(0.001)
            session_key = api_models.SessionKey.generate_key(email=request.user.email)
        api_models.SessionKey.objects.create(user=request.user, key=session_key)
    else:
        session_key = api_models.SessionKey.objects.get(user=request.user).key
    # todo plot as in https://simpleisbetterthancomplex.com/tutorial/2020/01/19/how-to-use-chart-js-with-django.html
    # todo customize plot as in https://www.chartjs.org/docs/latest/charts/line.html
    return render(request=request, template_name='home.html', context={
        'name': name if name else request.user.username,
        'at_home': True,
        'exercises': models.Exercise.objects.all(),
        'body_parts': models.BodyPart.objects.all(),
        'categories': models.Category.objects.all(),
        'sessionKey': session_key,
        'workouts_by_days': workouts_by_days
    })


@login_required
def handle_calculators(request):
    return render(request=request, template_name='calculators/calculators.html', context={
        'title': '체력 계산기',
        'at_calculators': True,
    })


@require_http_methods(['GET', 'POST'])
def handle_one_rep_max_calculator(request):
    data = {
        'title': '1 Rep Max 계산기',
        'at_calculators': True,

        'result_number': None,
        'result_table_1': [],
        'result_table_2': [],
        'calculator_result_status': None,
    }
    if request.method == 'GET':
        for index, item in enumerate(Tools.ONE_REP_MAX_PERCENTAGES):
            data['result_table_2'].append(
                {'percentage': item, 'reps_of_1rm': index + 1}
            )

        return render(request=request, template_name='calculators/one rep max calculator.html', context=data)
    elif request.method == 'POST':
        result = Tools.calculate_one_rep_max(
            float(request.POST['liftmass']),
            int((request.POST['repetitions']))
        )
        max_percentage = 100
        data['result_number'] = result
        data['calculator_result_status'] = Status.OK

        # Populate Table 1 with content
        for item in Tools.ONE_REP_MAX_REPS:
            data['result_table_1'].append(
                {'percentage': max_percentage, 'liftmass': round(result * max_percentage / 100, 1), 'reps_of_1rm': item}
            )
            max_percentage -= 5

        # Populate Table 2 with content
        for index, item in enumerate(Tools.ONE_REP_MAX_PERCENTAGES):
            data['result_table_2'].append(
                {'percentage': item, 'liftmass': round(result * item / 100, 1), 'reps_of_1rm': index + 1}
            )
        return render(request=request, template_name='calculators/one rep max calculator.html', context=data)


@login_required
@require_http_methods(['GET', 'POST'])
def handle_plate_barbell_racking_calculator(request):
    data = {
        'title': '플레이트 바벨 건 드리는 계산기',
        'at_calculators': True,

        'total_lift_mass': 20,
        'fail_lift_mass': None,
        'fail_lift_mass_difference': None,
        'bar_weight': 20,
        'num_of_plates': None,
        'plates_data': None,
        'plate_quantity_2_5': 10,
        'plate_quantity_5': 10,
        'plate_quantity_10': 10,
        'plate_quantity_15': 10,
        'plate_quantity_20': 10,
        'plate_quantity_25': 0,
        'calculator_result_status': None,
    }
    if request.method == 'POST':
        total_lift = float(request.POST['liftmass'])
        bar_weight = float(request.POST['barliftmass'])
        plate_quantity_2_5 = int(request.POST['plate_quantity_2_5'])
        plate_quantity_5 = int(request.POST['plate_quantity_5'])
        plate_quantity_10 = int(request.POST['plate_quantity_10'])
        plate_quantity_15 = int(request.POST['plate_quantity_15'])
        plate_quantity_20 = int(request.POST['plate_quantity_20'])
        plate_quantity_25 = int(request.POST['plate_quantity_25'])
        plates = [
            (25, plate_quantity_25),
            (20, plate_quantity_20),
            (15, plate_quantity_15),
            (10, plate_quantity_10),
            (5, plate_quantity_5),
            (2.5, plate_quantity_2_5)
        ]
        plates_data = {}

        initial_weight_on_one_side = (total_lift - bar_weight) / 2
        weight_one_side = initial_weight_on_one_side

        for item in plates:
            stop = False
            current_plate_num = item[1]
            while not stop and current_plate_num > 0:
                if weight_one_side - item[0] >= 0:
                    weight_one_side = weight_one_side - item[0]
                    if not plates_data.get(str(item[0])):
                        plates_data[str(item[0])] = 1
                    else:
                        plates_data[str(item[0])] += 1
                    current_plate_num -= 1
                else:
                    stop = True

        if weight_one_side != 0:
            data['calculator_result_status'] = Status.FAIL
            data['fail_lift_mass'] = total_lift - 2 * weight_one_side
            data['fail_lift_mass_difference'] = total_lift - data['fail_lift_mass']

        print(plates_data)
        # Construct data
        data['total_lift_mass'] = total_lift
        data['bar_weight'] = bar_weight
        data['num_of_plates'] = sum(plates_data.values())
        data['plates_data'] = plates_data
        data['plate_quantity_2_5'] = plate_quantity_2_5
        data['plate_quantity_5'] = plate_quantity_5
        data['plate_quantity_10'] = plate_quantity_10
        data['plate_quantity_15'] = plate_quantity_15
        data['plate_quantity_20'] = plate_quantity_20
        data['plate_quantity_25'] = plate_quantity_25
        data['calculator_result_status'] = Status.OK

    return render(request=request, template_name='calculators/plate barbell racking calculator.html', context=data)


@login_required
@require_http_methods(['GET', 'POST'])
def handle_wilks_calculator(request):
    data = {
        'title': 'Wilks 계산기',
        'at_calculators': True,

        'wilks_score': None,
        'gender': None,
        'body_weight': None,
        'total_lift_mass': None,
        'wilks_score_boundaries': None,
        'calculator_result_status': None,
    }
    if request.method == 'POST':
        gender = request.POST['gender']
        body_weight = float(request.POST['bodymass'])
        input_method = request.POST['method']
        if input_method == 'total':
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

        wilks_score = Tools.calculate_wilks_score(str(gender).upper(), body_weight, total_lift_mass)

        # Construct the resulting data
        data['wilks_score'] = wilks_score
        data['body_weight'] = body_weight
        data['gender'] = gender
        data['total_lift_mass'] = total_lift_mass
        data['calculator_result_status'] = Status.OK

    return render(request=request, template_name='calculators/wilks calculator.html', context=data)


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
            day = int(request.POST['birthday'][:2])
            month = int(request.POST['birthday'][2:4])
            year = int(request.POST['birthday'][4:])
            if 1930 < year < datetime.now().year and 0 < month < 13 and 0 < day < 32:
                preferences.date_of_birth = datetime.now().replace(year=year, month=month, day=day, hour=0, minute=0,
                                                                   second=0, microsecond=0)
        if 'share' in request.POST:
            preferences.shared_profile = True if request.POST['share'] == 'true' else False
        if 'oldpassword' in request.POST and 'newpassword' in request.POST and 'repeatpassword' in request.POST and \
                request.POST['newpassword'] == request.POST['repeatpassword']:
            if request.user.check_password(raw_password=request.POST['oldpassword']):
                request.user.set_password(request.POST['newpassword'])
                request.user.save()
        preferences.save()

    return render(request=request, template_name='settings.html', context={
        'title': '설정',
        'preferences': preferences,
        'gender': models.Preferences.Gender,
        'at_settings': True
    })


@require_http_methods(['GET', 'POST'])
def handle_password_reset(request):
    if request.method == 'GET':
        # param check
        if 'k' not in request.GET:
            return redirect(to='login')
        else:
            session_key = request.GET['k']
        # session_key check
        if not api_models.SessionKey.objects.filter(key=session_key).exists():
            return redirect(to='login')
        # render reset password html
        return render(request=request, template_name='resetPassword.html', context={
            'title': '잊어버린 비밀번호 변경',
            'sessionKey': session_key
        })
    else:
        # param check
        if 'sessionKey' not in request.POST or 'new_password' not in request.POST:
            return redirect(to='login')
        else:
            session_key = request.POST['sessionKey']
            new_password = request.POST['new_password']
        # session_key check
        if not api_models.SessionKey.objects.filter(key=session_key).exists():
            return redirect(to='login')
        else:
            user = api_models.SessionKey.objects.get(key=session_key).user
        # check password length
        if len(new_password) < 4:
            return redirect(to='login')
        # update password
        user.set_password(new_password)
        user.save()
        authenticate(request, username=user.username, password=new_password)
        login(request=request, user=user)
        return redirect(to='login')


@login_required
@require_http_methods(['POST'])
def handle_add_workout(request):
    try:
        claimed_exercises = json.loads(request.POST['exercises'])
        exercises = []
        for exercise in claimed_exercises:
            if models.Exercise.objects.filter(name=exercise['exerciseName']).exists():
                exercises += [exercise]
        if len(exercises) == 0:
            return JsonResponse(data={'success': False, 'error': 'empty or invalid exercises provided'})
    except json.JSONDecodeError or TypeError as e:
        return JsonResponse(data={'success': False, 'error': str(e)})

    # create workout session
    db_workout = models.WorkoutSession.objects.create(user=request.user, title=request.POST['title'], duration=int(request.POST['duration']))
    db_workout.save()
    # create lifts
    for exercise in exercises:
        db_exercise = models.Exercise.objects.get(name=exercise['exerciseName'])
        lift_mass = float(exercise['liftMass'])
        repetitions = int(float(exercise['repetitions']))
        models.Lift.objects.create(
            exercise=db_exercise,
            workout_session=db_workout,
            lift_mass=lift_mass,
            repetitions=repetitions,
            one_rep_max=Tools.calculate_one_rep_max(lift_mass, repetitions)
        )

    return JsonResponse(data={'success': True})


@login_required
@require_http_methods(['GET'])
def handle_calendar(request):
    if not api_models.SessionKey.objects.filter(user=request.user).exists():
        session_key = api_models.SessionKey.generate_key(email=request.user.email)
        while api_models.SessionKey.objects.filter(key=session_key).exists():
            time.sleep(0.001)
            session_key = api_models.SessionKey.generate_key(email=request.user.email)
        api_models.SessionKey.objects.create(user=request.user, key=session_key)
    else:
        session_key = api_models.SessionKey.objects.get(user=request.user).key
    return render(request=request, template_name='calendar.html', context={
        'title': '내 캘린더',
        'at_calendar': True,
        'sessionKey': session_key,
        'exercises': models.Exercise.objects.all(),
    })


@login_required
@require_http_methods(['GET'])
def handle_favorite_workouts(request):
    favorite_workout_sessions = models.FavoriteWorkout.objects.filter(user=request.user)
    workouts_by_days = {}
    for favorite_workout in favorite_workout_sessions:
        db_lifts = models.Lift.objects.filter(workout_session=favorite_workout.workout_session).order_by('id')
        day_str = favorite_workout.workout_session.get_day_str()
        for db_lift in db_lifts:
            if day_str in workouts_by_days:
                if favorite_workout.workout_session in workouts_by_days[day_str]:
                    workouts_by_days[day_str][favorite_workout.workout_session] += [db_lift]
                else:
                    workouts_by_days[day_str][favorite_workout.workout_session] = [db_lift]
            else:
                workouts_by_days[day_str] = {favorite_workout.workout_session: [db_lift]}
    if not api_models.SessionKey.objects.filter(user=request.user).exists():
        session_key = api_models.SessionKey.generate_key(email=request.user.email)
        while api_models.SessionKey.objects.filter(key=session_key).exists():
            time.sleep(0.001)
            session_key = api_models.SessionKey.generate_key(email=request.user.email)
        api_models.SessionKey.objects.create(user=request.user, key=session_key)
    else:
        session_key = api_models.SessionKey.objects.get(user=request.user).key
    # todo plot as in https://simpleisbetterthancomplex.com/tutorial/2020/01/19/how-to-use-chart-js-with-django.html
    # todo customize plot as in https://www.chartjs.org/docs/latest/charts/line.html
    return render(request=request, template_name='favoriteWorkouts.html', context={
        'title': '좋아하는 운동 불러오기',
        'at_home': True,
        'sessionKey': session_key,
        'exercises': models.Exercise.objects.all(),
        'workouts_by_days': workouts_by_days,
    })
