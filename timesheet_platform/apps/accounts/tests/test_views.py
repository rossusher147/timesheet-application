from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import ROLE_APPROVER, ROLE_EMPLOYEE
from testsupport.factories import BaseAppTestCase, DEFAULT_PASSWORD


class AccountViewTests(BaseAppTestCase):
    def test_non_hr_user_is_redirected_from_people_search(self):
        employee = self.create_employee("employee.user", approver=self.create_approver("approver.user"))
        self.client.force_login(employee)

        response = self.client.get(reverse("accounts:search"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_hr_can_create_user_from_people_flow(self):
        hr_user = self.create_hr("hr.user")
        approver = self.create_approver("approver.user")
        project = self.create_activity("P100")
        self.client.force_login(hr_user)

        response = self.client.post(
            reverse("accounts:create"),
            data={
                "username": "employee.user",
                "first_name": "Employee",
                "last_name": "User",
                "email": "employee.user@example.com",
                "business_unit": "Consulting",
                "weekly_contracted_hours": "37.50",
                "approver": approver.pk,
                "roles": [self.role_group(ROLE_EMPLOYEE).pk],
                "assigned_activities": [project.pk],
                "password1": DEFAULT_PASSWORD,
                "password2": DEFAULT_PASSWORD,
            },
        )

        created_user = get_user_model().objects.get(username="employee.user")
        self.assertRedirects(response, reverse("accounts:detail", args=[created_user.pk]))
        self.assertEqual(created_user.approver, approver)
        self.assertEqual(created_user.role_names, [ROLE_EMPLOYEE])
        self.assertQuerySetEqual(created_user.assigned_activity_codes, [project], transform=lambda value: value)

    def test_hr_can_edit_user_profile(self):
        hr_user = self.create_hr("hr.user")
        first_approver = self.create_approver("approver.one")
        second_approver = self.create_approver("approver.two")
        employee = self.create_employee("employee.user", approver=first_approver)
        project = self.create_activity("P200")
        self.client.force_login(hr_user)

        response = self.client.post(
            reverse("accounts:edit", args=[employee.pk]),
            data={
                "username": employee.username,
                "first_name": "Updated",
                "last_name": "User",
                "email": employee.email,
                "business_unit": "Operations",
                "weekly_contracted_hours": "30.00",
                "approver": second_approver.pk,
                "roles": [self.role_group(ROLE_APPROVER).pk],
                "assigned_activities": [project.pk],
            },
        )

        self.assertRedirects(response, reverse("accounts:detail", args=[employee.pk]))
        employee.refresh_from_db()
        self.assertEqual(employee.first_name, "Updated")
        self.assertEqual(employee.approver, second_approver)
        self.assertEqual(employee.weekly_contracted_hours, 30)
        self.assertEqual(employee.role_names, [ROLE_APPROVER])
        self.assertQuerySetEqual(employee.assigned_activity_codes, [project], transform=lambda value: value)
