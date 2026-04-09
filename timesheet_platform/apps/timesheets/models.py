from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Timesheet(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="timesheets",
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_timesheets",
    )
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )
    submission_due_at = models.DateTimeField()
    approval_due_at = models.DateTimeField()
    submitted_at = models.DateTimeField(blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)
    latest_rejection_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-period_start", "-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "period_start"],
                name="unique_timesheet_per_user_period",
            )
        ]

    def __str__(self):
        return f"{self.user} {self.period_start:%Y-%m-%d}"

    @property
    def expected_weekly_hours(self):
        return self.user.weekly_contracted_hours

    @property
    def total_hours(self):
        return self.entries.aggregate(total=Sum("duration")).get("total") or Decimal("0.00")

    @property
    def is_submission_overdue(self):
        return self.status == self.Status.IN_PROGRESS and timezone.now() >= self.submission_due_at

    @property
    def is_approval_overdue(self):
        return self.status == self.Status.SUBMITTED and timezone.now() >= self.approval_due_at

    @property
    def has_been_rejected_before(self):
        return self.workflow_events.filter(event_type="rejected").exists()


class TimeEntry(models.Model):
    class BillingType(models.TextChoices):
        INTERNAL = "internal", "Internal"
        BILLABLE = "billable", "Billable"
        NON_BILLABLE = "non_billable", "Non-Billable"

    class EntryCategory(models.TextChoices):
        PROJECT_WORK = "project_work", "Project Work"
        LEAVE = "leave", "Leave"
        NON_PROJECT = "non_project", "Non-Project"

    timesheet = models.ForeignKey(
        Timesheet,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    activity_code = models.ForeignKey(
        "activities.ActivityCode",
        on_delete=models.PROTECT,
        related_name="time_entries",
    )
    work_date = models.DateField()
    duration = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.25"))],
    )
    billing_type = models.CharField(
        max_length=16,
        choices=BillingType.choices,
        default=BillingType.INTERNAL,
    )
    entry_category = models.CharField(
        max_length=16,
        choices=EntryCategory.choices,
        default=EntryCategory.PROJECT_WORK,
    )
    system_controlled_hours = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["work_date", "activity_code__code", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["timesheet", "activity_code", "work_date"],
                name="unique_entry_per_day_activity",
            )
        ]

    def __str__(self):
        return f"{self.timesheet} {self.work_date} {self.activity_code}"
