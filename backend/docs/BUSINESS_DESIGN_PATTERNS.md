# Design Patterns for Business Creation and Operations

## Overview

This document explains all design patterns used in business-related creation and operations in the Service Provider application. The system uses **Builder Pattern** and **Factory Pattern** to create businesses, services, and manage categories with validation, defaults, and type-specific configurations.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Builder Pattern - Business Construction](#builder-pattern---business-construction)
3. [Factory Pattern - Business Types](#factory-pattern---business-types)
4. [Factory Pattern - Service Creation](#factory-pattern---service-creation)
5. [Factory Pattern - Category Management](#factory-pattern---category-management)
6. [Complete Business Creation Flow](#complete-business-creation-flow)
7. [Benefits and Best Practices](#benefits-and-best-practices)

---

## Architecture Overview

### Design Patterns Used

```
┌─────────────────────────────────────────────────────────────┐
│                  BUSINESS CREATION SYSTEM                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────────────┐   ┌─────────────────┐   ┌───────────────┐
│    BUILDER    │   │     FACTORY     │   │    FACTORY    │
│    PATTERN    │   │     PATTERN     │   │    PATTERN    │
│               │   │                 │   │               │
│   Business    │   │  BusinessType   │   │   Service     │
│ Construction  │   │   Categories    │   │  Templates    │
└───────────────┘   └─────────────────┘   └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ↓
              ┌───────────────────────────┐
              │    FACTORY PATTERN        │
              │  Category Management      │
              └───────────────────────────┘
```

### Pattern Responsibilities

| Pattern | File | Responsibility |
|---------|------|---------------|
| **Builder** | `patterns/builder_business.py` | Step-by-step business construction with validation |
| **Factory (Business)** | `patterns/factory_business.py` | Create category-specific business types |
| **Factory (Service)** | `patterns/factory_service.py` | Create services with category templates |
| **Factory (Category)** | `patterns/factory_category.py` | Manage categories (static + dynamic) |
| **Controller** | `controllers/business_controller.py` | Orchestrates all patterns |

---

## Builder Pattern - Business Construction

### Purpose
Provides a **fluent interface** for step-by-step business construction with validation at each step.

### Implementation

**File:** `patterns/builder_business.py`

```python
class BusinessBuilder:
    """Builder for constructing Business objects"""
    
    def __init__(self):
        self._name = None
        self._email = None
        self._phone = None
        # ... other fields
    
    def set_name(self, name):
        """Set and validate business name"""
        if not name or len(name.strip()) == 0:
            raise ValueError("Business name cannot be empty")
        self._name = name.strip()
        return self  # ← Fluent interface
    
    def set_email(self, email):
        """Set and validate email"""
        if not email or '@' not in email:
            raise ValueError("Invalid email address")
        self._email = email.strip()
        return self
    
    def build(self):
        """Build and return Business object"""
        is_valid, error = self.validate()
        if not is_valid:
            raise ValueError(f"Cannot build business: {error}")
        
        business = Business(
            name=self._name,
            email=self._email,
            phone=self._phone,
            # ... other fields
        )
        return business
    
    def build_and_save(self):
        """Build and save to database"""
        business = self.build()
        business.save()  # Uses SingletonDB connection
        return business
```

### Usage in Controller

**File:** `controllers/business_controller.py`

```python
def create_business(owner_id=None, data=None, profile_pic=None, gallery_pics=None, services=None):
    # Upload images first
    profile_pic_url = upload_profile_pic(profile_pic)
    gallery_urls = upload_gallery_pics(gallery_pics)
    
    # ===== BUILDER PATTERN =====
    builder = BusinessBuilder()
    
    # Step-by-step construction with validation
    builder.set_name(data['name'])                      # Validates name
    builder.set_email(data['email'])                    # Validates email format
    builder.set_phone(data['phone'])                    # Validates phone
    builder.set_street_house(data['street_house'])      # Required field check
    builder.set_city(data['city'])                      # Required field check
    builder.set_district(data['district'])              # Required field check
    builder.set_category(data['category'])              # Validates category
    
    # Optional fields
    if data.get('description'):
        builder.set_description(data['description'])
    else:
        # Use Factory to get default description
        business_type_class = BusinessFactory._business_types.get(data['category'])
        if business_type_class:
            default_desc = business_type_class(None, {}).get_default_description()
            builder.set_description(default_desc)
    
    # Set uploaded media
    if profile_pic_url:
        builder.set_profile_pic_url(profile_pic_url)
    if gallery_urls:
        builder.set_gallery_urls(gallery_urls)
    
    # Build and save
    business = builder.build_and_save()  # ← Creates and saves business
    
    return business
```

### Builder Pattern Benefits

```python
# ✅ Fluent Interface
business = (BusinessBuilder()
            .set_name("ABC Plumbing")
            .set_email("abc@plumbing.com")
            .set_phone("555-1234")
            .set_category("plumbing")
            .set_city("New York")
            .build_and_save())

# ✅ Validation at Each Step
try:
    builder.set_email("invalid-email")  # Raises ValueError immediately
except ValueError as e:
    print(f"Validation failed: {e}")

# ✅ Immutable Product
business = builder.build()  # Business created
# Cannot modify business through builder anymore

# ✅ Reusable Builder
builder.reset()
business2 = builder.set_name("XYZ Cleaning")...
```

---

## Factory Pattern - Business Types

### Purpose
Creates **category-specific business types** with default services, descriptions, and configurations.

### Implementation

**File:** `patterns/factory_business.py`

```python
# Product Interface
class BusinessType:
    """Base class for all business types"""
    
    business_type = "generic"
    default_services = []
    
    def get_default_description(self):
        return f"Professional {self.business_type} services"
    
    def get_default_services(self):
        return self.default_services


# Concrete Products
class CleaningBusiness(BusinessType):
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


# Factory
class BusinessFactory:
    _business_types = {
        'cleaning': CleaningBusiness,
        'plumbing': PlumbingBusiness,
        'electric': ElectricalBusiness,
        'painting': PaintingBusiness,
        'carpentry': CarpentryBusiness,
        'gardening': GardeningBusiness
    }
    
    @staticmethod
    def get_default_services(category):
        """Get default services for a category"""
        business_class = BusinessFactory._business_types.get(category, BusinessType)
        return business_class.default_services
    
    @staticmethod
    def register_business_type(category, business_class):
        """Register new business type dynamically"""
        if not issubclass(business_class, BusinessType):
            raise ValueError("business_class must inherit from BusinessType")
        BusinessFactory._business_types[category] = business_class
```

### Usage in Controller

```python
def create_business(owner_id, data, ...):
    builder = BusinessBuilder()
    # ... set fields ...
    
    # ===== FACTORY PATTERN: Get default description =====
    if not data.get('description'):
        business_type_class = BusinessFactory._business_types.get(data['category'])
        if business_type_class:
            default_desc = business_type_class(None, {}).get_default_description()
            builder.set_description(default_desc)
    
    business = builder.build_and_save()
    
    # ===== FACTORY PATTERN: Get default services =====
    if not services:
        default_services = BusinessFactory.get_default_services(data['category'])
        for svc in default_services:
            service_obj = Service(
                business_id=business.business_id,
                name=svc['name'],
                price=svc['price'],
                duration_minutes=svc['duration_minutes']
            )
            service_obj.save()
    
    return business
```

### Factory Pattern Benefits

```python
# ✅ Category-Specific Defaults
category = 'plumbing'
default_services = BusinessFactory.get_default_services(category)
# Returns: [Pipe Repair, Leak Fixing, Drain Cleaning, Toilet Repair, Water Heater]

category = 'cleaning'
default_services = BusinessFactory.get_default_services(category)
# Returns: [House Cleaning, Deep Cleaning, Office Cleaning, Window Cleaning]

# ✅ Easy Extension
class HVACBusiness(BusinessType):
    business_type = "hvac"
    default_services = [
        {"name": "AC Repair", "price": 100.0, "duration_minutes": 90},
        {"name": "Heating Repair", "price": 120.0, "duration_minutes": 120}
    ]

BusinessFactory.register_business_type('hvac', HVACBusiness)
# Now available for all businesses!

# ✅ Consistent Defaults
# Every plumbing business gets same default services
# Every cleaning business gets same default services
```

---

## Factory Pattern - Service Creation

### Purpose
Creates **services with category-specific templates**, validation rules, and price ranges.

### Implementation

**File:** `patterns/factory_service.py`

```python
# Template Interface
class ServiceTemplate:
    """Base template for service creation"""
    
    service_type = "generic"
    default_duration = 60
    price_range = (30.0, 500.0)
    
    def validate(self):
        """Validate service data"""
        price = float(self.data['price'])
        if not (self.price_range[0] <= price <= self.price_range[1]):
            raise ValueError(f"Price must be between {self.price_range[0]} and {self.price_range[1]}")
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


# Concrete Templates
class CleaningServiceTemplate(ServiceTemplate):
    service_type = "cleaning"
    default_duration = 120  # 2 hours
    price_range = (30.0, 200.0)
    
    def get_default_description(self):
        return f"{self.data['name']} - Thorough and professional cleaning service"


class PlumbingServiceTemplate(ServiceTemplate):
    service_type = "plumbing"
    default_duration = 90  # 1.5 hours
    price_range = (50.0, 300.0)
    
    def get_default_description(self):
        return f"{self.data['name']} - Licensed plumber with guaranteed work"


# Factory
class ServiceFactory:
    _service_templates = {
        'cleaning': CleaningServiceTemplate,
        'plumbing': PlumbingServiceTemplate,
        'electric': ElectricalServiceTemplate,
        'painting': PaintingServiceTemplate
    }
    
    @staticmethod
    def create_service(business_id, category, data):
        """Create service with category-specific template"""
        template_class = ServiceFactory._service_templates.get(category, ServiceTemplate)
        template = template_class(business_id, data)
        return template.create()
```

### Usage in Controller

**File:** `controllers/business_controller.py`

```python
def create_service(business_id, data):
    """Create service using Factory Pattern"""
    
    # Get business to determine category
    business = get_business(business_id)
    if not business:
        raise ValueError("Business not found")
    
    # ===== FACTORY PATTERN =====
    try:
        # Create service with category-specific template
        service = ServiceFactory.create_service(
            business_id=business_id,
            category=business.category,  # ← Uses business category
            data=data
        )
        service.save()
        return service
    except ValueError as e:
        raise ValueError(f"Service validation failed: {str(e)}")
```

### Service Factory Benefits

```python
# ✅ Category-Specific Validation
# Cleaning service: price must be $30-$200
data = {'name': 'House Cleaning', 'price': 250.0}
service = ServiceFactory.create_service(business_id, 'cleaning', data)
# Raises ValueError: Price must be between 30.0 and 200.0

# Plumbing service: price can be $50-$300 (different range)
data = {'name': 'Pipe Repair', 'price': 250.0}
service = ServiceFactory.create_service(business_id, 'plumbing', data)
# Valid! ✓

# ✅ Smart Duration Defaults
# Cleaning → 120 minutes
# Plumbing → 90 minutes
# Electric → 90 minutes
# Painting → 240 minutes

# ✅ Auto-Generated Descriptions
data = {'name': 'Deep Cleaning', 'price': 100.0}
service = ServiceFactory.create_service(business_id, 'cleaning', data)
# Description: "Deep Cleaning - Thorough and professional cleaning service"

data = {'name': 'Leak Fixing', 'price': 60.0}
service = ServiceFactory.create_service(business_id, 'plumbing', data)
# Description: "Leak Fixing - Licensed plumber with guaranteed work"
```

---

## Factory Pattern - Category Management

### Purpose
Manages all categories (static + dynamic) with search, validation, and metadata.

### Implementation

**File:** `patterns/factory_category.py`

```python
# Product
class Category:
    """Category with metadata"""
    
    def __init__(self, name, display_name, description, icon, tags):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.icon = icon
        self.tags = tags
    
    def to_dict(self):
        return {
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'icon': self.icon,
            'tags': self.tags
        }


# Factory
class CategoryFactory:
    _categories = {
        'cleaning': Category(
            name='cleaning',
            display_name='Cleaning Services',
            description='Professional cleaning for homes, offices, and commercial spaces',
            icon='🧹',
            tags=['house cleaning', 'office cleaning', 'deep cleaning', 'maid service']
        ),
        'plumbing': Category(
            name='plumbing',
            display_name='Plumbing Services',
            description='Licensed plumbers for repairs, installations, and maintenance',
            icon='🔧',
            tags=['pipe repair', 'leak fixing', 'drain cleaning', 'water heater']
        ),
        # ... more categories
    }
    
    @staticmethod
    def get_category(name):
        """Get category by name"""
        return CategoryFactory._categories.get(name)
    
    @staticmethod
    def get_all_categories():
        """Get all categories"""
        return list(CategoryFactory._categories.values())
    
    @staticmethod
    def search_categories(query):
        """Search categories by query"""
        query_lower = query.lower()
        matches = []
        for category in CategoryFactory._categories.values():
            if (query_lower in category.name.lower() or
                query_lower in category.description.lower() or
                any(query_lower in tag.lower() for tag in category.tags)):
                matches.append(category)
        return matches
    
    @staticmethod
    def validate_category(name):
        """Check if category exists"""
        return name in CategoryFactory._categories
    
    @staticmethod
    def register_category(category):
        """Register new category dynamically"""
        CategoryFactory._categories[category.name] = category
```

### Usage in Controller

**File:** `controllers/category_controller.py`

```python
def get_category(name):
    """Get category using Factory"""
    return CategoryFactory.get_category(name)

def get_all_categories():
    """Get all categories using Factory"""
    return CategoryFactory.get_all_categories()

def search_categories(query):
    """Search categories using Factory"""
    return CategoryFactory.search_categories(query)

def validate_category(name):
    """Validate category using Factory"""
    return CategoryFactory.validate_category(name)

def register_category(name, display_name, description, icon, tags):
    """Register new category using Factory"""
    if CategoryFactory.validate_category(name):
        raise ValueError(f"Category '{name}' already exists")
    
    category = Category(
        name=name.lower(),
        display_name=display_name,
        description=description,
        icon=icon,
        tags=tags
    )
    CategoryFactory.register_category(category)
    return category
```

### Category Factory Benefits

```python
# ✅ Centralized Category Management
categories = CategoryFactory.get_all_categories()
# Returns all available categories

# ✅ Search Functionality
results = CategoryFactory.search_categories('clean')
# Returns: [Cleaning Services] (matches name and tags)

results = CategoryFactory.search_categories('water')
# Returns: [Plumbing Services] (matches tags: 'water heater')

# ✅ Easy Validation
if CategoryFactory.validate_category('plumbing'):
    # Category exists
    pass

# ✅ Dynamic Registration
new_category = Category(
    name='hvac',
    display_name='HVAC Services',
    description='Heating and cooling experts',
    icon='❄️',
    tags=['ac repair', 'heating', 'ventilation']
)
CategoryFactory.register_category(new_category)
# Now available everywhere!
```

---

## Complete Business Creation Flow

### End-to-End Example

```python
# ==========================================
# STEP 1: User submits business creation form
# ==========================================
form_data = {
    'name': 'ABC Plumbing Services',
    'email': 'contact@abcplumbing.com',
    'phone': '555-1234',
    'street_house': '123 Main Street',
    'city': 'New York',
    'district': 'Manhattan',
    'category': 'plumbing',
    'description': ''  # Empty - will use Factory default
}

# ==========================================
# STEP 2: Controller receives request
# ==========================================
def create_business(owner_id, data, profile_pic, gallery_pics, services=None):
    
    # Upload images (Cloudinary integration)
    profile_pic_url = upload_to_cloudinary(profile_pic)
    gallery_urls = upload_gallery(gallery_pics)
    
    # ==========================================
    # STEP 3: BUILDER PATTERN - Construct business
    # ==========================================
    builder = BusinessBuilder()
    
    # Validates each field
    builder.set_owner_id(owner_id)
    builder.set_name(data['name'])          # ✓ Not empty
    builder.set_email(data['email'])        # ✓ Has @ symbol
    builder.set_phone(data['phone'])        # ✓ Not empty
    builder.set_street_house(data['street_house'])
    builder.set_city(data['city'])
    builder.set_district(data['district'])
    builder.set_category(data['category']) # ✓ Valid category
    
    # ==========================================
    # STEP 4: FACTORY PATTERN - Get default description
    # ==========================================
    if not data.get('description'):
        # Factory provides category-specific description
        business_type = BusinessFactory._business_types.get('plumbing')
        default_desc = business_type(None, {}).get_default_description()
        # Returns: "Licensed plumbing services. Emergency repairs, installations, and maintenance."
        builder.set_description(default_desc)
    
    # Set media
    builder.set_profile_pic_url(profile_pic_url)
    builder.set_gallery_urls(gallery_urls)
    
    # Build and save
    business = builder.build_and_save()
    # Business created with:
    # - All fields validated ✓
    # - Category-specific description ✓
    # - Saved to MongoDB via SingletonDB ✓
    
    # ==========================================
    # STEP 5: FACTORY PATTERN - Create default services
    # ==========================================
    if not services:
        # Factory provides default services for category
        default_services = BusinessFactory.get_default_services('plumbing')
        # Returns: [
        #   {"name": "Pipe Repair", "price": 75.0, "duration_minutes": 90},
        #   {"name": "Leak Fixing", "price": 60.0, "duration_minutes": 60},
        #   {"name": "Drain Cleaning", "price": 55.0, "duration_minutes": 60},
        #   {"name": "Toilet Repair", "price": 65.0, "duration_minutes": 90},
        #   {"name": "Water Heater Installation", "price": 200.0, "duration_minutes": 180}
        # ]
        
        for svc in default_services:
            # ==========================================
            # STEP 6: FACTORY PATTERN - Create each service
            # ==========================================
            service = ServiceFactory.create_service(
                business_id=business.business_id,
                category='plumbing',
                data=svc
            )
            # Each service:
            # - Validated against plumbing price range ($50-$300) ✓
            # - Default duration: 90 minutes ✓
            # - Category-specific description ✓
            service.save()
    
    return business

# ==========================================
# RESULT: Fully configured plumbing business
# ==========================================
# Business:
#   - Name: ABC Plumbing Services
#   - Email: contact@abcplumbing.com (validated)
#   - Category: plumbing
#   - Description: "Licensed plumbing services..." (Factory default)
#   - Profile picture: Uploaded to Cloudinary
#   - Gallery: 3 images uploaded
#
# Services (automatically created):
#   1. Pipe Repair - $75.00 - 90 minutes
#   2. Leak Fixing - $60.00 - 60 minutes
#   3. Drain Cleaning - $55.00 - 60 minutes
#   4. Toilet Repair - $65.00 - 90 minutes
#   5. Water Heater Installation - $200.00 - 180 minutes
```

---

## Benefits and Best Practices

### 1. **Builder Pattern Benefits**

✅ **Fluent Interface**
```python
business = (BusinessBuilder()
            .set_name("ABC")
            .set_email("abc@example.com")
            .set_category("plumbing")
            .build())
```

✅ **Validation at Each Step**
```python
builder.set_email("invalid")  # Raises ValueError immediately
```

✅ **Immutable Product**
```python
business = builder.build()  # Cannot modify after build
```

✅ **Reusable**
```python
builder.reset()  # Reuse for another business
```

---

### 2. **Factory Pattern Benefits**

✅ **Category-Specific Defaults**
- Each business type has appropriate default services
- Each service type has appropriate price ranges and durations

✅ **Easy Extension**
```python
# Add new business type
class HVACBusiness(BusinessType):
    business_type = "hvac"
    default_services = [...]

BusinessFactory.register_business_type('hvac', HVACBusiness)
```

✅ **Consistent Behavior**
- All plumbing businesses get same defaults
- All cleaning services validated against same rules

✅ **Centralized Logic**
- Change plumbing defaults in one place
- Affects all plumbing businesses

---

### 3. **Combined Pattern Benefits**

✅ **Separation of Concerns**
```
Builder  → Handles construction and validation
Factory  → Provides category-specific logic
```

✅ **SOLID Principles**
- **Single Responsibility**: Each class has one job
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: All business types are interchangeable
- **Interface Segregation**: Clear interfaces for each pattern
- **Dependency Inversion**: Depends on abstractions, not concrete classes

✅ **Testability**
```python
# Test builder independently
def test_builder():
    builder = BusinessBuilder()
    builder.set_name("Test")
    business = builder.build()
    assert business.name == "Test"

# Test factory independently
def test_factory():
    services = BusinessFactory.get_default_services('plumbing')
    assert len(services) == 5
    assert services[0]['name'] == 'Pipe Repair'
```

---

### 4. **Best Practices**

#### When Creating a Business:
1. ✅ Always use `BusinessBuilder` for construction
2. ✅ Use `BusinessFactory` for category defaults
3. ✅ Never directly instantiate `Business` model
4. ✅ Validate all inputs through builder

#### When Creating a Service:
1. ✅ Always use `ServiceFactory.create_service()`
2. ✅ Pass business category for appropriate template
3. ✅ Let factory handle validation and defaults
4. ✅ Never directly instantiate `Service` model

#### When Managing Categories:
1. ✅ Use `CategoryFactory` for all category operations
2. ✅ Use `category_controller` functions, not direct factory access
3. ✅ Register new categories through `register_category()`
4. ✅ Validate categories before using them

---

## Pattern Interaction Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                     USER REQUEST                               │
│          "Create plumbing business with services"              │
└────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                  CONTROLLER LAYER                              │
│            business_controller.create_business()               │
└────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
    ┌───────────────────────┐   ┌──────────────────────┐
    │   BUILDER PATTERN     │   │  FACTORY PATTERN     │
    │                       │   │                      │
    │  BusinessBuilder()    │   │ BusinessFactory      │
    │  .set_name()          │   │ .get_default_desc()  │
    │  .set_email()         │   │ .get_default_svc()   │
    │  .set_category()      │   │                      │
    │  .build_and_save()    │   │                      │
    └───────────────────────┘   └──────────────────────┘
                    │                   │
                    └─────────┬─────────┘
                              ↓
            ┌─────────────────────────────┐
            │     SINGLETON PATTERN       │
            │    SingletonDB.save()       │
            │  (One MongoDB connection)   │
            └─────────────────────────────┘
                              ↓
            ┌─────────────────────────────┐
            │  FACTORY PATTERN (Services) │
            │  ServiceFactory              │
            │  .create_service()           │
            │  (Creates 5 default services)│
            └─────────────────────────────┘
                              ↓
            ┌─────────────────────────────┐
            │     SINGLETON PATTERN       │
            │    SingletonDB.save()       │
            │  (Same MongoDB connection)  │
            └─────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────┐
│                     RESULT                                     │
│  Business created with:                                        │
│  - Validated fields (Builder)                                  │
│  - Category-specific description (Factory)                     │
│  - 5 default plumbing services (Factory)                       │
│  - All saved via single DB connection (Singleton)              │
└────────────────────────────────────────────────────────────────┘
```

---

## Summary

### Design Patterns Used

| Pattern | Purpose | File |
|---------|---------|------|
| **Builder** | Step-by-step business construction with validation | `patterns/builder_business.py` |
| **Factory (Business)** | Category-specific business types and defaults | `patterns/factory_business.py` |
| **Factory (Service)** | Service templates with category validation | `patterns/factory_service.py` |
| **Factory (Category)** | Category management and metadata | `patterns/factory_category.py` |
| **Singleton** | Single database connection | `database/singleton_db.py` |

### Key Takeaways

1. **Builder Pattern** = Construction + Validation
2. **Factory Pattern** = Category-Specific Defaults
3. **Combined** = Powerful, Flexible, Maintainable
4. **All patterns** work together seamlessly
5. **SOLID principles** followed throughout
6. **Easy to extend** with new categories and types
7. **Testable** - Each pattern can be tested independently

**Every business creation uses ALL these patterns working together!** 🎯
