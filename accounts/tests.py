from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from blog.models import Blog


class ProfileTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw-alice-123")
        self.bob = User.objects.create_user("bob", password="pw-bob-123")

    def test_profile_lists_only_that_users_blogs(self):
        Blog.objects.create(owner=self.alice, name="Alice Cooks", slug="alice-cooks")
        Blog.objects.create(owner=self.bob, name="Bob Travels", slug="bob-travels")
        resp = self.client.get(reverse("profile", args=["alice"]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "@alice")
        self.assertContains(resp, "Alice Cooks")
        self.assertNotContains(resp, "Bob Travels")

    def test_unknown_user_404(self):
        self.assertEqual(self.client.get(reverse("profile", args=["nobody"])).status_code, 404)

    def test_profile_empty_state(self):
        resp = self.client.get(reverse("profile", args=["alice"]))
        self.assertContains(resp, "No blogs yet")

    def test_blog_page_links_to_author_profile(self):
        Blog.objects.create(owner=self.alice, name="Alice Cooks", slug="alice-cooks")
        resp = self.client.get(reverse("blog:blog_detail", args=["alice-cooks"]))
        self.assertContains(resp, reverse("profile", args=["alice"]))
