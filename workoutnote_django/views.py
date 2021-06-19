from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from random import randint
from utils import utils
from . import models


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
            if user:
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
        return redirect(to='index')
    elif request.method == 'GET':
        return render(request=request, template_name='index/auth register.html')
    elif 'email' in request.POST and 'password' in request.POST:
        email = request.POST['email']
        password = request.POST['password']
        if User.objects.filter(username=email).exists() or len(password) < 4 or models.EmailVerificationRequests.objects.filter(email=email).exists():
            return redirect(to='register')
        else:
            User.objects.create_user(username=email, password=password).save()
            user = authenticate(request, username=email, password=password)
            if user:
                verification_code = ''.join([str(randint(0, 9)) for _ in range(6)])
                message = utils.create_message(
                    sender='deltoidsoft@gmail.com',
                    to=request.user.username,
                    subject='[Workoutnote registration] email verification code',
                    message_text=f'Your email verification code is : {verification_code}'
                )
                utils.send_email(target_email=user.username, message=message)
                models.EmailVerificationRequests.objects.create(email=email, verification_code=verification_code).save()
                login(request=request, user=user)
                return redirect(to='email confirmation')
            else:
                return redirect(to='register')  # whatever the reason could be
    else:
        return redirect(to='index')


@login_required
@require_http_methods(['GET', 'POST'])
def handle_email_confirmation(request):
    if request.method == 'GET':
        return render(request=request, template_name='index/email confirmation.html')
    elif 'code' in request.POST and models.EmailVerificationRequests.objects.filter(email=request.user.username).exists():
        verification = models.EmailVerificationRequests.objects.get(email=request.user.username)
        if verification.verification_code == request.POST['code']:
            request.user.email = request.user.username
            request.user.save()
            if 'next' in request.POST and len(request.POST['next']) > 0:
                return redirect(to=request.POST['next'])
            else:
                return redirect(to='profile main')
        else:
            return redirect(to='email confirmation')
    return redirect(to='index')


@login_required
@require_http_methods(['GET'])
def handle_logout(request):
    logout(request=request)
    return redirect(to='index')


# endregion


def handle_faq(request):
    return render(request=request, template_name='index/faq.html')


def handle_about(request):
    return render(request=request, template_name='index/about.html')


def handle_index(request):
    return render(request=request, template_name='index/index.html')


def handle_calculators(request):
    return render(request=request, template_name='index/calculators.html')


def handle_strength_standards(request):
    return render(request=request, template_name='index/strength standards.html')


def handle_training_log_tutorial(request):
    return render(request=request, template_name='index/training log tutorial.html')


def handle_one_rep_max_calculator(request):
    return render(request=request, template_name='index/one rep max calculator.html')


def handle_plate_barbell_racking_calculator(request):
    return render(request=request, template_name='index/plate barbell racking calculator.html')


def handle_powerlifting_calculator(request):
    return render(request=request, template_name='index/powerlifting calculator.html')


def handle_wilks_calculator(request):
    return render(request=request, template_name='index/wilks calculator.html')


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


def handle_workouts(request):
    return render(request=request, template_name='profile/workouts.html')


def handle_lifts(request):
    return render(request=request, template_name='profile/lifts.html')


def handle_exercises(request):
    return render(request=request, template_name='profile/exercises.html')
