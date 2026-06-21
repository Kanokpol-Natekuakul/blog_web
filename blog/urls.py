from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    # Fixed routes first — they must win over the top-level slug patterns
    # below (otherwise "dashboard" etc. would be read as a blog slug).
    path("dashboard/", views.dashboard, name="dashboard"),
    path("blogs/new/", views.blog_create, name="blog_create"),
    path("blogs/<slug:blog_slug>/edit/", views.blog_edit, name="blog_edit"),
    path("blogs/<slug:blog_slug>/delete/", views.blog_delete, name="blog_delete"),
    # Public, top-level slug routes (catch-all) last.
    path("<slug:blog_slug>/", views.blog_detail, name="blog_detail"),
    path("<slug:blog_slug>/<slug:post_slug>/", views.post_detail, name="post_detail"),
]
