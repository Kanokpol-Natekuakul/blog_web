import tempfile
from io import BytesIO

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Blog, Post
from .validators import validate_image_size


def _image_upload(name="cover.png", fmt="PNG"):
    buf = BytesIO()
    Image.new("RGB", (10, 10), "blue").save(buf, format=fmt)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=f"image/{fmt.lower()}")


class BlogManagementTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw-alice-123")
        self.bob = User.objects.create_user("bob", password="pw-bob-123")

    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse("blog:dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)

    def test_dashboard_lists_only_own_blogs(self):
        Blog.objects.create(owner=self.alice, name="Alice Blog", slug="alice-blog")
        Blog.objects.create(owner=self.bob, name="Bob Blog", slug="bob-blog")
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("blog:dashboard"))
        self.assertContains(resp, "Alice Blog")
        self.assertNotContains(resp, "Bob Blog")

    def test_create_blog_sets_owner(self):
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("blog:blog_create"),
            {"name": "My Blog", "description": "", "slug": "my-blog"},
        )
        self.assertRedirects(resp, reverse("blog:dashboard"))
        blog = Blog.objects.get(slug="my-blog")
        self.assertEqual(blog.owner, self.alice)

    def test_duplicate_slug_rejected(self):
        Blog.objects.create(owner=self.bob, name="Taken", slug="taken")
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("blog:blog_create"),
            {"name": "Mine", "description": "", "slug": "taken"},
        )
        self.assertEqual(resp.status_code, 200)  # re-rendered with error
        self.assertEqual(Blog.objects.filter(slug="taken").count(), 1)

    def test_reserved_slug_rejected(self):
        self.client.force_login(self.alice)
        resp = self.client.post(
            reverse("blog:blog_create"),
            {"name": "Admin", "description": "", "slug": "admin"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "reserved")
        self.assertFalse(Blog.objects.filter(slug="admin").exists())

    def test_non_owner_cannot_edit(self):
        Blog.objects.create(owner=self.bob, name="Bob Blog", slug="bob-blog")
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("blog:blog_edit", args=["bob-blog"]))
        self.assertEqual(resp.status_code, 404)

    def test_non_owner_cannot_delete(self):
        Blog.objects.create(owner=self.bob, name="Bob Blog", slug="bob-blog")
        self.client.force_login(self.alice)
        resp = self.client.post(reverse("blog:blog_delete", args=["bob-blog"]))
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Blog.objects.filter(slug="bob-blog").exists())

    def test_delete_cascades_to_posts(self):
        blog = Blog.objects.create(owner=self.alice, name="Alice Blog", slug="alice-blog")
        Post.objects.create(blog=blog, title="P1", body="x", slug="p1")
        self.client.force_login(self.alice)
        resp = self.client.post(reverse("blog:blog_delete", args=["alice-blog"]))
        self.assertRedirects(resp, reverse("blog:dashboard"))
        self.assertFalse(Blog.objects.filter(slug="alice-blog").exists())
        self.assertEqual(Post.objects.count(), 0)


class PostManagementTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw-alice-123")
        self.bob = User.objects.create_user("bob", password="pw-bob-123")
        self.blog = Blog.objects.create(owner=self.alice, name="Alice Blog", slug="alice-blog")

    def _create(self, **overrides):
        data = {"title": "Hello", "body": "hi", "slug": "hello", "status": "draft"}
        data.update(overrides)
        return self.client.post(reverse("blog:post_create", args=[self.blog.slug]), data)

    def test_create_draft_is_hidden_publicly(self):
        self.client.force_login(self.alice)
        self._create(status="draft")
        post = Post.objects.get(slug="hello")
        self.assertEqual(post.status, "draft")
        self.assertIsNone(post.published_at)
        # public blog page omits it; public post page 404s
        self.assertNotContains(
            self.client.get(reverse("blog:blog_detail", args=[self.blog.slug])), "Hello"
        )
        self.assertEqual(
            self.client.get(reverse("blog:post_detail", args=[self.blog.slug, "hello"])).status_code,
            404,
        )

    def test_publish_stamps_published_at_and_is_visible(self):
        self.client.force_login(self.alice)
        self._create(status="published")
        post = Post.objects.get(slug="hello")
        self.assertEqual(post.status, "published")
        self.assertIsNotNone(post.published_at)
        self.assertContains(
            self.client.get(reverse("blog:blog_detail", args=[self.blog.slug])), "Hello"
        )

    def test_unpublish_keeps_published_at_and_hides(self):
        self.client.force_login(self.alice)
        self._create(status="published")
        post = Post.objects.get(slug="hello")
        original = post.published_at
        # edit back to draft
        self.client.post(
            reverse("blog:post_edit", args=[self.blog.slug, "hello"]),
            {"title": "Hello", "body": "hi", "slug": "hello", "status": "draft"},
        )
        post.refresh_from_db()
        self.assertEqual(post.status, "draft")
        self.assertEqual(post.published_at, original)  # preserved
        self.assertEqual(
            self.client.get(reverse("blog:post_detail", args=[self.blog.slug, "hello"])).status_code,
            404,
        )

    def test_duplicate_slug_within_blog_rejected(self):
        Post.objects.create(blog=self.blog, title="One", body="x", slug="dup")
        self.client.force_login(self.alice)
        resp = self._create(slug="dup")
        self.assertEqual(resp.status_code, 200)  # re-rendered with error
        self.assertEqual(Post.objects.filter(blog=self.blog, slug="dup").count(), 1)

    def test_same_slug_allowed_in_different_blog(self):
        other = Blog.objects.create(owner=self.alice, name="Other", slug="other")
        Post.objects.create(blog=other, title="One", body="x", slug="hello")
        self.client.force_login(self.alice)
        resp = self._create(slug="hello")  # same slug, different blog
        self.assertRedirects(resp, reverse("blog:post_list", args=[self.blog.slug]))
        self.assertTrue(Post.objects.filter(blog=self.blog, slug="hello").exists())

    def test_non_owner_cannot_create_post(self):
        self.client.force_login(self.bob)
        resp = self._create()
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(Post.objects.count(), 0)

    def test_non_owner_cannot_edit_or_delete_post(self):
        Post.objects.create(blog=self.blog, title="One", body="x", slug="p1")
        self.client.force_login(self.bob)
        self.assertEqual(
            self.client.get(reverse("blog:post_edit", args=[self.blog.slug, "p1"])).status_code, 404
        )
        self.assertEqual(
            self.client.post(reverse("blog:post_delete", args=[self.blog.slug, "p1"])).status_code, 404
        )
        self.assertTrue(Post.objects.filter(slug="p1").exists())

    def test_owner_can_delete_post(self):
        Post.objects.create(blog=self.blog, title="One", body="x", slug="p1")
        self.client.force_login(self.alice)
        resp = self.client.post(reverse("blog:post_delete", args=[self.blog.slug, "p1"]))
        self.assertRedirects(resp, reverse("blog:post_list", args=[self.blog.slug]))
        self.assertFalse(Post.objects.filter(slug="p1").exists())


class PolishTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw-alice-123")
        self.bob = User.objects.create_user("bob", password="pw-bob-123")
        self.blog = Blog.objects.create(owner=self.alice, name="Alice Blog", slug="alice-blog")

    def test_home_page_ok(self):
        resp = self.client.get(reverse("blog:home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Write your own blog")

    def test_excerpt_skips_heading_and_takes_first_paragraph(self):
        post = Post(
            blog=self.blog,
            title="T",
            slug="t",
            body="# A Heading\n\nThis is the first paragraph.\n\nSecond paragraph.",
        )
        self.assertEqual(post.excerpt, "This is the first paragraph.")

    def test_toggle_publish_flips_state(self):
        post = Post.objects.create(blog=self.blog, title="T", body="x", slug="t")
        self.client.force_login(self.alice)
        resp = self.client.post(reverse("blog:post_toggle", args=[self.blog.slug, "t"]))
        self.assertEqual(resp.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.status, "published")
        self.assertIsNotNone(post.published_at)
        self.assertContains(resp, "Unpublish")
        # toggle back
        self.client.post(reverse("blog:post_toggle", args=[self.blog.slug, "t"]))
        post.refresh_from_db()
        self.assertEqual(post.status, "draft")

    def test_toggle_requires_post(self):
        Post.objects.create(blog=self.blog, title="T", body="x", slug="t")
        self.client.force_login(self.alice)
        resp = self.client.get(reverse("blog:post_toggle", args=[self.blog.slug, "t"]))
        self.assertEqual(resp.status_code, 405)

    def test_non_owner_cannot_toggle(self):
        Post.objects.create(blog=self.blog, title="T", body="x", slug="t")
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("blog:post_toggle", args=[self.blog.slug, "t"]))
        self.assertEqual(resp.status_code, 404)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CoverImageTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw-alice-123")
        self.blog = Blog.objects.create(owner=self.alice, name="Alice Blog", slug="alice-blog")
        self.client.force_login(self.alice)

    def test_create_post_with_cover_image(self):
        resp = self.client.post(
            reverse("blog:post_create", args=[self.blog.slug]),
            {"title": "Hello", "body": "hi", "slug": "hello", "status": "draft",
             "cover_image": _image_upload()},
        )
        self.assertRedirects(resp, reverse("blog:post_list", args=[self.blog.slug]))
        post = Post.objects.get(slug="hello")
        self.assertTrue(post.cover_image.name.startswith("covers/"))

    def test_reject_disallowed_extension(self):
        resp = self.client.post(
            reverse("blog:post_create", args=[self.blog.slug]),
            {"title": "H", "body": "x", "slug": "h", "status": "draft",
             "cover_image": _image_upload("c.gif", "GIF")},
        )
        self.assertEqual(resp.status_code, 200)  # re-rendered with error
        self.assertFalse(Post.objects.filter(slug="h").exists())

    def test_size_validator_rejects_large_file(self):
        class Big:
            size = 6 * 1024 * 1024
        with self.assertRaises(ValidationError):
            validate_image_size(Big())

    def test_post_without_cover_is_allowed(self):
        resp = self.client.post(
            reverse("blog:post_create", args=[self.blog.slug]),
            {"title": "No Cover", "body": "x", "slug": "nc", "status": "draft"},
        )
        self.assertRedirects(resp, reverse("blog:post_list", args=[self.blog.slug]))
        self.assertFalse(Post.objects.get(slug="nc").cover_image)
