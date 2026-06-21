from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BlogForm
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


@login_required
def dashboard(request):
    """The signed-in user's list of their own Blogs."""
    blogs = request.user.blogs.all()
    return render(request, "blog/dashboard.html", {"blogs": blogs})


@login_required
def blog_create(request):
    if request.method == "POST":
        form = BlogForm(request.POST)
        if form.is_valid():
            blog = form.save(commit=False)
            blog.owner = request.user
            blog.save()
            return redirect("blog:dashboard")
    else:
        form = BlogForm()
    return render(request, "blog/blog_form.html", {"form": form, "is_create": True})


@login_required
def blog_edit(request, blog_slug):
    # Scoping by owner means a non-owner gets 404, not someone else's edit form.
    blog = get_object_or_404(Blog, slug=blog_slug, owner=request.user)
    if request.method == "POST":
        form = BlogForm(request.POST, instance=blog)
        if form.is_valid():
            form.save()
            return redirect("blog:dashboard")
    else:
        form = BlogForm(instance=blog)
    return render(request, "blog/blog_form.html", {"form": form, "is_create": False, "blog": blog})


@login_required
def blog_delete(request, blog_slug):
    blog = get_object_or_404(Blog, slug=blog_slug, owner=request.user)
    if request.method == "POST":
        blog.delete()  # cascades to the blog's posts
        return redirect("blog:dashboard")
    return render(request, "blog/blog_confirm_delete.html", {"blog": blog})
