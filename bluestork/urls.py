from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Bluestork Admin"
admin.site.site_title = "Bluestork"
admin.site.index_title = "Bluestork administration"

urlpatterns = [
    path("admin/", admin.site.urls),

    # Main Bluestork application
    path("", include("core.urls")),

    # Notification Centre
    path("notifications/", include("notifications.urls")),
]