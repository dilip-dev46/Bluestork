from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.notification_list, name="list"),
    path("data/", views.notification_data, name="data"),
    path(
        "read/<int:notification_id>/",
        views.mark_as_read,
        name="mark_read"
    ),
    path(
        "read-all/",
        views.mark_all_as_read,
        name="mark_all_read"
    ),
]