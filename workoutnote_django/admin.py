from django.contrib import admin
from .models import (Exercise, Lift, Preferences, BodyWeight)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'body_part', 'category']


@admin.register(Lift)
class LiftAdmin(admin.ModelAdmin):
    list_display = ['user', 'exercise', 'body_weight', 'lift_mass', 'repetitions']


@admin.register(Preferences)
class LiftAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'gender', 'date_of_birth']


@admin.register(BodyWeight)
class BodyweightAdmin(admin.ModelAdmin):
    list_display = ['user', 'user', 'date']
