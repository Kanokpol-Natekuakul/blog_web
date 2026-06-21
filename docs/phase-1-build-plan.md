# Phase 1 — Build Plan

Goal: ship the walking skeleton — *sign up → create a blog → write a post → publish → a stranger reads it* — built in an order that puts something visible in the browser as early as possible.

Principles:
- **One small step at a time.** Each step ends with something you can see or click. Commit after each step.
- **Front-load the payoff.** We use the Django admin to create data early so you can see a rendered, public post *before* building any forms.
- **SQLite for dev now, Postgres before deploy.** (ADR-0003 allows this — don't fight Postgres setup on day one.)
- **Definition of Done (DoD)** for each step = the thing you can verify in the browser.

---

## Step 0 — Project skeleton
Set up a Python virtualenv, install Django, create the project, run the dev server. `git init`.
**DoD:** Django welcome page loads at `localhost:8000`.

## Step 1 — Core models + admin
Create the `Blog` and `Post` models (owner = Django's built-in `User`). Register both in the Django admin. Run the first migration.
- Blog: name, description, slug, owner, created
- Post: blog (FK), title, body (Markdown text), slug, status (draft/published), created, updated, published_at
**DoD:** create a Blog and a Post through `/admin` (no front-end yet).

## Step 2 — Public reading pages  ← first real payoff
Build the two public, no-login pages using the data you made in admin:
- `site.com/{blog-slug}` — lists the blog's **published** posts (empty-state text if none)
- `site.com/{blog-slug}/{post-slug}` — renders one published post
Wire Markdown → HTML **with sanitization** here (ADR-0004): a markdown lib + `bleach`. Drafts return 404 for non-owners.
**DoD:** open an incognito window and read your published post, with bold/headings/links rendering safely.

## Step 3 — Auth
Use Django's auth: signup, login, logout. The built-in `User.username` *is* your `@username`.
**DoD:** sign up a new account, log in, log out.

## Step 4 — Blog management (owner UI)
Logged-in users create / edit / delete their own Blogs through real forms. Enforce slug uniqueness across the platform (first-come-first-served) and owner-only edit/delete. Deleting a blog cascades to its posts.
**DoD:** create your blog through the UI (not admin) and see it at its public URL.

## Step 5 — Post authoring (owner UI)
Create / edit / delete Posts. Save as Draft, Publish, and pull a Published post back to Draft. Post slug unique within its blog.
**DoD:** write a post as draft (invisible publicly), publish it (now visible), unpublish it (gone again).

## Step 6 — User profile
`site.com/@username` — public page listing all of that user's blogs.
**DoD:** visit your own and someone else's profile and reach their blogs.

## Step 7 — Landing + polish
- `site.com/` simple landing page (what this is + signup/login).
- Auto-excerpt from the first paragraph on blog listing pages.
- Apply your HTML/CSS for a clean look.
- Sprinkle HTMX where it helps (e.g. live slug-availability check, inline publish toggle) — optional, not blocking.
**DoD:** the whole flow looks and feels like a real site.

## Step 8 — Postgres + deploy
Switch the dev DB from SQLite to PostgreSQL; deploy somewhere public.
**DoD:** the platform is live on a real URL.

---

## Out of scope for Phase 1 (don't build these yet)
Images, tags, comments, likes, the home feed, Google OAuth + email verification → **Phase 2**. Follow, search → **Phase 3**. (See ADRs and `CONTEXT.md`.)
