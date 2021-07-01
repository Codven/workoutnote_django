"""workoutnote_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('init-exercises/', views.handle_init_exercises),
    path('generate-dummy-data/', views.handle_generate_dummy_data),

    path('about/', views.handle_about, name='about'),
    path('faq/', views.handle_faq, name='faq'),
    path('privacy-policy/', views.handle_faq, name='privacy policy'),

    path('', views.handle_login, name='index'),
    path('calculators/', views.handle_calculators, name='calculators'),
    path('strength-standards/', views.handle_strength_standards, name='strength standards'),
    path('training-log-tutorial/', views.handle_training_log_tutorial, name='training log tutorial'),
    path('one-rep-max-calculator/', views.handle_one_rep_max_calculator, name='one rep max calculator'),
    path('plate-barbell-racking-calculator/', views.handle_plate_barbell_racking_calculator, name='plate barbell racking calculator'),
    path('powerlifting-calculator/', views.handle_powerlifting_calculator, name='powerlifting calculator'),
    path('wilks-calculator/', views.handle_wilks_calculator, name='wilks calculator'),
    path('powerlifting-standards/', views.handle_powerlifting_standards, name='powerlifting standards'),

    path('accounts/login/', views.handle_login, name='login'),
    path('accounts/register/', views.handle_register, name='register'),
    path('accounts/logout/', views.handle_logout, name='logout'),

    path('profile-main/', views.handle_profile_main, name='profile main'),
    path('settings/', views.handle_settings, name='settings'),
    path('analyse-lift/<int:lift_id>/', views.handle_analyse_lift, name='analyse lift'),
    path('find-lifters/', views.handle_find_lifters, name='find lifters'),
    path('workouts/', views.handle_workouts, name='workouts'),
    path('lifts/', views.handle_lifts, name='lifts'),
    path('add-lift/', views.handle_add_lift, name='add lift'),
    path('exercises/', views.handle_exercises, name='exercises'),
    path('bodyweight/', views.handle_bodyweight, name='bodyweight'),

]
