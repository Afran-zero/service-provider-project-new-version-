# controllers/business_controller.py
from models.business import Business, Service
from utils import upload_image_to_cloudinary, delete_image_from_cloudinary, get_cloudinary_url, get_cloudinary_thumbnail_url
import datetime


def create_business(owner_id=None, data=None, profile_pic=None, gallery_pics=None, services=None):
    """Create a new business with profile picture and gallery.

    owner_id is optional; if not provided the business will be created
    without a linked user account. You may also pass `owner_name` inside
    `data` for non-user owners.
    """
    if data is None:
        data = {}

    profile_pic_url = None
    gallery_urls = []

    # Determine an owner key for storage paths (use owner_id if available)
    owner_key = owner_id or data.get('owner_id') or 'no_owner'

    # Upload profile picture if provided
    if profile_pic:
        folder = f"businesses/{owner_key}"
        public_id = f"profile_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        profile_pic_url = upload_image_to_cloudinary(profile_pic, folder, public_id)

    # Upload gallery images if provided
    if gallery_pics:
        folder = f"businesses/{owner_key}/gallery"
        for idx, gallery_pic in enumerate(gallery_pics):
            public_id = f"gallery_{idx}_{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            gallery_url = upload_image_to_cloudinary(gallery_pic, folder, public_id)
            if gallery_url:
                gallery_urls.append(gallery_url)

    business = Business(
        owner_id=owner_id or data.get('owner_id'),
        owner_name=data.get('owner_name'),
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        street_house=data['street_house'],
        city=data['city'],
        district=data['district'],
        description=data.get('description', ''),
        profile_pic_url=profile_pic_url,
        gallery_urls=gallery_urls,
        category=data['category']
    )
    business.save()

    # If services were provided as a list of dicts, create Service documents
    if services and isinstance(services, list):
        for svc in services:
            try:
                name = svc.get('name')
                if not name:
                    continue
                price = float(svc.get('price', 0.0) or 0.0)
                duration = int(svc.get('duration_minutes', svc.get('duration', 60) or 60))
                description = svc.get('description')
                service_obj = Service(
                    business_id=business.business_id,
                    name=name,
                    description=description,
                    price=price,
                    duration_minutes=duration
                )
                service_obj.save()
            except Exception:
                # skip faulty service entries
                continue

    return business


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
        'profile_pic_url': business.profile_pic_url,
        'profile_pic_optimized': get_cloudinary_url(business.profile_pic_url, width=500, height=500) if business.profile_pic_url else None,
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


# Service Management Functions
def create_service(business_id, data):
    """Create a new service for a business"""
    service = Service(
        business_id=business_id,
        name=data['name'],
        description=data.get('description', ''),
        price=data['price'],
        duration_minutes=data.get('duration_minutes', 60)
    )
    service.save()
    return service


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