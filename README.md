# Blog Platform

A multi-tenant blogging platform where anyone can sign up and run one or more of
their own blogs — à la WordPress.com / Substack. Built as a full-stack Django
learning project.

A **User** owns one or more **Blogs**; each Blog holds **Posts** written in
Markdown. Posts are **Drafts** until **Published**, can carry platform-wide
**Tags**, and readers can **Comment**, **Like**, and **Follow** a blog to build
a personalised feed. There's a global home feed and full-text-ish **search**.

## Features

- **Accounts** — email/username signup & login with mandatory email
  verification (via django-allauth); optional "Sign in with Google".
- **Blogs & Posts** — owner CRUD, Markdown authoring (sanitised on render),
  draft/publish toggle, per-post cover images.
- **Discovery** — global home feed, platform-wide tags, search across published
  posts (title + body) and blogs (name + description).
- **Social** — comments (with owner moderation), likes, and following a blog for
  a personalised `/following` feed.
- **Polished UI** — an editorial "ink on paper" design, automatic dark mode
  (follows the OS), WCAG AA contrast, keyboard/skip-link support, responsive
  touch targets. No build step — server-rendered templates + a little HTMX.

## Tech stack

Django 6 · PostgreSQL (SQLite for local dev) · server-rendered Django templates
+ HTMX · django-allauth · Markdown + nh3 (sanitisation) · WhiteNoise + Gunicorn
for production. Python **3.13**. See [`docs/adr/`](docs/adr/) for the decisions
behind these choices.

## Getting started (local development)

Prerequisites: Python 3.13 and Git. (PostgreSQL is optional locally — it falls
back to SQLite.)

```bash
# 1. Clone and enter the project
git clone <repo-url> blog_web
cd blog_web

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows (PowerShell/cmd)
# source venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env from the template, then set a SECRET_KEY
copy .env.example .env         # Windows   (cp on macOS/Linux)
#   - leave DEBUG=True for development
#   - leave DATABASE_URL blank to use SQLite (or point it at Postgres)
#   generate a key:
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"

# 5. Apply migrations
python manage.py migrate

# 6. (optional) Load demo data — users, blogs, posts, tags, follows, likes
python manage.py seed_demo

# 7. (optional) Create an admin user for /admin
python manage.py createsuperuser

# 8. Run the dev server
python manage.py runserver
```

Open **http://127.0.0.1:8000/**.

> On Windows you can also run the server without activating the venv:
> `venv\Scripts\python.exe manage.py runserver`

### Demo accounts (after `seed_demo`)

Three pre-verified users, all with password **`demo-pass-123`**
(override with `--password`):

| User | Blog |
|------|------|
| `alice` | Python Weekly |
| `bob` | Travel Log |
| `carol` | Cooking Notes |

`seed_demo` is idempotent — safe to re-run. **Don't run it against a production
database.**

### A note on email verification in development

Signup requires confirming your email. In development (`DEBUG=True`) emails are
**printed to the terminal running the server** — open the console, find the
verification link, and visit it to activate the account. (Demo users created by
`seed_demo` are already verified, so they can log in directly.)

## Using the app

1. **Sign up** → confirm via the link (console link in dev) → log in.
2. **Create a blog** from *My blogs* (`/dashboard/`); it gets a public URL at
   `site/<blog-slug>`.
3. **Write a post** in Markdown, save as draft, then publish it.
4. **Read & discover** — the home feed, a blog page (`/<blog-slug>/`), a post
   (`/<blog-slug>/<post-slug>/`), tag pages (`/tags/<tag>/`), or **search**.
5. **Engage** — follow a blog (see its posts under `/following/`), like and
   comment on published posts. A blog owner can moderate (delete) comments.
6. **Profiles** live at `/@<username>/` and list a user's blogs.

Dark mode follows your operating system's appearance setting — no toggle needed.

## Running the tests

```bash
python manage.py test
```

## Project layout

```
config/      Django project: settings, root URLs, WSGI/ASGI
blog/        Blogs, Posts, Tags, Comments, Likes, Follows (models, views, tests)
             └ management/commands/seed_demo.py
accounts/    Public user profiles
templates/   Base layout, home, shared partials (_feed, _post_row)
static/css/  The single stylesheet (design tokens + components)
docs/        ADRs, phase build plans, and the deploy runbook
```

## Deployment

The code is production-ready (Gunicorn, WhiteNoise, `DATABASE_URL`, env-driven
secrets, SSL/HSTS hardening when `DEBUG=False`). Step-by-step instructions —
Postgres, environment variables, SMTP, and known limitations — are in
**[`docs/deploy.md`](docs/deploy.md)**.
