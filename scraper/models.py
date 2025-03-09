from django.db import models
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework_api_key.models import AbstractAPIKey

class ScrapeAPIKey(AbstractAPIKey):
    organization = models.CharField(max_length=255)
    expires_at = models.DateTimeField(null=True)
    
    class Meta:
        verbose_name = "Scraping API key"
        verbose_name_plural = "Scraping API keys"

class JobLog(models.Model):
    task = models.ForeignKey('ScrapeTask', on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=20, choices=[
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
    ])
    message = models.TextField()
    stack_trace = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['task', 'level', 'timestamp']),
        ]

class ScrapeResult(models.Model):
    task = models.ForeignKey('ScrapeTask', on_delete=models.CASCADE, related_name='stored_results')
    selector = models.CharField(max_length=255)
    content = models.TextField()
    extracted_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(null=True, blank=True)  # Store additional info like position, etc.

    class Meta:
        ordering = ['extracted_at']
        indexes = [
            models.Index(fields=['task', 'extracted_at']),
        ]

    def __str__(self):
        return f"Result for {self.task.url} - {self.selector[:30]}"

class ScrapeTask(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('PAUSED', 'Paused'),
        ('INTERRUPTED', 'Interrupted'),
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
    ]
    
    url = models.URLField(max_length=2048, validators=[URLValidator()])
    selectors = models.JSONField(default=list)  # Store multiple selectors
    selector = models.CharField(max_length=255, null=True, blank=True)  # Keep for backwards compatibility
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='PENDING')
    progress = models.FloatField(default=0)  # 0 to 100
    current_position = models.IntegerField(default=0)  # Track where we left off
    total_items = models.IntegerField(null=True)
    last_processed_url = models.URLField(null=True, blank=True)
    resume_token = models.TextField(null=True, blank=True)  # Store any state needed for resuming
    result = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    retry_count = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)
    requires_cookies = models.BooleanField(default=False)
    api_key = models.ForeignKey(ScrapeAPIKey, on_delete=models.SET_NULL, null=True, blank=True)
    execution_time = models.FloatField(null=True)
    retries_left = models.IntegerField(default=3)
    priority = models.IntegerField(default=0)

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

    def log(self, level, message, stack_trace=None):
        return JobLog.objects.create(
            task=self,
            level=level,
            message=message,
            stack_trace=stack_trace
        )

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
        return (timezone.now() - self.last_updated).total_seconds() > 1800

    def __str__(self):
        return f"{self.domain} - {self.last_updated}"