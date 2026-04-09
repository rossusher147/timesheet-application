from apps.accounts.models import ROLE_APPROVER, ROLE_EMPLOYEE, ROLE_HR
from testsupport.factories import BaseAppTestCase


class UserModelTests(BaseAppTestCase):
    def test_role_helpers_reflect_group_membership(self):
        approver = self.create_approver("approver.user")
        employee = self.create_employee("employee.user", approver=approver)
        hr_user = self.create_hr("hr.user")

        self.assertTrue(employee.is_employee_role)
        self.assertFalse(employee.is_approver_role)
        self.assertEqual(employee.role_names, [ROLE_EMPLOYEE])

        self.assertTrue(approver.is_approver_role)
        self.assertEqual(approver.role_names, [ROLE_APPROVER])

        self.assertTrue(hr_user.is_hr_role)
        self.assertEqual(hr_user.role_names, [ROLE_HR])

    def test_assigned_activity_codes_are_distinct_and_ordered(self):
        employee = self.create_employee("employee.user", approver=self.create_approver("approver.user"))
        project_b = self.create_activity("P200")
        project_a = self.create_activity("P100")
        self.assign_activity(employee, project_b)
        self.assign_activity(employee, project_a)

        self.assertQuerySetEqual(employee.assigned_activity_codes, [project_a, project_b], transform=lambda value: value)
