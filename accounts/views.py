from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render


def profile(request, username):
    """Public profile page listing all of a User's Blogs."""
    profile_user = get_object_or_404(User, username=username)
    return render(
        request,
        "accounts/profile.html",
        {"profile_user": profile_user, "blogs": profile_user.blogs.all()},
    )
