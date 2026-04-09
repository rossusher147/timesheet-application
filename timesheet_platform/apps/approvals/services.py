from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import WorkflowEvent
from apps.notifications.models import Notification
from apps.timesheets.models import Timesheet
from apps.timesheets.services import create_notification, create_workflow_event


def _ensure_approver_action(timesheet, approver):
    if timesheet.approver_id != approver.id:
        raise ValidationError("You are not the approver for this timesheet.")
    if timesheet.status != Timesheet.Status.SUBMITTED:
        raise ValidationError("Only submitted timesheets can be approved or rejected.")


@transaction.atomic
def approve_timesheet(timesheet, approver):
    _ensure_approver_action(timesheet, approver)
    timesheet.status = Timesheet.Status.APPROVED
    timesheet.approved_at = timezone.now()
    timesheet.latest_rejection_note = ""
    timesheet.save(update_fields=["status", "approved_at", "latest_rejection_note", "updated_at"])
    event = create_workflow_event(timesheet, approver, WorkflowEvent.EventType.APPROVED)
    create_notification(
        recipient=timesheet.user,
        title="Timesheet approved",
        body=f"Your timesheet for {timesheet.period_start} has been approved.",
        notification_type=Notification.NotificationType.APPROVAL,
        severity=Notification.Severity.SUCCESS,
        timesheet=timesheet,
        workflow_event=event,
    )
    return timesheet


@transaction.atomic
def reject_timesheet(timesheet, approver, rejection_note):
    _ensure_approver_action(timesheet, approver)
    if not rejection_note.strip():
        raise ValidationError("A rejection note is required.")
    timesheet.status = Timesheet.Status.REJECTED
    timesheet.rejected_at = timezone.now()
    timesheet.latest_rejection_note = rejection_note.strip()
    timesheet.save(update_fields=["status", "rejected_at", "latest_rejection_note", "updated_at"])
    event = create_workflow_event(
        timesheet,
        approver,
        WorkflowEvent.EventType.REJECTED,
        comment=timesheet.latest_rejection_note,
    )
    create_notification(
        recipient=timesheet.user,
        title="Timesheet rejected",
        body=f"Your timesheet for {timesheet.period_start} was rejected. Note: {timesheet.latest_rejection_note}",
        notification_type=Notification.NotificationType.REJECTION,
        severity=Notification.Severity.ERROR,
        timesheet=timesheet,
        workflow_event=event,
    )
    return timesheet
