from django import forms
from .models import SupportTicket


class SupportTicketForm(forms.ModelForm):

    class Meta:
        model = SupportTicket
        fields = [
            "subject",
            "category",
            "description",
            "attachment",
        ]

        widgets = {
            "subject": forms.TextInput(attrs={
                "placeholder": "Enter your issue title",
                "class": "form-control",
            }),

            "category": forms.Select(attrs={
                "class": "form-control",
            }),

            "description": forms.Textarea(attrs={
                "placeholder": "Describe your issue (maximum 500 words)",
                "rows": 6,
                "class": "form-control",
            }),

            "attachment": forms.ClearableFileInput(attrs={
                "accept": "image/*",
                "class": "form-control",
            }),
        }

    def clean_description(self):
        description = self.cleaned_data.get("description", "")

        if len(description.split()) > 500:
            raise forms.ValidationError(
                "Your description cannot exceed 500 words."
            )

        return description

    def clean_attachment(self):
        attachment = self.cleaned_data.get("attachment")

        if attachment:
            if attachment.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    "Image size must be below 5 MB."
                )

            allowed_types = [
                "image/jpeg",
                "image/png",
                "image/webp",
            ]

            if attachment.content_type not in allowed_types:
                raise forms.ValidationError(
                    "Only JPG, PNG and WEBP images are allowed."
                )

        return attachment