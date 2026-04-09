from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import build_approver_dashboard, build_employee_dashboard


@login_required
def home(request):
    employee_dashboard = None
    approver_dashboard = None
    if not getattr(request.user, "is_hr_role", False):
        employee_dashboard = build_employee_dashboard(request.user)
    if getattr(request.user, "is_approver_role", False) and not getattr(request.user, "is_hr_role", False):
        approver_dashboard = build_approver_dashboard(request.user)
    return render(
        request,
        "dashboards/home.html",
        {
            "employee_dashboard": employee_dashboard,
            "approver_dashboard": approver_dashboard,
        },
    )
