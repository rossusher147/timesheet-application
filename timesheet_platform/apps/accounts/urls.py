from django.urls import path

from apps.accounts import views


app_name = "accounts"

urlpatterns = [
    path("", views.user_search, name="search"),
    path("search/", views.user_search, name="search_alt"),
    path("create/", views.user_create, name="create"),
    path("<int:pk>/", views.user_detail, name="detail"),
    path("<int:pk>/edit/", views.user_edit, name="edit"),
]
