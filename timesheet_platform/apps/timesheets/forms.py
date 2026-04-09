from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from .models import TimeEntry, Timesheet


class TimesheetCreateForm(forms.Form):
    period_start = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Choose the Monday for the week you want to create.",
    )

    def clean_period_start(self):
        period_start = self.cleaned_data["period_start"]
        if period_start.weekday() != 0:
            raise forms.ValidationError("Timesheets must start on a Monday.")
        return period_start


class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ("activity_code", "work_date", "duration", "notes")
        widgets = {
            "work_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, user=None, period_start=None, period_end=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.period_start = period_start
        self.period_end = period_end
        if user is not None:
            self.fields["activity_code"].queryset = (
                self.fields["activity_code"]
                .queryset.filter(user_assignments__user=user, is_active=True)
                .distinct()
                .order_by("code")
            )
        if period_start and period_end:
            self.fields["work_date"].help_text = f"Use dates from {period_start} to {period_end}."

    def clean_work_date(self):
        work_date = self.cleaned_data.get("work_date")
        if work_date and self.period_start and self.period_end:
            if work_date < self.period_start or work_date > self.period_end:
                raise forms.ValidationError("Entry date must fall within the Monday to Friday timesheet week.")
        return work_date

    def clean(self):
        cleaned_data = super().clean()
        activity_code = cleaned_data.get("activity_code")
        work_date = cleaned_data.get("work_date")
        if not activity_code or not work_date:
            return cleaned_data

        if activity_code.is_system_controlled_hours:
            fixed_hours = activity_code.fixed_hours or activity_code.default_duration
            cleaned_data["duration"] = fixed_hours
            self.cleaned_data["duration"] = fixed_hours
        return cleaned_data


class BaseTimeEntryFormSet(BaseInlineFormSet):
    def __init__(self, *args, user=None, period_start=None, period_end=None, **kwargs):
        self.user = user
        self.period_start = period_start
        self.period_end = period_end
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs.update(
            {
                "user": self.user,
                "period_start": self.period_start,
                "period_end": self.period_end,
            }
        )
        return kwargs

    def clean(self):
        super().clean()
        seen = set()
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            activity_code = form.cleaned_data.get("activity_code")
            work_date = form.cleaned_data.get("work_date")
            if not activity_code or not work_date:
                continue
            key = (activity_code.pk, work_date)
            if key in seen:
                raise forms.ValidationError("Use only one row per activity code and day in a timesheet.")
            seen.add(key)


TimeEntryFormSet = inlineformset_factory(
    Timesheet,
    TimeEntry,
    form=TimeEntryForm,
    formset=BaseTimeEntryFormSet,
    extra=5,
    can_delete=True,
)
