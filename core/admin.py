from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Parcel, PartnerRoute, Profile, TrackingPoint

User = get_user_model()


class ProfileInline(admin.StackedInline):
    """Set the role here. To create a Parcel Assigner: add a user, choose role = Parcel Assigner."""
    model = Profile
    can_delete = False
    min_num = 1
    max_num = 1
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = [ProfileInline]
    list_display = ("username", "first_name", "get_role", "is_staff", "is_active")

    @admin.display(description="Bluestork role")
    def get_role(self, obj):
        p = Profile.objects.filter(user=obj).first()
        return p.get_role_display() if p else "-"


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ("code", "customer", "pickup_district", "drop_district", "status", "partner", "price", "partner_payout", "created_at")
    list_filter = ("status", "pickup_district", "drop_district")
    search_fields = ("code", "customer__username", "receiver_name", "receiver_phone")
    readonly_fields = ("code", "pickup_otp", "delivery_otp")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone", "vehicle_type", "vehicle_number", "is_available")
    list_filter = ("role", "is_available")


admin.site.register(PartnerRoute)
admin.site.register(TrackingPoint)
