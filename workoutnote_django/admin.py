from workoutnote_django.models import Exercise
from workoutnote_django.models import Lift
from workoutnote_django.models import Preferences
from workoutnote_django.models import WorkoutSession
from workoutnote_django.models import BodyPart
from workoutnote_django.models import Category
from workoutnote_django.models import EmailConfirmationCodes
from workoutnote_django.models import FavoriteExercises
from workoutnote_django.models import FavoriteWorkouts
from django.contrib import admin


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'name_translations', 'body_part', 'category']


@admin.register(FavoriteExercises)
class FavoriteExercisesAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'exercise']


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


@admin.register(FavoriteWorkouts)
class FavoriteWorkoutsAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'workout_session']


@admin.register(Lift)
class LiftAdmin(admin.ModelAdmin):
    list_display = ['id', 'timestamp', 'exercise', 'workout_session', 'lift_mass', 'repetitions', 'one_rep_max']


@admin.register(EmailConfirmationCodes)
class EmailConfirmationCodesAdmin(admin.ModelAdmin):
    list_display = ['email', 'verification_code']
