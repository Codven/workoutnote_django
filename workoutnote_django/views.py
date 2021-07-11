from django.utils import timezone
import random
import json
import re

from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User as django_User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.conf import settings

from utils.tools import Tools, Levels, Status
from workoutnote_django import models

LIMIT_OF_ACCEPTABLE_DATA_AMOUNT = 5


@login_required
def handle_init_exercises(request):
    if request.user.is_superuser:
        models.Exercise.init_from_csv()
    return redirect(to='index')


@login_required
def handle_generate_dummy_data(request):
    if request.user.is_superuser:
        Tools.generate_dummy_data()
    return redirect(to='index')


# region authentication
@require_http_methods(['GET', 'POST'])
def handle_login(request):
    if request.user.is_authenticated:
        return redirect(to='index')
    elif request.method == 'GET':
        return render(request=request, template_name='auth.html', context={
            'title': ''
        })
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
                    return redirect(to='index')
            else:
                return redirect(to='login')
    return redirect(to='index')


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
        elif 'verification_code' in request.POST and models.EmailConfirmationCodes.objects.filter(email=email).exists():
            expected_code = models.EmailConfirmationCodes.objects.get(email=email).verification_code
            provided_code = request.POST['verification_code']
            if provided_code == expected_code:
                models.EmailConfirmationCodes.objects.filter(email=email).delete()
                django_User.objects.create_user(username=email, password=password).save()
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
            if not models.EmailConfirmationCodes.objects.filter(email=email).exists():
                verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                email_message = EmailMessage(
                    'Workoutnote.com email verification',
                    f'Email verification code is : {verification_code}',
                    settings.EMAIL_HOST_USER,
                    [email],
                )
                email_message.fail_silently = False
                email_message.send()
                models.EmailConfirmationCodes.objects.create(email=email, verification_code=verification_code)
            return render(request=request, template_name='auth.html', context={
                'verify_now': True,
                'name': name,
                'email': email,
                'password': password
            })
    else:
        return redirect(to='index')


@login_required
@require_http_methods(['GET'])
def handle_logout(request):
    logout(request=request)
    return redirect(to='index')


# endregion

@login_required
def handle_index(request):
    if request.user.is_superuser:
        return redirect(to='logout')
    name = models.Preferences.objects.get(user=request.user).name
    db_workout_sessions = models.WorkoutSession.objects.filter(user=request.user).order_by('-timestamp')
    workouts_by_days = {}
    for db_workout_session in db_workout_sessions:
        db_lifts = models.Lift.objects.filter(workout_session=db_workout_session)
        day_str = db_workout_session.get_day_str()
        for db_lift in db_lifts:
            if day_str in workouts_by_days:
                if db_workout_session in workouts_by_days[day_str]:
                    if db_lift.exercise in workouts_by_days[day_str][db_workout_session]:
                        workouts_by_days[day_str][db_workout_session][db_lift.exercise]['count'] += 1
                        workouts_by_days[day_str][db_workout_session][db_lift.exercise]['lifts'] += [db_lift]
                    else:
                        workouts_by_days[day_str][db_workout_session][db_lift.exercise] = {'count': 1, 'lifts': [db_lift]}
                else:
                    workouts_by_days[day_str][db_workout_session] = {db_lift.exercise: {'count': 1, 'lifts': [db_lift]}}
            else:
                workouts_by_days[day_str] = {db_workout_session: {db_lift.exercise: {'count': 1, 'lifts': [db_lift]}}}
    return render(request=request, template_name='home.html', context={
        'name': name if name else request.user.username,
        'at_home': True,
        'exercises': models.Exercise.objects.all(),
        'workouts_by_days': workouts_by_days
    })


@login_required
def handle_calculators(request):
    return render(request=request, template_name='calculators/calculators.html', context={
        'title': '체력 계산기',
        'at_calculators': True,
    })


@login_required
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
        data = Tools.handle_one_rep_max_calculator_post_req(
            data,
            float(request.POST['liftmass']),
            int((request.POST['repetitions']))
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
def handle_powerlifting_calculator(request):
    data = {
        'title': '파워 리프팅 계산기',
        'at_calculators': True,

        'lvl_txt': None,
        'lvl_stars_number': None,
        'lvl_percentage': None,
        'gender': None,
        'body_weight': None,
        'total_lift_mass': None,
        'wilks_score': None,
        'lvl_boundaries': None,
        'calculator_result_status': None,
    }
    if request.method == 'POST':
        gender = request.POST['gender']
        body_weight = round(float(request.POST['bodymass']))
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

        filtered_prefs = models.Preferences.objects.filter(gender=str(gender).upper())
        if not filtered_prefs:
            data['calculator_result_status'] = Status.FAIL
            data['body_weight'] = body_weight
            data['wilks_score'] = wilks_score
            return render(request=request, template_name='calculators/powerlifting calculator.html', context=data)

        user_ids = filtered_prefs.values_list('user', flat=True)
        # TODO: check logic of data filtering
        filtered_lifts = models.Lift.objects.filter(
            body_weight=body_weight,
            user_id__in=user_ids,
            exercise__in=Tools.POWERLIFTING_EXERCISE_NAMES
        )
        if len(filtered_lifts) < LIMIT_OF_ACCEPTABLE_DATA_AMOUNT:
            data['calculator_result_status'] = Status.FAIL
            data['body_weight'] = body_weight
            data['wilks_score'] = wilks_score
            return render(request=request, template_name='calculators/powerlifting calculator.html', context=data)

        sorted_1rms_for_given_bw = list(filtered_lifts.order_by('one_rep_max').values_list('one_rep_max', flat=True))

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
        data['wilks_score'] = wilks_score
        data['lvl_boundaries'] = lvl_boundaries
        data['calculator_result_status'] = Status.OK

    return render(request=request, template_name='calculators/powerlifting calculator.html', context=data)


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
                preferences.date_of_birth = datetime.now().replace(year=year, month=month, day=day, hour=0, minute=0, second=0, microsecond=0)
        if 'share' in request.POST:
            preferences.shared_profile = True if request.POST['share'] == 'true' else False
        if 'oldpassword' in request.POST and 'newpassword' in request.POST and 'repeatpassword' in request.POST and request.POST['newpassword'] == request.POST['repeatpassword']:
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


@login_required
def handle_analyse_lift(request, lift_id):
    lift = models.Lift.objects.filter(pk=lift_id).first()
    data = {
        'lift': lift,
        'rounded_body_weight': lift.body_weight,
        'body_weight_ratio': round(lift.lift_mass / lift.body_weight, 2),
        'step1_result': None,
        'step3_result': None,
        'step4_result': None,
        'step4_lvl_standard_limit': None,
    }
    # TODO: temporarily put MALE instead of real known gender
    filtered_prefs = models.Preferences.objects.filter(gender=str('MALE').upper())
    user_ids = filtered_prefs.values_list('user', flat=True)
    # region filter data for the 1st Step
    filtered_lifts = models.Lift.objects.filter(
        exercise__name=lift.exercise.name,
        user_id__in=user_ids
    )
    if len(filtered_lifts) > LIMIT_OF_ACCEPTABLE_DATA_AMOUNT:
        sorted_1rms_for_given_bw = list(filtered_lifts.order_by('one_rep_max').values_list('one_rep_max', flat=True))
        data['step1_result'] = Tools.get_level_in_percentage(sorted_1rms_for_given_bw, lift.one_rep_max)
    # endregion

    # filter data for 3rd and 4th Steps
    filtered_lifts = filtered_lifts.filter(body_weight=round(lift.body_weight))
    if len(filtered_lifts) > LIMIT_OF_ACCEPTABLE_DATA_AMOUNT:
        sorted_1rms_for_given_bw = list(filtered_lifts.order_by('one_rep_max').values_list('one_rep_max', flat=True))
        data['step3_result'] = Tools.get_level_in_percentage(sorted_1rms_for_given_bw, lift.one_rep_max)
        lvl_boundaries = Tools.get_level_boundaries_for_bodyweight(sorted_1rms_for_given_bw)
        lvl_txt = Tools.get_string_level(lvl_boundaries, lift.one_rep_max)
        data['step4_result'] = lvl_txt
        data['lvl_standard_limit'] = int(Levels.LIMITS[lvl_txt])
    # endregion
    return render(request=request, template_name='profile/analyse lift.html', context=data)


@login_required
@require_http_methods(['GET', 'POST'])
def handle_exercises(request):
    then = timezone.now() - timedelta(days=6 * 30)
    lifts = models.Lift.objects.filter(user=request.user, timestamp__gte=then)
    plot_data = []
    if lifts.exists():
        for lift in lifts:
            plot_data += [(lift.timestamp, lift.one_rep_max)]
    plot_data.sort(key=lambda x: x[0])
    days = []
    one_rep_maxes = []
    for day, one_rep_max in plot_data:
        days += [Tools.date2str(timezone.localtime(day), readable=True)]
        one_rep_maxes += [one_rep_max]

    # todo plot as in https://simpleisbetterthancomplex.com/tutorial/2020/01/19/how-to-use-chart-js-with-django.html
    # todo customize plot as in https://www.chartjs.org/docs/latest/charts/line.html
    return render(request=request, template_name='profile/exercises.html', context={
        'days': days,
        'one_rep_maxes': one_rep_maxes
    })


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
        ).save()

    return JsonResponse(data={'success': True})
