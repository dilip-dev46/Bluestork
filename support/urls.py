from django.urls import path
from . import views

app_name = "support"

urlpatterns = [
    path("", views.help_support, name="help"),
    path("submit/", views.submit_ticket, name="submit"),
    path("my-tickets/", views.my_tickets, name="my_tickets"),
    path(
        "ticket/<int:ticket_id>/",
        views.ticket_detail,
        name="ticket_detail"
    ),
    path("about/", views.about_bluestork, name="about"),
]