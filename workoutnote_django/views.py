import json
import random
import re
import time
from datetime import datetime
import numpy as np

from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as django_User
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from utils.tools import Tools
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
        res = render(request=request, template_name='auth_kr.html' if 'lang' in request.GET and request.GET['lang'] == 'kr' else 'auth_en.html')
        if 'lang' in request.GET:
            res.set_cookie('lang', request.GET['lang'])
        return res
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
            return render(request=request, template_name='auth_en.html', context={
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


def handle_privacy_policy(request):
    return render(request=request, template_name='privacy policy.html')


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
    lang = request.COOKIES.get('lang')
    return render(request=request, template_name='home_kr.html' if lang is not None and lang == 'kr' else 'home_en.html', context={
        'name': name if name else request.user.username,
        'at_home': True,
        'exercises': models.Exercise.objects.all(),
        'body_parts': models.BodyPart.objects.all(),
        'sessionKey': session_key,
        'workouts_by_days': workouts_by_days
    })


@login_required
def handle_calculators(request):
    lang = request.COOKIES.get('lang')
    if not api_models.SessionKey.objects.filter(user=request.user).exists():
        session_key = api_models.SessionKey.generate_key(email=request.user.email)
        while api_models.SessionKey.objects.filter(key=session_key).exists():
            time.sleep(0.001)
            session_key = api_models.SessionKey.generate_key(email=request.user.email)
        api_models.SessionKey.objects.create(user=request.user, key=session_key)
    else:
        session_key = api_models.SessionKey.objects.get(user=request.user).key
    return render(request=request, template_name='calculators_kr.html' if lang is not None and lang == 'kr' else 'calculators_en.html', context={'at_calculators': True, 'sessionKey': session_key})


def handle_param_calculators(request, session_key, calculator, language):
    """
    :param session_key (str) - user's session key, received after authentication
    :param calculator (str) - possible options are 'deltoid_test' or 'deltoid_result' (lowercase)
    :param language (str) - possible options are 'en' or 'kr' (lowercase)
    :param request - django default i.e. provided by default
    """
    if not api_models.SessionKey.objects.filter(key=session_key).exists():
        return redirect(to='login')
    if language not in ['en', 'ru'] or calculator not in ['deltoid_test', 'deltoid_result']:
        return redirect(to='login')

    login(request=request, user=api_models.SessionKey.objects.get(key=session_key).user)
    res = render(request=request, template_name='calculators_kr.html' if language is not None and language == 'kr' else 'calculators_en.html', context={
        'at_calculators': True,
        'sessionKey': session_key,
        'init_calculator': calculator
    })
    res.set_cookie('lang', language)
    return res


@login_required
@require_http_methods(['GET', 'POST'])
def handle_settings(request):
    lang = None
    if 'lang' in request.GET:
        lang = request.GET['lang']

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

    if lang is None:
        lang = request.COOKIES.get('lang')
        return render(request=request, template_name='settings_kr.html' if lang is not None and lang == 'kr' else 'settings_en.html', context={
            'title': '설정' if lang is not None and lang == 'kr' else 'My page',
            'preferences': preferences,
            'gender': models.Preferences.Gender,
            'at_settings': True
        })
    else:
        res = render(request=request, template_name='settings_kr.html' if lang is not None and lang == 'kr' else 'settings_en.html', context={
            'title': '설정' if lang is not None and lang == 'kr' else 'My page',
            'preferences': preferences,
            'gender': models.Preferences.Gender,
            'at_settings': True
        })
        res.set_cookie('lang', request.GET['lang'])
        return res


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
        lang = request.COOKIES.get('lang')
        return render(request=request, template_name='resetPassword_kr.html' if lang is not None and lang == 'kr' else 'resetPassword_en.html', context={
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
    lang = request.COOKIES.get('lang')
    return render(request=request, template_name='calendar_kr.html' if lang is not None and lang == 'kr' else 'calendar_en.html', context={
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
    lang = request.COOKIES.get('lang')
    return render(request=request, template_name='favoriteWorkouts_kr.html' if lang is not None and lang == 'kr' else 'favoriteWorkouts_en.html', context={
        'at_home': True,
        'sessionKey': session_key,
        'exercises': models.Exercise.objects.all(),
        'workouts_by_days': workouts_by_days,
    })


@login_required
@require_http_methods(['GET'])
def handle_report(request):
    results = models.OneRepMaxResults.objects.filter(user=request.user)
    if not results.exists():
        return redirect(to='calculators')

    # allowed percentage range [10%, 90%] region
    def get_percentile(arr, threshold):
        arr = np.array(arr)
        return 10 + (sum(arr <= threshold) / len(arr)) * 72

    def float2str(number):
        return f'{number:.1f}'.replace('.0', '')

    # region load all values
    shoulder_values = []
    chest_values = []
    back_values = []
    abs_values = []
    legs_values = []
    for item in models.OneRepMaxResults.objects.all():
        shoulder_values += [item.shoulder]
        chest_values += [item.chest]
        back_values += [item.back]
        abs_values += [item.abs]
        legs_values += [item.legs]
    # endregion

    # region compute percentiles
    last_res = results.order_by('-timestamp').first()
    shoulder_percentile = get_percentile(shoulder_values, last_res.shoulder)
    chest_percentile = get_percentile(chest_values, last_res.chest)
    back_percentile = get_percentile(back_values, last_res.back)
    abs_percentile = get_percentile(abs_values, last_res.abs)
    legs_percentile = get_percentile(legs_values, last_res.legs)
    # endregion

    # region gather score history
    top_part_scores = []
    mid_part_scores = []
    legs_scores = []
    total_scores = []
    for item in models.OneRepMaxResults.objects.filter(user=request.user).order_by('-timestamp'):
        ts = int(item.timestamp.timestamp() * 1000)
        top_part_scores += [{'timestamp': ts, 'score': (item.shoulder + item.chest) / 2}]
        mid_part_scores += [{'timestamp': ts, 'score': (item.back + item.abs) / 2}]
        legs_scores += [{'timestamp': ts, 'score': item.legs}]
        total_scores += [{'timestamp': ts, 'score': item.shoulder + item.chest + item.back + item.abs + item.legs}]
        if len(total_scores) == 4:
            break
    # endregion

    return render(request=request, template_name='report_kr.html', context={
        'timestamp': int(last_res.timestamp.timestamp() * 1000),
        'name': last_res.name,
        'gender': '남성' if last_res.gender == models.OneRepMaxResults.Gender.MALE.lower() else '여성',
        'age': last_res.age,
        'height': float2str(last_res.height),
        'weight': float2str(last_res.weight),

        'shoulder': float2str(last_res.shoulder),
        'chest': float2str(last_res.chest),
        'back': float2str(last_res.back),
        'abs': float2str(last_res.abs),
        'legs': float2str(last_res.legs),

        'cumulativeScore': last_res.shoulder + last_res.chest + last_res.back + last_res.abs + last_res.legs,
        'averageScore': f'{(last_res.shoulder + last_res.chest + last_res.back + last_res.abs + last_res.legs) / 5:.1f}',

        'shoulderPercentage': shoulder_percentile,
        'chestPercentage': chest_percentile,
        'avgTopPartPercentile': (shoulder_percentile + chest_percentile) / 2,
        'avgTopPartScore': float2str((last_res.shoulder + last_res.chest) / 2),

        'backPercentage': back_percentile,
        'absPercentage': abs_percentile,
        'avgMidPartPercentile': (back_percentile + abs_percentile) / 2,
        'avgMidPartScore': float2str((last_res.back + last_res.abs) / 2),

        'legsPercentile': legs_percentile,

        'topPartScores': top_part_scores,
        'midPartScores': mid_part_scores,
        'legsScores': legs_scores,
        'totalScores': total_scores,
    })


@login_required
@require_http_methods(['GET'])
def handle_deltoid_photo_card(request):
    def float2str(number):
        return f'{number:.1f}'.replace('.0', '')

    q = models.OneRepMaxResults.objects.filter(user=request.user)
    if not q.exists():
        return redirect(to='calculators')

    last_res = q.order_by('-timestamp').first()
    lang = request.COOKIES.get('lang')
    return render(request=request, template_name='deltoid_photo_card_kr.html' if lang is not None and lang == 'kr' else 'deltoid_photo_card_en.html', context={
        'name': last_res.name,
        'gender': '남성' if last_res.gender == models.OneRepMaxResults.Gender.MALE.lower() else '여성' if lang == 'kr' else last_res.gender,
        'age': last_res.age,
        'timestamp': int(last_res.timestamp.timestamp() * 1000),

        'shoulder': float2str(last_res.shoulder),
        'chest': float2str(last_res.chest),
        'back': float2str(last_res.back),
        'abs': float2str(last_res.abs),
        'legs': float2str(last_res.legs),
        'averageScore': float2str((last_res.shoulder + last_res.chest + last_res.back + last_res.abs + last_res.legs) / 5)
    })


def handle_workout_photo_card(request, session_key, workout_id, language):
    """
    :param session_key (str) - user's session key, received after authentication
    :param workout_id (int) - id of workout to be printed
    :param language (str) - possible options are 'en' or 'kr' (lowercase)
    :param request - django default i.e. provided by default
    """
    if not api_models.SessionKey.objects.filter(key=session_key).exists():
        return redirect(to='login')
    if language not in ['en', 'kr']:
        return redirect(to='login')
    user = api_models.SessionKey.objects.get(key=session_key).user
    login(request=request, user=user)
    if not models.WorkoutSession.objects.filter(user=user, id=workout_id):
        return redirect(to='index')
    workout = models.WorkoutSession.objects.get(id=workout_id)
    all_lifts = models.Lift.objects.filter(workout_session=workout)
    total_weight = 0
    lifts_summary = {}
    for lift in all_lifts:
        total_weight += lift.lift_mass * lift.repetitions
        if lift.exercise in lifts_summary:
            lifts_summary[lift.exercise]['mass'] += lift.lift_mass
            lifts_summary[lift.exercise]['reps'] += lift.repetitions
        else:
            lifts_summary[lift.exercise] = {'mass': lift.lift_mass, 'reps': lift.repetitions}
    exercise_names = []
    lift_stats = []

    def trunc(_str, _len):
        return f'{_str[:_len]}…' if len(_str) > _len else _str

    for exercise in lifts_summary:
        exercise_names += [trunc(f'{exercise.translate(language)} ({exercise.body_part.translate(language)})', 32)]
        lift_stats += [(lifts_summary[exercise]['mass'], lifts_summary[exercise]['reps'])]

    res = render(request=request, template_name='workout_photo_card_kr.html' if language is not None and language == 'kr' else 'workout_photo_card_en.html', context={
        'timestamp': int(workout.timestamp.timestamp() * 1000),
        'title': workout.title,
        'total_weight': total_weight,

        'exercise_names': exercise_names,
        'lift_stats': lift_stats,
    })
    res.set_cookie('lang', language)
    return res
