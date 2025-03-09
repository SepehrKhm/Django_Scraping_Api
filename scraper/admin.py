from django.contrib import admin
from django.forms import ModelForm, CharField, Textarea, ValidationError
from django.utils.html import format_html
from .models import ScrapeTask, SiteCookie, JobLog, ScrapeAPIKey, ScrapeResult
from rest_framework_api_key.admin import APIKeyModelAdmin

class ScrapeTaskAdminForm(ModelForm):
    selectors_json = CharField(
        widget=Textarea(attrs={'rows': 4}),
        help_text='Enter selectors as JSON array. Example: ["h1", ".content p", "#main-title"]',
        required=True,
        label='Selectors (JSON array)'
    )

    class Meta:
        model = ScrapeTask
        fields = '__all__'
        exclude = ['selectors']

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', {})
        if instance:
            import json
            initial['selectors_json'] = json.dumps(instance.selectors or [])
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def clean_selectors_json(self):
        import json
        try:
            selectors = json.loads(self.cleaned_data['selectors_json'])
            if not isinstance(selectors, list):
                raise ValidationError("Selectors must be a JSON array")
            if not selectors:
                raise ValidationError("At least one selector is required")
            return selectors
        except json.JSONDecodeError:
            raise ValidationError("Invalid JSON format")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.selectors = self.cleaned_data['selectors_json']
        if commit:
            instance.save()
        return instance

@admin.register(ScrapeTask)
class ScrapeTaskAdmin(admin.ModelAdmin):
    form = ScrapeTaskAdminForm
    list_display = ['url', 'status', 'created_at', 'execution_time', 'priority']
    list_filter = ['status', 'requires_cookies', 'created_at']
    search_fields = ['url']
    readonly_fields = ['created_at', 'updated_at', 'execution_time']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('url', 'selectors_json', 'requires_cookies', 'priority')
        }),
        ('Status', {
            'fields': ('status', 'result', 'execution_time')
        }),
        ('Timing', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(JobLog)
class JobLogAdmin(admin.ModelAdmin):
    list_display = ['task', 'timestamp', 'level', 'message']
    list_filter = ['level', 'timestamp']
    search_fields = ['message', 'stack_trace']
    readonly_fields = ['timestamp']

@admin.register(ScrapeAPIKey)
class ScrapeAPIKeyAdmin(APIKeyModelAdmin):
    list_display = ['name', 'organization', 'created', 'expires_at']
    search_fields = ['name', 'organization']
    readonly_fields = ['created']

@admin.register(ScrapeResult)
class ScrapeResultAdmin(admin.ModelAdmin):
    list_display = ['task', 'selector', 'content_preview', 'extracted_at']
    list_filter = ['extracted_at', 'selector']
    search_fields = ['content', 'selector']
    readonly_fields = ['extracted_at']

    def content_preview(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview' 