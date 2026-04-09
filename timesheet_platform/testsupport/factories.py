from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from apps.accounts.models import ROLE_APPROVER, ROLE_EMPLOYEE, ROLE_HR, ROLE_NAMES
from apps.activities.models import ActivityCode, UserActivityAssignment
from apps.timesheets.models import TimeEntry, Timesheet
from apps.timesheets.services import apply_entry_defaults, to_business_deadline


DEFAULT_PASSWORD = "Valid-pass12345"
DEFAULT_WEEK_START = date(2026, 4, 6)


class BaseAppTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for role_name in ROLE_NAMES:
            Group.objects.get_or_create(name=role_name)

    def role_group(self, role_name):
        return Group.objects.get(name=role_name)

    def create_user(
        self,
        username,
        *,
        roles=None,
        approver=None,
        password=DEFAULT_PASSWORD,
        first_name="Test",
        last_name="User",
        email="",
        weekly_hours=Decimal("37.50"),
        **extra_fields,
    ):
        user = get_user_model().objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email or f"{username}@example.com",
            weekly_contracted_hours=Decimal(str(weekly_hours)),
            approver=approver,
            **extra_fields,
        )
        if roles:
            user.groups.set(Group.objects.filter(name__in=roles))
        return user

    def create_employee(self, username, *, approver, **extra_fields):
        return self.create_user(username, roles=[ROLE_EMPLOYEE], approver=approver, **extra_fields)

    def create_approver(self, username, *, approver=None, **extra_fields):
        return self.create_user(username, roles=[ROLE_APPROVER], approver=approver, **extra_fields)

    def create_hr(self, username, **extra_fields):
        return self.create_user(username, roles=[ROLE_HR], **extra_fields)

    def create_activity(
        self,
        code,
        *,
        name=None,
        category=ActivityCode.CATEGORY_PROJECT,
        billing_type=None,
        fixed_hours=None,
        default_duration=None,
        is_system_controlled_hours=False,
        is_active=True,
    ):
        if billing_type is None:
            if category == ActivityCode.CATEGORY_PROJECT:
                billing_type = ActivityCode.BILLING_BILLABLE
            elif category == ActivityCode.CATEGORY_INTERNAL:
                billing_type = ActivityCode.BILLING_INTERNAL
            else:
                billing_type = ActivityCode.BILLING_NON_BILLABLE

        return ActivityCode.objects.create(
            code=code,
            name=name or code,
            category=category,
            billing_type_default=billing_type,
            fixed_hours=fixed_hours,
            default_duration=default_duration,
            is_system_controlled_hours=is_system_controlled_hours,
            is_active=is_active,
        )

    def assign_activity(self, user, activity_code, *, assigned_by=None):
        return UserActivityAssignment.objects.create(
            user=user,
            activity_code=activity_code,
            assigned_by=assigned_by,
        )

    def create_timesheet(
        self,
        user,
        *,
        approver=None,
        period_start=DEFAULT_WEEK_START,
        status=Timesheet.Status.IN_PROGRESS,
        submission_due_at=None,
        approval_due_at=None,
        latest_rejection_note="",
    ):
        approver = approver or user.approver or user
        period_end = period_start + timedelta(days=4)
        return Timesheet.objects.create(
            user=user,
            approver=approver,
            period_start=period_start,
            period_end=period_end,
            status=status,
            submission_due_at=submission_due_at or to_business_deadline(period_start + timedelta(days=3)),
            approval_due_at=approval_due_at or to_business_deadline(period_start + timedelta(days=4)),
            latest_rejection_note=latest_rejection_note,
        )

    def add_entry(
        self,
        timesheet,
        activity_code,
        *,
        work_date=None,
        duration=Decimal("7.50"),
        notes="",
        apply_defaults=True,
    ):
        entry = TimeEntry(
            timesheet=timesheet,
            activity_code=activity_code,
            work_date=work_date or timesheet.period_start,
            duration=Decimal(str(duration)),
            notes=notes,
        )
        if apply_defaults:
            apply_entry_defaults(entry)
        entry.save()
        return entry

    def add_week_entries(self, timesheet, activity_code, *, hours_per_day=Decimal("7.50"), notes=""):
        entries = []
        for day_offset in range(5):
            entries.append(
                self.add_entry(
                    timesheet,
                    activity_code,
                    work_date=timesheet.period_start + timedelta(days=day_offset),
                    duration=hours_per_day,
                    notes=notes,
                )
            )
        return entries
