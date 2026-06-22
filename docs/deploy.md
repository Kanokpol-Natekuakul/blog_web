# Deploy runbook

How to put this platform live. Written for **Render** (free tier works), but
the steps generalise to Railway, Fly.io, or any host that runs a `Procfile`
web process with a managed Postgres add-on.

The code is already deploy-ready: `gunicorn` + `whitenoise` (static files),
`dj-database-url` (reads `DATABASE_URL`), env-driven secrets, and production
hardening (SSL redirect, secure cookies) that switches on when `DEBUG=False`.
What's left is host setup and the secrets only you can provide.

---

## 0. Before you start — what you need
- A host account (Render).
- A Postgres database (Render provisions one in a click).
- **An SMTP provider** — required, because email verification is *mandatory*:
  a new signup can't log in until they click the link in their email. Free
  options: Brevo, Mailgun, Resend, or Gmail SMTP for low volume.
- (Optional) Google OAuth credentials, only if you want the "Sign in with
  Google" button to work. The site runs fine without it.

## Option A — one-click Blueprint (recommended)

The repo ships a `render.yaml`. In Render: **New → Blueprint**, connect this
repo, and Render provisions the Postgres database and web service, generates
`SECRET_KEY`, wires `DATABASE_URL`, and sets `DEBUG=False` automatically. It
will prompt you for the **email vars** (`EMAIL_HOST`, `EMAIL_HOST_USER`,
`EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`) — fill those from your SMTP
provider. `ALLOWED_HOSTS`/CSRF are derived from the service hostname in
settings, so there's nothing else to set. Then skip to **step 4** to smoke-test.

Steps 1–3 below are the **manual alternative** (Option B) if you'd rather click
through the dashboard yourself.

## 1. Provision Postgres
Create a Postgres instance on the host and copy its **internal** connection
URL. It becomes the `DATABASE_URL` env var. `psycopg` (v3) is already in
`requirements.txt`, and the `release:` line in the `Procfile` runs
`migrate` automatically on each deploy.

## 2. Create the web service
Point the host at this repo. It auto-detects Python (pinned to 3.13 via
`.python-version`) and the `Procfile`:
```
web: gunicorn config.wsgi
release: python manage.py migrate
```
Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
(the manifest static storage is used automatically when `DEBUG=False`).

## 3. Set environment variables
On the host's dashboard, set (see `.env.example` for the full list):

| Var | Value |
|-----|-------|
| `SECRET_KEY` | a long random string — `python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | your hostname, e.g. `myblog.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://myblog.onrender.com` |
| `DATABASE_URL` | from step 1 |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | from your SMTP provider |
| `EMAIL_USE_TLS` | `True` |
| `DEFAULT_FROM_EMAIL` | a verified sender, e.g. `no-reply@yourdomain.com` |

> `DEBUG=False` is what turns on SSL redirect, secure cookies, and the
> compressed/hashed static storage. Don't forget it.

## 4. First deploy & smoke test
1. Trigger the deploy; watch the `release` phase run migrations.
2. Create an admin user from the host's shell:
   `python manage.py createsuperuser`
3. Open the site, sign up a normal account, and confirm the verification
   email actually arrives and the link logs you in. **This is the step most
   likely to fail** — if no email arrives, your SMTP env vars are wrong.
4. Create a blog, publish a post, follow another blog, run a search.

> To populate a staging/demo environment quickly, run
> `python manage.py seed_demo` from the host shell. It creates demo users
> (alice/bob/carol, password `demo-pass-123` — override with `--password`)
> with **verified** emails so they can log in immediately, plus blogs, posts,
> tags, follows, likes, and comments. It's idempotent. Don't run it against a
> real production database.

## 5. (Optional) Google OAuth
1. In **Google Cloud Console** → *APIs & Services → Credentials*, create an
   **OAuth client ID** (type: *Web application*). Add the authorised redirect
   URI: `https://<your-host>/accounts/google/login/callback/` (and
   `http://127.0.0.1:8000/accounts/google/login/callback/` for local testing).
2. Set the resulting credentials as environment variables — `GOOGLE_CLIENT_ID`
   and `GOOGLE_CLIENT_SECRET` (Render dashboard, or your local `.env`). The
   "Sign in with Google" button appears automatically once both are present; no
   Django admin / Social Application step is needed.

---

## Known limitations (deferred, by design)
- **Uploaded cover images don't persist.** Hosts like Render use an ephemeral
  filesystem, so files saved to `MEDIA_ROOT` vanish on redeploy. ADR-0005
  plans object storage (S3/Cloudinary) for "cloud later" — wire that up before
  relying on uploads in production. Text posts, follows, search, etc. all live
  in Postgres and are unaffected.
- **Reserved-slug collisions.** Blog slugs live at the URL root; a blog slug
  equal to a real path (e.g. `admin`) is shadowed. A reserved-slug list guards
  signup, but audit it before launch.
