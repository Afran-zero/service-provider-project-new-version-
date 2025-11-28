import random
import os
from dotenv import load_dotenv
from patterns.cloudinary_adapter import get_cloudinary_adapter

# Load environment variables
load_dotenv()

# Hardcoded PIN for verification (email/phone)
HARDCODED_PIN = "123456"

# In-memory store for verification (for demo)
verification_codes = {}

# Adapter instances
_cloudinary_adapter = None


def _get_cloudinary():
    """Get Cloudinary adapter instance (lazy loaded)"""
    global _cloudinary_adapter
    if _cloudinary_adapter is None:
        _cloudinary_adapter = get_cloudinary_adapter()
    return _cloudinary_adapter


def generate_verification_code():
    """Generate hardcoded PIN for verification"""
    return HARDCODED_PIN


def send_verification_email(email, code):
    """
    Mock send verification email (prints to console)
    Uses hardcoded PIN regardless of generated code
    
    Args:
        email: Recipient email address
        code: Generated code (ignored, uses HARDCODED_PIN)
    """
    verification_codes[email] = HARDCODED_PIN
    print(f"[VERIFICATION EMAIL] To: {email}")
    print(f"[VERIFICATION EMAIL] Code: {HARDCODED_PIN}")
    return HARDCODED_PIN


def send_verification_sms(phone, code):
    """
    Mock send verification SMS (prints to console)
    Uses hardcoded PIN regardless of generated code
    
    Args:
        phone: Recipient phone number
        code: Generated code (ignored, uses HARDCODED_PIN)
    """
    verification_codes[phone] = HARDCODED_PIN
    print(f"[VERIFICATION SMS] To: {phone}")
    print(f"[VERIFICATION SMS] Code: {HARDCODED_PIN}")
    return HARDCODED_PIN


def email_verification(email, code):
    """Verify email code against hardcoded PIN"""
    return code == HARDCODED_PIN


def phone_verification(phone, code):
    """Verify phone code against hardcoded PIN"""
    return code == HARDCODED_PIN


def upload_image_to_cloudinary(file, folder="uploads", public_id=None):
    """
    Upload an image file to Cloudinary using adapter.
    
    Args:
        file: FileStorage object from Flask request.files
        folder: Cloudinary folder name (default: "uploads")
        public_id: Custom public ID for the image (optional)
    
    Returns:
        Secure URL string, or None on failure
    """
    adapter = _get_cloudinary()
    
    try:
        transformations = {
            "width": 500,
            "height": 500,
            "quality": "auto:good",
            "crop": "limit"
        }
        
        result = adapter.upload(file, folder, public_id, transformations)
        return result.get('url') if result else None
        
    except Exception as e:
        print(f"[ERROR] Image upload failed: {str(e)}")
        return None


def delete_image_from_cloudinary(public_id_or_url):
    """
    Delete an image from Cloudinary using adapter.
    
    Args:
        public_id_or_url: The public ID or URL of the image to delete
    
    Returns:
        True if successful, False otherwise
    """
    adapter = _get_cloudinary()
    return adapter.delete(public_id_or_url)


def get_cloudinary_url(public_id_or_url, width=None, height=None, quality="auto:good", lazy=False):
    """
    Generate optimized Cloudinary URL using adapter.
    
    Args:
        public_id_or_url: Cloudinary public_id or full URL
        width: Target width (optional)
        height: Target height (optional)
        quality: Image quality ('auto', 'auto:low', 'auto:good', 'auto:best', or 1-100)
        lazy: Enable lazy loading optimization (default: False)
    
    Returns:
        Optimized Cloudinary URL with transformations
    """
    adapter = _get_cloudinary()
    
    transformations = {}
    if width:
        transformations['width'] = width
    if height:
        transformations['height'] = height
    if quality:
        transformations['quality'] = quality
    if lazy:
        transformations['effect'] = 'blur:100'
    
    url = adapter.get_url(public_id_or_url, transformations)
    return url if url else public_id_or_url


def get_cloudinary_thumbnail_url(public_id_or_url, size=150):
    """
    Generate thumbnail URL using adapter.
    
    Args:
        public_id_or_url: Cloudinary public_id or full URL
        size: Thumbnail size (square, default: 150px)
    
    Returns:
        Optimized thumbnail URL
    """
    adapter = _get_cloudinary()
    return adapter.get_thumbnail_url(public_id_or_url, size)
