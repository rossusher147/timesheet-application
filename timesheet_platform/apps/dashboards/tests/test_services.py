from datetime import date, datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.utils import timezone

from apps.dashboards.services import build_approver_dashboard, build_employee_dashboard
from apps.timesheets.models import Timesheet
from testsupport.factories import BaseAppTestCase


class DashboardServiceTests(BaseAppTestCase):
    def _freeze_business_time(self, value):
        return (
            patch("apps.dashboards.services.get_business_now", return_value=value),
            patch("apps.timesheets.services.get_business_now", return_value=value),
        )

    def test_employee_dashboard_shows_submission_reminder_midweek(self):
        current_time = timezone.make_aware(datetime(2026, 4, 8, 10, 0), ZoneInfo("Europe/London"))
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        self.create_timesheet(employee, period_start=current_time.date() - timedelta(days=current_time.date().weekday()))

        dashboard_patch, services_patch = self._freeze_business_time(current_time)
        with dashboard_patch, services_patch:
            dashboard = build_employee_dashboard(employee)

        self.assertEqual(dashboard["reminders"][0]["title"], "Submit this week's timesheet")

    def test_employee_dashboard_shows_overdue_and_rejected_reminders(self):
        friday_time = timezone.make_aware(datetime(2026, 4, 10, 18, 0), ZoneInfo("Europe/London"))
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        timesheet = self.create_timesheet(employee, period_start=friday_time.date() - timedelta(days=4))

        dashboard_patch, services_patch = self._freeze_business_time(friday_time)
        with dashboard_patch, services_patch:
            overdue_dashboard = build_employee_dashboard(employee)

        self.assertEqual(overdue_dashboard["reminders"][0]["title"], "Timesheet overdue")

        timesheet.status = Timesheet.Status.REJECTED
        timesheet.save(update_fields=["status", "updated_at"])
        with dashboard_patch, services_patch:
            rejected_dashboard = build_employee_dashboard(employee)

        self.assertEqual(rejected_dashboard["reminders"][0]["title"], "Rejected timesheet needs resubmission")

    def test_employee_dashboard_shows_missing_current_week_timesheet_warning(self):
        current_time = timezone.make_aware(datetime(2026, 4, 8, 10, 0), ZoneInfo("Europe/London"))
        employee = self.create_employee("employee.user", approver=self.create_approver("approver.user"))

        dashboard_patch, services_patch = self._freeze_business_time(current_time)
        with dashboard_patch, services_patch:
            dashboard = build_employee_dashboard(employee)

        self.assertEqual(dashboard["reminders"][0]["title"], "No current week timesheet started")

    def test_approver_dashboard_collects_review_and_overdue_sections(self):
        current_time = timezone.make_aware(datetime(2026, 4, 10, 11, 0), ZoneInfo("Europe/London"))
        senior_approver = self.create_approver("senior.approver")
        approver = self.create_approver("approver.user", approver=senior_approver)
        employee = self.create_employee("employee.user", approver=approver)
        second_employee = self.create_employee("employee.two", approver=approver)

        self.create_timesheet(approver, approver=senior_approver)
        self.create_timesheet(employee, approver=approver, status=Timesheet.Status.SUBMITTED)
        self.create_timesheet(
            second_employee,
            approver=approver,
            period_start=date(2026, 3, 30),
            status=Timesheet.Status.SUBMITTED,
            approval_due_at=timezone.make_aware(datetime(2026, 4, 3, 17, 0), ZoneInfo("Europe/London")),
        )
        self.create_timesheet(
            employee,
            approver=approver,
            period_start=date(2026, 3, 23),
            status=Timesheet.Status.REJECTED,
        )
        self.create_timesheet(
            second_employee,
            approver=approver,
            period_start=date(2026, 3, 16),
            status=Timesheet.Status.IN_PROGRESS,
            submission_due_at=timezone.make_aware(datetime(2026, 4, 9, 17, 0), ZoneInfo("Europe/London")),
        )

        dashboard_patch, services_patch = self._freeze_business_time(current_time)
        with dashboard_patch, services_patch:
            dashboard = build_approver_dashboard(approver)

        self.assertEqual(dashboard["pending_reviews"].count(), 2)
        self.assertEqual(dashboard["waiting_for_resubmission"].count(), 1)
        self.assertEqual(dashboard["missed_submissions"].count(), 1)
        reminder_titles = {reminder["title"] for reminder in dashboard["reminders"]}
        self.assertIn("Reviews due today", reminder_titles)
        self.assertIn("Overdue approvals", reminder_titles)
        self.assertIn("Your own timesheet still needs submitting", reminder_titles)
