from django.contrib import admin

from apps.activities.models import ActivityCode, UserActivityAssignment


@admin.register(ActivityCode)
class ActivityCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "billing_type_default", "is_system_controlled_hours", "is_active")
    list_filter = ("category", "billing_type_default", "is_system_controlled_hours", "is_active")
    search_fields = ("code", "name")


@admin.register(UserActivityAssignment)
class UserActivityAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "activity_code", "assigned_by", "assigned_at")
    list_filter = ("activity_code__category",)
    search_fields = ("user__username", "activity_code__code", "activity_code__name")
    autocomplete_fields = ("user", "activity_code", "assigned_by")
