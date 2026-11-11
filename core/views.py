import uuid
import hashlib
from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    ParcelForm,
    PartnerProfileForm,
    PartnerRouteForm,
    PartnerSignupForm,
    SignupForm,
    UserProfileForm,
)

from .models import Parcel, PartnerRoute, Profile, TrackingPoint
from notifications.models import Notification
from .utils import DISTRICTS, MAX_WEIGHT_KG, invoice_pdf, payout_pdf, quote

User = get_user_model()

ROLE_LABEL = {
    "customer": "Customer",
    "partner": "Pickup Partner",
    "assigner": "Parcel Assigner",
}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def get_profile(user):
    return Profile.objects.get_or_create(user=user)[0]


def send_notification(user, title, message, notification_type, parcel=None):
    """Create one notification for a specific user."""
    if not user:
        return

    Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        notification_type=notification_type,
        parcel=parcel,
    )


def notify_assigners(title, message, notification_type, parcel=None):
    """Notify every active Bluestork assigner."""
    assigners = User.objects.filter(
        profile__role="assigner",
        is_active=True,
    )

    for assigner in assigners:
        send_notification(
            assigner,
            title,
            message,
            notification_type,
            parcel,
        )


def notify_admins(title, message, notification_type, parcel=None):
    """Notify active Django superuser accounts."""
    admins = User.objects.filter(
        is_superuser=True,
        is_active=True,
    )

    for admin in admins:
        send_notification(
            admin,
            title,
            message,
            notification_type,
            parcel,
        )


def role_required(role):
    def deco(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect(f"{role}_login")

            if get_profile(request.user).role != role:
                messages.error(
                    request,
                    f"Please log in with your {ROLE_LABEL[role]} ID."
                )
                return redirect(f"{role}_login")

            return view(request, *args, **kwargs)

        return wrapper
    return deco


def parcel_for(request, code):

    if not request.user.is_authenticated:
        raise Http404

    p = get_object_or_404(Parcel, code=code)
    role = get_profile(request.user).role

    ok = (
        (role == "customer" and p.customer_id == request.user.id)
        or (role == "partner" and p.partner_id == request.user.id)
        or role == "assigner"
    )

    if not ok:
        raise Http404

    return p, role


def candidate_partners(parcel):

    out = []

    for prof in Profile.objects.filter(
        role="partner",
        is_available=True
    ).select_related("user"):

        if prof.capacity_kg < parcel.weight_kg:
            continue

        score, note = 0, "No matching route set"

        for r in prof.user.routes.all():

            if (
                r.from_district == parcel.pickup_district
                and r.to_district == parcel.drop_district
            ):
                score = 3
                note = f"Exact route on {r.travel_date:%d %b}"
                break

            if {
                r.from_district,
                r.to_district
            } == {
                parcel.pickup_district,
                parcel.drop_district
            }:
                score, note = max(score, 2), "Reverse route"

            elif (
                parcel.pickup_district in (r.from_district, r.to_district)
                or parcel.drop_district in (r.from_district, r.to_district)
            ):
                if score < 1:
                    score, note = 1, "Partial route match"

        out.append((score, note, prof))

    out.sort(
        key=lambda t: (
            -t[0],
            t[2].user.first_name or t[2].user.username
        )
    )

    return out


# ------------------------------------------------------------------
# Public pages
# ------------------------------------------------------------------

def landing(request):
    return render(request, "landing.html")


def home(request):
    return render(request, "home.html")


def settings_page(request):
    return render(request, "settings.html")


def role_login(request, role):

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():

        user = form.get_user()

        if get_profile(user).role != role:
            form.add_error(
                None,
                f"This ID is not registered as a {ROLE_LABEL[role]}."
            )
        else:
            login(request, user)
            return redirect(f"{role}_dashboard")

    return render(request, "login.html", {
        "form": form,
        "role": role,
        "role_label": ROLE_LABEL[role],
    })


def role_signup(request, role):

    form_class = PartnerSignupForm if role == "partner" else SignupForm
    form = form_class(request.POST or None)

    if request.method == "POST" and form.is_valid():

        user = form.save_with_role(role)
        login(request, user)

        messages.success(
            request,
            "Account created. Welcome to Bluestork!"
        )

        return redirect(f"{role}_dashboard")

    return render(request, "signup.html", {
        "form": form,
        "role": role,
        "role_label": ROLE_LABEL[role],
    })


@require_POST
def logout_view(request):
    logout(request)
    return redirect("home")


def quote_api(request):

    try:
        pickup = request.GET["pickup"]
        drop = request.GET["drop"]
        weight = float(request.GET.get("weight") or 1)

        if (
            pickup not in DISTRICTS
            or drop not in DISTRICTS
            or pickup == drop
            or not (0 < weight <= MAX_WEIGHT_KG)
        ):
            raise ValueError

    except (KeyError, ValueError):
        return JsonResponse({"ok": False})

    km, price, _ = quote(pickup, drop, weight)

    return JsonResponse({
        "ok": True,
        "km": km,
        "price": price,
    })


# ------------------------------------------------------------------
# Customer
# ------------------------------------------------------------------

@role_required("customer")
def customer_dashboard(request):

    parcels = request.user.parcels.all()

    return render(request, "customer_dashboard.html", {
        "parcels": parcels,
    })


@role_required("customer")
def parcel_new(request):

    form = ParcelForm(request.POST or None)

    if request.method == "POST" and form.is_valid():

        p = form.save(commit=False)
        p.customer = request.user

        p.distance_km, p.price, p.partner_payout = quote(
            p.pickup_district,
            p.drop_district,
            p.weight_kg
        )

        p.save()

        send_notification(
            request.user,
            "Parcel Created",
            f"Your parcel {p.code} has been created successfully. Complete payment to proceed.",
            "parcel",
            p,
        )

        notify_admins(
            "New Parcel Created",
            f"A new parcel {p.code} has been created.",
            "parcel",
            p,
        )

        return redirect("pay", code=p.code)

    return render(request, "parcel_new.html", {
        "form": form,
    })


@role_required("customer")
def pay(request, code):

    p = get_object_or_404(
        Parcel,
        code=code,
        customer=request.user
    )

    if p.status != "created":
        return redirect("parcel_detail", code=p.code)

    if request.method == "POST":

        p.status = "paid"
        p.paid_at = timezone.now()
        p.pay_method = request.POST.get("method", "UPI")[:20]
        p.txn_id = "SIM" + uuid.uuid4().hex[:10].upper()

        p.save()

        send_notification(
            request.user,
            "Payment Successful",
            f"Payment for parcel {p.code} was successful.",
            "payment",
            p,
        )

        notify_assigners(
            "New Parcel Ready for Assignment",
            f"Parcel {p.code} is paid and waiting for a pickup partner.",
            "parcel",
            p,
        )

        messages.success(
            request,
            "Payment successful (simulated). Your invoice is ready to download."
        )

        return redirect("parcel_detail", code=p.code)

    return render(request, "pay.html", {
        "p": p,
    })


# ------------------------------------------------------------------
# Partner
# ------------------------------------------------------------------

@role_required("partner")
def partner_dashboard(request):

    profile = get_profile(request.user)
    jobs = request.user.jobs.all()

    return render(request, "partner_dashboard.html", {
        "profile": profile,
        "profile_form": PartnerProfileForm(instance=profile),
        "route_form": PartnerRouteForm(),
        "routes": request.user.routes.all(),
        "new_jobs": jobs.filter(status="assigned"),
        "active_jobs": jobs.filter(
            status__in=["accepted", "in_transit"]
        ),
        "done_jobs": jobs.filter(
            status__in=["delivered", "partner_paid"]
        ),
        "earned": sum(
            j.partner_payout
            for j in jobs.filter(status="partner_paid")
        ),
        "pending": sum(
            j.partner_payout
            for j in jobs.filter(status="delivered")
        ),
    })


@role_required("partner")
@require_POST
def partner_profile(request):

    form = PartnerProfileForm(
        request.POST,
        instance=get_profile(request.user)
    )

    if form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
    else:
        messages.error(
            request,
            "Please check your profile details."
        )

    return redirect("partner_dashboard")


@role_required("partner")
@require_POST
def route_add(request):

    form = PartnerRouteForm(request.POST)

    if form.is_valid():

        r = form.save(commit=False)
        r.partner = request.user
        r.save()

        messages.success(request, "Route added.")

    else:
        messages.error(
            request,
            "Could not add route: "
            + " ".join(
                e for errs in form.errors.values() for e in errs
            )
        )

    return redirect("partner_dashboard")


@role_required("partner")
@require_POST
def route_delete(request, pk):

    get_object_or_404(
        PartnerRoute,
        pk=pk,
        partner=request.user
    ).delete()

    return redirect("partner_dashboard")


# ------------------------------------------------------------------
# Assigner
# ------------------------------------------------------------------

@role_required("assigner")
def assigner_dashboard(request):

    def with_candidates(qs):
        return [
            (p, candidate_partners(p))
            for p in qs
        ]

    return render(request, "assigner_dashboard.html", {
        "to_assign": with_candidates(
            Parcel.objects.filter(status="paid").order_by("paid_at")
        ),
        "assigned": with_candidates(
            Parcel.objects.filter(status="assigned")
        ),
        "active": Parcel.objects.filter(
            status__in=["accepted", "in_transit"]
        ),
        "to_pay": Parcel.objects.filter(status="delivered"),
        "completed": Parcel.objects.filter(
            status="partner_paid"
        )[:10],
        "partner_count": Profile.objects.filter(
            role="partner",
            is_available=True
        ).count(),
    })


@role_required("assigner")
@require_POST
def assign(request, code):

    p = get_object_or_404(
        Parcel,
        code=code,
        status__in=["paid", "assigned"]
    )

    partner = get_object_or_404(
        User,
        pk=request.POST.get("partner"),
        profile__role="partner"
    )

    p.partner = partner
    p.status = "assigned"
    p.assigned_at = timezone.now()
    p.save()

    send_notification(
        partner,
        "New Parcel Assigned",
        f"Parcel {p.code} has been assigned to you.",
        "assignment",
        p,
    )

    send_notification(
        p.customer,
        "Pickup Partner Assigned",
        f"A pickup partner has been assigned to parcel {p.code}.",
        "assignment",
        p,
    )

    notify_admins(
        "Parcel Assigned",
        f"Parcel {p.code} was assigned to {partner.username}.",
        "assignment",
        p,
    )

    messages.success(
        request,
        f"{p.code} assigned to {partner.first_name or partner.username}."
    )

    return redirect("assigner_dashboard")


@role_required("assigner")
@require_POST
def payout(request, code):

    p = get_object_or_404(
        Parcel,
        code=code,
        status="delivered"
    )

    p.status = "partner_paid"
    p.payout_at = timezone.now()
    p.payout_ref = "PO" + uuid.uuid4().hex[:10].upper()
    p.save()

    send_notification(
        p.partner,
        "Payout Completed",
        f"Your payout of Rs. {p.partner_payout} for parcel {p.code} has been recorded successfully.",
        "payout",
        p,
    )

    notify_admins(
        "Partner Payout Recorded",
        f"Payout for parcel {p.code} has been recorded.",
        "payout",
        p,
    )

    messages.success(
        request,
        f"Paid Rs. {p.partner_payout} to the partner (simulated)."
    )

    return redirect("assigner_dashboard")


# ------------------------------------------------------------------
# Profile section - Customer, Partner and Assigner
# ------------------------------------------------------------------

def profile_page(request):

    if not request.user.is_authenticated:
        return redirect("home")

    profile = get_profile(request.user)

    if request.method == "POST":

        user_form = UserProfileForm(
            request.POST,
            instance=request.user
        )

        if user_form.is_valid():
            user_form.save()

            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect("profile")

        messages.error(
            request,
            "Please check your profile details."
        )

    else:
        user_form = UserProfileForm(instance=request.user)

    return render(request, "profile.html", {
        "user_form": user_form,
        "profile": profile,
    })


# ------------------------------------------------------------------
# Shared parcel pages
# ------------------------------------------------------------------

def parcel_detail(request, code):

    p, role = parcel_for(request, code)

    pc = DISTRICTS[p.pickup_district]
    dc = DISTRICTS[p.drop_district]

    last = p.points.first()

    map_data = {
        "code": p.code,
        "pickup": {
            "name": p.pickup_district,
            "lat": pc[0],
            "lng": pc[1],
        },
        "drop": {
            "name": p.drop_district,
            "lat": dc[0],
            "lng": dc[1],
        },
        "last": {
            "lat": last.lat,
            "lng": last.lng,
        } if last else None,
        "status": p.status,
        "can_share": role == "partner" and p.status == "in_transit",
    }

    return render(request, "parcel_detail.html", {
        "p": p,
        "role": role,
        "map_data": map_data,
    })


@require_POST
def respond(request, code):

    p, role = parcel_for(request, code)

    if role != "partner" or p.status != "assigned":
        raise Http404

    if request.POST.get("action") == "accept":

        p.status = "accepted"
        p.save()

        send_notification(
            p.customer,
            "Partner Accepted Parcel",
            f"The pickup partner has accepted parcel {p.code}.",
            "assignment",
            p,
        )

        notify_assigners(
            "Partner Accepted Parcel",
            f"Partner {request.user.username} accepted parcel {p.code}.",
            "assignment",
            p,
        )

        messages.success(
            request,
            "Job accepted. Meet the customer and ask for the pickup OTP."
        )

    else:

        p.status = "paid"
        p.partner = None
        p.assigned_at = None
        p.save()

        send_notification(
            p.customer,
            "Assignment Update",
            f"The previous partner declined parcel {p.code}. Another partner will be assigned.",
            "assignment",
            p,
        )

        notify_assigners(
            "Partner Rejected Parcel",
            f"Partner {request.user.username} rejected parcel {p.code}.",
            "assignment",
            p,
        )

        messages.info(
            request,
            "Job rejected. The assigner will pick another partner."
        )

        return redirect("partner_dashboard")

    return redirect("parcel_detail", code=p.code)


@require_POST
def pickup(request, code):

    p, role = parcel_for(request, code)

    if role != "partner" or p.status != "accepted":
        raise Http404

    if request.POST.get("otp", "").strip() == p.pickup_otp:

        p.status = "in_transit"
        p.picked_at = timezone.now()
        p.save()

        send_notification(
            p.customer,
            "Parcel Picked Up",
            f"Your parcel {p.code} has been picked up and is now in transit.",
            "delivery",
            p,
        )

        notify_admins(
            "Parcel Picked Up",
            f"Parcel {p.code} is now in transit.",
            "delivery",
            p,
        )

        messages.success(
            request,
            "Pickup verified. Parcel is now in transit."
        )

    else:
        messages.error(
            request,
            "Wrong pickup OTP. Ask the customer for the 6-digit code."
        )

    return redirect("parcel_detail", code=p.code)


@require_POST
def deliver(request, code):

    p, role = parcel_for(request, code)

    if role != "partner" or p.status != "in_transit":
        raise Http404

    if request.POST.get("otp", "").strip() == p.delivery_otp:

        p.status = "delivered"
        p.delivered_at = timezone.now()
        p.save()

        send_notification(
            p.customer,
            "Parcel Delivered",
            f"Your parcel {p.code} has been successfully delivered.",
            "delivery",
            p,
        )

        notify_assigners(
            "Parcel Delivered",
            f"Parcel {p.code} has been delivered and is awaiting partner payout.",
            "delivery",
            p,
        )

        notify_admins(
            "Parcel Delivered",
            f"Parcel {p.code} was successfully delivered.",
            "delivery",
            p,
        )

        messages.success(
            request,
            "Delivery verified. The assigner will now pay your share."
        )

    else:
        messages.error(
            request,
            "Wrong delivery OTP. Ask the receiver for the 6-digit code."
        )

    return redirect("parcel_detail", code=p.code)


def invoice(request, code):

    p, role = parcel_for(request, code)

    if role == "partner" or not p.paid_at:
        raise Http404

    resp = HttpResponse(
        invoice_pdf(p),
        content_type="application/pdf"
    )

    resp["Content-Disposition"] = (
        f'attachment; filename="Bluestork-Invoice-{p.code}.pdf"'
    )

    return resp


def payout_slip(request, code):

    p, role = parcel_for(request, code)

    if role == "customer" or p.status != "partner_paid":
        raise Http404

    resp = HttpResponse(
        payout_pdf(p),
        content_type="application/pdf"
    )

    resp["Content-Disposition"] = (
        f'attachment; filename="Bluestork-Payout-{p.code}.pdf"'
    )

    return resp


@require_POST
def ping(request, code):

    p, role = parcel_for(request, code)

    if role != "partner" or p.status != "in_transit":
        return JsonResponse({"ok": False}, status=400)

    try:
        lat = float(request.POST["lat"])
        lng = float(request.POST["lng"])
    except (KeyError, ValueError):
        return JsonResponse({"ok": False}, status=400)

    TrackingPoint.objects.create(
        parcel=p,
        lat=lat,
        lng=lng
    )

    return JsonResponse({"ok": True})


def location(request, code):

    p, _ = parcel_for(request, code)
    last = p.points.first()

    return JsonResponse({
        "status": p.status,
        "status_label": p.get_status_display(),
        "last": {
            "lat": last.lat,
            "lng": last.lng,
            "at": timezone.localtime(
                last.created_at
            ).strftime("%I:%M:%S %p"),
        } if last else None,
    })


# ------------------------------------------------------------------
# Dashboard live-update API
# ------------------------------------------------------------------

def dashboard_live_api(request):

    if not request.user.is_authenticated:
        return JsonResponse({"ok": False}, status=401)

    role = get_profile(request.user).role

    if role == "customer":
        parcels = Parcel.objects.filter(customer=request.user)

    elif role == "partner":
        parcels = Parcel.objects.filter(partner=request.user)

    elif role == "assigner":
        parcels = Parcel.objects.all()

    else:
        return JsonResponse({"ok": False}, status=403)

    parcel_data = list(
        parcels.order_by("code").values_list(
            "code",
            "status",
            "partner_id",
            "paid_at",
            "assigned_at",
            "picked_at",
            "delivered_at",
            "payout_at",
        )
    )

    if role == "assigner":
        partner_data = list(
            Profile.objects.filter(
                role="partner"
            ).order_by("id").values_list(
                "id",
                "is_available",
                "capacity_kg",
            )
        )
    else:
        partner_data = []

    raw_data = repr((parcel_data, partner_data))

    signature = hashlib.sha256(
        raw_data.encode("utf-8")
    ).hexdigest()

    return JsonResponse({
        "ok": True,
        "signature": signature,
    })