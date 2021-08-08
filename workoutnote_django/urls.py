from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),

    path('init-configs/', views.handle_init_configs),
    path('generate-dummy-data/', views.handle_generate_dummy_data),

    path('', views.handle_index, name='index'),
    path('calculators/', views.handle_calculators, name='calculators'),
    path('one-rep-max-calculator/', views.handle_one_rep_max_calculator, name='one rep max calculator'),
    path('plate-barbell-racking-calculator/', views.handle_plate_barbell_racking_calculator, name='plate barbell racking calculator'),
    path('wilks-calculator/', views.handle_wilks_calculator, name='wilks calculator'),

    path('accounts/login/', views.handle_login, name='login'),
    path('accounts/register/', views.handle_register, name='register'),
    path('accounts/logout/', views.handle_logout, name='logout'),

    path('settings/', views.handle_settings, name='settings'),
    path('add-workout/', views.handle_add_workout, name='add workout'),
    path('calendar/', views.handle_calendar, name='calendar'),
    path('favorite-workouts/', views.handle_favorite_workouts, name='favorite workouts'),

    # APIs
    path('api/', include('api.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
