# Cover images: one per post, local media now, cloud storage later

Each Post may have one optional **cover image** (a single `ImageField`), shown as a thumbnail on listings/feeds and at the top of the post. Inline images within the post body are deliberately out of scope for now — they need an upload-while-editing flow that is much more involved.

Uploads are stored on the local filesystem (`MEDIA_ROOT`) for development. Accepted formats are jpg/png/webp, max 5 MB.

## Consequences

Local filesystem storage does **not** survive on typical deploy targets (Render/Railway have ephemeral disks — uploads vanish on restart). Before deploying, image storage must move to a persistent service (planned: **Cloudinary**, which has a free tier). This is a known migration, deferred until deploy.
