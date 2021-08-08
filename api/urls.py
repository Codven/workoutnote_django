from django.urls import re_path
from . import views

urlpatterns = [
    # auth
    re_path('^login/?', views.handle_login_api),
    re_path('^send_verification_code/?', views.handle_send_verification_code_api),
    re_path('^verify_register/?', views.handle_verify_register_api),

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

    # favorites
    re_path('^set_favorite_exercise/?', views.handle_set_favorite_exercise_api),
    re_path('^unset_favorite_exercise/?', views.handle_unset_favorite_exercise_api),
    re_path('^fetch_favorite_exercises/?', views.handle_fetch_favorite_exercises_api),

    re_path('^set_favorite_workout/?', views.handle_set_favorite_workout_api),
    re_path('^unset_favorite_workout/?', views.handle_unset_favorite_workout_api),
    re_path('^fetch_favorite_workouts/?', views.handle_fetch_favorite_workouts_api),
]
