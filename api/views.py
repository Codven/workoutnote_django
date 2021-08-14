from django.views.decorators.http import require_http_methods
from workoutnote_django import models as wn_models, settings
from django.contrib.auth.models import User as django_User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, authenticate
from django.core.mail import EmailMessage
from datetime import datetime, timedelta
from django.http import JsonResponse
from utils.tools import Tools
from api import models
import random
import time
import json
import pytz


# region auth
@csrf_exempt
@require_http_methods(['POST'])
def handle_login_api(request):
    # 0. expected and received params
    required_params = ['email', 'password']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        email = received_params['email']
        password = received_params['password']

    # 2. django authentication
    user = authenticate(username=email, password=password)
    if not user or not user.is_authenticated:
        return JsonResponse(data={'success': False, 'reason': 'authentication failure'})

    # 3. generate session key and login
    if not models.SessionKey.objects.filter(user=user).exists():
        session_key = models.SessionKey.generate_key(email=email)
        while models.SessionKey.objects.filter(key=session_key).exists():
            time.sleep(0.001)
            session_key = models.SessionKey.generate_key(email=email)
        models.SessionKey.objects.create(user=user, key=session_key)
    else:
        session_key = models.SessionKey.objects.get(user=user).key
    login(request=request, user=user)
    return JsonResponse(data={'success': True, 'sessionKey': session_key})


@csrf_exempt
@require_http_methods(['POST'])
def handle_send_verification_code_api(request):
    # 0. expected and received params
    required_params = ['email']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        email = received_params['email']

    # 2. check pre-existing email confirmation code
    if wn_models.EmailConfirmationCode.objects.filter(email=email).exists():
        wn_models.EmailConfirmationCode.objects.filter(email=email).delete()

    # 3. generate email confirmation code
    verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    email_message = EmailMessage(
        'Workoutnote.com email verification',
        f'Email verification code is : {verification_code}',
        settings.EMAIL_HOST_USER,
        [email],
    )
    email_message.fail_silently = False
    email_message.send()
    wn_models.EmailConfirmationCode.objects.create(email=email, verification_code=verification_code)
    return JsonResponse(data={'success': True})


@csrf_exempt
@require_http_methods(['POST'])
def handle_verify_register_api(request):
    # 0. expected and received params
    required_params = ['name', 'email', 'password', 'verification_code']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        name = received_params['name']
        email = received_params['email']
        password = received_params['password']
        provided_verification_code = received_params['verification_code']

    # 2. expected email verification code check
    if not wn_models.EmailConfirmationCode.objects.filter(email=email).exists():
        return JsonResponse(data={'success': False, 'reason': 'user already exists or password is too short'})
    else:
        email_confirmation = wn_models.EmailConfirmationCode.objects.get(email=email)

    # 3. pre-existing user and password length check
    if django_User.objects.filter(username=email).exists() or len(password) < 4:
        return JsonResponse(data={'success': False, 'reason': 'user already exists or password is too short'})

    # 4. verify and register
    if provided_verification_code == email_confirmation.verification_code:
        email_confirmation.delete()
        django_User.objects.create_user(username=email, password=password)
        user = authenticate(request, username=email, password=password)
        if user:
            wn_models.Preferences.objects.create(user=user, name=name)
            return JsonResponse(data={'success': True})
        else:
            return JsonResponse(data={'success': False, 'reason': 'Unknown, please contact backend developer!'})  # whatever the reason could be
    else:
        return JsonResponse(data={'success': False, 'reason': 'incorrect verification code'})


# endregion


# region settings
@csrf_exempt
@require_http_methods(['POST'])
def handle_fetch_settings_api(request):
    # 0. expected and received params
    required_params = ['sessionKey']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. fix preferences (if not exists for some reason*)
    if not wn_models.Preferences.objects.filter(user=user).exists():
        wn_models.Preferences.objects.create(user=user)

    # 4. fetch preferences
    preferences = wn_models.Preferences.objects.get(user=user)
    return JsonResponse(data={
        'success': True,
        'name': preferences.name,
        'date_of_birth': preferences.date_of_birth,
        'gender': preferences.gender,
        'is_profile_shared': preferences.shared_profile,
    })


@csrf_exempt
@require_http_methods(['POST'])
def handle_update_settings_api(request):
    # 0. expected and received params
    required_params = ['sessionKey', 'new_name', 'new_date_of_birth', 'new_gender', 'new_is_profile_shared']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']
        new_name = received_params['new_name']
        new_date_of_birth = received_params['new_date_of_birth']
        new_gender = received_params['new_gender']
        new_is_profile_shared = received_params['new_is_profile_shared']

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. fix preferences (if not exists for some reason*)
    if not wn_models.Preferences.objects.filter(user=user).exists():
        wn_models.Preferences.objects.create(user=user)

    # 4. update preferences
    preferences = wn_models.Preferences.objects.get(user=user)
    preferences.name = new_name
    preferences.date_of_birth = new_date_of_birth
    preferences.gender = new_gender
    preferences.shared_profile = new_is_profile_shared
    preferences.save()
    return JsonResponse(data={'success': True})


@csrf_exempt
@require_http_methods(['POST'])
def handle_send_reset_password_email_api(request):
    # 0. expected and received params
    required_params = ['email']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        email = received_params['email']

    # 2. check user and session_key
    if not django_User.objects.filter(username=email).exists():
        return JsonResponse(data={'success': False, 'reason': 'user does not exist'})
    else:
        user = django_User.objects.get(username=email)
    if not models.SessionKey.objects.filter(user__username=email).exists():
        session_key = models.SessionKey.generate_key(email=email)
        while models.SessionKey.objects.filter(key=session_key).exists():
            time.sleep(0.001)
            session_key = models.SessionKey.generate_key(email=email)
        models.SessionKey.objects.create(user=user, key=session_key)
    else:
        session_key = models.SessionKey.objects.get(user=user).key

    # 3. generate email confirmation code
    email_message = EmailMessage(
        'Workoutnote.com password reset link (do not share this!)',
        f'Please proceed to the following link if you forgot your password, and would like to change it.\nhttps://workoutnote.com/reset_password/?k={session_key}"',
        settings.EMAIL_HOST_USER,
        [email],
    )
    email_message.fail_silently = False
    email_message.send()
    return JsonResponse(data={'success': True})


# endregion


# region exercises & body parts
@csrf_exempt
@require_http_methods(['POST'])
def handle_fetch_exercises_api(request):
    exercises = wn_models.Exercise.objects.all()
    exercises_arr = []
    for exercise in exercises:
        exercises_arr += [{
            'id': exercise.id,
            'name': exercise.name,
            'name_translations': exercise.name_translations,
            'body_part_str': exercise.body_part.name,
            'category_str': exercise.category.name,
            'icon_str': exercise.icon.name,
        }]
    return JsonResponse(data={
        'success': True,
        'exercises': exercises_arr
    })


@csrf_exempt
@require_http_methods(['POST'])
def handle_fetch_body_parts_api(request):
    body_parts = wn_models.BodyPart.objects.all()
    body_parts_arr = []
    for body_part in body_parts:
        body_parts_arr += [{
            'id': body_part.id,
            'name': body_part.name,
        }]
    return JsonResponse(data={
        'success': True,
        'body_parts': body_parts_arr
    })


# endregion


# region workout
@csrf_exempt
@require_http_methods(['POST'])
def handle_insert_workout_api(request):
    # 0. expected and received params
    required_params = ['sessionKey', 'title', 'duration']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']
        title = received_params['title']
        duration = int(received_params['duration'])
        timestamp = int(datetime.now().timestamp() * 1000)

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. create workout session
    workout_session = wn_models.WorkoutSession.objects.create(user=user, timestamp=timestamp, title=title, duration=duration)
    return JsonResponse(data={
        'success': True,
        'workout_session': {
            'id': workout_session.id,
            'title': workout_session.title,
            'timestamp': int(workout_session.timestamp.timestamp() * 1000),
            'duration': workout_session.duration,
        }
    })


@csrf_exempt
def handle_fetch_workouts_api(request):
    # 0. expected and received params
    required_params = ['sessionKey', 'fromTimestampMs', 'tillTimestampMs']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']
        date_from_ts = datetime.utcfromtimestamp(int(received_params['fromTimestampMs']) / 1000)
        date_till_ts = datetime.utcfromtimestamp(int(received_params['tillTimestampMs']) / 1000)

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. fetch workouts
    workout_sessions = []
    for workout_session in wn_models.WorkoutSession.objects.filter(user=user, timestamp__gte=date_from_ts, timestamp__lt=date_till_ts):
        lifts = []
        for lift in wn_models.Lift.objects.filter(workout_session=workout_session):
            lifts += [{
                'id': lift.id,
                'timestamp': int(lift.timestamp.timestamp() * 1000),
                'one_rep_max': lift.one_rep_max,
                'exercise_id': lift.exercise.id,
                'exercise_name': lift.exercise.name,
                'exercise_name_translations': lift.exercise.name_translations,
                'lift_mass': lift.lift_mass,
                'repetitions': lift.repetitions,
            }]
        workout_sessions += [
            {
                'id': workout_session.id,
                'title': workout_session.title,
                'timestamp': int(workout_session.timestamp.timestamp() * 1000),
                'duration': workout_session.duration,
                'isFavorite': wn_models.FavoriteWorkout.objects.filter(user=user, workout_session=workout_session).exists(),
                'lifts': lifts
            }
        ]
    return JsonResponse(data={
        'success': True,
        'workouts': workout_sessions,
    })


@csrf_exempt
def handle_update_workout_api(request):
    # 0. expected and received params
    required_params = ['sessionKey', 'workout_session_id', 'new_title', 'new_duration']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']
        workout_session_id = received_params['workout_session_id']
        new_title = received_params['new_title']
        new_duration = received_params['new_duration']

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. workout_session_id check
    if not wn_models.WorkoutSession.objects.filter(id=workout_session_id, user=user).exists():
        return JsonResponse(data={'success': False, 'reason': f'invalid workoutSessionId({received_params["workoutSessionId"]}), please double check the value'})
    else:
        workout_session = wn_models.WorkoutSession.objects.get(id=workout_session_id, user=user)

    # 4. update workout session
    workout_session.title = new_title
    workout_session.duration = new_duration
    workout_session.save()
    return JsonResponse(data={
        'success': True,
        'workout_session': {
            'id': workout_session.id,
            'title': workout_session.title,
            'timestamp': int(workout_session.timestamp.timestamp() * 1000),
            'duration': workout_session.duration,
        }
    })


@csrf_exempt
def handle_remove_workout_api(request):
    # 0. expected and received params
    required_params = ['sessionKey', 'workout_session_id']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']
        workout_session_id = received_params['workout_session_id']

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. workout_session_id check
    if not wn_models.WorkoutSession.objects.filter(id=workout_session_id, user=user).exists():
        return JsonResponse(data={'success': False, 'reason': f'invalid workoutSessionId({received_params["workoutSessionId"]}), please double check the value'})
    else:
        workout_session = wn_models.WorkoutSession.objects.get(id=workout_session_id, user=user)

    # 4. remove workout session
    workout_session.delete()
    return JsonResponse(data={
        'success': True,
        'removed_workout_session': {
            'id': workout_session.id,
            'title': workout_session.title,
            'timestamp': int(workout_session.timestamp.timestamp() * 1000),
            'duration': workout_session.duration,
        }
    })


# endregion


# region calendar
@csrf_exempt
@require_http_methods(['POST'])
def handle_fetch_workout_days(request):
    # 0. expected and received params
    required_params = ['sessionKey', 'timezoneOffsetMinutes']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']
        timezone_offset_minutes = int(received_params['timezoneOffsetMinutes'])

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. fetch workout days
    workout_sessions = wn_models.WorkoutSession.objects.filter(user=user)
    workout_days = set()
    tss = set()
    if workout_sessions.exists():
        for workout_session in workout_sessions:
            timestamp = workout_session.timestamp - timedelta(minutes=timezone_offset_minutes)
            workout_days.add(f'{timestamp.year}/{timestamp.month}/{timestamp.day}')
    return JsonResponse(data={'success': True, 'workoutDays': list(workout_days)})


# endregion


# region lifts
@csrf_exempt
@require_http_methods(['POST'])
def handle_insert_lift_api(request):
    # 0. expected and received params
    required_params = ['sessionKey', 'workout_session_id', 'exercise_id', 'lift_mass', 'repetitions']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']
        workout_session_id = int(received_params['workout_session_id'])
        exercise_id = int(received_params['exercise_id'])
        lift_mass = float(received_params['lift_mass'])
        repetitions = int(received_params['repetitions'])

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. workout_session_id check
    if not wn_models.WorkoutSession.objects.filter(id=workout_session_id, user=user).exists():
        return JsonResponse(data={'success': False, 'reason': f'invalid workoutSessionId({workout_session_id}), please double check the value'})
    else:
        workout_session = wn_models.WorkoutSession.objects.get(id=workout_session_id, user=user)

    # 4. exercise_id check
    if not wn_models.Exercise.objects.filter(id=exercise_id).exists():
        return JsonResponse(data={'success': False, 'reason': f'invalid exerciseId({exercise_id}), please double check the value'})
    else:
        exercise = wn_models.Exercise.objects.get(id=exercise_id)

    # 5. create lift
    lift = wn_models.Lift.objects.create(
        timestamp=int(datetime.now().timestamp() * 1000),
        workout_session=workout_session,
        exercise=exercise,
        lift_mass=lift_mass,
        repetitions=repetitions,
        one_rep_max=Tools.calculate_one_rep_max(lift_mass=lift_mass, repetitions=repetitions),
    )
    return JsonResponse(data={
        'success': True,
        'lift': {
            'id': lift.id,
            'timestamp': int(lift.timestamp.timestamp() * 1000),
            'exercise_id': lift.exercise.id,
            'exercise_name': lift.exercise.name,
            'workout_session_id': lift.workout_session.id,
            'lift_mass': lift.lift_mass,
            'repetitions': lift.repetitions,
            'one_rep_max': lift.one_rep_max,
        }
    })


@csrf_exempt
@require_http_methods(['POST'])
def handle_update_lift_api(request):
    # 0. expected and received params
    required_params = ['sessionKey', 'workout_session_id', 'lift_id', 'new_exercise_id', 'new_lift_mass', 'new_repetitions']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']
        workout_session_id = int(received_params['workout_session_id'])
        lift_id = int(received_params['lift_id'])
        new_exercise_id = int(received_params['new_exercise_id'])
        new_lift_mass = float(received_params['new_lift_mass'])
        new_repetitions = int(received_params['new_repetitions'])

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. workout_session_id check
    if not wn_models.WorkoutSession.objects.filter(id=workout_session_id, user=user).exists():
        return JsonResponse(data={'success': False, 'reason': f'invalid workoutSessionId({workout_session_id}), please double check the value'})
    else:
        workout_session = wn_models.WorkoutSession.objects.get(id=workout_session_id, user=user)

    # 4. lift_id check
    if not wn_models.Lift.objects.filter(id=lift_id, workout_session=workout_session).exists():
        return JsonResponse(data={'success': False, 'reason': f'invalid liftId({lift_id}), please double check the value'})
    else:
        lift = wn_models.Lift.objects.get(id=lift_id, workout_session=workout_session)

    # 5. new_exercise_id check
    if not wn_models.Exercise.objects.filter(id=new_exercise_id).exists():
        return JsonResponse(data={'success': False, 'reason': f'invalid exerciseId({new_exercise_id}), please double check the value'})
    else:
        new_exercise = wn_models.Exercise.objects.get(id=new_exercise_id)

    # 6. update lift
    lift.exercise = new_exercise
    lift.lift_mass = new_lift_mass
    lift.repetitions = new_repetitions
    lift.save()
    return JsonResponse(data={
        'success': True,
        'lift': {
            'id': lift.id,
            'timestamp': int(lift.timestamp.timestamp() * 1000),
            'exercise_id': lift.exercise.id,
            'exercise_name': lift.exercise.name,
            'workout_session_id': lift.workout_session.id,
            'lift_mass': lift.lift_mass,
            'repetitions': lift.repetitions,
            'one_rep_max': lift.one_rep_max,
        }
    })


@csrf_exempt
@require_http_methods(['POST'])
def handle_remove_lift_api(request):
    # 0. expected and received params
    required_params = ['sessionKey', 'workout_session_id', 'lift_id']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']
        workout_session_id = int(received_params['workout_session_id'])
        lift_id = int(received_params['lift_id'])

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. workout_session_id check
    if not wn_models.WorkoutSession.objects.filter(id=workout_session_id, user=user).exists():
        return JsonResponse(data={'success': False, 'reason': f'invalid workoutSessionId({workout_session_id}), please double check the value'})
    else:
        workout_session = wn_models.WorkoutSession.objects.get(id=workout_session_id, user=user)

    # 4. lift_id check
    if not wn_models.Lift.objects.filter(id=lift_id, workout_session=workout_session).exists():
        return JsonResponse(data={'success': False, 'reason': f'invalid liftId({lift_id}), please double check the value'})
    else:
        lift = wn_models.Lift.objects.get(id=lift_id, workout_session=workout_session)

    # 5. remove lift
    lift.delete()
    return JsonResponse(data={
        'success': True,
        'lift': {
            'id': lift.id,
            'timestamp': int(lift.timestamp.timestamp() * 1000),
            'exercise_id': lift.exercise.id,
            'exercise_name': lift.exercise.name,
            'workout_session_id': lift.workout_session.id,
            'lift_mass': lift.lift_mass,
            'repetitions': lift.repetitions,
            'one_rep_max': lift.one_rep_max,
        }
    })


# endregion


# region favorites

@csrf_exempt
@require_http_methods(['POST'])
def handle_set_favorite_exercise_api(request):
    # 0. expected and received params
    required_params = ['sessionKey', 'exercise_id']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']
        exercise_id = int(received_params['exercise_id'])

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. exercise_id check
    if not wn_models.Exercise.objects.filter(id=exercise_id).exists():
        return JsonResponse(data={'success': False, 'reason': f'invalid exerciseId({exercise_id}), please double check the value'})
    else:
        exercise = wn_models.Exercise.objects.get(id=exercise_id)

    # 4. set exercise as favorite
    if not wn_models.FavoriteExercise.objects.filter(user=user, exercise=exercise).exists():
        wn_models.FavoriteExercise.objects.create(user=user, exercise=exercise)
    return JsonResponse(data={'success': True})


@csrf_exempt
@require_http_methods(['POST'])
def handle_unset_favorite_exercise_api(request):
    # 0. expected and received params
    required_params = ['sessionKey', 'exercise_id']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']
        exercise_id = int(received_params['exercise_id'])

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. exercise_id check
    if not wn_models.Exercise.objects.filter(id=exercise_id).exists():
        return JsonResponse(data={'success': False, 'reason': f'invalid exerciseId({exercise_id}), please double check the value'})
    else:
        exercise = wn_models.Exercise.objects.get(id=exercise_id)

    # 4. set exercise as favorite
    if wn_models.FavoriteExercise.objects.filter(user=user, exercise=exercise).exists():
        wn_models.FavoriteExercise.objects.filter(user=user, exercise=exercise).delete()
    return JsonResponse(data={'success': True})


@csrf_exempt
@require_http_methods(['POST'])
def handle_fetch_favorite_exercises_api(request):
    # 0. expected and received params
    required_params = ['sessionKey']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. fetch favorite exercises
    exercises_arr = []
    for favorite_exercise in wn_models.FavoriteExercise.objects.filter(user=user):
        exercises_arr += [{
            'id': favorite_exercise.exercise.id,
            'name': favorite_exercise.exercise.name,
            'name_translations': favorite_exercise.exercise.name_translations,
            'body_part_str': favorite_exercise.exercise.body_part.name,
            'category_str': favorite_exercise.exercise.category.name,
            'icon_str': favorite_exercise.exercise.icon.name,
        }]
    return JsonResponse(data={
        'success': True,
        'exercises': exercises_arr
    })


@csrf_exempt
@require_http_methods(['POST'])
def handle_set_favorite_workout_api(request):
    # 0. expected and received params
    required_params = ['sessionKey', 'workout_session_id']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']
        workout_session_id = int(received_params['workout_session_id'])

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. workout_session_id check
    if not wn_models.WorkoutSession.objects.filter(id=workout_session_id, user=user).exists():
        return JsonResponse(data={'success': False, 'reason': f'invalid workoutSessionId({workout_session_id}), please double check the value'})
    else:
        workout_session = wn_models.WorkoutSession.objects.get(id=workout_session_id, user=user)

    # 4. set workout session as favorite
    if not wn_models.FavoriteWorkout.objects.filter(user=user, workout_session=workout_session).exists():
        wn_models.FavoriteWorkout.objects.create(user=user, workout_session=workout_session)
    return JsonResponse(data={'success': True})


@csrf_exempt
@require_http_methods(['POST'])
def handle_unset_favorite_workout_api(request):
    # 0. expected and received params
    required_params = ['sessionKey', 'workout_session_id']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']
        workout_session_id = int(received_params['workout_session_id'])

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. workout_session_id check
    if not wn_models.WorkoutSession.objects.filter(id=workout_session_id, user=user).exists():
        return JsonResponse(data={'success': False, 'reason': f'invalid workoutSessionId({workout_session_id}), please double check the value'})
    else:
        workout_session = wn_models.WorkoutSession.objects.get(id=workout_session_id, user=user)

    # 4. set workout session as favorite
    if wn_models.FavoriteWorkout.objects.filter(user=user, workout_session=workout_session).exists():
        wn_models.FavoriteWorkout.objects.filter(user=user, workout_session=workout_session).delete()
    return JsonResponse(data={'success': True})


@csrf_exempt
@require_http_methods(['POST'])
def handle_fetch_favorite_workouts_api(request):
    # 0. expected and received params
    required_params = ['sessionKey']
    received_params = json.loads(request.body.decode('utf8'))

    # 1. all params check
    if False in [x in received_params for x in required_params]:
        return JsonResponse(data={'success': False, 'reason': f'bad params, must provide {",".join(required_params)}'})
    else:
        session_key = received_params['sessionKey']

    # 2. sessionKey check
    if not models.SessionKey.objects.filter(key=session_key).exists():
        return JsonResponse(data={'success': False, 'reason': 'double check sessionKey value'})
    else:
        user = models.SessionKey.objects.get(key=session_key).user

    # 3. fetch favorite workouts
    workout_sessions_arr = []
    for favorite_workout in wn_models.FavoriteWorkout.objects.filter(user=user):
        lifts_arr = []
        for lift in wn_models.Lift.objects.filter(workout_session=favorite_workout.workout_session):
            lifts_arr += [{
                'id': lift.id,
                'timestamp': int(lift.timestamp.timestamp() * 1000),
                'one_rep_max': lift.one_rep_max,
                'exercise_id': lift.exercise.id,
                'exercise_name': lift.exercise.name,
                'exercise_name_translations': lift.exercise.name_translations,
                'lift_mass': lift.lift_mass,
                'repetitions': lift.repetitions,
            }]
        workout_sessions_arr += [{
            'id': favorite_workout.workout_session.id,
            'title': favorite_workout.workout_session.title,
            'timestamp': int(favorite_workout.workout_session.timestamp.timestamp() * 1000),
            'duration': favorite_workout.workout_session.duration,
            'lifts': lifts_arr
        }]
    return JsonResponse(data={
        'success': True,
        'workoutSessions': workout_sessions_arr
    })
# endregion
