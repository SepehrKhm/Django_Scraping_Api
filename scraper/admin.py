from django.contrib import admin
from django.utils.html import format_html
from .models import ScrapeTask, SiteCookie, JobLog, ScrapeAPIKey

@admin.register(JobLog)
class JobLogAdmin(admin.ModelAdmin):
    list_display = ['task', 'timestamp', 'level', 'message']
    list_filter = ['level', 'timestamp']
    search_fields = ['message', 'stack_trace']
    readonly_fields = ['timestamp']

@admin.register(ScrapeTask)
class ScrapeTaskAdmin(admin.ModelAdmin):
    list_display = ['url', 'status', 'created_at', 'execution_time', 'priority']
    list_filter = ['status', 'requires_cookies', 'created_at']
    search_fields = ['url', 'selector']
    readonly_fields = ['created_at', 'updated_at', 'execution_time']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('url', 'selector', 'requires_cookies', 'priority')
        }),
        ('Status', {
            'fields': ('status', 'result', 'execution_time')
        }),
        ('Timing', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('url', 'selector')
        return self.readonly_fields

@admin.register(ScrapeAPIKey)
class ScrapeAPIKeyAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'created', 'expires_at']
    search_fields = ['name', 'organization']
    readonly_fields = ['created']
    
    def has_change_permission(self, request, obj=None):
        return False  # API keys cannot be modified, only created or deleted
