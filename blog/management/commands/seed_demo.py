"""Populate the database with realistic demo data.

Idempotent: re-running updates the same rows instead of duplicating them, so
it's safe to run on a fresh deploy or after a reset. Created users get a
*verified* email (see CONTEXT / the dev-seed note) so they can log in right
away despite mandatory email verification.

    python manage.py seed_demo
    python manage.py seed_demo --password mypass
"""

from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from blog.models import Blog, Comment, Follow, Like, Post, Tag

# (username, email, blog_slug, blog_name, blog_description)
USERS = [
    ("alice", "alice@example.com", "python-weekly", "Python Weekly",
     "A blog about Python, Django, and the snakes in between."),
    ("bob", "bob@example.com", "travel-log", "Travel Log",
     "Notes and photos from the road."),
    ("carol", "carol@example.com", "cooking-notes", "Cooking Notes",
     "Recipes I actually cook on weeknights."),
]

# blog_slug -> list of (post_slug, title, status, [tags], body)
POSTS = {
    "python-weekly": [
        ("django-orm-tips", "Five Django ORM tips", "published",
         ["python", "django"],
         "# Django ORM tips\n\nThe ORM rewards a little study. Here are five "
         "things I reach for often.\n\nUse `select_related` to avoid N+1 "
         "queries. Reach for `Q` objects when filters get conditional."),
        ("type-hints", "Why I finally use type hints", "published",
         ["python"],
         "Type hints caught a whole class of bugs before runtime for me. "
         "Editors light up, and refactors stop being scary."),
        ("draft-async", "Async Django (draft)", "draft",
         ["python", "django"],
         "Still figuring out where async actually pays off. Notes to self."),
    ],
    "travel-log": [
        ("kyoto-autumn", "Kyoto in autumn", "published",
         ["travel"],
         "# Kyoto in autumn\n\nThe maples turn and the temples empty out by "
         "dusk. Go early, walk slowly."),
        ("sleeper-trains", "In praise of sleeper trains", "published",
         ["travel"],
         "You board tired in one city and wake up rested in another. The best "
         "kind of travel is the kind you sleep through."),
    ],
    "cooking-notes": [
        ("weeknight-dal", "A weeknight dal", "published",
         ["food"],
         "# Weeknight dal\n\nRed lentils, onion, tomato, and whatever spices "
         "are open. Twenty minutes, one pot."),
        ("draft-bread", "Sourdough attempt #4 (draft)", "draft",
         ["food"],
         "The crumb is closer. The crust still fights me."),
    ],
}

# follower_username -> [blog_slug followed, ...]
FOLLOWS = {
    "alice": ["travel-log", "cooking-notes"],
    "bob": ["python-weekly"],
    "carol": ["python-weekly", "travel-log"],
}


class Command(BaseCommand):
    help = "Create idempotent demo data (users, blogs, posts, tags, follows, likes, comments)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="demo-pass-123",
            help="Password set on every demo user (default: demo-pass-123).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        password = options["password"]
        users = self._seed_users(password)
        self._seed_posts(users)
        self._seed_follows(users)
        self._seed_engagement(users)

        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready: {User.objects.count()} users, "
            f"{Blog.objects.count()} blogs, {Post.objects.count()} posts, "
            f"{Follow.objects.count()} follows, {Like.objects.count()} likes, "
            f"{Comment.objects.count()} comments."
        ))
        self.stdout.write(f"All demo users share the password: {password!r}")

    def _seed_users(self, password):
        users = {}
        for username, email, slug, name, description in USERS:
            user, _ = User.objects.get_or_create(
                username=username, defaults={"email": email}
            )
            user.email = email
            user.set_password(password)
            user.save()
            # Verified email so login works under mandatory verification.
            # allauth allows only one primary email per user, so drop any stale
            # addresses (e.g. from an earlier manual signup) before upserting
            # the canonical demo one — otherwise the new primary collides.
            EmailAddress.objects.filter(user=user).exclude(email=email).delete()
            EmailAddress.objects.update_or_create(
                user=user, email=email,
                defaults={"verified": True, "primary": True},
            )
            Blog.objects.update_or_create(
                slug=slug,
                defaults={"owner": user, "name": name, "description": description},
            )
            users[username] = user
        return users

    def _seed_posts(self, users):
        now = timezone.now()
        order = 0  # space published_at apart so the feed orders sensibly
        for slug, posts in POSTS.items():
            blog = Blog.objects.get(slug=slug)
            for post_slug, title, status, tag_names, body in posts:
                published_at = None
                if status == Post.Status.PUBLISHED:
                    published_at = now - timezone.timedelta(hours=order)
                    order += 1
                post, _ = Post.objects.update_or_create(
                    blog=blog, slug=post_slug,
                    defaults={
                        "title": title,
                        "body": body,
                        "status": status,
                        "published_at": published_at,
                    },
                )
                tags = [
                    Tag.objects.get_or_create(slug=t, defaults={"name": t})[0]
                    for t in tag_names
                ]
                post.tags.set(tags)

    def _seed_follows(self, users):
        for username, blog_slugs in FOLLOWS.items():
            follower = users[username]
            for slug in blog_slugs:
                Follow.objects.get_or_create(
                    blog=Blog.objects.get(slug=slug), user=follower
                )

    def _seed_engagement(self, users):
        """A handful of likes and comments on published posts."""
        dal = Post.objects.get(slug="weeknight-dal")
        kyoto = Post.objects.get(slug="kyoto-autumn")
        orm = Post.objects.get(slug="django-orm-tips")

        for post, who in [(orm, "bob"), (orm, "carol"), (kyoto, "alice"), (dal, "alice")]:
            Like.objects.get_or_create(post=post, user=users[who])

        Comment.objects.get_or_create(
            post=orm, author=users["bob"],
            defaults={"body": "select_related saved my page load times, thanks!"},
        )
        Comment.objects.get_or_create(
            post=kyoto, author=users["carol"],
            defaults={"body": "Adding this to the list. How crowded was it really?"},
        )
