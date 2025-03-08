from django.contrib import admin
from .models import ScrapeTask

@admin.register(ScrapeTask)
class ScrapeTaskAdmin(admin.ModelAdmin):
    list_display = ['url', 'status', 'created_at', 'retry_count']
    list_filter = ['status', 'created_at']
    search_fields = ['url', 'selector']
    readonly_fields = ['created_at', 'updated_at', 'retry_count']
    ordering = ['-created_at']
