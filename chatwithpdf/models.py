# models.py

from django.db import models

class TokenUsage(models.Model):
    role = models.CharField(max_length=50)
    content = models.TextField()
    tokens = models.IntegerField()
    cost = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
