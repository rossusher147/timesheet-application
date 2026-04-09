from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.accounts.forms import UserCreateForm, UserSearchForm, UserUpdateForm
from apps.accounts.models import ROLE_HR, User


def is_hr(user):
    return user.is_authenticated and user.groups.filter(name=ROLE_HR).exists()


hr_required = user_passes_test(is_hr)


@login_required
@hr_required
def user_search(request):
    form = UserSearchForm(request.GET or None)
    users = User.objects.select_related("approver").prefetch_related("groups").all()

    if form.is_valid():
        query = form.cleaned_data.get("q")
        if query:
            users = users.filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
                | Q(business_unit__icontains=query)
            )

    users = users.order_by("last_name", "first_name", "username")
    return render(request, "accounts/user_search.html", {"form": form, "users": users})


@login_required
@hr_required
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Created user {user.username}.")
            return redirect(reverse("accounts:detail", args=[user.pk]))
    else:
        form = UserCreateForm()

    return render(request, "accounts/user_form.html", {"form": form, "mode": "create"})


@login_required
@hr_required
def user_detail(request, pk):
    user_obj = get_object_or_404(User.objects.select_related("approver").prefetch_related("groups"), pk=pk)
    return render(request, "accounts/user_detail.html", {"profile_user": user_obj})


@login_required
@hr_required
def user_edit(request, pk):
    user_obj = get_object_or_404(User.objects.select_related("approver").prefetch_related("groups"), pk=pk)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated profile for {user_obj.username}.")
            return redirect(reverse("accounts:detail", args=[user_obj.pk]))
    else:
        form = UserUpdateForm(instance=user_obj)

    return render(
        request,
        "accounts/user_form.html",
        {"profile_user": user_obj, "form": form, "mode": "edit"},
    )
