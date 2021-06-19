from django.shortcuts import render


def handle_index(request):
    return render(request=request, template_name='index.html')


def handle_calculators(request):
    return render(request=request, template_name='calculators.html')


def handle_strength_standards(request):
    return render(request=request, template_name='strength_standards.html')


def handle_training_log_tutorial(request):
    return render(request=request, template_name='training-log-tutorial.html')


from django.template.response import TemplateResponse


def login_register(request):
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

    return TemplateResponse(request=request, template='login.html', context=data)
