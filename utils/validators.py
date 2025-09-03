from django.core.exceptions import ValidationError

def validate_file_size(file, limit_mb=32):
    """Raise error if file exceeds `limit_mb` MB."""
    if file.size > limit_mb * 1024 * 1024:
        raise ValidationError(f"File too large. Max size is {limit_mb} MB.")
