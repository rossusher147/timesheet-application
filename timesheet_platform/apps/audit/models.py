from django.conf import settings
from django.db import models


class WorkflowEvent(models.Model):
    class EventType(models.TextChoices):
        DRAFT_CREATED = "draft_created", "Draft Created"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        RESUBMITTED = "resubmitted", "Resubmitted"

    timesheet = models.ForeignKey(
        "timesheets.Timesheet",
        on_delete=models.CASCADE,
        related_name="workflow_events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workflow_events",
    )
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    comment = models.TextField(blank=True)
    metadata_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.timesheet_id} {self.event_type}"
