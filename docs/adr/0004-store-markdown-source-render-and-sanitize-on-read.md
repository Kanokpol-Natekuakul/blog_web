# Store Markdown source; render and sanitize HTML on read

Post bodies are authored in Markdown. We store the **Markdown source** as the source of truth and convert it to HTML when displaying, passing the output through an HTML sanitizer that strips dangerous tags and attributes (`<script>`, `onerror`, etc.). We use **`nh3`** (the maintained Rust-based successor recommended by the now-unmaintained `bleach`) as the sanitizer.

Raw/embedded HTML in posts is **not** allowed. On a public multi-tenant platform every post body is untrusted input from a stranger, so permitting raw HTML would be stored XSS. We accept reduced authoring flexibility in exchange for safety.

Storing the source (rather than rendered HTML) keeps posts editable and lets us change the rendering/sanitization rules later without data migration.
