from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render


def profile(request, username):
    """Public profile page listing all of a User's Blogs."""
    profile_user = get_object_or_404(User, username=username)
    return render(
        request,
        "accounts/profile.html",
        {"profile_user": profile_user, "blogs": profile_user.blogs.all()},
    )


def signup(request):
    """Register a new account, then log the user in."""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("blog:dashboard")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
