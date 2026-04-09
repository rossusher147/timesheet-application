from datetime import date
from decimal import Decimal

from apps.activities.models import ActivityCode
from apps.timesheets.forms import TimeEntryForm, TimeEntryFormSet, TimesheetCreateForm
from testsupport.factories import BaseAppTestCase


class TimesheetCreateFormTests(BaseAppTestCase):
    def test_period_start_must_be_monday(self):
        form = TimesheetCreateForm(data={"period_start": "2026-04-07"})

        self.assertFalse(form.is_valid())
        self.assertIn("Timesheets must start on a Monday.", form.errors["period_start"])


class TimeEntryFormTests(BaseAppTestCase):
    def test_activity_queryset_only_shows_assigned_active_codes(self):
        employee = self.create_employee("employee.user", approver=self.create_approver("approver.user"))
        assigned_active = self.create_activity("P100")
        assigned_inactive = self.create_activity("P200", is_active=False)
        unassigned = self.create_activity("P300")
        self.assign_activity(employee, assigned_active)
        self.assign_activity(employee, assigned_inactive)

        form = TimeEntryForm(user=employee, period_start=date(2026, 4, 6), period_end=date(2026, 4, 10))

        self.assertQuerySetEqual(form.fields["activity_code"].queryset, [assigned_active], transform=lambda value: value)
        self.assertNotIn(unassigned, form.fields["activity_code"].queryset)

    def test_work_date_must_fall_within_timesheet_week(self):
        employee = self.create_employee("employee.user", approver=self.create_approver("approver.user"))
        project = self.create_activity("P100")
        self.assign_activity(employee, project)
        form = TimeEntryForm(
            data={
                "activity_code": project.pk,
                "work_date": "2026-04-11",
                "duration": "7.50",
                "notes": "",
            },
            user=employee,
            period_start=date(2026, 4, 6),
            period_end=date(2026, 4, 10),
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Entry date must fall within the Monday to Friday timesheet week.", form.errors["work_date"])

    def test_system_controlled_activity_overrides_manual_duration(self):
        employee = self.create_employee("employee.user", approver=self.create_approver("approver.user"))
        leave_code = self.create_activity(
            "LEAVE_001",
            category=ActivityCode.CATEGORY_ANNUAL_LEAVE,
            fixed_hours=Decimal("3.75"),
            default_duration=Decimal("3.75"),
            is_system_controlled_hours=True,
        )
        self.assign_activity(employee, leave_code)
        form = TimeEntryForm(
            data={
                "activity_code": leave_code.pk,
                "work_date": "2026-04-07",
                "duration": "1.00",
                "notes": "Attempted override",
            },
            user=employee,
            period_start=date(2026, 4, 6),
            period_end=date(2026, 4, 10),
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["duration"], Decimal("3.75"))


class TimeEntryFormSetTests(BaseAppTestCase):
    def test_formset_rejects_duplicate_activity_for_same_day(self):
        employee = self.create_employee("employee.user", approver=self.create_approver("approver.user"))
        project = self.create_activity("P100")
        self.assign_activity(employee, project)
        timesheet = self.create_timesheet(employee)
        formset = TimeEntryFormSet(
            data={
                "entries-TOTAL_FORMS": "2",
                "entries-INITIAL_FORMS": "0",
                "entries-MIN_NUM_FORMS": "0",
                "entries-MAX_NUM_FORMS": "1000",
                "entries-0-id": "",
                "entries-0-activity_code": str(project.pk),
                "entries-0-work_date": "2026-04-07",
                "entries-0-duration": "7.50",
                "entries-0-notes": "",
                "entries-1-id": "",
                "entries-1-activity_code": str(project.pk),
                "entries-1-work_date": "2026-04-07",
                "entries-1-duration": "7.50",
                "entries-1-notes": "",
            },
            instance=timesheet,
            user=employee,
            period_start=timesheet.period_start,
            period_end=timesheet.period_end,
        )

        self.assertFalse(formset.is_valid())
        self.assertIn("duplicate", str(formset.non_form_errors()).lower())
