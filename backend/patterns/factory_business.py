# patterns/factory_business.py
"""
Factory Pattern for Business Type Creation

Creates different business types with type-specific configurations,
validation rules, and default services.
"""

from models.business import Business
import uuid


class BusinessType:
    """Base class for business types"""
    
    business_type = "generic"
    required_fields = ['name', 'email', 'phone', 'street_house', 'city', 'district']
    default_services = []
    
    def __init__(self, owner_id, data):
        self.owner_id = owner_id
        self.data = data
    
    def validate(self):
        """Validate business-specific requirements"""
        for field in self.required_fields:
            if not self.data.get(field):
                raise ValueError(f"Missing required field: {field}")
        return True
    
    def create(self):
        """Create business with type-specific defaults"""
        self.validate()
        
        business = Business(
            owner_id=self.owner_id,
            name=self.data['name'],
            email=self.data['email'],
            phone=self.data['phone'],
            street_house=self.data['street_house'],
            city=self.data['city'],
            district=self.data['district'],
            description=self.data.get('description', self.get_default_description()),
            category=self.business_type,
            profile_pic_url=self.data.get('profile_pic_url'),
            gallery_urls=self.data.get('gallery_urls', [])
        )
        return business
    
    def get_default_description(self):
        """Get default description for business type"""
        return f"Professional {self.business_type} services"
    
    def get_default_services(self):
        """Get list of default services for this business type"""
        return self.default_services


class CleaningBusiness(BusinessType):
    """Cleaning service business"""
    
    business_type = "cleaning"
    default_services = [
        {"name": "House Cleaning", "price": 50.0, "duration_minutes": 120},
        {"name": "Deep Cleaning", "price": 100.0, "duration_minutes": 240},
        {"name": "Office Cleaning", "price": 80.0, "duration_minutes": 180},
        {"name": "Window Cleaning", "price": 30.0, "duration_minutes": 60}
    ]
    
    def get_default_description(self):
        return "Professional cleaning services for homes and offices. Reliable, thorough, and affordable."


class PlumbingBusiness(BusinessType):
    """Plumbing service business"""
    
    business_type = "plumbing"
    default_services = [
        {"name": "Pipe Repair", "price": 75.0, "duration_minutes": 90},
        {"name": "Leak Fixing", "price": 60.0, "duration_minutes": 60},
        {"name": "Drain Cleaning", "price": 55.0, "duration_minutes": 60},
        {"name": "Toilet Repair", "price": 65.0, "duration_minutes": 90},
        {"name": "Water Heater Installation", "price": 200.0, "duration_minutes": 180}
    ]
    
    def get_default_description(self):
        return "Licensed plumbing services. Emergency repairs, installations, and maintenance."


class ElectricalBusiness(BusinessType):
    """Electrical service business"""
    
    business_type = "electric"
    default_services = [
        {"name": "Wiring Installation", "price": 120.0, "duration_minutes": 150},
        {"name": "Light Fixture Installation", "price": 50.0, "duration_minutes": 60},
        {"name": "Circuit Breaker Repair", "price": 90.0, "duration_minutes": 90},
        {"name": "Outlet Installation", "price": 40.0, "duration_minutes": 45},
        {"name": "Electrical Inspection", "price": 100.0, "duration_minutes": 120}
    ]
    
    def get_default_description(self):
        return "Licensed electricians providing safe and reliable electrical services."


class PaintingBusiness(BusinessType):
    """Painting service business"""
    
    business_type = "painting"
    default_services = [
        {"name": "Interior Painting", "price": 150.0, "duration_minutes": 360},
        {"name": "Exterior Painting", "price": 200.0, "duration_minutes": 480},
        {"name": "Wall Touch-up", "price": 50.0, "duration_minutes": 90},
        {"name": "Ceiling Painting", "price": 80.0, "duration_minutes": 120}
    ]
    
    def get_default_description(self):
        return "Professional painting services for residential and commercial properties."


class CarpentryBusiness(BusinessType):
    """Carpentry service business"""
    
    business_type = "carpentry"
    default_services = [
        {"name": "Furniture Assembly", "price": 60.0, "duration_minutes": 90},
        {"name": "Cabinet Installation", "price": 150.0, "duration_minutes": 180},
        {"name": "Door Installation", "price": 100.0, "duration_minutes": 120},
        {"name": "Custom Shelving", "price": 120.0, "duration_minutes": 150},
        {"name": "Wood Repair", "price": 70.0, "duration_minutes": 90}
    ]
    
    def get_default_description(self):
        return "Skilled carpentry services for custom woodwork and installations."


class GardeningBusiness(BusinessType):
    """Gardening/Landscaping service business"""
    
    business_type = "gardening"
    default_services = [
        {"name": "Lawn Mowing", "price": 40.0, "duration_minutes": 60},
        {"name": "Garden Maintenance", "price": 70.0, "duration_minutes": 120},
        {"name": "Tree Trimming", "price": 90.0, "duration_minutes": 150},
        {"name": "Landscape Design", "price": 200.0, "duration_minutes": 240},
        {"name": "Weed Control", "price": 50.0, "duration_minutes": 90}
    ]
    
    def get_default_description(self):
        return "Expert gardening and landscaping services to beautify your outdoor spaces."


class BusinessFactory:
    """
    Factory class that creates appropriate business type instances
    """
    
    _business_types = {
        'cleaning': CleaningBusiness,
        'plumbing': PlumbingBusiness,
        'electric': ElectricalBusiness,
        'painting': PaintingBusiness,
        'carpentry': CarpentryBusiness,
        'gardening': GardeningBusiness
    }
    
    @staticmethod
    def create_business(owner_id, category, data):
        """
        Create a business of the specified type with appropriate defaults
        
        Args:
            owner_id: User ID of business owner
            category: Business category/type
            data: Business data dict
            
        Returns:
            Business object ready to save
            
        Raises:
            ValueError: If category is not supported
        """
        business_class = BusinessFactory._business_types.get(category)
        
        if not business_class:
            # Fall back to generic business type
            business_class = BusinessType
        
        business_type_instance = business_class(owner_id, data)
        return business_type_instance.create()
    
    @staticmethod
    def get_default_services(category):
        """
        Get default services for a business category
        
        Args:
            category: Business category
            
        Returns:
            List of default service dicts
        """
        business_class = BusinessFactory._business_types.get(category, BusinessType)
        return business_class.default_services
    
    @staticmethod
    def get_supported_categories():
        """Get list of all supported business categories"""
        return list(BusinessFactory._business_types.keys())
    
    @staticmethod
    def register_business_type(category, business_class):
        """
        Register a new business type
        
        Args:
            category: Category name
            business_class: BusinessType subclass
        """
        if not issubclass(business_class, BusinessType):
            raise ValueError("business_class must be a subclass of BusinessType")
        BusinessFactory._business_types[category] = business_class
