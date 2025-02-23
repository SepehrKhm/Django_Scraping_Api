from django.db import models

class ScrapeTask(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
    ]
    
    url = models.URLField(max_length=2048)
    selector = models.CharField(max_length=255)
    status = models.CharField(max_length=7, choices=STATUS_CHOICES, default='PENDING')
    result = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)