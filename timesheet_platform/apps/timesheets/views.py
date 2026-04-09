from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TimeEntryFormSet, TimesheetCreateForm
from .models import TimeEntry, Timesheet
from .services import (
    apply_entry_defaults,
    batch_submit_timesheets,
    current_week_start,
    get_or_create_timesheet_for_period,
    submit_timesheet,
    week_dates,
)


def _ensure_timesheet_access(request_user, timesheet):
    if getattr(request_user, "is_hr_role", False):
        raise PermissionDenied
    if timesheet.user_id != request_user.id:
        raise PermissionDenied


def _group_entries_by_day(timesheet):
    grouped = {day: [] for day in week_dates(timesheet.period_start)}
    for entry in timesheet.entries.select_related("activity_code"):
        grouped.setdefault(entry.work_date, []).append(entry)
    return grouped


@login_required
def timesheet_list(request):
    if getattr(request.user, "is_hr_role", False):
        raise PermissionDenied

    create_form = TimesheetCreateForm(initial={"period_start": current_week_start().isoformat()})
    timesheets = request.user.timesheets.select_related("approver").prefetch_related(
        Prefetch("entries", queryset=TimeEntry.objects.select_related("activity_code"))
    )
    return render(
        request,
        "timesheets/list.html",
        {
            "create_form": create_form,
            "timesheets": timesheets,
        },
    )


@login_required
def create_timesheet(request):
    if getattr(request.user, "is_hr_role", False):
        raise PermissionDenied
    if request.method != "POST":
        return redirect("timesheets:list")

    form = TimesheetCreateForm(request.POST)
    if not form.is_valid():
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
        return redirect("timesheets:list")

    try:
        timesheet, created = get_or_create_timesheet_for_period(request.user, form.cleaned_data["period_start"])
    except ValidationError as exc:
        messages.error(request, exc.message)
        return redirect("timesheets:list")

    messages.success(request, "Timesheet created." if created else "That timesheet already exists, so we opened it for you.")
    return redirect("timesheets:edit", pk=timesheet.pk)


@login_required
def timesheet_detail(request, pk):
    timesheet = get_object_or_404(
        Timesheet.objects.select_related("approver", "user").prefetch_related(
            "workflow_events__actor",
            "notifications",
            "entries__activity_code",
        ),
        pk=pk,
    )
    _ensure_timesheet_access(request.user, timesheet)
    return render(
        request,
        "timesheets/detail.html",
        {
            "timesheet": timesheet,
            "entries_by_day": _group_entries_by_day(timesheet),
            "week_days": week_dates(timesheet.period_start),
        },
    )


@login_required
def edit_timesheet(request, pk):
    timesheet = get_object_or_404(
        Timesheet.objects.select_related("approver", "user").prefetch_related("entries__activity_code"),
        pk=pk,
    )
    _ensure_timesheet_access(request.user, timesheet)
    if timesheet.status == Timesheet.Status.APPROVED:
        raise PermissionDenied

    if request.method == "POST":
        formset = TimeEntryFormSet(
            request.POST,
            instance=timesheet,
            user=request.user,
            period_start=timesheet.period_start,
            period_end=timesheet.period_end,
        )
        action = request.POST.get("action", "save")
        if formset.is_valid():
            instances = formset.save(commit=False)
            for deleted in formset.deleted_objects:
                deleted.delete()
            for instance in instances:
                apply_entry_defaults(instance)
                instance.save()
            formset.save_m2m()
            messages.success(request, "Timesheet draft saved.")
            if action == "submit":
                try:
                    submit_timesheet(timesheet, request.user)
                except ValidationError as exc:
                    messages.error(request, exc.message)
                else:
                    messages.success(request, "Timesheet submitted for approval.")
                    return redirect("timesheets:detail", pk=timesheet.pk)
            return redirect("timesheets:edit", pk=timesheet.pk)
    else:
        formset = TimeEntryFormSet(
            instance=timesheet,
            user=request.user,
            period_start=timesheet.period_start,
            period_end=timesheet.period_end,
        )

    return render(
        request,
        "timesheets/form.html",
        {
            "timesheet": timesheet,
            "formset": formset,
            "week_days": week_dates(timesheet.period_start),
        },
    )


@login_required
def batch_submit(request):
    if getattr(request.user, "is_hr_role", False):
        raise PermissionDenied
    if request.method != "POST":
        raise PermissionDenied

    selected_ids = request.POST.getlist("selected_timesheets")
    queryset = Timesheet.objects.filter(
        user=request.user,
        pk__in=selected_ids,
        status__in=[Timesheet.Status.IN_PROGRESS, Timesheet.Status.REJECTED],
    ).select_related("approver", "user")
    if not queryset.exists():
        messages.error(request, "Choose at least one timesheet to submit.")
        return redirect("timesheets:list")

    try:
        submitted = batch_submit_timesheets(queryset, request.user)
    except ValidationError as exc:
        messages.error(request, exc.message)
    else:
        messages.success(request, f"Submitted {len(submitted)} timesheet(s).")
    return redirect("timesheets:list")
