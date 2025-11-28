# controllers/user_controller.py
# Changes: Check for existing phone in register_user; Remove strategy.verify from login_user since handled in route; Hardcode code in send_forgot_password_email and comment out send
from models.user import User
# from patterns.auth_strategy import AuthStrategy  # Removed as not needed for login now
from utils import (
    send_verification_email, 
    generate_verification_code, 
    upload_image_to_cloudinary,
    get_cloudinary_url,
    get_cloudinary_thumbnail_url
)
import datetime
import mongoengine as me

# Registration
def register_user(data, role='customer'):
    """
    Register a new user with optional role specification.
    
    Args:
        data: Dictionary with user registration details
        role: User role ('customer' or 'business_owner'). Defaults to 'customer'.
    
    Returns:
        Tuple (user, error_message)
    """
    # Validate role
    valid_roles = ('customer', 'business_owner')
    if role not in valid_roles:
        return None, f"Invalid role. Must be one of: {', '.join(valid_roles)}"
    
    existing_email = User.objects(email=data['email']).first()
    if existing_email:
        return None, "Email already registered."
    existing_phone = User.objects(phone=data['phone']).first()
    if existing_phone:
        return None, "Phone already registered."
    user = User(
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        street_house=data['street_house'],
        city=data['city'],
        district=data['district'],
        role=role  # Set the role from parameter
    )
    user.set_password(data['password'])
    user.save()
    return user, None

# Login (email or phone)
def login_user(identifier, password):  # Removed request_data as verification handled in route
    user = User.objects(me.Q(email=identifier) | me.Q(phone=identifier)).first()
    if not user:
        return None, "User not found"
    if not user.check_password(password):
        return None, "Incorrect password"
    return user, None

# Forgot password email trigger
def send_forgot_password_email(email):
    user = User.objects(email=email).first()
    if not user:
        return None
    code = "123456"  # Hardcoded as per instructions
    # send_verification_email(email, code)  # Commented out for now
    return code

# Reset password
def reset_password(email, code_entered, real_code, new_password):
    if code_entered != real_code:
        return False
    user = User.objects(email=email).first()
    if user:
        user.set_password(new_password)
        user.updated_at = datetime.datetime.utcnow()
        user.save()
        return True
    return False

# Update profile and profile picture
def update_profile(user_id, data, profile_picture_file=None):
    """
    Update user profile information and optionally upload profile picture to Cloudinary.
    
    Args:
        user_id: User's unique ID
        data: Dictionary of fields to update (name, phone, address, etc.)
        profile_picture_file: FileStorage object from request.files (optional)
    
    Returns:
        Tuple (user, error_message)
    """
    user = User.objects(user_id=user_id).first()
    if not user:
        return None, "User not found"
    
    # Handle profile picture upload to Cloudinary
    if profile_picture_file:
        try:
            cloudinary_response = upload_image_to_cloudinary(
                profile_picture_file,
                folder="user_profiles",
                public_id=f"user_{user_id}"
            )
            if cloudinary_response:
                # Store the secure URL from Cloudinary
                user.profile_pic_url = cloudinary_response['secure_url']
            else:
                return None, "Failed to upload profile picture"
        except Exception as e:
            return None, f"Error uploading image: {str(e)}"
    
    # Update other fields
    allowed_fields = ['name', 'phone', 'street_house', 'city', 'district']
    for key, value in data.items():
        if key in allowed_fields and value:
            setattr(user, key, value)
    
    user.updated_at = datetime.datetime.utcnow()
    user.save()
    return user, None


def get_user_profile(user_id, thumbnail_size=150):
    """
    Get user profile with optimized Cloudinary image URLs for lazy loading.
    
    Args:
        user_id: User's unique ID
        thumbnail_size: Size for thumbnail version (default: 150px)
    
    Returns:
        Dictionary with user data and optimized image URLs, or None if not found
    """
    user = User.objects(user_id=user_id).first()
    if not user:
        return None
    
    # Convert to dictionary
    user_data = {
        'user_id': user.user_id,
        'name': user.name,
        'email': user.email,
        'phone': user.phone,
        'street_house': user.street_house,
        'city': user.city,
        'district': user.district,
        'is_verified': user.is_verified,
        'created_at': user.created_at,
        'updated_at': user.updated_at,
        'profile_pic_url': user.profile_pic_url,
        'profile_pic_optimized': None,
        'profile_pic_thumbnail': None
    }
    
    # Generate optimized URLs with lazy loading if profile picture exists
    if user.profile_pic_url:
        # Full size optimized with lazy loading
        user_data['profile_pic_optimized'] = get_cloudinary_url(
            user.profile_pic_url,
            width=500,
            height=500,
            quality="auto:good",
            lazy=True
        )
        # Thumbnail for lists/previews
        user_data['profile_pic_thumbnail'] = get_cloudinary_thumbnail_url(
            user.profile_pic_url,
            size=thumbnail_size
        )
    
    return user_data