# controllers/business_controller.py
from models.business import Business, Service
from utils import upload_image_to_cloudinary, delete_image_from_cloudinary, get_cloudinary_url, get_cloudinary_thumbnail_url
from patterns.builder_business import BusinessBuilder
from patterns.factory_business import BusinessFactory
from patterns.factory_service import ServiceFactory
import datetime


def create_business(owner_id=None, data=None, profile_pic=None, gallery_pics=None, services=None):
    """
    Create a new business using Builder Pattern with Factory defaults.
    
    Design Pattern: Builder Pattern
    - Provides step-by-step construction with validation
    - Uses Factory for category-specific defaults
    """
    if data is None:
        data = {}

    profile_pic_url = None
    gallery_urls = []
    owner_key = owner_id or data.get('owner_id') or 'no_owner'

    # Upload profile picture
    if profile_pic:
        if owner_id:
            try:
                from models.user import User
                user = User.objects.get(user_id=owner_id)
                user_folder = "user_profiles"
                public_id = f"user_{owner_id}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                uploaded_url = upload_image_to_cloudinary(profile_pic, user_folder, public_id)
                if uploaded_url:
                    user.profile_pic_url = uploaded_url
                    user.updated_at = datetime.datetime.utcnow()
                    user.save()
                    profile_pic_url = uploaded_url
            except Exception:
                folder = f"businesses/{owner_key}"
                public_id = f"profile_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                profile_pic_url = upload_image_to_cloudinary(profile_pic, folder, public_id)
        else:
            folder = f"businesses/{owner_key}"
            public_id = f"profile_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            profile_pic_url = upload_image_to_cloudinary(profile_pic, folder, public_id)

    # Upload gallery images
    if gallery_pics:
        folder = f"businesses/{owner_key}/gallery"
        for idx, gallery_pic in enumerate(gallery_pics):
            public_id = f"gallery_{idx}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            gallery_url = upload_image_to_cloudinary(gallery_pic, folder, public_id)
            if gallery_url:
                gallery_urls.append(gallery_url)

    # ===== BUILDER PATTERN IMPLEMENTATION =====
    try:
        builder = BusinessBuilder()
        
        # Set owner information
        if owner_id:
            builder.set_owner_id(owner_id)
        if data.get('owner_name'):
            builder.set_owner_name(data['owner_name'])
        
        # Set required fields (validates each field)
        builder.set_name(data['name'])
        builder.set_email(data['email'])
        builder.set_phone(data['phone'])
        builder.set_street_house(data['street_house'])
        builder.set_city(data['city'])
        builder.set_district(data['district'])
        builder.set_category(data['category'])
        
        # Set description (use Factory default if not provided)
        if data.get('description'):
            builder.set_description(data['description'])
        else:
            business_type_class = BusinessFactory._business_types.get(data['category'])
            if business_type_class:
                default_desc = business_type_class(None, {}).get_default_description()
                builder.set_description(default_desc)
        
        # Set uploaded media
        if profile_pic_url:
            builder.set_profile_pic_url(profile_pic_url)
        if gallery_urls:
            builder.set_gallery_urls(gallery_urls)
        
        # Build and save business
        business = builder.build_and_save()
        
        # Create services (use provided or Factory defaults)
        if services and isinstance(services, list):
            for svc in services:
                try:
                    name = svc.get('name')
                    if not name:
                        continue
                    service_obj = Service(
                        business_id=business.business_id,
                        name=name,
                        description=svc.get('description'),
                        price=float(svc.get('price', 0.0) or 0.0),
                        duration_minutes=int(svc.get('duration_minutes', svc.get('duration', 60) or 60))
                    )
                    service_obj.save()
                except Exception:
                    continue
        else:
            # Use Factory to get default services for category
            default_services = BusinessFactory.get_default_services(data['category'])
            for svc in default_services:
                try:
                    service_obj = Service(
                        business_id=business.business_id,
                        name=svc['name'],
                        description=svc.get('description'),
                        price=svc['price'],
                        duration_minutes=svc['duration_minutes']
                    )
                    service_obj.save()
                except Exception:
                    continue
        
        return business
        
    except ValueError as e:
        raise ValueError(f"Business validation failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to create business: {str(e)}")


def get_business(business_id):
    """Get a single business by ID"""
    try:
        business = Business.objects.get(business_id=business_id)
        return business
    except Business.DoesNotExist:
        return None


def get_business_details(business_id):
    """Get business details with optimized image URLs"""
    business = get_business(business_id)
    if not business:
        return None
    # Determine original profile image: prefer business profile_pic_url, else owner's user profile_pic_url
    original_url = business.profile_pic_url
    if not original_url and business.owner_id:
        try:
            from models.user import User
            owner = User.objects.get(user_id=business.owner_id)
            if getattr(owner, 'profile_pic_url', None):
                original_url = owner.profile_pic_url
        except Exception as e:
            try:
                print(f"[WARN] Unable to fetch owner profile image for business {business.business_id}: {e}")
            except Exception:
                pass
    if not original_url:
        try:
            print(f"[DEBUG] No profile image for business {business.business_id} (neither business nor owner).")
        except Exception:
            pass

    # Provide both a lazy placeholder (blurred) and a full-quality URL for progressive loading
    profile_full = None
    profile_lazy = None
    if original_url:
        # Attempt to build transformed URLs; fall back to original if adapter returns None
        profile_full = get_cloudinary_url(original_url, width=800, height=800, quality="auto:good") or original_url
        profile_lazy = get_cloudinary_url(original_url, width=40, height=40, quality="auto:low", lazy=True) or original_url

    result = {
        'business_id': business.business_id,
        'owner_id': business.owner_id,
        'name': business.name,
        'email': business.email,
        'phone': business.phone,
        'street_house': business.street_house,
        'city': business.city,
        'district': business.district,
        'description': business.description,
        'category': business.category,
        'is_active': business.is_active,
        'created_at': business.created_at,
        'profile_pic_url': original_url,  # original stored URL (business or owner)
        'profile_pic_full': profile_full,
        'profile_pic_lazy': profile_lazy,
        'profile_pic_thumbnail': get_cloudinary_thumbnail_url(business.profile_pic_url, size=150) if business.profile_pic_url else None,
        'gallery_urls': business.gallery_urls,
        'gallery_thumbnails': [get_cloudinary_thumbnail_url(url, size=200) for url in business.gallery_urls]
    }
    return result


def update_business(business_id, data, profile_pic=None, gallery_pics=None):
    """Update business information with optional image uploads"""
    business = get_business(business_id)
    if not business:
        return None

    # Update profile picture if provided
    if profile_pic:
        # Delete old profile picture if exists
        if business.profile_pic_url:
            delete_image_from_cloudinary(business.profile_pic_url)

        owner_key = business.owner_id or business.business_id
        folder = f"businesses/{owner_key}"
        public_id = f"profile_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        business.profile_pic_url = upload_image_to_cloudinary(profile_pic, folder, public_id)

    # Add new gallery images if provided
    if gallery_pics:
        owner_key = business.owner_id or business.business_id
        folder = f"businesses/{owner_key}/gallery"
        for idx, gallery_pic in enumerate(gallery_pics):
            public_id = f"gallery_{len(business.gallery_urls) + idx}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            gallery_url = upload_image_to_cloudinary(gallery_pic, folder, public_id)
            if gallery_url:
                business.gallery_urls.append(gallery_url)

    # Update text fields
    if 'name' in data:
        business.name = data['name']
    if 'email' in data:
        business.email = data['email']
    if 'phone' in data:
        business.phone = data['phone']
    if 'street_house' in data:
        business.street_house = data['street_house']
    if 'city' in data:
        business.city = data['city']
    if 'district' in data:
        business.district = data['district']
    if 'description' in data:
        business.description = data['description']
    if 'category' in data:
        business.category = data['category']

    business.updated_at = datetime.datetime.utcnow()
    business.save()
    return business


def list_businesses(category=None, city=None, district=None, is_active=True):
    """List businesses with optional filters"""
    query = {}
    if category:
        query['category'] = category
    if city:
        query['city'] = city
    if district:
        query['district'] = district
    if is_active is not None:
        query['is_active'] = is_active

    businesses = Business.objects(**query).order_by('-created_at')
    return businesses


def deactivate_business(business_id):
    """Deactivate a business"""
    business = get_business(business_id)
    if not business:
        return None

    business.is_active = False
    business.updated_at = datetime.datetime.utcnow()
    business.save()
    return business


def delete_gallery_image(business_id, gallery_url):
    """Remove an image from business gallery"""
    business = get_business(business_id)
    if not business or gallery_url not in business.gallery_urls:
        return None

    # Delete from Cloudinary
    delete_image_from_cloudinary(gallery_url)

    # Remove from list
    business.gallery_urls.remove(gallery_url)
    business.updated_at = datetime.datetime.utcnow()
    business.save()
    return business


def add_gallery_images(business_id, gallery_pics):
    """Add multiple images to an existing business gallery.

    Args:
        business_id: Target business ID
        gallery_pics: List of FileStorage objects

    Returns:
        List of newly added image URLs
    """
    business = get_business(business_id)
    if not business:
        return []
    if not gallery_pics:
        return []

    owner_key = business.owner_id or business.business_id
    folder = f"businesses/{owner_key}/gallery"
    new_urls = []
    for gallery_pic in gallery_pics:
        if not gallery_pic or not getattr(gallery_pic, 'filename', None):
            continue
        public_id = f"gallery_{len(business.gallery_urls) + len(new_urls)}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        gallery_url = upload_image_to_cloudinary(gallery_pic, folder, public_id)
        if gallery_url:
            business.gallery_urls.append(gallery_url)
            new_urls.append(gallery_url)
    if new_urls:
        business.updated_at = datetime.datetime.utcnow()
        business.save()
    return new_urls


# Service Management Functions
def create_service(business_id, data):
    """
    Create a new service using Factory Pattern.
    
    Design Pattern: Factory Pattern
    - Creates services with category-specific defaults
    - Validates price ranges and duration
    - Applies appropriate templates
    """
    # Get business to determine category
    business = get_business(business_id)
    if not business:
        raise ValueError("Business not found")
    
    # ===== FACTORY PATTERN IMPLEMENTATION =====
    try:
        # Use ServiceFactory to create service with category-specific defaults
        service = ServiceFactory.create_service(
            business_id=business_id,
            category=business.category,
            data=data
        )
        service.save()
        return service
    except ValueError as e:
        raise ValueError(f"Service validation failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to create service: {str(e)}")


def get_service(service_id):
    """Get a single service by ID"""
    try:
        service = Service.objects.get(service_id=service_id)
        return service
    except Service.DoesNotExist:
        return None


def get_services_by_business(business_id, is_active=True):
    """Get all services for a business"""
    query = {'business_id': business_id}
    if is_active is not None:
        query['is_active'] = is_active

    services = Service.objects(**query).order_by('name')
    return services


def update_service(service_id, data):
    """Update service information"""
    service = get_service(service_id)
    if not service:
        return None

    if 'name' in data:
        service.name = data['name']
    if 'description' in data:
        service.description = data['description']
    if 'price' in data:
        service.price = data['price']
    if 'duration_minutes' in data:
        service.duration_minutes = data['duration_minutes']
    if 'is_active' in data:
        service.is_active = data['is_active']

    service.updated_at = datetime.datetime.utcnow()
    service.save()
    return service


def deactivate_service(service_id):
    """Deactivate a service"""
    service = get_service(service_id)
    if not service:
        return None

    service.is_active = False
    service.updated_at = datetime.datetime.utcnow()
    service.save()
    return service


# Wrapper functions for views
def get_all_businesses():
    """Get all active businesses - wrapper for list_businesses"""
    return list_businesses(is_active=True)


def get_business_by_id(business_id):
    """Compatibility wrapper: return detailed business info for views expecting `get_business_by_id`."""
    return get_business_details(business_id)