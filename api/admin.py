from api.models import SessionKey
from django.contrib import admin


@admin.register(SessionKey)
class SessionKeyAdmin(admin.ModelAdmin):
    list_display = ['user', 'key']
