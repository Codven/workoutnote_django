from workoutnote_django.models import Exercise, Lift, Preferences, WorkoutSession, BodyPart, Category
from django.contrib import admin


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'body_part', 'category']


@admin.register(BodyPart)
class BodyPartAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']


@admin.register(Preferences)
class PreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'gender', 'date_of_birth', 'shared_profile']


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'timestamp', 'user', 'title', 'duration']


@admin.register(Lift)
class LiftAdmin(admin.ModelAdmin):
    list_display = ['id', 'timestamp', 'exercise', 'workout_session', 'lift_mass', 'repetitions', 'one_rep_max']
