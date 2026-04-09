from apps.accounts.forms import UserCreateForm, UserUpdateForm
from apps.accounts.models import ROLE_APPROVER, ROLE_EMPLOYEE
from testsupport.factories import BaseAppTestCase, DEFAULT_PASSWORD


class UserCreateFormTests(BaseAppTestCase):
    def test_create_form_creates_user_with_roles_and_assignments(self):
        approver = self.create_approver("approver.user")
        project = self.create_activity("P100")
        form = UserCreateForm(
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
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()

        self.assertTrue(user.check_password(DEFAULT_PASSWORD))
        self.assertEqual(user.approver, approver)
        self.assertEqual(user.role_names, [ROLE_EMPLOYEE])
        self.assertQuerySetEqual(user.assigned_activity_codes, [project], transform=lambda value: value)

    def test_create_form_requires_at_least_one_role(self):
        approver = self.create_approver("approver.user")
        form = UserCreateForm(
            data={
                "username": "employee.user",
                "first_name": "Employee",
                "last_name": "User",
                "email": "employee.user@example.com",
                "business_unit": "Consulting",
                "weekly_contracted_hours": "37.50",
                "approver": approver.pk,
                "roles": [],
                "password1": DEFAULT_PASSWORD,
                "password2": DEFAULT_PASSWORD,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Select at least one role.", form.errors["roles"])


class UserUpdateFormTests(BaseAppTestCase):
    def test_update_form_disables_username(self):
        user = self.create_employee("employee.user", approver=self.create_approver("approver.user"))
        form = UserUpdateForm(instance=user)

        self.assertTrue(form.fields["username"].disabled)

    def test_update_form_syncs_roles_and_assigned_activities(self):
        first_approver = self.create_approver("approver.one")
        second_approver = self.create_approver("approver.two")
        user = self.create_employee("employee.user", approver=first_approver)
        original_project = self.create_activity("P100")
        replacement_project = self.create_activity("P200")
        self.assign_activity(user, original_project)

        form = UserUpdateForm(
            data={
                "username": user.username,
                "first_name": "Updated",
                "last_name": "User",
                "email": user.email,
                "business_unit": "Operations",
                "weekly_contracted_hours": "30.00",
                "approver": second_approver.pk,
                "roles": [self.role_group(ROLE_APPROVER).pk],
                "assigned_activities": [replacement_project.pk],
            },
            instance=user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        updated_user = form.save()

        updated_user.refresh_from_db()
        self.assertEqual(updated_user.first_name, "Updated")
        self.assertEqual(updated_user.approver, second_approver)
        self.assertEqual(updated_user.weekly_contracted_hours, 30)
        self.assertEqual(updated_user.role_names, [ROLE_APPROVER])
        self.assertQuerySetEqual(updated_user.assigned_activity_codes, [replacement_project], transform=lambda value: value)
