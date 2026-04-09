from django.core.exceptions import ValidationError

from apps.approvals.services import approve_timesheet, reject_timesheet
from apps.audit.models import WorkflowEvent
from apps.notifications.models import Notification
from apps.timesheets.models import Timesheet
from testsupport.factories import BaseAppTestCase


class ApprovalServiceTests(BaseAppTestCase):
    def test_approve_timesheet_marks_it_approved_and_notifies_employee(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        timesheet = self.create_timesheet(
            employee,
            approver=approver,
            status=Timesheet.Status.SUBMITTED,
            latest_rejection_note="Old note",
        )

        approve_timesheet(timesheet, approver)

        timesheet.refresh_from_db()
        self.assertEqual(timesheet.status, Timesheet.Status.APPROVED)
        self.assertEqual(timesheet.latest_rejection_note, "")
        self.assertTrue(timesheet.workflow_events.filter(event_type=WorkflowEvent.EventType.APPROVED).exists())
        self.assertTrue(
            Notification.objects.filter(
                recipient=employee,
                timesheet=timesheet,
                notification_type=Notification.NotificationType.APPROVAL,
            ).exists()
        )

    def test_reject_timesheet_requires_note_and_records_notification(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        timesheet = self.create_timesheet(employee, approver=approver, status=Timesheet.Status.SUBMITTED)

        with self.assertRaisesMessage(ValidationError, "A rejection note is required."):
            reject_timesheet(timesheet, approver, "   ")

        reject_timesheet(timesheet, approver, "Please clarify leave hours.")

        timesheet.refresh_from_db()
        self.assertEqual(timesheet.status, Timesheet.Status.REJECTED)
        self.assertEqual(timesheet.latest_rejection_note, "Please clarify leave hours.")
        self.assertTrue(timesheet.workflow_events.filter(event_type=WorkflowEvent.EventType.REJECTED).exists())
        self.assertTrue(
            Notification.objects.filter(
                recipient=employee,
                timesheet=timesheet,
                notification_type=Notification.NotificationType.REJECTION,
            ).exists()
        )

    def test_only_assigned_approver_can_action_a_submitted_timesheet(self):
        approver = self.create_approver("approver.user")
        other_approver = self.create_approver("other.approver")
        employee = self.create_employee("employee.user", approver=approver)
        timesheet = self.create_timesheet(employee, approver=approver, status=Timesheet.Status.SUBMITTED)

        with self.assertRaisesMessage(ValidationError, "You are not the approver for this timesheet."):
            approve_timesheet(timesheet, other_approver)

        timesheet.status = Timesheet.Status.IN_PROGRESS
        timesheet.save(update_fields=["status", "updated_at"])
        with self.assertRaisesMessage(ValidationError, "Only submitted timesheets can be approved or rejected."):
            reject_timesheet(timesheet, approver, "Need more detail.")
