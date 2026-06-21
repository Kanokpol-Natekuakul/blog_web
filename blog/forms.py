from django import forms
from django.utils.text import slugify

from .models import Blog, Comment, Post, Tag

# Slugs that would collide with fixed top-level routes (see config/urls.py).
# A Blog may not claim these, or its public page would be unreachable.
RESERVED_SLUGS = {
    "admin", "accounts", "blogs", "dashboard", "tags", "comments",
    "static", "media", "login", "logout", "signup",
}


class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ["name", "description", "slug"]

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if slug in RESERVED_SLUGS:
            raise forms.ValidationError("This slug is reserved. Please choose another.")
        return slug


class PostForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        help_text="Comma-separated, e.g. python, django, web",
    )

    class Meta:
        model = Post
        fields = ["title", "body", "slug", "status", "cover_image"]

    def __init__(self, *args, blog=None, **kwargs):
        # The owning Blog comes from the URL, not the form, so we receive it
        # here to validate slug uniqueness within that Blog.
        super().__init__(*args, **kwargs)
        self.blog = blog
        if self.instance.pk:
            self.fields["tags"].initial = ", ".join(
                t.name for t in self.instance.tags.all()
            )

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        qs = Post.objects.filter(blog=self.blog, slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                "A post with this slug already exists in this blog."
            )
        return slug

    def save_tags(self, post):
        """Parse the comma-separated input into Tags and attach them.

        Names are normalised to lowercase so 'Python' and 'python' are one
        Tag. Call after the Post has a primary key.
        """
        names = {n.strip().lower() for n in self.cleaned_data["tags"].split(",")}
        tags = []
        for name in names:
            if not name:
                continue
            tag, _ = Tag.objects.get_or_create(name=name, defaults={"slug": slugify(name)})
            tags.append(tag)
        post.tags.set(tags)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3})}
