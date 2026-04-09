from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import WorkflowEvent
from apps.notifications.models import Notification

from .models import TimeEntry, Timesheet


BUSINESS_TZ = ZoneInfo(getattr(settings, "TIME_ZONE", "Europe/London"))


def get_business_now():
    return timezone.now().astimezone(BUSINESS_TZ)


def current_week_start(reference=None):
    reference_date = (reference or get_business_now()).date()
    return reference_date - timedelta(days=reference_date.weekday())


def get_week_bounds(period_start):
    return period_start, period_start + timedelta(days=4)


def week_dates(period_start):
    return [period_start + timedelta(days=index) for index in range(5)]


def to_business_deadline(target_date):
    return timezone.make_aware(datetime.combine(target_date, time(hour=17, minute=0)), BUSINESS_TZ)


def create_workflow_event(timesheet, actor, event_type, comment="", metadata=None):
    return WorkflowEvent.objects.create(
        timesheet=timesheet,
        actor=actor,
        event_type=event_type,
        comment=comment,
        metadata_json=metadata or {},
    )


def create_notification(recipient, title, body, notification_type, severity, timesheet=None, workflow_event=None):
    return Notification.objects.create(
        recipient=recipient,
        timesheet=timesheet,
        workflow_event=workflow_event,
        notification_type=notification_type,
        title=title,
        body=body,
        severity=severity,
    )


def get_or_create_timesheet_for_period(user, period_start):
    if period_start.weekday() != 0:
        raise ValidationError("Timesheets must start on a Monday.")
    if not user.approver_id:
        raise ValidationError("You need an assigned approver before you can create a timesheet.")

    period_start, period_end = get_week_bounds(period_start)
    timesheet, created = Timesheet.objects.get_or_create(
        user=user,
        period_start=period_start,
        defaults={
            "approver": user.approver,
            "period_end": period_end,
            "submission_due_at": to_business_deadline(period_start + timedelta(days=3)),
            "approval_due_at": to_business_deadline(period_start + timedelta(days=4)),
        },
    )
    if created:
        create_workflow_event(timesheet, user, WorkflowEvent.EventType.DRAFT_CREATED)
    return timesheet, created


def apply_entry_defaults(entry):
    activity = entry.activity_code
    entry.billing_type = activity.billing_type_default
    if activity.category in {"bank_holiday", "annual_leave", "sick_leave"}:
        entry.entry_category = TimeEntry.EntryCategory.LEAVE
    elif activity.category in {"internal", "other"}:
        entry.entry_category = TimeEntry.EntryCategory.NON_PROJECT
    else:
        entry.entry_category = TimeEntry.EntryCategory.PROJECT_WORK
    entry.system_controlled_hours = activity.is_system_controlled_hours
    if activity.is_system_controlled_hours:
        entry.duration = activity.fixed_hours or activity.default_duration


def validate_timesheet_for_submission(timesheet):
    entries = list(timesheet.entries.select_related("activity_code"))
    if not entries:
        raise ValidationError("Add at least one time entry before submitting.")

    total_hours = timesheet.total_hours
    if total_hours != timesheet.expected_weekly_hours:
        raise ValidationError(
            f"Weekly total must equal {timesheet.expected_weekly_hours} hours before submission. Current total: {total_hours}."
        )

    for entry in entries:
        if entry.work_date < timesheet.period_start or entry.work_date > timesheet.period_end:
            raise ValidationError("All entries must fall inside the Monday to Friday week.")
        if not entry.activity_code.user_assignments.filter(user=timesheet.user).exists():
            raise ValidationError(f"{entry.activity_code.code} is not assigned to {timesheet.user.username}.")
        if entry.activity_code.is_system_controlled_hours:
            required_hours = entry.activity_code.fixed_hours or entry.activity_code.default_duration
            if entry.duration != required_hours:
                raise ValidationError(f"{entry.activity_code.code} uses fixed hours of {required_hours}.")


@transaction.atomic
def submit_timesheet(timesheet, actor):
    if actor.id != timesheet.user_id:
        raise ValidationError("You can only submit your own timesheets.")
    if timesheet.status not in [Timesheet.Status.IN_PROGRESS, Timesheet.Status.REJECTED]:
        raise ValidationError("Only in-progress or rejected timesheets can be submitted.")
    validate_timesheet_for_submission(timesheet)
    is_resubmission = timesheet.workflow_events.filter(
        event_type=WorkflowEvent.EventType.REJECTED
    ).exists()
    event_type = WorkflowEvent.EventType.RESUBMITTED if is_resubmission else WorkflowEvent.EventType.SUBMITTED
    timesheet.status = Timesheet.Status.SUBMITTED
    timesheet.submitted_at = timezone.now()
    timesheet.save(update_fields=["status", "submitted_at", "updated_at"])

    event = create_workflow_event(timesheet, actor, event_type)
    employee_title = "Timesheet resubmitted" if is_resubmission else "Timesheet submitted"
    create_notification(
        recipient=timesheet.user,
        title=employee_title,
        body=f"Your timesheet for {timesheet.period_start} has been sent for review.",
        notification_type=Notification.NotificationType.RESUBMISSION if is_resubmission else Notification.NotificationType.SUBMISSION,
        severity=Notification.Severity.INFO,
        timesheet=timesheet,
        workflow_event=event,
    )
    approver_title = "Timesheet resubmitted for review" if is_resubmission else "New timesheet to review"
    create_notification(
        recipient=timesheet.approver,
        title=approver_title,
        body=f"{timesheet.user.get_full_name() or timesheet.user.username} submitted the week starting {timesheet.period_start}.",
        notification_type=Notification.NotificationType.RESUBMISSION if is_resubmission else Notification.NotificationType.SUBMISSION,
        severity=Notification.Severity.WARNING,
        timesheet=timesheet,
        workflow_event=event,
    )
    return timesheet


@transaction.atomic
def batch_submit_timesheets(timesheets, actor):
    submitted = []
    for timesheet in timesheets.select_related("user", "approver"):
        if timesheet.status not in [Timesheet.Status.IN_PROGRESS, Timesheet.Status.REJECTED]:
            raise ValidationError("Only in-progress or rejected timesheets can be batch submitted.")
        submit_timesheet(timesheet, actor)
        submitted.append(timesheet)
    return submitted
