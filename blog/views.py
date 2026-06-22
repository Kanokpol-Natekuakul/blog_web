from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import BlogForm, CommentForm, PostForm
from .models import Blog, Comment, Follow, Like, Post, Tag

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


def search(request):
    """Search published Posts (title + body) and Blogs (name + description).

    Case-insensitive substring match (``icontains``) — fine on SQLite; a
    Postgres full-text upgrade is a later optimisation (see the Phase 3 plan).
    """
    query = request.GET.get("q", "").strip()
    posts = blogs = []
    if query:
        posts = (
            Post.objects.filter(status=Post.Status.PUBLISHED)
            .filter(Q(title__icontains=query) | Q(body__icontains=query))
            .select_related("blog", "blog__owner")
            .order_by("-published_at", "-created")
        )
        blogs = Blog.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).select_related("owner")
    return render(
        request,
        "blog/search.html",
        {"query": query, "posts": posts, "blogs": blogs},
    )


@login_required
def following_feed(request):
    """Personalised feed: recent published posts from blogs the user follows."""
    posts = (
        Post.objects.filter(
            status=Post.Status.PUBLISHED,
            blog__followers__user=request.user,
        )
        .select_related("blog", "blog__owner")
        .order_by("-published_at", "-created")
    )
    page_obj = Paginator(posts, FEED_PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "blog/following.html", {"page_obj": page_obj})


def blog_detail(request, blog_slug):
    """Public page for a Blog: lists its published posts."""
    blog = get_object_or_404(Blog, slug=blog_slug)
    posts = blog.posts.filter(status=Post.Status.PUBLISHED)
    context = {"blog": blog, "posts": posts}
    context.update(_follow_context(blog, request.user))
    return render(request, "blog/blog_detail.html", context)


def _follow_context(blog, user):
    following = user.is_authenticated and blog.followers.filter(user=user).exists()
    # An owner can't follow their own blog; hide the button for them.
    can_follow = user.is_authenticated and user != blog.owner
    return {
        "blog": blog,
        "following": following,
        "can_follow": can_follow,
        "follower_count": blog.followers.count(),
    }


@login_required
@require_POST
def follow_toggle(request, blog_slug):
    blog = get_object_or_404(Blog, slug=blog_slug)
    if request.user == blog.owner:
        raise PermissionDenied  # you can't follow your own blog
    follow = Follow.objects.filter(blog=blog, user=request.user).first()
    if follow:
        follow.delete()
    else:
        Follow.objects.create(blog=blog, user=request.user)
    if request.headers.get("HX-Request"):
        return render(request, "blog/_follow_button.html", _follow_context(blog, request.user))
    return redirect("blog:blog_detail", blog_slug=blog.slug)


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
    context = {
        "post": post,
        "comments": post.comments.select_related("author"),
        "comment_form": CommentForm(),
    }
    context.update(_like_context(post, request.user))
    return render(request, "blog/post_detail.html", context)


def _like_context(post, user):
    liked = user.is_authenticated and post.likes.filter(user=user).exists()
    return {"post": post, "liked": liked, "like_count": post.likes.count()}


@login_required
@require_POST
def like_toggle(request, post_id):
    post = get_object_or_404(Post, pk=post_id, status=Post.Status.PUBLISHED)
    like = Like.objects.filter(post=post, user=request.user).first()
    if like:
        like.delete()
    else:
        Like.objects.create(post=post, user=request.user)
    if request.headers.get("HX-Request"):
        return render(request, "blog/_like_button.html", _like_context(post, request.user))
    return redirect("blog:post_detail", blog_slug=post.blog.slug, post_slug=post.slug)


@login_required
@require_POST
def comment_create(request, post_id):
    post = get_object_or_404(Post, pk=post_id, status=Post.Status.PUBLISHED)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect("blog:post_detail", blog_slug=post.blog.slug, post_slug=post.slug)


@login_required
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    # Either the comment's author or the blog's owner may delete it.
    if request.user != comment.author and request.user != comment.post.blog.owner:
        raise PermissionDenied
    post = comment.post
    comment.delete()
    return redirect("blog:post_detail", blog_slug=post.blog.slug, post_slug=post.slug)


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
            try:
                post = form.save(commit=False)
                _apply_publish_state(post)
                post.save()
                form.save_tags(post)
                return redirect("blog:post_list", blog_slug=blog.slug)
            except Exception as e:
                import traceback
                from django.http import HttpResponse
                tb = traceback.format_exc()
                return HttpResponse(f"Exception during post creation:\n{tb}", content_type="text/plain", status=500)
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
