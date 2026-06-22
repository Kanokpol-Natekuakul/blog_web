from django.contrib import admin

from .models import Blog, Follow, Post, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "owner", "created")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "blog", "status", "published_at", "created")
    list_filter = ("status", "blog")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "body")
    filter_horizontal = ("tags",)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("user", "blog", "created")
    search_fields = ("user__username", "blog__name")
