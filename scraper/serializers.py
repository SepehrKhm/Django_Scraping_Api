from rest_framework import serializers
from .models import ScrapeTask, JobLog

class JobLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobLog
        fields = ['id', 'task', 'timestamp', 'level', 'message', 'stack_trace']
        read_only_fields = ['timestamp']

class ScrapeTaskSerializer(serializers.ModelSerializer):
    logs = JobLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = ScrapeTask
        fields = ['id', 'url', 'selector', 'status', 'result', 
                 'created_at', 'requires_cookies', 'logs']
        read_only_fields = ['status', 'result', 'created_at', 'logs']