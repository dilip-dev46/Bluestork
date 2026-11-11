from django.contrib import admin
from .models import SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "subject",
        "category",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "category",
        "created_at",
    )

    search_fields = (
        "user__username",
        "subject",
        "description",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_editable = ("status",)

    ordering = ("-created_at",)