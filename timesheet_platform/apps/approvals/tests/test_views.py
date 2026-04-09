from django.urls import reverse

from apps.timesheets.models import Timesheet
from testsupport.factories import BaseAppTestCase


class ApprovalViewTests(BaseAppTestCase):
    def test_employee_cannot_access_approval_queue(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        self.client.force_login(employee)

        response = self.client.get(reverse("approvals:queue"))

        self.assertEqual(response.status_code, 403)

    def test_only_assigned_approver_can_view_approval_detail(self):
        approver = self.create_approver("approver.user")
        other_approver = self.create_approver("other.approver")
        employee = self.create_employee("employee.user", approver=approver)
        timesheet = self.create_timesheet(employee, approver=approver, status=Timesheet.Status.SUBMITTED)
        self.client.force_login(other_approver)

        response = self.client.get(reverse("approvals:detail", args=[timesheet.pk]))

        self.assertEqual(response.status_code, 404)

    def test_approver_can_approve_submitted_timesheet(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        timesheet = self.create_timesheet(employee, approver=approver, status=Timesheet.Status.SUBMITTED)
        self.client.force_login(approver)

        response = self.client.post(reverse("approvals:approve", args=[timesheet.pk]))

        self.assertRedirects(response, reverse("approvals:detail", args=[timesheet.pk]))
        timesheet.refresh_from_db()
        self.assertEqual(timesheet.status, Timesheet.Status.APPROVED)

    def test_approver_can_reject_submitted_timesheet(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        timesheet = self.create_timesheet(employee, approver=approver, status=Timesheet.Status.SUBMITTED)
        self.client.force_login(approver)

        response = self.client.post(
            reverse("approvals:reject", args=[timesheet.pk]),
            data={"rejection_note": "Please fix Monday entries."},
        )

        self.assertRedirects(response, reverse("approvals:detail", args=[timesheet.pk]))
        timesheet.refresh_from_db()
        self.assertEqual(timesheet.status, Timesheet.Status.REJECTED)
        self.assertEqual(timesheet.latest_rejection_note, "Please fix Monday entries.")
