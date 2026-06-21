# Use Django's built-in auth; email+password first, OAuth later

We use Django's built-in authentication (password hashing, sessions) rather than implementing our own. Although this is a learning project and we considered rolling our own auth to learn the internals, we chose Django's batteries-included auth to ship safely and avoid security mistakes — accepting that we learn auth at the usage/concept level rather than from scratch.

Email+password is the Phase 1 login method. Google OAuth is deferred to a later phase (e.g. via django-allauth). Facebook was rejected because its app review / business verification is infra overhead unrelated to the learning goal.

When OAuth is added, a login that presents an email already tied to an existing account links to that **same account** rather than creating a second one.

## Consequences

Account linking by email is only safe when the email is **verified**. Email verification must be in place before Google OAuth ships. Phase 1 (email+password only) does not require verification.
