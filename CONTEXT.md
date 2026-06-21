# Blog Platform

A multi-tenant platform where anyone can sign up and run one or more of their own blogs (à la WordPress.com / Substack). Built as a full-stack learning project.

## Language

**User**:
A person with an account on the platform. A User is both a private owner (logs in, owns Blogs) and a public identity with a profile page listing their Blogs. One User can own multiple Blogs.
_Avoid_: Account, Member, Author

**Username**:
The unique, user-chosen Slug that addresses a User's public profile, written with an `@` prefix in URLs (`site.com/@alice`) to keep it out of the Blog slug namespace. Unique across the platform, first-come-first-served.
_Avoid_: Handle, Nickname

**Blog**:
A named, self-contained publication owned by a User, with its own identity and URL — like a personal magazine. A User may own several. Posts live inside a Blog.
_Avoid_: Site, Channel, Publication

**Post**:
A single piece of writing that belongs to exactly one Blog.
_Avoid_: Article, Story, Entry

**Slug**:
The URL-safe identifier that addresses a Blog or Post in a path. A Blog slug is unique across the whole platform; a Post slug is unique only within its Blog. Users choose their own.
_Avoid_: Handle, Permalink, Path

**Draft**:
The state of a Post that is not visible to the public — whether it has never been published or was published and later pulled back. Only the owner can see it.
_Avoid_: Unpublished, Hidden, Private

**Published**:
The state of a Post that is visible to the public at its URL. Publishing is reversible: a Published Post can be returned to Draft.
_Avoid_: Live, Public
