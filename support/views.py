from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404

from .models import SupportTicket
from .forms import SupportTicketForm


@login_required
def help_support(request):
    form = SupportTicketForm()

    tickets = SupportTicket.objects.filter(
        user=request.user
    )[:5]

    return render(request, "support/help_support.html", {
        "form": form,
        "tickets": tickets,
    })


@login_required
def submit_ticket(request):
    if request.method == "POST":
        form = SupportTicketForm(request.POST, request.FILES)

        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()

            messages.success(
                request,
                f"Your support ticket #{ticket.id} was submitted successfully."
            )

            return redirect("support:my_tickets")

        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)

    return redirect("support:help")


@login_required
def my_tickets(request):
    tickets = SupportTicket.objects.filter(
        user=request.user
    )

    return render(request, "support/my_tickets.html", {
        "tickets": tickets
    })


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(
        SupportTicket,
        id=ticket_id,
        user=request.user
    )

    return render(request, "support/ticket_detail.html", {
        "ticket": ticket
    })


def about_bluestork(request):
    return render(request, "support/about.html")