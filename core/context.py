from .models import Profile


def role(request):
    """Makes `current_role` available in every template (used by the side menu)."""
    r = None
    if request.user.is_authenticated:
        r = Profile.objects.filter(user=request.user).values_list("role", flat=True).first() or "customer"
    return {"current_role": r}
