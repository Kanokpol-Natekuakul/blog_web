from django import forms

from .models import Blog

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
