from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from apps.timesheets.models import Timesheet
from apps.timesheets.services import week_dates

from .forms import RejectionForm
from .services import approve_timesheet, reject_timesheet


def _ensure_approver(user):
    if not getattr(user, "is_approver_role", False) or getattr(user, "is_hr_role", False):
        raise PermissionDenied


@login_required
def approval_queue(request):
    _ensure_approver(request.user)
    queue = Timesheet.objects.filter(
        approver=request.user,
        status=Timesheet.Status.SUBMITTED,
    ).select_related("user")
    waiting_for_resubmission = Timesheet.objects.filter(
        approver=request.user,
        status=Timesheet.Status.REJECTED,
    ).select_related("user")
    return render(
        request,
        "approvals/queue.html",
        {
            "queue": queue,
            "waiting_for_resubmission": waiting_for_resubmission,
        },
    )


@login_required
def approval_detail(request, pk):
    _ensure_approver(request.user)
    timesheet = get_object_or_404(
        Timesheet.objects.select_related("user", "approver").prefetch_related(
            "entries__activity_code",
            "workflow_events__actor",
        ),
        pk=pk,
        approver=request.user,
    )
    entries = list(timesheet.entries.select_related("activity_code"))
    entries_by_day = {
        day: [entry for entry in entries if entry.work_date == day]
        for day in week_dates(timesheet.period_start)
    }
    return render(
        request,
        "approvals/detail.html",
        {
            "timesheet": timesheet,
            "entries_by_day": entries_by_day,
            "week_days": week_dates(timesheet.period_start),
            "rejection_form": RejectionForm(),
        },
    )


@login_required
def approval_approve(request, pk):
    _ensure_approver(request.user)
    if request.method != "POST":
        raise PermissionDenied
    timesheet = get_object_or_404(Timesheet, pk=pk, approver=request.user)
    try:
        approve_timesheet(timesheet, request.user)
    except ValidationError as exc:
        messages.error(request, exc.message)
    else:
        messages.success(request, "Timesheet approved.")
    return redirect("approvals:detail", pk=pk)


@login_required
def approval_reject(request, pk):
    _ensure_approver(request.user)
    if request.method != "POST":
        raise PermissionDenied
    timesheet = get_object_or_404(Timesheet, pk=pk, approver=request.user)
    form = RejectionForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Add a rejection note before rejecting a timesheet.")
        return redirect("approvals:detail", pk=pk)
    try:
        reject_timesheet(timesheet, request.user, form.cleaned_data["rejection_note"])
    except ValidationError as exc:
        messages.error(request, exc.message)
    else:
        messages.success(request, "Timesheet rejected and sent back to the employee.")
    return redirect("approvals:detail", pk=pk)
