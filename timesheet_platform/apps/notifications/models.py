from django.conf import settings
from django.db import models


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        SUBMISSION = "submission", "Submission"
        APPROVAL = "approval", "Approval"
        REJECTION = "rejection", "Rejection"
        RESUBMISSION = "resubmission", "Resubmission"
        REMINDER_SUMMARY = "reminder_summary", "Reminder Summary"
        OTHER = "other", "Other"

    class Severity(models.TextChoices):
        INFO = "info", "Info"
        SUCCESS = "success", "Success"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    timesheet = models.ForeignKey(
        "timesheets.Timesheet",
        on_delete=models.CASCADE,
        related_name="notifications",
        blank=True,
        null=True,
    )
    workflow_event = models.ForeignKey(
        "audit.WorkflowEvent",
        on_delete=models.SET_NULL,
        related_name="notifications",
        blank=True,
        null=True,
    )
    notification_type = models.CharField(
        max_length=32,
        choices=NotificationType.choices,
        default=NotificationType.OTHER,
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    severity = models.CharField(max_length=16, choices=Severity.choices, default=Severity.INFO)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.recipient} - {self.title}"
