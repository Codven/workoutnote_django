from django.shortcuts import render


def handle_index(request):
    return render(request=request, template_name='index.html')


def handle_calculators(request):
    return render(request=request, template_name='calculators.html')


def handle_strength_standards(request):
    return render(request=request, template_name='strength_standards.html')


def handle_training_log_tutorial(request):
    return render(request=request, template_name='training-log-tutorial.html')


def login(request):
    return render(request=request, template_name='login.html')
