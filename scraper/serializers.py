from rest_framework import serializers
from .models import ScrapeTask, JobLog, ScrapeResult

class JobLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobLog
        fields = ['id', 'task', 'timestamp', 'level', 'message', 'stack_trace']
        read_only_fields = ['timestamp']

class ScrapeResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapeResult
        fields = ['selector', 'content', 'extracted_at', 'metadata']

class ScrapeTaskSerializer(serializers.ModelSerializer):
    logs = JobLogSerializer(many=True, read_only=True)
    stored_results = ScrapeResultSerializer(many=True, read_only=True)
    selectors = serializers.JSONField(required=True)  # Accept JSON array of selectors

    class Meta:
        model = ScrapeTask
        fields = ['id', 'url', 'selectors', 'status', 'result', 
                 'created_at', 'requires_cookies', 'logs', 'stored_results',
                 'progress', 'current_position', 'total_items']
        read_only_fields = ['status', 'result', 'created_at', 'logs', 
                          'stored_results', 'progress', 'current_position', 
                          'total_items']

    def validate_selectors(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Selectors must be an array")
        if not value:
            raise serializers.ValidationError("At least one selector is required")
        if not all(isinstance(s, str) for s in value):
            raise serializers.ValidationError("All selectors must be strings")
        return value