from django.contrib import admin

from .models import SavedReport


@admin.register(SavedReport)
class SavedReportAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "analysis_type", "is_pinned", "created_at")
    search_fields = ("user__username", "title", "analysis_type", "symbol")
    list_filter = ("analysis_type", "agent_type", "created_at")
