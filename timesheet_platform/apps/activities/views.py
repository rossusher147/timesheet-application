from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProjectForm
from .models import ActivityCode


def is_hr(user):
    return user.is_authenticated and getattr(user, "is_hr_role", False)


hr_required = user_passes_test(is_hr)


@login_required
@hr_required
def project_list(request):
    projects = ActivityCode.objects.filter(
        category=ActivityCode.CATEGORY_PROJECT,
        is_active=True,
    ).prefetch_related("user_assignments__user")
    return render(request, "activities/project_list.html", {"projects": projects})


@login_required
@hr_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            messages.success(request, f"Created project {project.code}.")
            return redirect("activities:list")
    else:
        form = ProjectForm()
    return render(request, "activities/project_form.html", {"form": form, "mode": "create"})


@login_required
@hr_required
def project_edit(request, pk):
    project = get_object_or_404(
        ActivityCode,
        pk=pk,
        category=ActivityCode.CATEGORY_PROJECT,
    )
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated project {project.code}.")
            return redirect("activities:list")
    else:
        form = ProjectForm(instance=project)
    return render(
        request,
        "activities/project_form.html",
        {"form": form, "mode": "edit", "project": project},
    )


@login_required
@hr_required
def project_delete(request, pk):
    if request.method != "POST":
        return redirect("activities:list")
    project = get_object_or_404(
        ActivityCode,
        pk=pk,
        category=ActivityCode.CATEGORY_PROJECT,
    )
    project.user_assignments.all().delete()
    project.is_active = False
    project.save(update_fields=["is_active", "updated_at"])
    messages.success(request, f"Removed user assignments and retired project {project.code}.")
    return redirect("activities:list")
