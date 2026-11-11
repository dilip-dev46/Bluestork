from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    )

    return render(request, "notifications/notification_list.html", {
        "notifications": notifications,
        "unread_count": notifications.filter(is_read=False).count(),
    })


@login_required
def notification_data(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    )

    unread_count = notifications.filter(is_read=False).count()

    latest = notifications[:10]

    data = [
        {
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "type": n.notification_type,
            "is_read": n.is_read,
            "created_at": n.created_at.strftime("%d %b %Y, %I:%M %p"),
        }
        for n in latest
    ]

    return JsonResponse({
        "unread_count": unread_count,
        "notifications": data,
    })


@login_required
@require_POST
def mark_as_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        recipient=request.user
    )

    notification.is_read = True
    notification.save(update_fields=["is_read"])

    return JsonResponse({"success": True})


@login_required
@require_POST
def mark_all_as_read(request):
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)

    return JsonResponse({"success": True})