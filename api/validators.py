import os
from django.core.exceptions import ValidationError
from PIL import Image
import magic

def validate_image_size(image):
    """Validate image file size"""
    max_size = 5 * 1024 * 1024  # 5MB
    
    if image.size > max_size:
        raise ValidationError(f'Image size should not exceed {max_size/1024/1024}MB.')

def validate_image_type(image):
    """Validate image file type using magic numbers"""
    allowed_mime_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    # Get file extension
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f'Unsupported file extension. Allowed: {", ".join(allowed_extensions)}')
    
    # Check MIME type using python-magic
    try:
        mime = magic.from_buffer(image.read(1024), mime=True)
        if mime not in allowed_mime_types:
            raise ValidationError(f'Unsupported file type. Allowed: {", ".join([m.split("/")[1] for m in allowed_mime_types])}')
    except Exception:
        # If magic fails, check extension
        if ext not in allowed_extensions:
            raise ValidationError('Invalid image file.')

def validate_image_dimensions(image):
    """Validate image dimensions"""
    min_width, min_height = 100, 100
    max_width, max_height = 5000, 5000
    
    try:
        with Image.open(image) as img:
            width, height = img.size
            
            if width < min_width or height < min_height:
                raise ValidationError(f'Image must be at least {min_width}x{min_height} pixels.')
            
            if width > max_width or height > max_height:
                raise ValidationError(f'Image must be less than {max_width}x{max_height} pixels.')
            
            # Reset file pointer
            image.seek(0)
    except Exception as e:
        raise ValidationError('Could not read image dimensions.')

def validate_image_aspect_ratio(image, width_ratio=1, height_ratio=1, tolerance=0.1):
    """Validate image aspect ratio"""
    try:
        with Image.open(image) as img:
            width, height = img.size
            expected_ratio = width_ratio / height_ratio
            actual_ratio = width / height
            
            if abs(actual_ratio - expected_ratio) > tolerance:
                raise ValidationError(f'Image must have {width_ratio}:{height_ratio} aspect ratio.')
            
            image.seek(0)
    except Exception:
        pass  # Skip aspect validation if image can't be opened

def validate_profile_image(image):
    """Complete validation for profile images"""
    validate_image_size(image)
    validate_image_type(image)
    validate_image_dimensions(image)
    validate_image_aspect_ratio(image, 1, 1)  # Square aspect ratio