# Phase 3 — Build Plan

Goal: turn the platform from "a pile of blogs" into something you *follow* and can *search*. Two features: **Follow** (subscribe to a Blog, get a personalised feed) and **Search** (find published Posts and Blogs).

Same principles as Phase 1: one small step at a time, each step ends with something visible, commit after each step.

Decisions (locked in for this phase):
- **You follow a *Blog*, not a User.** A Blog is the publication (à la Substack); the personalised feed is the posts from the Blogs you follow. (See `CONTEXT.md` → **Follow**.)
- **Search covers published Posts (title + body) and Blogs (name + description).** Plain `icontains` on SQLite for now; Postgres full-text is a later optimisation, not a blocker.

---

## Step 3.1 — Follow model + follow/unfollow a Blog  ← first payoff
Add a `Follow(user, blog)` model (unique per pair, like `Like`). A logged-in user can follow/unfollow a Blog from its public page via an HTMX toggle button; show the follower count. Anonymous visitors see the count and a prompt to log in.
**DoD:** log in, open a blog you don't own, click *Follow* — the button flips to *Following* and the count goes up without a page reload; click again to unfollow.

## Step 3.2 — Following feed
A `/following` page (login required) listing the most recent published posts from the Blogs you follow, paginated like the home feed. Add a nav link for signed-in users. Empty-state points users at search / the home feed to find blogs to follow.
**DoD:** follow a couple of blogs, open *Following*, see their published posts newest-first; unfollow one and its posts drop out.

## Step 3.3 — Search Posts + Blogs
A `/search?q=` page with a search box in the header. Match published Posts on title + body and Blogs on name + description (case-insensitive contains). Show the two result groups with counts; sensible empty state for no query / no results.
**DoD:** type a word that appears in a post body and in a blog name — both groups return the right hits; an unmatched word shows "no results".

---

## Out of scope for Phase 3 (later)
Follow a *User* (vs a Blog), follow counts on profiles, notifications/email digests, Postgres full-text search & ranking, tag-based search facets. Deploy hardening continues to live with the ops work, not here.
