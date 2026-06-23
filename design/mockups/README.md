# RECTO — Editorial magazine mockups

Standalone, high-fidelity HTML/CSS mockups for an editorial-magazine blog
design. **Self-contained — they do not touch the Django app.** Open any file
directly in a browser (no build step, no server).

## Pages

| File | Deliverable |
|------|-------------|
| `index.html` | Homepage (hero cover story + latest grid + newsletter) |
| `article.html` | Article page (70/30 split, sidebar, prose, share bar) |
| `category.html` | Category / archive (filter bar, 2-col grid, pagination) |
| `styleguide.html` | Component library — colors, type scale, controls, cards |
| `css/recto.css` | The shared design system (tokens + components) |

Open `index.html` to start; every page links to the others.

## Design direction

A magazine called **RECTO** (a printing term — the right-hand page). The look
is deliberately *not* the usual cream-paper-plus-terracotta default:

- **Color** — cool near-white paper `#FCFBF8`, warm ink `#17150F`, an
  editorial **red** `#C42E2E` brand accent, and six per-category accent hues.
- **Type** — *Libre Caslon Display* (masthead/headlines), *Inter* (body + UI),
  *Space Mono* (metadata).
- **Signature** — the monospace **production slug**: `№ 042 · TECHNOLOGY · 7 MIN`.
  Folio numbers are real publishing artifacts, so the numbering encodes
  something true rather than decorating.

## Honoured from the brief

Serif headings + sans body · flat (no gradients/heavy shadows) · per-category
pill colors · 1200px max width · 8px spacing scale · ~700px reading measure ·
16/9 card images · blockquote left-border accent · subtle card hover.

## Quality floor

Responsive 1280 → 768 → 375 (hamburger, scrollable pills, stacked hero,
row-list cards, sidebar-below-body, floating mobile share bar), visible
keyboard focus, `prefers-reduced-motion` respected, semantic HTML5
(`<article> <nav> <aside> <header> <footer>`), lazy-loaded below-fold images.

## Notes

Images are placeholders from `picsum.photos`; avatars from `i.pravatar.cc`
(an internet connection is needed to load them). All copy is original sample
editorial content, not lorem ipsum.
