from django.urls import re_path
from . import views

urlpatterns = [
    # auth
    re_path('^login/?', views.handle_login_api),

    # settings
    re_path('^fetch_settings/?', views.handle_fetch_settings_api),
    re_path('^update_settings/?', views.handle_update_settings_api),

    # exercises & body parts
    re_path('^fetch_exercises/?', views.handle_fetch_exercises_api),
    re_path('^fetch_body_parts/?', views.handle_fetch_body_parts_api),

    # workout
    re_path('^insert_workout/?', views.handle_insert_workout_api),
    re_path('^fetch_workouts/?', views.handle_fetch_workouts_api),

    # lifts
    re_path('^insert_lift/?', views.handle_insert_lift_api),
]
