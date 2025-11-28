# patterns/factory_service.py
"""
Factory Pattern for Service Creation

Creates services with category-specific defaults, pricing tiers,
and validation rules.
"""

from models.business import Service
import uuid


class ServiceTemplate:
    """Base template for service creation"""
    
    service_type = "generic"
    default_duration = 60  # minutes
    price_range = (30.0, 500.0)  # min, max
    
    def __init__(self, business_id, data):
        self.business_id = business_id
        self.data = data
    
    def validate(self):
        """Validate service data"""
        if not self.data.get('name'):
            raise ValueError("Service name is required")
        
        if not self.data.get('price'):
            raise ValueError("Service price is required")
        
        price = float(self.data['price'])
        if not (self.price_range[0] <= price <= self.price_range[1]):
            raise ValueError(
                f"Price must be between {self.price_range[0]} and {self.price_range[1]}"
            )
        
        return True
    
    def create(self):
        """Create service with defaults"""
        self.validate()
        
        service = Service(
            business_id=self.business_id,
            name=self.data['name'],
            description=self.data.get('description', self.get_default_description()),
            price=float(self.data['price']),
            duration_minutes=int(self.data.get('duration_minutes', self.default_duration))
        )
        return service
    
    def get_default_description(self):
        """Get default description"""
        return f"Professional {self.service_type} service"


class CleaningServiceTemplate(ServiceTemplate):
    """Template for cleaning services"""
    
    service_type = "cleaning"
    default_duration = 120
    price_range = (30.0, 200.0)
    
    def get_default_description(self):
        return f"{self.data['name']} - Thorough and professional cleaning service"


class PlumbingServiceTemplate(ServiceTemplate):
    """Template for plumbing services"""
    
    service_type = "plumbing"
    default_duration = 90
    price_range = (50.0, 300.0)
    
    def get_default_description(self):
        return f"{self.data['name']} - Licensed plumber with guaranteed work"


class ElectricalServiceTemplate(ServiceTemplate):
    """Template for electrical services"""
    
    service_type = "electric"
    default_duration = 90
    price_range = (40.0, 250.0)
    
    def get_default_description(self):
        return f"{self.data['name']} - Certified electrician ensuring safety and quality"


class PaintingServiceTemplate(ServiceTemplate):
    """Template for painting services"""
    
    service_type = "painting"
    default_duration = 240
    price_range = (50.0, 500.0)
    
    def get_default_description(self):
        return f"{self.data['name']} - Quality painting with premium materials"


class ServiceFactory:
    """
    Factory for creating services with category-specific defaults
    """
    
    _service_templates = {
        'cleaning': CleaningServiceTemplate,
        'plumbing': PlumbingServiceTemplate,
        'electric': ElectricalServiceTemplate,
        'painting': PaintingServiceTemplate
    }
    
    # Predefined service packages
    _service_packages = {
        'basic_cleaning': {
            'name': 'Basic Cleaning',
            'description': 'Standard cleaning for small spaces',
            'price': 50.0,
            'duration_minutes': 120
        },
        'deep_cleaning': {
            'name': 'Deep Cleaning',
            'description': 'Comprehensive cleaning including hard-to-reach areas',
            'price': 100.0,
            'duration_minutes': 240
        },
        'emergency_plumbing': {
            'name': 'Emergency Plumbing',
            'description': '24/7 emergency plumbing service',
            'price': 150.0,
            'duration_minutes': 60
        },
        'standard_plumbing': {
            'name': 'Standard Plumbing',
            'description': 'Regular plumbing maintenance and repairs',
            'price': 75.0,
            'duration_minutes': 90
        },
        'basic_electrical': {
            'name': 'Basic Electrical Work',
            'description': 'Simple electrical repairs and installations',
            'price': 60.0,
            'duration_minutes': 60
        },
        'advanced_electrical': {
            'name': 'Advanced Electrical Work',
            'description': 'Complex wiring and electrical system work',
            'price': 150.0,
            'duration_minutes': 150
        }
    }
    
    @staticmethod
    def create_service(business_id, category, data):
        """
        Create a service with category-specific defaults
        
        Args:
            business_id: ID of the business
            category: Service category
            data: Service data dict
            
        Returns:
            Service object ready to save
        """
        template_class = ServiceFactory._service_templates.get(category, ServiceTemplate)
        template = template_class(business_id, data)
        return template.create()
    
    @staticmethod
    def create_service_from_package(business_id, package_name):
        """
        Create a service from a predefined package
        
        Args:
            business_id: ID of the business
            package_name: Name of the package
            
        Returns:
            Service object ready to save
            
        Raises:
            ValueError: If package doesn't exist
        """
        package_data = ServiceFactory._service_packages.get(package_name)
        if not package_data:
            raise ValueError(f"Package '{package_name}' not found")
        
        service = Service(
            business_id=business_id,
            name=package_data['name'],
            description=package_data['description'],
            price=package_data['price'],
            duration_minutes=package_data['duration_minutes']
        )
        return service
    
    @staticmethod
    def get_available_packages():
        """Get all available service packages"""
        return ServiceFactory._service_packages
    
    @staticmethod
    def create_bulk_services(business_id, category, services_data):
        """
        Create multiple services at once
        
        Args:
            business_id: ID of the business
            category: Service category
            services_data: List of service data dicts
            
        Returns:
            List of Service objects
        """
        services = []
        for service_data in services_data:
            try:
                service = ServiceFactory.create_service(business_id, category, service_data)
                services.append(service)
            except ValueError as e:
                # Log error but continue with other services
                print(f"Error creating service: {e}")
        
        return services
    
    @staticmethod
    def register_template(category, template_class):
        """
        Register a new service template
        
        Args:
            category: Category name
            template_class: ServiceTemplate subclass
        """
        if not issubclass(template_class, ServiceTemplate):
            raise ValueError("template_class must be a subclass of ServiceTemplate")
        ServiceFactory._service_templates[category] = template_class
    
    @staticmethod
    def register_package(package_name, package_data):
        """
        Register a new service package
        
        Args:
            package_name: Unique package name
            package_data: Package data dict
        """
        required_fields = ['name', 'description', 'price', 'duration_minutes']
        for field in required_fields:
            if field not in package_data:
                raise ValueError(f"Package data missing required field: {field}")
        
        ServiceFactory._service_packages[package_name] = package_data
