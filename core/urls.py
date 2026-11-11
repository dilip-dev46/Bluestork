from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from . import views as v


urlpatterns = [
    path("", v.landing, name="landing"),
    path("home/", v.home, name="home"),
    path("settings/", v.settings_page, name="settings"),

    # Profile
    path("profile/", v.profile_page, name="profile"),

    # Password Change
    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change_form.html",
            success_url=reverse_lazy("password_change_done"),
        ),
        name="password_change",
    ),

    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done.html"
        ),
        name="password_change_done",
    ),

    # Logout
    path("logout/", v.logout_view, name="logout"),

    # APIs
    path("api/quote/", v.quote_api, name="quote"),
    path("api/dashboard-live/", v.dashboard_live_api, name="dashboard_live_api"),

    # Customer
    path("customer/", v.customer_dashboard, name="customer_dashboard"),
    path("customer/login/", v.role_login, {"role": "customer"}, name="customer_login"),
    path("customer/signup/", v.role_signup, {"role": "customer"}, name="customer_signup"),
    path("customer/new/", v.parcel_new, name="parcel_new"),
    path("customer/pay/<str:code>/", v.pay, name="pay"),

    # Partner
    path("partner/", v.partner_dashboard, name="partner_dashboard"),
    path("partner/login/", v.role_login, {"role": "partner"}, name="partner_login"),
    path("partner/signup/", v.role_signup, {"role": "partner"}, name="partner_signup"),
    path("partner/profile/", v.partner_profile, name="partner_profile"),
    path("partner/routes/add/", v.route_add, name="route_add"),
    path("partner/routes/<int:pk>/delete/", v.route_delete, name="route_delete"),

    # Assigner
    path("assigner/", v.assigner_dashboard, name="assigner_dashboard"),
    path("assigner/login/", v.role_login, {"role": "assigner"}, name="assigner_login"),
    path("assigner/assign/<str:code>/", v.assign, name="assign"),
    path("assigner/payout/<str:code>/", v.payout, name="payout"),

    # Parcel operations
    path("parcel/<str:code>/", v.parcel_detail, name="parcel_detail"),
    path("parcel/<str:code>/respond/", v.respond, name="respond"),
    path("parcel/<str:code>/pickup/", v.pickup, name="pickup"),
    path("parcel/<str:code>/deliver/", v.deliver, name="deliver"),
    path("parcel/<str:code>/invoice/", v.invoice, name="invoice"),
    path("parcel/<str:code>/payout-slip/", v.payout_slip, name="payout_slip"),
    path("parcel/<str:code>/ping/", v.ping, name="ping"),
    path("parcel/<str:code>/location/", v.location, name="location"),

    # Support
    path("support/", include("support.urls")),
]

# Serve uploaded media files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )