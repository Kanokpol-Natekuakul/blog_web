"""Template filters for the blog app."""
import markdown as md
import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Explicit allowlist: only these tags/attributes survive sanitization.
# Anything else a post author writes (e.g. <script>, onerror=...) is stripped.
# See ADR-0004.
ALLOWED_TAGS = {
    "p", "br", "hr",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "em", "b", "i", "del", "blockquote",
    "ul", "ol", "li",
    "code", "pre",
    "a", "img",
    "table", "thead", "tbody", "tr", "th", "td",
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title"},
}


@register.filter
def markdownify(value):
    """Render Markdown source to sanitized, safe-to-display HTML."""
    html = md.markdown(value or "", extensions=["fenced_code", "tables"])
    clean = nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
    return mark_safe(clean)


# The editorial design has no real "categories", so we colour each post card
# deterministically from its primary key — stable per post, lively in a grid.
_ACCENTS = (
    "cat--tech", "cat--culture", "cat--design",
    "cat--science", "cat--business", "cat--opinion",
)


@register.filter
def accent_class(pk):
    """Map a post's pk to one of the six category accent classes."""
    try:
        return _ACCENTS[int(pk) % len(_ACCENTS)]
    except (TypeError, ValueError):
        return _ACCENTS[0]
