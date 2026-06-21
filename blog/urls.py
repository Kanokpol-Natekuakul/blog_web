from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("", views.home, name="home"),
    # Fixed routes first — they must win over the top-level slug patterns
    # below (otherwise "dashboard" etc. would be read as a blog slug).
    path("dashboard/", views.dashboard, name="dashboard"),
    path("tags/<slug:tag_slug>/", views.tag_detail, name="tag_detail"),
    path("blogs/new/", views.blog_create, name="blog_create"),
    path("blogs/<slug:blog_slug>/edit/", views.blog_edit, name="blog_edit"),
    path("blogs/<slug:blog_slug>/delete/", views.blog_delete, name="blog_delete"),
    path("blogs/<slug:blog_slug>/posts/", views.post_list, name="post_list"),
    path("blogs/<slug:blog_slug>/posts/new/", views.post_create, name="post_create"),
    path("blogs/<slug:blog_slug>/posts/<slug:post_slug>/edit/", views.post_edit, name="post_edit"),
    path("blogs/<slug:blog_slug>/posts/<slug:post_slug>/delete/", views.post_delete, name="post_delete"),
    path("blogs/<slug:blog_slug>/posts/<slug:post_slug>/toggle/", views.post_toggle_publish, name="post_toggle"),
    # Public, top-level slug routes (catch-all) last.
    path("<slug:blog_slug>/", views.blog_detail, name="blog_detail"),
    path("<slug:blog_slug>/<slug:post_slug>/", views.post_detail, name="post_detail"),
]
