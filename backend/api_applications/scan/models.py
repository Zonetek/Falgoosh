from django.db import models
from django.conf import settings

class Scan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scans')
    target = models.TextField(max_length=250)
    ports = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20 , choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    result_reference = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Scan #{self.id} - {self.target}"