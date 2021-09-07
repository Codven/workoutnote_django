import json
import random
import re
import time
from datetime import datetime

from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as django_User
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import render, redirect
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
        'sessionKey': session_key,
        'workouts_by_days': workouts_by_days
    })


@login_required
def handle_calculators(request):
    return render(request=request, template_name='calculators.html', context={'at_calculators': True, })


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
    workouts_by_days = {}
    for db_workout_session in models.WorkoutSession.objects.filter(user=request.user).order_by('-timestamp'):
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
    return render(request=request, template_name='calendar.html', context={
        'at_calendar': True,
        'sessionKey': session_key,
        'exercises': models.Exercise.objects.all(),
        'workouts_by_days': workouts_by_days
    })


@login_required
@require_http_methods(['GET'])
def handle_favorite_workouts(request):
    favorite_workout_sessions = models.FavoriteWorkout.objects.filter(user=request.user)
    # map day->workout->lift
    temp = {}
    for favorite_workout in favorite_workout_sessions:
        db_lifts = models.Lift.objects.filter(workout_session=favorite_workout.workout_session).order_by('id')
        day_str = favorite_workout.workout_session.get_day_str()
        for db_lift in db_lifts:
            if day_str in temp:
                if favorite_workout.workout_session in temp[day_str]:
                    temp[day_str][favorite_workout.workout_session] += [db_lift]
                else:
                    temp[day_str][favorite_workout.workout_session] = [db_lift]
            else:
                temp[day_str] = {favorite_workout.workout_session: [db_lift]}
    # copy & sort by recency
    workouts_by_days = []
    for day_str in temp:
        workout_sessions = []
        for workout_session in temp[day_str]:
            workout_sessions += [(workout_session, temp[day_str][workout_session])]
        workout_sessions.sort(key=lambda x: x[0].timestamp, reverse=True)
        workouts_by_days += [(day_str, workout_sessions)]
    workouts_by_days.sort(key=lambda x: x[0], reverse=True)

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
        'at_home': True,
        'sessionKey': session_key,
        'exercises': models.Exercise.objects.all(),
        'workouts_by_days': workouts_by_days,
    })
