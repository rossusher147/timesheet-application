from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "notification_type", "severity", "created_at", "read_at")
    list_filter = ("notification_type", "severity", "created_at")
    search_fields = ("recipient__username", "title", "body")
    readonly_fields = ("created_at",)
