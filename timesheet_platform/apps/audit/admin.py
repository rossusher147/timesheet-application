from django.contrib import admin

from .models import WorkflowEvent


@admin.register(WorkflowEvent)
class WorkflowEventAdmin(admin.ModelAdmin):
    list_display = ("timesheet", "event_type", "actor", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("timesheet__user__username", "actor__username", "comment")
    readonly_fields = ("created_at",)
