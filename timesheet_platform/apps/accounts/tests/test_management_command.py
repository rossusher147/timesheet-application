import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.accounts.models import ROLE_HR
from apps.activities.models import ActivityCode
from testsupport.factories import BaseAppTestCase


class BootstrapDemoDataCommandTests(BaseAppTestCase):
    def test_command_creates_demo_hr_user_and_starter_codes(self):
        with patch.dict(
            os.environ,
            {
                "DEMO_HR_USERNAME": "demo.hr",
                "DEMO_HR_PASSWORD": "Replacement-pass12345",
                "DEMO_HR_FIRST_NAME": "Demo",
                "DEMO_HR_LAST_NAME": "HR",
                "RESET_DEMO_HR_PASSWORD": "true",
            },
            clear=False,
        ):
            call_command("bootstrap_demo_data")

        hr_user = get_user_model().objects.get(username="demo.hr")
        self.assertTrue(hr_user.check_password("Replacement-pass12345"))
        self.assertTrue(hr_user.is_staff)
        self.assertTrue(hr_user.is_superuser)
        self.assertTrue(hr_user.groups.filter(name=ROLE_HR).exists())
        self.assertEqual(ActivityCode.objects.count(), 4)

    def test_command_is_idempotent_for_existing_demo_user(self):
        existing_user = self.create_hr(
            "demo.hr",
            first_name="Old",
            last_name="Name",
            is_staff=False,
            is_superuser=False,
        )

        with patch.dict(
            os.environ,
            {
                "DEMO_HR_USERNAME": "demo.hr",
                "DEMO_HR_FIRST_NAME": "Updated",
                "DEMO_HR_LAST_NAME": "Demo",
                "RESET_DEMO_HR_PASSWORD": "false",
            },
            clear=False,
        ):
            call_command("bootstrap_demo_data")

        existing_user.refresh_from_db()
        self.assertEqual(existing_user.first_name, "Updated")
        self.assertEqual(existing_user.last_name, "Demo")
        self.assertTrue(existing_user.is_staff)
        self.assertTrue(existing_user.is_superuser)
