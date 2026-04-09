from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.accounts.models import User
from apps.activities.models import UserActivityAssignment


class UserActivityAssignmentInline(admin.TabularInline):
    model = UserActivityAssignment
    fk_name = "user"
    extra = 0
    autocomplete_fields = ["activity_code", "assigned_by"]


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Business Details", {"fields": ("business_unit", "weekly_contracted_hours", "approver")}),
    )
    list_display = ("username", "get_full_name", "email", "business_unit", "weekly_contracted_hours", "is_staff")
    list_filter = ("is_staff", "is_active", "groups", "business_unit")
    search_fields = ("username", "first_name", "last_name", "email", "business_unit")
    autocomplete_fields = ["approver"]
    inlines = [UserActivityAssignmentInline]
