from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("<slug:blog_slug>/", views.blog_detail, name="blog_detail"),
    path("<slug:blog_slug>/<slug:post_slug>/", views.post_detail, name="post_detail"),
]
