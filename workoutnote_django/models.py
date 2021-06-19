from django.db import models


class EmailVerificationRequests(models.Model):
    email = models.EmailField(primary_key=True)
    verification_code = models.CharField(max_length=30)
    creation_time = models.TimeField(auto_now_add=False)
