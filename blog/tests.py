from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Blog, Post


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
