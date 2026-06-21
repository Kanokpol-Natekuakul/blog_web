# Authentication via django-allauth; email verification on, Google OAuth scaffolded

We use **django-allauth** for account management (signup, login, logout, email verification, and social login), replacing the hand-rolled email+password views from the early build. allauth is the industry standard and gives us verification and OAuth without writing security-sensitive flows ourselves. (We deliberately rolled our own auth first to learn the mechanics, then adopted allauth for the real feature set.)

Email verification is **mandatory**: a new account cannot log in until its email is confirmed. In development the console email backend prints the verification link to the terminal; production needs real SMTP.

**Google OAuth** is scaffolded (the provider app is installed and configured) but not active — it requires a Google Cloud OAuth client ID/secret, which is deferred until we choose to set it up. When a Google login presents an email already tied to an account, allauth links to that same account.

## Consequences

Account linking by email is safe here because allauth only treats an email as usable once **verified** — which mandatory verification guarantees — closing the pre-account-hijacking gap noted earlier.
