from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password

from apps.activities.models import ActivityCode, UserActivityAssignment
from apps.accounts.models import ROLE_NAMES, User


class UserSearchForm(forms.Form):
    q = forms.CharField(required=False, label="Search")


class UserAdminBaseForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    assigned_activities = forms.ModelMultipleChoiceField(
        queryset=ActivityCode.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "business_unit",
            "weekly_contracted_hours",
            "approver",
        ]
        widgets = {
            "business_unit": forms.TextInput(attrs={"placeholder": "Business unit"}),
            "weekly_contracted_hours": forms.NumberInput(attrs={"step": "0.25"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["roles"].queryset = Group.objects.filter(name__in=ROLE_NAMES).order_by("name")
        self.fields["approver"].queryset = User.objects.order_by("username")
        self.fields["assigned_activities"].queryset = ActivityCode.objects.filter(is_active=True).order_by("code")

        if self.instance.pk:
            self.initial["roles"] = self.instance.groups.filter(name__in=ROLE_NAMES)
            self.initial["assigned_activities"] = self.instance.assigned_activity_codes
            self.fields["approver"].queryset = self.fields["approver"].queryset.exclude(pk=self.instance.pk)

    def _sync_roles(self, user):
        user.groups.set(self.cleaned_data.get("roles"))

    def _sync_assigned_activities(self, user):
        selected_codes = list(self.cleaned_data.get("assigned_activities", []))
        UserActivityAssignment.objects.filter(user=user).exclude(activity_code__in=selected_codes).delete()

        existing_code_ids = set(
            UserActivityAssignment.objects.filter(user=user, activity_code__in=selected_codes).values_list(
                "activity_code_id", flat=True
            )
        )
        assignments = [
            UserActivityAssignment(user=user, activity_code=activity_code)
            for activity_code in selected_codes
            if activity_code.pk not in existing_code_ids
        ]
        if assignments:
            UserActivityAssignment.objects.bulk_create(assignments)

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            self.save_m2m()
            self._sync_roles(user)
            self._sync_assigned_activities(user)
        return user

    def clean_roles(self):
        roles = self.cleaned_data.get("roles")
        if not roles:
            raise forms.ValidationError("Select at least one role.")
        return roles


class UserCreateForm(UserAdminBaseForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
    )

    class Meta(UserAdminBaseForm.Meta):
        fields = UserAdminBaseForm.Meta.fields

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields must match.")
        if password2:
            validate_password(password2)
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self.save_m2m()
            self._sync_roles(user)
            self._sync_assigned_activities(user)
        return user


class UserUpdateForm(UserAdminBaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].disabled = True
