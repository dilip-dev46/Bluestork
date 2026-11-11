from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Parcel, PartnerRoute, Profile
from .utils import MAX_WEIGHT_KG

User = get_user_model()


# --------------------------------------------------
# Signup form
# --------------------------------------------------

class SignupForm(UserCreationForm):
    full_name = forms.CharField(max_length=60)
    phone = forms.CharField(max_length=15)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def save_with_role(self, role):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["full_name"]
        user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = role
        profile.phone = self.cleaned_data["phone"]

        self.fill_profile(profile)
        profile.save()

        return user

    def fill_profile(self, profile):
        pass


class PartnerSignupForm(SignupForm):
    vehicle_type = forms.ChoiceField(choices=Profile.VEHICLES)

    vehicle_number = forms.CharField(
        max_length=20,
        label="Vehicle number"
    )

    capacity_kg = forms.IntegerField(
        min_value=1,
        max_value=500,
        initial=10,
        label="Parcel capacity (kg)"
    )

    def fill_profile(self, profile):
        profile.vehicle_type = self.cleaned_data["vehicle_type"]
        profile.vehicle_number = self.cleaned_data["vehicle_number"]
        profile.capacity_kg = self.cleaned_data["capacity_kg"]


# --------------------------------------------------
# User profile form
# Only name and email are editable
# --------------------------------------------------

class UserProfileForm(forms.ModelForm):

    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "email",
        ]

        labels = {
            "first_name": "First name",
            "last_name": "Last name",
            "email": "Email address",
        }

        widgets = {
            "first_name": forms.TextInput(
                attrs={"placeholder": "Enter first name"}
            ),

            "last_name": forms.TextInput(
                attrs={"placeholder": "Enter last name"}
            ),

            "email": forms.EmailInput(
                attrs={"placeholder": "Enter email address"}
            ),
        }


# --------------------------------------------------
# Customer and assigner profile details
# --------------------------------------------------

class ProfileDetailsForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ["phone"]

        labels = {
            "phone": "Phone number",
        }


# --------------------------------------------------
# Partner profile form
# --------------------------------------------------

class PartnerProfileForm(forms.ModelForm):

    class Meta:
        model = Profile

        fields = [
            "phone",
            "vehicle_type",
            "vehicle_number",
            "capacity_kg",
            "is_available",
        ]

        labels = {
            "capacity_kg": "Capacity (kg)",
            "is_available": "I am available for parcels",
        }


# --------------------------------------------------
# Parcel form
# --------------------------------------------------

class ParcelForm(forms.ModelForm):

    agreed = forms.BooleanField(
        label=(
            "I confirm the parcel has no prohibited items "
            "(explosives, drugs, weapons, cash, illegal goods)."
        ),
    )

    class Meta:
        model = Parcel

        fields = [
            "pickup_district",
            "pickup_address",
            "drop_district",
            "drop_address",
            "receiver_name",
            "receiver_phone",
            "size",
            "weight_kg",
            "description",
        ]

        labels = {
            "weight_kg": "Weight (kg)",
            "description": "What is inside?",
        }

    def clean(self):
        data = super().clean()

        if (
            data.get("pickup_district")
            and data.get("pickup_district") == data.get("drop_district")
        ):
            self.add_error(
                "drop_district",
                "Pickup and drop districts must be different."
            )

        w = data.get("weight_kg")

        if w is not None and not (0 < w <= MAX_WEIGHT_KG):
            self.add_error(
                "weight_kg",
                f"Weight must be between 0.1 and {MAX_WEIGHT_KG} kg."
            )

        return data


# --------------------------------------------------
# Partner route form
# --------------------------------------------------

class PartnerRouteForm(forms.ModelForm):

    travel_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )

    class Meta:
        model = PartnerRoute

        fields = [
            "from_district",
            "to_district",
            "travel_date",
        ]

    def clean(self):
        data = super().clean()

        if (
            data.get("from_district")
            and data.get("from_district") == data.get("to_district")
        ):
            self.add_error(
                "to_district",
                "From and To must be different."
            )

        return data