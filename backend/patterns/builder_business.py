"""
Builder Design Pattern for Business Creation

Provides a fluent interface to build and create Business objects
with validation and default values. This pattern allows step-by-step
construction of complex Business entities.
"""

from models.business import Business
import uuid


class BusinessBuilder:
    """
    Builder class for creating Business objects with a fluent interface.
    
    Allows step-by-step construction of a Business with validation
    and sensible defaults.
    
    Example:
        business = (BusinessBuilder()
                    .set_name("Smith Plumbing")
                    .set_email("smith@plumbing.com")
                    .set_phone("555-1234")
                    .set_category("plumbing")
                    .set_city("New York")
                    .set_district("Manhattan")
                    .set_street_house("123 Main St")
                    .set_description("Professional plumbing services")
                    .build())
    """
    
    def __init__(self):
        """Initialize builder with default values."""
        self._business_id = str(uuid.uuid4())
        self._owner_id = None
        self._owner_name = None
        self._name = None
        self._email = None
        self._phone = None
        self._street_house = None
        self._city = None
        self._district = None
        self._description = None
        self._profile_pic_url = None
        self._gallery_urls = []
        self._category = None
        self._is_active = True
    
    def set_business_id(self, business_id):
        """Set custom business ID (optional, generates UUID by default)."""
        self._business_id = business_id
        return self
    
    def set_owner_id(self, owner_id):
        """Set the owner user ID (optional for admin-created businesses)."""
        self._owner_id = owner_id
        return self
    
    def set_owner_name(self, owner_name):
        """Set the owner name (used when no user account linked)."""
        self._owner_name = owner_name
        return self
    
    def set_name(self, name):
        """Set business name (required)."""
        if not name or len(name.strip()) == 0:
            raise ValueError("Business name cannot be empty")
        self._name = name.strip()
        return self
    
    def set_email(self, email):
        """Set business email (required)."""
        if not email or '@' not in email:
            raise ValueError("Invalid email address")
        self._email = email.strip()
        return self
    
    def set_phone(self, phone):
        """Set business phone (required)."""
        if not phone or len(phone.strip()) == 0:
            raise ValueError("Phone number cannot be empty")
        self._phone = phone.strip()
        return self
    
    def set_street_house(self, street_house):
        """Set street/house address (required)."""
        if not street_house or len(street_house.strip()) == 0:
            raise ValueError("Street/house address cannot be empty")
        self._street_house = street_house.strip()
        return self
    
    def set_city(self, city):
        """Set city (required)."""
        if not city or len(city.strip()) == 0:
            raise ValueError("City cannot be empty")
        self._city = city.strip()
        return self
    
    def set_district(self, district):
        """Set district (required)."""
        if not district or len(district.strip()) == 0:
            raise ValueError("District cannot be empty")
        self._district = district.strip()
        return self
    
    def set_category(self, category):
        """Set service category (required)."""
        if not category or len(category.strip()) == 0:
            raise ValueError("Category cannot be empty")
        self._category = category.strip()
        return self
    
    def set_description(self, description):
        """Set business description (optional)."""
        if description:
            self._description = description.strip()
        return self
    
    def set_profile_pic_url(self, profile_pic_url):
        """Set profile picture URL (optional)."""
        if profile_pic_url:
            self._profile_pic_url = profile_pic_url.strip()
        return self
    
    def add_gallery_image(self, image_url):
        """Add an image to the gallery."""
        if image_url and image_url.strip():
            self._gallery_urls.append(image_url.strip())
        return self
    
    def set_gallery_urls(self, gallery_urls):
        """Set gallery images as a list."""
        if gallery_urls and isinstance(gallery_urls, list):
            self._gallery_urls = [url.strip() for url in gallery_urls if url]
        return self
    
    def set_is_active(self, is_active):
        """Set business active status (default: True)."""
        self._is_active = bool(is_active)
        return self
    
    def validate(self):
        """
        Validate that all required fields are set.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        required_fields = {
            'name': self._name,
            'email': self._email,
            'phone': self._phone,
            'street_house': self._street_house,
            'city': self._city,
            'district': self._district,
            'category': self._category,
        }
        
        for field_name, field_value in required_fields.items():
            if not field_value:
                return False, f"Missing required field: {field_name}"
        
        return True, None
    
    def build(self):
        """
        Build and return the Business object.
        
        Returns:
            Business: The constructed Business object
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        is_valid, error = self.validate()
        if not is_valid:
            raise ValueError(f"Cannot build business: {error}")
        
        # Create Business document (MongoEngine)
        business = Business(
            business_id=self._business_id,
            owner_id=self._owner_id,
            owner_name=self._owner_name,
            name=self._name,
            email=self._email,
            phone=self._phone,
            street_house=self._street_house,
            city=self._city,
            district=self._district,
            description=self._description,
            profile_pic_url=self._profile_pic_url,
            gallery_urls=self._gallery_urls,
            category=self._category,
            is_active=self._is_active
        )
        
        return business
    
    def build_and_save(self):
        """
        Build and save the Business to MongoDB.
        
        Returns:
            Business: The saved Business object
            
        Raises:
            ValueError: If validation fails or save fails
        """
        business = self.build()
        try:
            business.save()
            return business
        except Exception as e:
            raise ValueError(f"Failed to save business: {str(e)}")
    
    def reset(self):
        """Reset builder to initial state for reuse."""
        self.__init__()
        return self
    
    def __repr__(self):
        """String representation of builder state."""
        return (
            f"BusinessBuilder(name={self._name}, email={self._email}, "
            f"category={self._category}, city={self._city}, active={self._is_active})"
        )


def create_business_from_dict(data):
    """
    Convenience function to create a Business using a dictionary.
    
    Args:
        data: Dictionary with business fields
        
    Returns:
        Business: The constructed and saved Business object
        
    Example:
        business = create_business_from_dict({
            'name': 'Smith Plumbing',
            'email': 'smith@plumbing.com',
            'phone': '555-1234',
            'category': 'plumbing',
            'city': 'New York',
            'district': 'Manhattan',
            'street_house': '123 Main St'
        })
    """
    builder = BusinessBuilder()
    
    if 'owner_id' in data:
        builder.set_owner_id(data['owner_id'])
    if 'owner_name' in data:
        builder.set_owner_name(data['owner_name'])
    
    builder.set_name(data.get('name'))
    builder.set_email(data.get('email'))
    builder.set_phone(data.get('phone'))
    builder.set_street_house(data.get('street_house'))
    builder.set_city(data.get('city'))
    builder.set_district(data.get('district'))
    builder.set_category(data.get('category'))
    
    if 'description' in data:
        builder.set_description(data['description'])
    if 'profile_pic_url' in data:
        builder.set_profile_pic_url(data['profile_pic_url'])
    if 'gallery_urls' in data:
        builder.set_gallery_urls(data['gallery_urls'])
    if 'is_active' in data:
        builder.set_is_active(data['is_active'])
    
    return builder.build_and_save()
