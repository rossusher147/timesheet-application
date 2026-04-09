from apps.activities.forms import ProjectForm
from apps.activities.models import ActivityCode, UserActivityAssignment
from testsupport.factories import BaseAppTestCase


class ProjectFormTests(BaseAppTestCase):
    def test_project_form_creates_project_and_assignments(self):
        employee = self.create_employee("employee.user", approver=self.create_approver("approver.user"))
        form = ProjectForm(
            data={
                "code": "P100",
                "name": "Project Alpha",
                "billing_type_default": ActivityCode.BILLING_BILLABLE,
                "assigned_users": [employee.pk],
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        project = form.save()

        self.assertEqual(project.category, ActivityCode.CATEGORY_PROJECT)
        self.assertTrue(project.is_active)
        self.assertFalse(project.is_system_controlled_hours)
        self.assertTrue(UserActivityAssignment.objects.filter(user=employee, activity_code=project).exists())

    def test_project_form_updates_assignments(self):
        approver = self.create_approver("approver.user")
        first_employee = self.create_employee("employee.one", approver=approver)
        second_employee = self.create_employee("employee.two", approver=approver)
        project = self.create_activity("P100")
        self.assign_activity(first_employee, project)

        form = ProjectForm(
            data={
                "code": project.code,
                "name": "Project Alpha",
                "billing_type_default": ActivityCode.BILLING_NON_BILLABLE,
                "assigned_users": [second_employee.pk],
            },
            instance=project,
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertFalse(UserActivityAssignment.objects.filter(user=first_employee, activity_code=project).exists())
        self.assertTrue(UserActivityAssignment.objects.filter(user=second_employee, activity_code=project).exists())
