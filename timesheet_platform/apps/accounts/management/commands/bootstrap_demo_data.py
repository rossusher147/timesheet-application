from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from apps.activities.models import ActivityCode
from apps.accounts.models import ROLE_APPROVER, ROLE_EMPLOYEE, ROLE_HR


class Command(BaseCommand):
    help = "Bootstrap local demo data for the MVP."

    def handle(self, *args, **options):
        for role_name in (ROLE_EMPLOYEE, ROLE_APPROVER, ROLE_HR):
            Group.objects.get_or_create(name=role_name)

        User = get_user_model()
        hr_username = self._env("DEMO_HR_USERNAME", "demo.hr")
        hr_password = self._env("DEMO_HR_PASSWORD", "demo-hr-password")
        hr_first_name = self._env("DEMO_HR_FIRST_NAME", "Demo")
        hr_last_name = self._env("DEMO_HR_LAST_NAME", "HR")
        hr_email = self._env("DEMO_HR_EMAIL", "demo.hr@example.com")
        hr_business_unit = self._env("DEMO_HR_BUSINESS_UNIT", "Operations")
        hr_is_staff = self._env("DEMO_HR_IS_STAFF", "true").lower() == "true"
        hr_is_superuser = self._env("DEMO_HR_IS_SUPERUSER", "true").lower() == "true"
        reset_password = self._env("RESET_DEMO_HR_PASSWORD", "false").lower() == "true"

        user, created = User.objects.get_or_create(
            username=hr_username,
            defaults={
                "first_name": hr_first_name,
                "last_name": hr_last_name,
                "email": hr_email,
                "business_unit": hr_business_unit,
                "weekly_contracted_hours": Decimal("37.50"),
                "is_staff": hr_is_staff,
                "is_superuser": hr_is_superuser,
                "is_active": True,
            },
        )

        if not created:
            user.first_name = hr_first_name
            user.last_name = hr_last_name
            user.email = hr_email
            user.business_unit = hr_business_unit
            user.weekly_contracted_hours = Decimal("37.50")
            user.is_staff = hr_is_staff
            user.is_superuser = hr_is_superuser
            user.is_active = True

        if created or reset_password:
            user.set_password(hr_password)
        user.save()
        user.groups.add(Group.objects.get(name=ROLE_HR))

        starter_codes = [
            ("P00012", "Project 00012", "project", "billable", None, None, False),
            ("LEAVE_001", "Annual Leave", "annual_leave", "non_billable", Decimal("3.75"), Decimal("3.75"), True),
            ("SICK_001", "Sick Leave", "sick_leave", "non_billable", Decimal("7.50"), Decimal("7.50"), True),
            ("BANK_001", "Bank Holiday", "bank_holiday", "non_billable", Decimal("7.50"), Decimal("7.50"), True),
        ]
        for code, name, category, billing_type, fixed_hours, default_duration, system_controlled in starter_codes:
            ActivityCode.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "category": category,
                    "billing_type_default": billing_type,
                    "fixed_hours": fixed_hours,
                    "default_duration": default_duration,
                    "is_system_controlled_hours": system_controlled,
                    "is_active": True,
                },
            )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created demo HR account '{user.username}'."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated demo HR account '{user.username}'."))
        if reset_password:
            self.stdout.write(self.style.WARNING("Demo HR password was reset from environment input."))
        self.stdout.write(self.style.SUCCESS("Seeded starter activity codes."))

    def _env(self, name, default):
        from os import getenv

        return getenv(name, default)
