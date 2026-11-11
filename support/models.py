from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class SupportTicket(models.Model):

    CATEGORY_CHOICES = [
        ("account", "Account Issues"),
        ("parcel", "Parcel & Delivery"),
        ("payment", "Payment Issues"),
        ("partner", "Partner Issues"),
        ("technical", "Technical Problems"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_tickets"
    )

    subject = models.CharField(max_length=150)

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="other"
    )

    description = models.TextField()

    attachment = models.ImageField(
        upload_to="support/attachments/",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    admin_response = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if len(self.description.split()) > 500:
            raise ValidationError({
                "description": "Description cannot exceed 500 words."
            })

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject}"

    class Meta:
        ordering = ["-created_at"]