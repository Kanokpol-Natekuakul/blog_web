from django import forms

from .models import Blog, Post

# Slugs that would collide with fixed top-level routes (see config/urls.py).
# A Blog may not claim these, or its public page would be unreachable.
RESERVED_SLUGS = {
    "admin", "accounts", "blogs", "dashboard",
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
    class Meta:
        model = Post
        fields = ["title", "body", "slug", "status", "cover_image"]

    def __init__(self, *args, blog=None, **kwargs):
        # The owning Blog comes from the URL, not the form, so we receive it
        # here to validate slug uniqueness within that Blog.
        super().__init__(*args, **kwargs)
        self.blog = blog

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
