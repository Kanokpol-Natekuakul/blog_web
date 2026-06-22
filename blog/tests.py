import tempfile
from io import BytesIO

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Blog, Comment, Follow, Like, Post, Tag
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


class TagTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw-alice-123")
        self.bob = User.objects.create_user("bob", password="pw-bob-123")
        self.ablog = Blog.objects.create(owner=self.alice, name="A", slug="a")
        self.bblog = Blog.objects.create(owner=self.bob, name="B", slug="b")

    def test_tags_created_deduped_and_lowercased(self):
        self.client.force_login(self.alice)
        self.client.post(
            reverse("blog:post_create", args=["a"]),
            {"title": "T", "body": "x", "slug": "t", "status": "published",
             "tags": "Python, Django, python"},
        )
        post = Post.objects.get(slug="t")
        self.assertEqual(sorted(post.tags.values_list("name", flat=True)), ["django", "python"])

    def test_editing_replaces_tags(self):
        post = Post.objects.create(blog=self.ablog, title="T", body="x", slug="t")
        post.tags.add(Tag.objects.create(name="old", slug="old"))
        self.client.force_login(self.alice)
        self.client.post(
            reverse("blog:post_edit", args=["a", "t"]),
            {"title": "T", "body": "x", "slug": "t", "status": "draft", "tags": "new"},
        )
        self.assertEqual(list(post.tags.values_list("name", flat=True)), ["new"])

    def test_tag_page_published_across_blogs_excludes_drafts(self):
        tag = Tag.objects.create(name="python", slug="python")
        p1 = Post.objects.create(blog=self.ablog, title="A post", body="x", slug="p1", status="published")
        p2 = Post.objects.create(blog=self.bblog, title="B post", body="x", slug="p2", status="published")
        draft = Post.objects.create(blog=self.ablog, title="Draft post", body="x", slug="p3", status="draft")
        for p in (p1, p2, draft):
            p.tags.add(tag)
        resp = self.client.get(reverse("blog:tag_detail", args=["python"]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "A post")
        self.assertContains(resp, "B post")
        self.assertNotContains(resp, "Draft post")

    def test_unknown_tag_404(self):
        self.assertEqual(
            self.client.get(reverse("blog:tag_detail", args=["nope"])).status_code, 404
        )


class FeedTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw-alice-123")
        self.bob = User.objects.create_user("bob", password="pw-bob-123")
        self.ablog = Blog.objects.create(owner=self.alice, name="A", slug="a")
        self.bblog = Blog.objects.create(owner=self.bob, name="B", slug="b")

    def test_feed_shows_published_across_blogs_excludes_drafts(self):
        Post.objects.create(blog=self.ablog, title="Alice Public", body="x", slug="ap", status="published")
        Post.objects.create(blog=self.bblog, title="Bob Public", body="x", slug="bp", status="published")
        Post.objects.create(blog=self.ablog, title="Secret Draft", body="x", slug="sd", status="draft")
        resp = self.client.get(reverse("blog:home"))
        self.assertContains(resp, "Alice Public")
        self.assertContains(resp, "Bob Public")
        self.assertNotContains(resp, "Secret Draft")

    def test_feed_paginates(self):
        for i in range(12):
            Post.objects.create(blog=self.ablog, title=f"P{i}", body="x", slug=f"p{i}", status="published")
        page1 = self.client.get(reverse("blog:home"))
        self.assertEqual(len(page1.context["page_obj"].object_list), 10)
        page2 = self.client.get(reverse("blog:home"), {"page": 2})
        self.assertEqual(len(page2.context["page_obj"].object_list), 2)

    def test_hero_only_for_anonymous(self):
        anon = self.client.get(reverse("blog:home"))
        self.assertContains(anon, "Write your own blog")
        self.client.force_login(self.alice)
        authed = self.client.get(reverse("blog:home"))
        self.assertNotContains(authed, "Write your own blog")


class CommentTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw-1")  # blog owner
        self.bob = User.objects.create_user("bob", password="pw-2")      # commenter
        self.carol = User.objects.create_user("carol", password="pw-3")  # unrelated
        self.blog = Blog.objects.create(owner=self.alice, name="A", slug="a")
        self.post = Post.objects.create(
            blog=self.blog, title="P", body="x", slug="p", status="published"
        )

    def test_anonymous_cannot_comment(self):
        resp = self.client.post(
            reverse("blog:comment_create", args=[self.post.pk]), {"body": "hi"}
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)
        self.assertEqual(Comment.objects.count(), 0)

    def test_logged_in_can_comment_and_it_shows(self):
        self.client.force_login(self.bob)
        self.client.post(
            reverse("blog:comment_create", args=[self.post.pk]), {"body": "Nice post!"}
        )
        self.assertEqual(Comment.objects.count(), 1)
        page = self.client.get(reverse("blog:post_detail", args=["a", "p"]))
        self.assertContains(page, "Nice post!")

    def test_cannot_comment_on_draft(self):
        draft = Post.objects.create(blog=self.blog, title="D", body="x", slug="d", status="draft")
        self.client.force_login(self.bob)
        resp = self.client.post(
            reverse("blog:comment_create", args=[draft.pk]), {"body": "hi"}
        )
        self.assertEqual(resp.status_code, 404)

    def test_author_can_delete_own_comment(self):
        c = Comment.objects.create(post=self.post, author=self.bob, body="mine")
        self.client.force_login(self.bob)
        self.client.post(reverse("blog:comment_delete", args=[c.pk]))
        self.assertFalse(Comment.objects.filter(pk=c.pk).exists())

    def test_blog_owner_can_delete_any_comment(self):
        c = Comment.objects.create(post=self.post, author=self.bob, body="bob's")
        self.client.force_login(self.alice)  # blog owner, not author
        self.client.post(reverse("blog:comment_delete", args=[c.pk]))
        self.assertFalse(Comment.objects.filter(pk=c.pk).exists())

    def test_unrelated_user_cannot_delete(self):
        c = Comment.objects.create(post=self.post, author=self.bob, body="bob's")
        self.client.force_login(self.carol)
        resp = self.client.post(reverse("blog:comment_delete", args=[c.pk]))
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=c.pk).exists())


class LikeTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw-1")
        self.bob = User.objects.create_user("bob", password="pw-2")
        self.blog = Blog.objects.create(owner=self.alice, name="A", slug="a")
        self.post = Post.objects.create(
            blog=self.blog, title="P", body="x", slug="p", status="published"
        )

    def test_anonymous_cannot_like(self):
        resp = self.client.post(reverse("blog:like_toggle", args=[self.post.pk]))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Like.objects.count(), 0)

    def test_toggle_likes_then_unlikes(self):
        self.client.force_login(self.bob)
        self.client.post(reverse("blog:like_toggle", args=[self.post.pk]))
        self.assertEqual(Like.objects.filter(post=self.post, user=self.bob).count(), 1)
        self.client.post(reverse("blog:like_toggle", args=[self.post.pk]))
        self.assertEqual(Like.objects.filter(post=self.post, user=self.bob).count(), 0)

    def test_like_widget_renders_on_post(self):
        Like.objects.create(post=self.post, user=self.bob)
        page = self.client.get(reverse("blog:post_detail", args=["a", "p"]))
        self.assertContains(page, 'id="like-button"')

    def test_cannot_like_draft(self):
        draft = Post.objects.create(blog=self.blog, title="D", body="x", slug="d", status="draft")
        self.client.force_login(self.bob)
        resp = self.client.post(reverse("blog:like_toggle", args=[draft.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_htmx_toggle_returns_partial(self):
        self.client.force_login(self.bob)
        resp = self.client.post(
            reverse("blog:like_toggle", args=[self.post.pk]), HTTP_HX_REQUEST="true"
        )
        self.assertContains(resp, "Liked")
        self.assertNotContains(resp, "<!DOCTYPE")


class FollowTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw-1")  # blog owner
        self.bob = User.objects.create_user("bob", password="pw-2")      # follower
        self.blog = Blog.objects.create(owner=self.alice, name="A", slug="a")

    def test_anonymous_cannot_follow(self):
        resp = self.client.post(reverse("blog:follow_toggle", args=["a"]))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Follow.objects.count(), 0)

    def test_toggle_follows_then_unfollows(self):
        self.client.force_login(self.bob)
        self.client.post(reverse("blog:follow_toggle", args=["a"]))
        self.assertEqual(Follow.objects.filter(blog=self.blog, user=self.bob).count(), 1)
        self.client.post(reverse("blog:follow_toggle", args=["a"]))
        self.assertEqual(Follow.objects.filter(blog=self.blog, user=self.bob).count(), 0)

    def test_owner_cannot_follow_own_blog(self):
        self.client.force_login(self.alice)
        resp = self.client.post(reverse("blog:follow_toggle", args=["a"]))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_button_renders_for_other_user(self):
        self.client.force_login(self.bob)
        page = self.client.get(reverse("blog:blog_detail", args=["a"]))
        self.assertContains(page, 'id="follow-button"')
        self.assertContains(page, "Follow")

    def test_owner_sees_count_but_no_button(self):
        Follow.objects.create(blog=self.blog, user=self.bob)
        self.client.force_login(self.alice)
        page = self.client.get(reverse("blog:blog_detail", args=["a"]))
        self.assertContains(page, "1 follower")
        self.assertNotContains(page, "hx-post")  # no toggle form for the owner

    def test_htmx_toggle_returns_partial(self):
        self.client.force_login(self.bob)
        resp = self.client.post(
            reverse("blog:follow_toggle", args=["a"]), HTTP_HX_REQUEST="true"
        )
        self.assertContains(resp, "Following")
        self.assertNotContains(resp, "<!DOCTYPE")


class FollowingFeedTests(TestCase):
    def setUp(self):
        self.alice = User.objects.create_user("alice", password="pw-1")
        self.bob = User.objects.create_user("bob", password="pw-2")
        self.carol = User.objects.create_user("carol", password="pw-3")
        self.ablog = Blog.objects.create(owner=self.alice, name="A", slug="a")
        self.cblog = Blog.objects.create(owner=self.carol, name="C", slug="c")

    def test_requires_login(self):
        resp = self.client.get(reverse("blog:following"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)

    def test_shows_only_followed_published_posts(self):
        Post.objects.create(blog=self.ablog, title="Alice Post", body="x", slug="ap", status="published")
        Post.objects.create(blog=self.ablog, title="Alice Draft", body="x", slug="ad", status="draft")
        Post.objects.create(blog=self.cblog, title="Carol Post", body="x", slug="cp", status="published")
        Follow.objects.create(blog=self.ablog, user=self.bob)  # bob follows A only
        self.client.force_login(self.bob)
        resp = self.client.get(reverse("blog:following"))
        self.assertContains(resp, "Alice Post")
        self.assertNotContains(resp, "Alice Draft")   # drafts excluded
        self.assertNotContains(resp, "Carol Post")    # unfollowed blog excluded

    def test_empty_state_when_following_nothing(self):
        self.client.force_login(self.bob)
        resp = self.client.get(reverse("blog:following"))
        self.assertContains(resp, "not following any blogs")
