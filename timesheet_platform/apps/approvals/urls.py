from django.urls import path

from . import views


urlpatterns = [
    path("", views.approval_queue, name="queue"),
    path("<int:pk>/", views.approval_detail, name="detail"),
    path("<int:pk>/approve/", views.approval_approve, name="approve"),
    path("<int:pk>/reject/", views.approval_reject, name="reject"),
]
