from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.audit.models import WorkflowEvent
from apps.notifications.models import Notification
from apps.timesheets.models import Timesheet
from apps.timesheets.services import (
    apply_entry_defaults,
    batch_submit_timesheets,
    current_week_start,
    get_or_create_timesheet_for_period,
    get_week_bounds,
    submit_timesheet,
    to_business_deadline,
    validate_timesheet_for_submission,
    week_dates,
)
from testsupport.factories import BaseAppTestCase


class TimesheetServiceTests(BaseAppTestCase):
    def test_calendar_helpers_return_expected_week_values(self):
        reference = timezone.make_aware(datetime(2026, 4, 9, 9, 0), ZoneInfo("Europe/London"))

        self.assertEqual(current_week_start(reference), date(2026, 4, 6))
        self.assertEqual(get_week_bounds(date(2026, 4, 6)), (date(2026, 4, 6), date(2026, 4, 10)))
        self.assertEqual(
            week_dates(date(2026, 4, 6)),
            [
                date(2026, 4, 6),
                date(2026, 4, 7),
                date(2026, 4, 8),
                date(2026, 4, 9),
                date(2026, 4, 10),
            ],
        )

    def test_to_business_deadline_sets_5pm_business_time(self):
        deadline = to_business_deadline(date(2026, 4, 10)).astimezone(ZoneInfo("Europe/London"))

        self.assertEqual((deadline.hour, deadline.minute), (17, 0))
        self.assertEqual(deadline.date(), date(2026, 4, 10))

    def test_get_or_create_timesheet_for_period_creates_draft_and_due_dates(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)

        timesheet, created = get_or_create_timesheet_for_period(employee, date(2026, 4, 6))
        reopened_timesheet, reopened = get_or_create_timesheet_for_period(employee, date(2026, 4, 6))

        self.assertTrue(created)
        self.assertFalse(reopened)
        self.assertEqual(timesheet.pk, reopened_timesheet.pk)
        self.assertEqual(timesheet.approver, approver)
        self.assertEqual(timesheet.period_end, date(2026, 4, 10))
        self.assertEqual(timesheet.submission_due_at, to_business_deadline(date(2026, 4, 9)))
        self.assertEqual(timesheet.approval_due_at, to_business_deadline(date(2026, 4, 10)))
        self.assertTrue(timesheet.workflow_events.filter(event_type=WorkflowEvent.EventType.DRAFT_CREATED).exists())

    def test_get_or_create_timesheet_for_period_validates_monday_and_approver(self):
        employee_without_approver = self.create_user("employee.user", roles=["Employee"])

        with self.assertRaisesMessage(ValidationError, "You need an assigned approver before you can create a timesheet."):
            get_or_create_timesheet_for_period(employee_without_approver, date(2026, 4, 6))

        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.two", approver=approver)
        with self.assertRaisesMessage(ValidationError, "Timesheets must start on a Monday."):
            get_or_create_timesheet_for_period(employee, date(2026, 4, 7))

    def test_apply_entry_defaults_maps_category_and_fixed_hours(self):
        project = self.create_activity("P100", category="project", billing_type="billable")
        internal = self.create_activity("INT_001", category="internal", billing_type="internal")
        leave = self.create_activity(
            "LEAVE_001",
            category="annual_leave",
            billing_type="non_billable",
            fixed_hours=Decimal("3.75"),
            default_duration=Decimal("3.75"),
            is_system_controlled_hours=True,
        )
        employee = self.create_employee("employee.user", approver=self.create_approver("approver.user"))
        timesheet = self.create_timesheet(employee)

        project_entry = timesheet.entries.model(timesheet=timesheet, activity_code=project, work_date=timesheet.period_start, duration=1)
        internal_entry = timesheet.entries.model(timesheet=timesheet, activity_code=internal, work_date=timesheet.period_start, duration=1)
        leave_entry = timesheet.entries.model(timesheet=timesheet, activity_code=leave, work_date=timesheet.period_start, duration=1)

        apply_entry_defaults(project_entry)
        apply_entry_defaults(internal_entry)
        apply_entry_defaults(leave_entry)

        self.assertEqual(project_entry.entry_category, project_entry.EntryCategory.PROJECT_WORK)
        self.assertEqual(project_entry.billing_type, "billable")
        self.assertEqual(internal_entry.entry_category, internal_entry.EntryCategory.NON_PROJECT)
        self.assertEqual(internal_entry.billing_type, "internal")
        self.assertEqual(leave_entry.entry_category, leave_entry.EntryCategory.LEAVE)
        self.assertEqual(leave_entry.duration, Decimal("3.75"))
        self.assertTrue(leave_entry.system_controlled_hours)

    def test_validate_timesheet_for_submission_requires_entries_and_expected_total(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        project = self.create_activity("P100")
        self.assign_activity(employee, project)
        timesheet = self.create_timesheet(employee)

        with self.assertRaisesMessage(ValidationError, "Add at least one time entry before submitting."):
            validate_timesheet_for_submission(timesheet)

        self.add_entry(timesheet, project, duration=Decimal("10.00"))
        with self.assertRaisesMessage(ValidationError, "Weekly total must equal 37.50 hours before submission. Current total: 10."):
            validate_timesheet_for_submission(timesheet)

    def test_validate_timesheet_for_submission_rejects_unassigned_activity(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        assigned = self.create_activity("P100")
        unassigned = self.create_activity("P200")
        self.assign_activity(employee, assigned)
        timesheet = self.create_timesheet(employee)
        self.add_entry(timesheet, unassigned, duration=Decimal("37.50"), apply_defaults=False)

        with self.assertRaisesMessage(ValidationError, "P200 is not assigned to employee.user."):
            validate_timesheet_for_submission(timesheet)

    def test_validate_timesheet_for_submission_rejects_fixed_hour_override(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        leave_code = self.create_activity(
            "LEAVE_001",
            category="annual_leave",
            fixed_hours=Decimal("7.50"),
            default_duration=Decimal("7.50"),
            is_system_controlled_hours=True,
        )
        self.assign_activity(employee, leave_code)
        timesheet = self.create_timesheet(employee)
        self.add_entry(timesheet, leave_code, duration=Decimal("6.00"), apply_defaults=False)
        for offset in range(1, 5):
            project = self.create_activity(f"P10{offset}")
            self.assign_activity(employee, project)
            self.add_entry(
                timesheet,
                project,
                work_date=timesheet.period_start + timedelta(days=offset),
                duration=Decimal("9.00") if offset == 4 else Decimal("7.50"),
            )

        with self.assertRaisesMessage(ValidationError, "LEAVE_001 uses fixed hours of 7.50."):
            validate_timesheet_for_submission(timesheet)

    def test_submit_timesheet_creates_submission_event_and_notifications(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        project = self.create_activity("P100")
        self.assign_activity(employee, project)
        timesheet = self.create_timesheet(employee)
        self.add_week_entries(timesheet, project)

        submit_timesheet(timesheet, employee)

        timesheet.refresh_from_db()
        notifications = Notification.objects.filter(timesheet=timesheet).order_by("recipient__username")
        self.assertEqual(timesheet.status, Timesheet.Status.SUBMITTED)
        self.assertIsNotNone(timesheet.submitted_at)
        self.assertTrue(timesheet.workflow_events.filter(event_type=WorkflowEvent.EventType.SUBMITTED).exists())
        self.assertEqual(notifications.count(), 2)
        self.assertEqual(
            list(notifications.values_list("notification_type", flat=True)),
            [Notification.NotificationType.SUBMISSION, Notification.NotificationType.SUBMISSION],
        )

    def test_submit_timesheet_after_rejection_creates_resubmission_event_and_notifications(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        project = self.create_activity("P100")
        self.assign_activity(employee, project)
        timesheet = self.create_timesheet(
            employee,
            status=Timesheet.Status.REJECTED,
            latest_rejection_note="Please fix Monday.",
        )
        self.add_week_entries(timesheet, project)
        WorkflowEvent.objects.create(
            timesheet=timesheet,
            actor=approver,
            event_type=WorkflowEvent.EventType.REJECTED,
            comment="Please fix Monday.",
        )

        submit_timesheet(timesheet, employee)

        timesheet.refresh_from_db()
        notifications = Notification.objects.filter(timesheet=timesheet)
        self.assertEqual(timesheet.status, Timesheet.Status.SUBMITTED)
        self.assertTrue(timesheet.workflow_events.filter(event_type=WorkflowEvent.EventType.RESUBMITTED).exists())
        self.assertEqual(set(notifications.values_list("notification_type", flat=True)), {Notification.NotificationType.RESUBMISSION})

    def test_batch_submit_timesheets_submits_multiple_valid_timesheets(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        project = self.create_activity("P100")
        self.assign_activity(employee, project)
        first = self.create_timesheet(employee, period_start=date(2026, 4, 6))
        second = self.create_timesheet(employee, period_start=date(2026, 4, 13))
        self.add_week_entries(first, project)
        self.add_week_entries(second, project)

        submitted = batch_submit_timesheets(Timesheet.objects.filter(pk__in=[first.pk, second.pk]), employee)

        self.assertEqual(len(submitted), 2)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.status, Timesheet.Status.SUBMITTED)
        self.assertEqual(second.status, Timesheet.Status.SUBMITTED)

    def test_batch_submit_timesheets_is_all_or_nothing_for_invalid_selection(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        project = self.create_activity("P100")
        self.assign_activity(employee, project)
        valid_timesheet = self.create_timesheet(employee, period_start=date(2026, 4, 6))
        invalid_timesheet = self.create_timesheet(employee, period_start=date(2026, 4, 13))
        self.add_week_entries(valid_timesheet, project)
        self.add_entry(invalid_timesheet, project, duration=Decimal("5.00"))

        with self.assertRaisesMessage(ValidationError, "Weekly total must equal 37.50 hours before submission. Current total: 5."):
            batch_submit_timesheets(Timesheet.objects.filter(pk__in=[valid_timesheet.pk, invalid_timesheet.pk]), employee)

        valid_timesheet.refresh_from_db()
        invalid_timesheet.refresh_from_db()
        self.assertEqual(valid_timesheet.status, Timesheet.Status.IN_PROGRESS)
        self.assertEqual(invalid_timesheet.status, Timesheet.Status.IN_PROGRESS)
        self.assertFalse(Notification.objects.filter(timesheet__in=[valid_timesheet, invalid_timesheet]).exists())
