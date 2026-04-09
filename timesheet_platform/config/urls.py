from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import include, path


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")
    return redirect("login")


urlpatterns = [
    path("", root_redirect, name="root"),
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", include(("apps.dashboards.urls", "dashboard"), namespace="dashboard")),
    path("timesheets/", include(("apps.timesheets.urls", "timesheets"), namespace="timesheets")),
    path("approvals/", include(("apps.approvals.urls", "approvals"), namespace="approvals")),
    path("people/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("projects/", include(("apps.activities.urls", "activities"), namespace="activities")),
]
