from django.urls import path

from . import views


urlpatterns = [
    path("", views.timesheet_list, name="list"),
    path("new/", views.create_timesheet, name="create"),
    path("batch-submit/", views.batch_submit, name="batch_submit"),
    path("<int:pk>/", views.timesheet_detail, name="detail"),
    path("<int:pk>/edit/", views.edit_timesheet, name="edit"),
]
