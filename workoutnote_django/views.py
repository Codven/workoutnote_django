from django.shortcuts import render
from django.template.response import TemplateResponse


def handle_index(request):
    return render(request=request, template_name='index/index.html')


def handle_calculators(request):
    return render(request=request, template_name='index/calculators.html')


def handle_strength_standards(request):
    return render(request=request, template_name='index/strength standards.html')


def handle_training_log_tutorial(request):
    return render(request=request, template_name='index/training log tutorial.html')


def handle_login_register(request):
    data = {
        'title': 'Log In',
        'subtitle': 'Need an account?',
        'subtitle_link': '/register',
        'subtitle_link_text': 'Register',
        'button_text': 'Log In',
        'forgot_password_link': '/forgot-password',
        'forgot_password_text': 'Forgot password?'
    }
    if request.path == '/register/':
        data['title'] = 'Register'
        data['subtitle'] = 'Already have an account?'
        data['subtitle_link'] = '/login'
        data['subtitle_link_text'] = 'Log In'
        data['button_text'] = 'Register'
        data['forgot_password_link'] = ''
        data['forgot_password_text'] = ''

    return TemplateResponse(request=request, template='index/sub html authentication.html', context=data)


def handle_one_rep_max_calculator(request):
    return render(request=request, template_name='index/one rep max calculator.html')


def handle_plate_barbell_racking_calculator(request):
    return render(request=request, template_name='index/plate barbell racking calculator.html')


def handle_powerlifting_calculator(request):
    return render(request=request, template_name='index/powerlifting calculator.html')


def handle_wilks_calculator(request):
    return render(request=request, template_name='index/wilks calculator.html')


def handle_login(request):
    return render(request=request, template_name='index/login.html')


def handle_register(request):
    return render(request=request, template_name='index/register.html')


def handle_profile_main(request):
    return render(request=request, template_name='profile/main.html')


def handle_settings(request):
    return render(request=request, template_name='profile/settings.html')


def handle_analyse_lift(request):
    return render(request=request, template_name='profile/analyse lift.html')

def handle_bodyweight(request):
    return render(request=request, template_name='profile/bodyweight.html')
