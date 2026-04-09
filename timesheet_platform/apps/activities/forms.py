from django import forms

from apps.accounts.models import ROLE_HR, User

from .models import ActivityCode, UserActivityAssignment


class ProjectForm(forms.ModelForm):
    assigned_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Choose the users who should be able to book against this project.",
    )

    class Meta:
        model = ActivityCode
        fields = ("code", "name", "billing_type_default")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_users"].queryset = (
            User.objects.filter(is_active=True)
            .exclude(groups__name=ROLE_HR)
            .distinct()
            .order_by("first_name", "last_name", "username")
        )
        self.fields["billing_type_default"].initial = ActivityCode.BILLING_BILLABLE
        if self.instance.pk:
            self.initial["assigned_users"] = self.instance.user_assignments.values_list("user_id", flat=True)

    def save(self, commit=True):
        project = super().save(commit=False)
        project.category = ActivityCode.CATEGORY_PROJECT
        project.is_system_controlled_hours = False
        project.fixed_hours = None
        project.default_duration = None
        project.is_active = True
        if commit:
            project.save()
            self.save_m2m()
            self._sync_assignments(project)
        return project

    def _sync_assignments(self, project):
        selected_users = list(self.cleaned_data.get("assigned_users", []))
        UserActivityAssignment.objects.filter(activity_code=project).exclude(user__in=selected_users).delete()
        existing_user_ids = set(
            UserActivityAssignment.objects.filter(activity_code=project, user__in=selected_users).values_list(
                "user_id", flat=True
            )
        )
        assignments = [
            UserActivityAssignment(user=user, activity_code=project)
            for user in selected_users
            if user.pk not in existing_user_ids
        ]
        if assignments:
            UserActivityAssignment.objects.bulk_create(assignments)
