from django.urls import reverse

from apps.notifications.models import Notification
from apps.timesheets.models import Timesheet
from testsupport.factories import BaseAppTestCase


class TimesheetViewTests(BaseAppTestCase):
    def _entry_formset_payload(self, activity_code, *, work_date="2026-04-06", duration="37.50", action="save"):
        return {
            "entries-TOTAL_FORMS": "1",
            "entries-INITIAL_FORMS": "0",
            "entries-MIN_NUM_FORMS": "0",
            "entries-MAX_NUM_FORMS": "1000",
            "entries-0-id": "",
            "entries-0-activity_code": str(activity_code.pk),
            "entries-0-work_date": work_date,
            "entries-0-duration": duration,
            "entries-0-notes": "Worked project time",
            "action": action,
        }

    def test_hr_user_cannot_access_timesheet_list(self):
        hr_user = self.create_hr("hr.user")
        self.client.force_login(hr_user)

        response = self.client.get(reverse("timesheets:list"))

        self.assertEqual(response.status_code, 403)

    def test_create_timesheet_redirects_to_edit_view(self):
        employee = self.create_employee("employee.user", approver=self.create_approver("approver.user"))
        self.client.force_login(employee)

        response = self.client.post(reverse("timesheets:create"), data={"period_start": "2026-04-06"})

        timesheet = Timesheet.objects.get(user=employee, period_start="2026-04-06")
        self.assertRedirects(response, reverse("timesheets:edit", args=[timesheet.pk]))

    def test_edit_timesheet_can_save_and_submit(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        project = self.create_activity("P100")
        self.assign_activity(employee, project)
        timesheet = self.create_timesheet(employee, approver=approver)
        self.client.force_login(employee)

        response = self.client.post(
            reverse("timesheets:edit", args=[timesheet.pk]),
            data=self._entry_formset_payload(project, action="submit"),
        )

        self.assertRedirects(response, reverse("timesheets:detail", args=[timesheet.pk]))
        timesheet.refresh_from_db()
        self.assertEqual(timesheet.status, Timesheet.Status.SUBMITTED)
        self.assertEqual(timesheet.entries.count(), 1)
        self.assertEqual(Notification.objects.filter(timesheet=timesheet).count(), 2)

    def test_detail_is_forbidden_for_other_users(self):
        approver = self.create_approver("approver.user")
        owner = self.create_employee("owner.user", approver=approver)
        other_user = self.create_employee("other.user", approver=approver)
        timesheet = self.create_timesheet(owner, approver=approver)
        self.client.force_login(other_user)

        response = self.client.get(reverse("timesheets:detail", args=[timesheet.pk]))

        self.assertEqual(response.status_code, 403)

    def test_approved_timesheet_cannot_be_edited(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        timesheet = self.create_timesheet(employee, approver=approver, status=Timesheet.Status.APPROVED)
        self.client.force_login(employee)

        response = self.client.get(reverse("timesheets:edit", args=[timesheet.pk]))

        self.assertEqual(response.status_code, 403)

    def test_batch_submit_submits_valid_timesheets(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        project = self.create_activity("P100")
        self.assign_activity(employee, project)
        timesheet = self.create_timesheet(employee, approver=approver)
        self.add_week_entries(timesheet, project)
        self.client.force_login(employee)

        response = self.client.post(
            reverse("timesheets:batch_submit"),
            data={"selected_timesheets": [timesheet.pk]},
        )

        self.assertRedirects(response, reverse("timesheets:list"))
        timesheet.refresh_from_db()
        self.assertEqual(timesheet.status, Timesheet.Status.SUBMITTED)

    def test_batch_submit_keeps_all_timesheets_in_progress_when_one_is_invalid(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        project = self.create_activity("P100")
        self.assign_activity(employee, project)
        valid_timesheet = self.create_timesheet(employee, approver=approver)
        invalid_timesheet = self.create_timesheet(employee, approver=approver, period_start=valid_timesheet.period_start.replace(day=13))
        self.add_week_entries(valid_timesheet, project)
        self.add_entry(invalid_timesheet, project, duration="5.00")
        self.client.force_login(employee)

        response = self.client.post(
            reverse("timesheets:batch_submit"),
            data={"selected_timesheets": [valid_timesheet.pk, invalid_timesheet.pk]},
            follow=True,
        )

        valid_timesheet.refresh_from_db()
        invalid_timesheet.refresh_from_db()
        self.assertEqual(valid_timesheet.status, Timesheet.Status.IN_PROGRESS)
        self.assertEqual(invalid_timesheet.status, Timesheet.Status.IN_PROGRESS)
        self.assertContains(response, "Weekly total must equal 37.50 hours before submission.")
