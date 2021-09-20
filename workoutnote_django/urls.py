from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('', views.handle_index, name='index'),
    path('admin/', admin.site.urls, name='admin'),
    path('api/', include('api.urls')),

    path('init-configs/', views.handle_init_configs),
    path('generate-dummy-data/', views.handle_generate_dummy_data),

    path('calculators/', views.handle_calculators, name='calculators'),

    path('accounts/login/', views.handle_login, name='login'),
    path('accounts/register/', views.handle_register, name='register'),
    path('accounts/logout/', views.handle_logout, name='logout'),

    path('settings/', views.handle_settings, name='settings'),
    path('reset_password/', views.handle_password_reset, name='reset password'),
    path('add-workout/', views.handle_add_workout, name='add workout'),
    path('calendar/', views.handle_calendar, name='calendar'),
    path('favorite-workouts/', views.handle_favorite_workouts, name='favorite workouts'),

    path('report/', views.handle_report, name='report'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
