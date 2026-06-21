from django.core.exceptions import ValidationError

MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


def validate_image_size(f):
    if f.size > MAX_IMAGE_BYTES:
        raise ValidationError("Image must be 5 MB or smaller.")
