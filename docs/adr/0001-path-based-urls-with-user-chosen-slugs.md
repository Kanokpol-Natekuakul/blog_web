# Path-based URLs with user-chosen, first-come-first-served slugs

We address Blogs and Posts by path (`site.com/{blogSlug}/{postSlug}`) rather than by subdomain (`{blogSlug}.site.com`), because subdomains drag in DNS, routing, and SSL work at the infra level that is irrelevant to the goal of practicing full-stack development.

Users choose their own Blog slug at creation time. A Blog slug must be unique across the entire platform and is allocated first-come-first-served — once taken, it is unavailable to anyone else.

Because URLs become permanent (links, bookmarks, SEO), this is expensive to change later, which is why it is recorded here.

## Consequences

When a User or Blog is deleted, its freed slug returns to the pool and may be claimed by someone else. Old external links pointing to the deleted slug will then resolve to the new owner's content — a deliberate trade-off (simple reclamation) over retiring slugs forever (which avoids accidental link inheritance / impersonation).
