from django.contrib import admin

from .models import TimeEntry, Timesheet


class TimeEntryInline(admin.TabularInline):
    model = TimeEntry
    extra = 0


@admin.register(Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    list_display = ("user", "period_start", "status", "approver", "submitted_at", "approved_at")
    list_filter = ("status", "period_start")
    search_fields = ("user__username", "approver__username")
    inlines = [TimeEntryInline]
    readonly_fields = ("created_at", "updated_at")
