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
    re_path('^request_password_reset/?', views.handle_send_reset_password_email_api),

    # exercises & body parts
    re_path('^fetch_exercises/?', views.handle_fetch_exercises_api),
    re_path('^fetch_body_parts/?', views.handle_fetch_body_parts_api),

    # workout
    re_path('^insert_workout/?', views.handle_insert_workout_api),
    re_path('^fetch_workouts/?', views.handle_fetch_workouts_api),
    re_path('^update_workout/?', views.handle_update_workout_api),
    re_path('^remove_workout/?', views.handle_remove_workout_api),

    # lifts
    re_path('^insert_lift/?', views.handle_insert_lift_api),
    re_path('^update_lift/?', views.handle_update_lift_api),
    re_path('^remove_lift/?', views.handle_remove_lift_api),

    # favorites
    re_path('^set_favorite_exercise/?', views.handle_set_favorite_exercise_api),
    re_path('^unset_favorite_exercise/?', views.handle_unset_favorite_exercise_api),
    re_path('^fetch_favorite_exercises/?', views.handle_fetch_favorite_exercises_api),

    # calendar
    re_path('^fetch_workout_days/?', views.handle_fetch_workout_days),

    # favorites
    re_path('^set_favorite_workout/?', views.handle_set_favorite_workout_api),
    re_path('^unset_favorite_workout/?', views.handle_unset_favorite_workout_api),
    re_path('^fetch_favorite_workouts/?', views.handle_fetch_favorite_workouts_api),

    # notes
    re_path('^fetch_note/?', views.handle_fetch_note_api),
    re_path('^set_note/?', views.handle_set_note_api),

    # one rep max tests
    re_path('^insert_1rm_result/?', views.handle_insert_1rm_result_api),
    re_path('^fetch_1rm_results/?', views.handle_fetch_1rm_results_api),
]
