from django.urls import reverse

from testsupport.factories import BaseAppTestCase


class DashboardViewTests(BaseAppTestCase):
    def test_home_requires_login(self):
        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_home_builds_employee_and_approver_dashboard_context_for_approvers(self):
        senior_approver = self.create_approver("senior.approver")
        approver = self.create_approver("approver.user", approver=senior_approver)
        self.client.force_login(approver)

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["employee_dashboard"])
        self.assertIsNotNone(response.context["approver_dashboard"])

    def test_home_hides_workflow_dashboards_for_hr_users(self):
        hr_user = self.create_hr("hr.user")
        self.client.force_login(hr_user)

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["employee_dashboard"])
        self.assertIsNone(response.context["approver_dashboard"])
