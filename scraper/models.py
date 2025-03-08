from django.db import models
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import json

class ScrapeTask(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
    ]
    
    url = models.URLField(max_length=2048, validators=[URLValidator()])
    selector = models.CharField(max_length=255)
    status = models.CharField(max_length=7, choices=STATUS_CHOICES, default='PENDING')
    result = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    retry_count = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['url']),
        ]

    def __str__(self):
        return f"{self.url} - {self.status}"

    def clean(self):
        if len(self.selector) < 1:
            raise ValidationError("Selector cannot be empty")

class SiteCookie(models.Model):
    domain = models.CharField(max_length=255)
    cookies = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)
    is_valid = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['domain']),
        ]

    @property
    def is_expired(self):
        # Check if cookie is older than 30 minutes
        return (timezone.now() - self.last_updated).total_seconds() > 1800

    def __str__(self):
        return f"{self.domain} - {self.last_updated}"