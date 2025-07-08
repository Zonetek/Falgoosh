from django.db import models
from api_applications.shared_models.models import CustomUser, UserProfile
class Scan(models.Model):
    SCAN_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='scans')
    target_ip = models.GenericIPAddressField()
    target_ports = models.TextField(help_text="Comma-separated port numbers or ranges")
    scan_type = models.CharField(max_length=50, default='tcp_scan')
    status = models.CharField(max_length=20, choices=SCAN_STATUS_CHOICES, default='pending')
    
    mongo_object_id = models.CharField(max_length=24, blank=True, null=True, help_text="MongoDB ObjectId for scan results")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'target_ip']),
            models.Index(fields=['mongo_object_id']),
        ]
    
    def __str__(self):
        return f"Scan {self.id} - {self.target_ip} - {self.user.username}"