from django.contrib import admin
from .models import (Exercise, Lift)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['name', 'body_part', 'category']


@admin.register(Lift)
class LiftAdmin(admin.ModelAdmin):
    list_display = ['user', 'exercise', 'body_weight', 'lift_mass', 'repetitions']
