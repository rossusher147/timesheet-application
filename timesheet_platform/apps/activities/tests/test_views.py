from django.urls import reverse

from testsupport.factories import BaseAppTestCase


class ProjectViewTests(BaseAppTestCase):
    def test_non_hr_user_is_redirected_from_projects(self):
        employee = self.create_employee("employee.user", approver=self.create_approver("approver.user"))
        self.client.force_login(employee)

        response = self.client.get(reverse("activities:list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_hr_can_create_update_and_retire_project(self):
        hr_user = self.create_hr("hr.user")
        approver = self.create_approver("approver.user")
        employee_one = self.create_employee("employee.one", approver=approver)
        employee_two = self.create_employee("employee.two", approver=approver)
        self.client.force_login(hr_user)

        create_response = self.client.post(
            reverse("activities:create"),
            data={
                "code": "P100",
                "name": "Project Alpha",
                "billing_type_default": "billable",
                "assigned_users": [employee_one.pk],
            },
        )

        self.assertRedirects(create_response, reverse("activities:list"))
        project = employee_one.assigned_activity_codes.get(code="P100")

        edit_response = self.client.post(
            reverse("activities:edit", args=[project.pk]),
            data={
                "code": "P100",
                "name": "Project Alpha Updated",
                "billing_type_default": "non_billable",
                "assigned_users": [employee_two.pk],
            },
        )

        self.assertRedirects(edit_response, reverse("activities:list"))
        self.assertFalse(project.user_assignments.filter(user=employee_one).exists())
        self.assertTrue(project.user_assignments.filter(user=employee_two).exists())

        delete_response = self.client.post(reverse("activities:delete", args=[project.pk]))

        self.assertRedirects(delete_response, reverse("activities:list"))
        project.refresh_from_db()
        self.assertFalse(project.is_active)
        self.assertFalse(project.user_assignments.exists())
