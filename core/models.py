import secrets

from django.conf import settings
from django.db import models

from .utils import DISTRICT_CHOICES

User = settings.AUTH_USER_MODEL


def gen_otp():
    return f"{secrets.randbelow(10**6):06d}"


def gen_code():
    return "BS" + "".join(secrets.choice("0123456789") for _ in range(8))


class Profile(models.Model):
    ROLES = [("customer", "Customer"), ("partner", "Pickup Partner"), ("assigner", "Parcel Assigner")]
    VEHICLES = [("bike", "Bike"), ("car", "Car"), ("van", "Van / Mini truck"), ("bus", "Bus / Travels")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLES, default="customer")
    phone = models.CharField(max_length=15, blank=True)
    # partner-only fields
    vehicle_type = models.CharField(max_length=10, choices=VEHICLES, blank=True)
    vehicle_number = models.CharField(max_length=20, blank=True)
    capacity_kg = models.PositiveIntegerField(default=10)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} ({self.get_role_display()})"


class PartnerRoute(models.Model):
    partner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="routes")
    from_district = models.CharField(max_length=30, choices=DISTRICT_CHOICES)
    to_district = models.CharField(max_length=30, choices=DISTRICT_CHOICES)
    travel_date = models.DateField()

    class Meta:
        ordering = ["travel_date"]

    def __str__(self):
        return f"{self.from_district} -> {self.to_district} on {self.travel_date}"


class Parcel(models.Model):
    STATUS = [
        ("created", "Awaiting payment"),
        ("paid", "Paid - waiting for assigner"),
        ("assigned", "Assigned to partner"),
        ("accepted", "Partner accepted"),
        ("in_transit", "In transit"),
        ("delivered", "Delivered"),
        ("partner_paid", "Partner paid"),
    ]
    FLOW = [s for s, _ in STATUS]
    SIZES = [("document", "Document / envelope"), ("small", "Small box"), ("medium", "Medium box"), ("large", "Large box")]

    code = models.CharField(max_length=12, unique=True, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="parcels")
    partner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="jobs")

    pickup_district = models.CharField(max_length=30, choices=DISTRICT_CHOICES)
    drop_district = models.CharField(max_length=30, choices=DISTRICT_CHOICES)
    pickup_address = models.CharField(max_length=200)
    drop_address = models.CharField(max_length=200)
    receiver_name = models.CharField(max_length=60)
    receiver_phone = models.CharField(max_length=15)
    size = models.CharField(max_length=10, choices=SIZES, default="small")
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1)
    description = models.CharField(max_length=150)

    distance_km = models.PositiveIntegerField(default=0)
    price = models.PositiveIntegerField(default=0)           # paid by customer to Bluestork (Rs.)
    partner_payout = models.PositiveIntegerField(default=0)  # paid by Bluestork to partner (Rs.)

    status = models.CharField(max_length=15, choices=STATUS, default="created")
    pickup_otp = models.CharField(max_length=6, default=gen_otp, editable=False)
    delivery_otp = models.CharField(max_length=6, default=gen_otp, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    pay_method = models.CharField(max_length=20, blank=True)
    txn_id = models.CharField(max_length=20, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    picked_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    payout_at = models.DateTimeField(null=True, blank=True)
    payout_ref = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.code:
            code = gen_code()
            while Parcel.objects.filter(code=code).exists():
                code = gen_code()
            self.code = code
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code}: {self.pickup_district} -> {self.drop_district}"

    @property
    def timeline(self):
        idx = self.FLOW.index(self.status)
        return [
            {"key": k, "label": label, "done": i < idx, "current": i == idx}
            for i, (k, label) in enumerate(self.STATUS)
        ]


class TrackingPoint(models.Model):
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, related_name="points")
    lat = models.FloatField()
    lng = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
