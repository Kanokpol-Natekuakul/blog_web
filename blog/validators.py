import os
from django.core.exceptions import ValidationError

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_image_size(f):
    if not f:
        return
    try:
        if f.size > MAX_IMAGE_BYTES:
            raise ValidationError("Image must be 5 MB or smaller.")
    except (ValueError, AttributeError):
        pass


def validate_file_extension(f):
    if not f or not f.name:
        return
    ext = os.path.splitext(f.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if ext not in valid_extensions:
        raise ValidationError(
            f"File extension \"{ext[1:] if ext.startswith('.') else ext}\" is not allowed. Allowed extensions are: jpg, jpeg, png, webp."
        )

