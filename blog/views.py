from django.shortcuts import get_object_or_404, render

from .models import Blog, Post


def blog_detail(request, blog_slug):
    """Public page for a Blog: lists its published posts."""
    blog = get_object_or_404(Blog, slug=blog_slug)
    posts = blog.posts.filter(status=Post.Status.PUBLISHED)
    return render(request, "blog/blog_detail.html", {"blog": blog, "posts": posts})


def post_detail(request, blog_slug, post_slug):
    """Public page for a single published Post.

    Drafts return 404 for everyone here. Owner draft-preview is added once
    auth exists (Step 3+).
    """
    post = get_object_or_404(
        Post,
        blog__slug=blog_slug,
        slug=post_slug,
        status=Post.Status.PUBLISHED,
    )
    return render(request, "blog/post_detail.html", {"post": post})
