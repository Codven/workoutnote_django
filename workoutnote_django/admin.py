from workoutnote_django.models import Exercise, Lift, Preferences, WorkoutSession
from django.contrib import admin


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'body_part', 'category']


@admin.register(Preferences)
class PreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'gender', 'date_of_birth', 'shared_profile']


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'title', 'duration']


@admin.register(Lift)
class LiftAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'exercise', 'workout_session', 'lift_mass', 'repetitions', 'one_rep_max']
