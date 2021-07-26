from django.db import models
from django.contrib.auth.models import User as django_User
import time
import hashlib


class SessionKey(models.Model):
    user = models.OneToOneField(to=django_User, on_delete=models.CASCADE, primary_key=True)
    key = models.CharField(max_length=256, unique=True)

    @staticmethod
    def generate_key(email):
        now_us = int(time.time() * 1000 * 1000)
        return hashlib.md5(f'{email}{now_us}'.encode()).hexdigest()
