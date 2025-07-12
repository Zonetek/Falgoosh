from django.db import models
from api_applications.shared_models.models import CustomUser, UserProfile
from django.conf import settings
class Scan(models.Model):
    SCAN_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scans')
    target_ip = models.GenericIPAddressField()
    target_ports = models.TextField(help_text="Comma-separated port numbers or ranges")
    scan_type = models.CharField(max_length=50, default='tcp_scan')
    status = models.CharField(max_length=20, choices=SCAN_STATUS_CHOICES, default='pending')

    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    domain = models.CharField(max_length=255, blank=True, null=True)
    organization = models.CharField(max_length=255, blank=True, null=True)
    isp = models.CharField(max_length=255, blank=True, null=True)
    asn = models.CharField(max_length=100, blank=True, null=True)
    
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
            models.Index(fields=['country', 'city']),  
            models.Index(fields=['organization']),      
        ]
    
    def __str__(self):
        return f"Scan {self.id} - {self.target_ip} - {self.user.username}"
    
    @property
    def location_display(self):
        location_parts = []
        if self.city:
            location_parts.append(self.city)
        if self.region:
            location_parts.append(self.region)
        if self.country:
            location_parts.append(self.country)
        return ', '.join(location_parts) if location_parts else 'Unknown'
    

    def has_geographic_data(self):
        return bool(self.latitude and self.longitude)
    
class ScanHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scan_history')
    scan = models.ForeignKey(Scan, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-timestamp']

