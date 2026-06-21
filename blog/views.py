from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import BlogForm, PostForm
from .models import Blog, Post, Tag

FEED_PAGE_SIZE = 10


def home(request):
    """Home feed: the most recent published posts across all blogs."""
    posts = (
        Post.objects.filter(status=Post.Status.PUBLISHED)
        .select_related("blog", "blog__owner")
        .order_by("-published_at", "-created")
    )
    page_obj = Paginator(posts, FEED_PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "home.html", {"page_obj": page_obj})


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


def tag_detail(request, tag_slug):
    """Published posts across all blogs that carry this tag."""
    tag = get_object_or_404(Tag, slug=tag_slug)
    posts = (
        tag.posts.filter(status=Post.Status.PUBLISHED)
        .select_related("blog", "blog__owner")
    )
    return render(request, "blog/tag_detail.html", {"tag": tag, "posts": posts})


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


def _apply_publish_state(post):
    """Stamp published_at the first time a Post becomes Published.

    The stamp is kept on unpublish/republish, so it records the original
    publication date.
    """
    if post.status == Post.Status.PUBLISHED and post.published_at is None:
        post.published_at = timezone.now()


@login_required
def post_list(request, blog_slug):
    """Owner's management list for a Blog: all posts, drafts included."""
    blog = get_object_or_404(Blog, slug=blog_slug, owner=request.user)
    return render(request, "blog/post_list.html", {"blog": blog, "posts": blog.posts.all()})


@login_required
def post_create(request, blog_slug):
    blog = get_object_or_404(Blog, slug=blog_slug, owner=request.user)
    post = Post(blog=blog)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post, blog=blog)
        if form.is_valid():
            post = form.save(commit=False)
            _apply_publish_state(post)
            post.save()
            form.save_tags(post)
            return redirect("blog:post_list", blog_slug=blog.slug)
    else:
        form = PostForm(instance=post, blog=blog)
    return render(request, "blog/post_form.html", {"form": form, "blog": blog, "is_create": True})


@login_required
def post_edit(request, blog_slug, post_slug):
    blog = get_object_or_404(Blog, slug=blog_slug, owner=request.user)
    post = get_object_or_404(Post, blog=blog, slug=post_slug)
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post, blog=blog)
        if form.is_valid():
            post = form.save(commit=False)
            _apply_publish_state(post)
            post.save()
            form.save_tags(post)
            return redirect("blog:post_list", blog_slug=blog.slug)
    else:
        form = PostForm(instance=post, blog=blog)
    return render(request, "blog/post_form.html", {"form": form, "blog": blog, "is_create": False, "post": post})


@login_required
def post_delete(request, blog_slug, post_slug):
    blog = get_object_or_404(Blog, slug=blog_slug, owner=request.user)
    post = get_object_or_404(Post, blog=blog, slug=post_slug)
    if request.method == "POST":
        post.delete()
        return redirect("blog:post_list", blog_slug=blog.slug)
    return render(request, "blog/post_confirm_delete.html", {"blog": blog, "post": post})


@login_required
@require_POST
def post_toggle_publish(request, blog_slug, post_slug):
    """Flip a post between Draft and Published (used via HTMX)."""
    blog = get_object_or_404(Blog, slug=blog_slug, owner=request.user)
    post = get_object_or_404(Post, blog=blog, slug=post_slug)
    post.status = (
        Post.Status.DRAFT
        if post.status == Post.Status.PUBLISHED
        else Post.Status.PUBLISHED
    )
    _apply_publish_state(post)
    post.save()
    return render(request, "blog/_post_status.html", {"blog": blog, "post": post})
