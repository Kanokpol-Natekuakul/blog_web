import markdown as md
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.html import strip_tags

from .validators import validate_image_size


class Blog(models.Model):
    """A named, self-contained publication owned by one User.

    Addressed by its slug at ``site.com/{slug}``. The slug is unique across
    the whole platform (first-come-first-served). Deleting a Blog cascades to
    its Posts; deleting the owner deletes their Blogs (see CASCADE below).
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blogs",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=80, unique=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    """A platform-wide label. Posts from any Blog can share a Tag."""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Post(models.Model):
    """A single piece of writing belonging to exactly one Blog.

    Authored in Markdown (stored as source — see ADR-0004). A Post is either
    a Draft (not public) or Published (visible at its URL); publishing is
    reversible. The slug is unique only within its Blog, so the full address
    ``site.com/{blog.slug}/{slug}`` is unique platform-wide.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    blog = models.ForeignKey(
        Blog,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    title = models.CharField(max_length=200)
    body = models.TextField(help_text="Markdown source")
    slug = models.SlugField(max_length=200)
    cover_image = models.ImageField(
        upload_to="covers/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_image_size,
        ],
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")

    class Meta:
        ordering = ["-published_at", "-created"]
        constraints = [
            models.UniqueConstraint(
                fields=["blog", "slug"],
                name="unique_post_slug_per_blog",
            ),
        ]

    def __str__(self):
        return self.title

    @property
    def excerpt(self):
        """First real paragraph (skipping headings) as plain text, for listings."""
        for block in self.body.split("\n\n"):
            text = block.strip()
            if text and not text.startswith("#"):
                return strip_tags(md.markdown(text)).strip()
        return ""


class Like(models.Model):
    """One user's like of a Post. At most one per (post, user)."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes"
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["post", "user"], name="unique_like_per_user_post"),
        ]

    def __str__(self):
        return f"{self.user} likes {self.post}"


class Follow(models.Model):
    """One user's follow of a Blog. At most one per (blog, user).

    Following a Blog subscribes the user to its published Posts, which show
    up on their personalised feed at ``/following``.
    """

    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name="followers")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["blog", "user"], name="unique_follow_per_user_blog"),
        ]

    def __str__(self):
        return f"{self.user} follows {self.blog}"


class Comment(models.Model):
    """A reader's plain-text comment on a published Post."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created"]

    def __str__(self):
        return f"{self.author} on {self.post}"
