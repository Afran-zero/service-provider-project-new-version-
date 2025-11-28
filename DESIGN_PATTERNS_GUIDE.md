# Design Patterns Implementation Guide

## Overview
This document details all design patterns implemented in the backend: Factory, Command, Observer, Adapter, Decorator, Proxy, and Repository.

## Quick Reference

| Pattern | Purpose | Location | Use Case |
|---------|---------|----------|----------|
| **Factory** | Create objects with category-specific defaults | `factory_business.py`, `factory_category.py`, `factory_service.py` | Business/category/service creation |
| **Repository** | Persist and retrieve domain objects | `models/category.py` (CategoryModel) + Factory | DB-backed category storage |
| **Proxy** | Control access to objects/routes | `proxy_access.py` | Gate business owners from public home |
| **Command** | Encapsulate requests as objects | `command_booking.py` | Booking actions (create, accept, reject, etc.) |
| **Observer** | Notify multiple objects of state changes | `observer_booking.py` | Booking notifications (email/SMS) |
| **Adapter** | Adapt incompatible interfaces | `cloudinary_adapter.py` | Image storage abstraction |
| **Decorator** | Add behavior to routes | `decorator_auth.py` | Role-based route protection |

## 1. Factory Pattern

### Factory: Business Types (`backend/patterns/factory_business.py`)

**Purpose:** Create business instances with category-specific defaults

**Classes:**
- `BusinessType` (Abstract base class)
- `CleaningBusiness`
- `PlumbingBusiness`
- `ElectricalBusiness`
- `PaintingBusiness`
- `CarpentryBusiness`
- `GardeningBusiness`

**Usage:**
```python
from patterns.factory_business import BusinessFactory

# Create a cleaning business with defaults
business = BusinessFactory.create_business(
    owner_id=user_id,
    category='cleaning',
    data={
        'name': 'Sparkle Clean',
        'email': 'info@sparkle.com',
        'phone': '1234567890',
        'street_house': '123 Main St',
        'city': 'New York',
        'district': 'Manhattan'
    }
)
# Automatically includes default services like "Standard Cleaning", "Deep Cleaning", "Move-out Cleaning"
```

### Factory: Categories (`backend/patterns/factory_category.py`)

**Purpose:** Manage service categories with DB-aware merging, supporting both built-in and dynamically created categories (Repository + Factory combined)

**Features:**
- 8 built-in categories: cleaning, plumbing, electrical, painting, carpentry, landscaping, hvac, other
- Dynamic DB-backed categories via CategoryModel
- Merges built-in + DB categories at read time (single source of truth)
- Icon support: emoji (e.g., 🧹) or Bootstrap suffix (e.g., bi-brush-fill or brush-fill)
- Search and autocomplete

**Key Methods:**
- `get_all_categories()` → List[Category] (merged built-in + DB)
- `get_category(name)` → Category (searches DB first, then built-in)
- `validate_category(name)` → bool (checks if category exists)
- `search_categories(query)` → List[Category] (fuzzy search)
- `get_category_suggestions(partial_query)` → List[dict] (autocomplete)

**Usage:**
```python
from patterns.factory_category import CategoryFactory

# Get all categories (built-in + DB-backed)
all_cats = CategoryFactory.get_all_categories()

# Get specific category
cat = CategoryFactory.get_category('cleaning')
print(cat.display_name, cat.icon)  # "Cleaning Services", "🧹"

# Search
results = CategoryFactory.search_categories('electric')

# Validate
is_valid = CategoryFactory.validate_category('plumbing')  # True
```

**Database Model** (`backend/models/category.py`):
```python
class CategoryModel(Document):
    name = StringField(required=True, unique=True)           # Slug: cleaning, plumbing, etc.
    display_name = StringField(required=True)                # "Cleaning Services"
    description = StringField(default='')                   # Optional description
    icon = StringField(default='')                          # 🧹 or bi-brush-fill or brush-fill
    tags = ListField(StringField(), default=list)           # ['house', 'office', 'deep clean']
```

**Admin Operations** (via `/admin/categories`):
- Create new category: POST `/admin/categories/create` with display_name, icon, tags
- Edit category: POST `/admin/categories/<name>/edit` (update metadata)
- Delete category: POST `/admin/categories/<name>/delete` (blocked if in use)
- Note: Built-in categories are read-only

### Factory: Services (`backend/patterns/factory_service.py`)

**Purpose:** Create services from templates with preset configurations

**Service Templates:**
- `CleaningServiceTemplate` - Standard, Deep, Move-out cleaning
- `PlumbingServiceTemplate` - Drain cleaning, pipe repair, toilet repair
- `ElectricalServiceTemplate` - Wiring inspection, outlet repair, light installation
- `PaintingServiceTemplate` - Interior, Exterior, Touch-up painting

**Service Packages:**
```python
from patterns.factory_service import ServiceFactory

# Get a predefined package
basic_cleaning = ServiceFactory.get_package('basic_cleaning')
# Returns: [
#   {'name': 'Standard Cleaning', 'description': '...', 'price': 80, 'duration': 120},
#   {'name': 'Kitchen Cleaning', 'description': '...', 'price': 50, 'duration': 90}
# ]

# Create services from template
services = ServiceFactory.create_from_template(
    business_id='123',
    category='cleaning',
    template_type='basic'
)

# Bulk create services
ServiceFactory.bulk_create_services(business_id='123', services_data=[...])
```

## 2. Repository Pattern

### Category Repository (`backend/models/category.py` + Factory merge)

**Purpose:** Persist and retrieve domain objects (categories) while keeping Factory agnostic to storage

**Pattern Structure:**
- **Domain Object:** `Category` (in-memory representation)
- **Repository:** `CategoryModel` (MongoDB document)
- **Factory:** `CategoryFactory` consumes repository via `_db_categories_map()`

**How It Works:**
1. Admin creates a category via `/admin/categories/create` → saved to MongoDB
2. CategoryFactory reads DB via `_db_categories_map()` at each call
3. Factory merges DB categories with built-ins
4. Views query Factory (not DB directly), ensuring single source of truth

**Benefits:**
- Decouples storage (MongoDB) from business logic (Factory)
- Built-in categories remain in code; custom categories in DB
- Easy to swap storage backend (PostgreSQL, Redis, etc.) without changing views
- Lazy loading: Factory only queries DB when `get_all_categories()` is called

**Usage:**
```python
from models.category import CategoryModel
from patterns.factory_category import CategoryFactory

# Direct DB access (repository)
cat = CategoryModel.objects(name='custom_plumbing').first()
cat.display_name = 'Advanced Plumbing'
cat.save()

# Via Factory (preferred in views)
all_cats = CategoryFactory.get_all_categories()  # Includes DB-backed
custom = CategoryFactory.get_category('custom_plumbing')
```

## 3. Proxy Pattern

### Access Proxy (`backend/patterns/proxy_access.py`)

**Purpose:** Control access to resources (e.g., public home page) based on user role and context

**Pattern Structure:**
- **Subject (Real):** Original route handler (e.g., `home.index()`)
- **Proxy:** `AccessProxy` intercepts, checks rules, delegates or redirects
- **Client:** Route handler or `app.before_request`

**Rules Implemented:**
- Business owners cannot access public home (`/`, `/home`) → redirected to dashboard or create business flow
- Customers and anonymous users can access home
- Early interception in `app.before_request` for double-slash attacks and owner re-routing

**Implementation:**
```python
# In app.py (before_request)
if current_user.is_authenticated and getattr(current_user, 'role', None) == 'business_owner':
    if request.path in ['/', '/home']:
        from patterns.proxy_access import AccessProxy
        proxy = AccessProxy(current_user)
        return redirect(proxy.destination_for_owner())

# In views/home.py (home.index)
@home_bp.route('/', methods=['GET'])
def index():
    proxy = AccessProxy(current_user)
    return proxy.render_or_redirect_home(lambda: render_template(...))
```

**AccessProxy Methods:**
- `can_access_public_home()` → bool (role != business_owner)
- `destination_for_owner()` → str (URL to dashboard or create business)
- `render_or_redirect_home(handler)` → response (call handler or redirect)

**Usage Example:**
```python
from patterns.proxy_access import AccessProxy

proxy = AccessProxy(current_user)

if not proxy.can_access_public_home():
    redirect_url = proxy.destination_for_owner()
    return redirect(redirect_url)

# Otherwise, render original page
return proxy.render_or_redirect_home(original_handler)
```

**Security Benefits:**
✅ Single point for access decisions (maintainability)
✅ Early interception prevents business owner from seeing marketing pages
✅ Rules centralized (easy to add subscription tiers, feature flags, etc.)
✅ Separation of concerns (routing vs. access control)

## 4. Command Pattern

### Location: `backend/patterns/command_booking.py`

**Purpose:** Encapsulate booking actions as commands that can be queued, retried, and undone

**Commands:**
1. `CreateBookingCommand` - Create a new booking
2. `CancelBookingCommand` - Cancel a booking
3. `AcceptBookingCommand` - Accept a booking (business owner)
4. `RejectBookingCommand` - Reject a booking
5. `CompleteBookingCommand` - Mark booking as completed

**Components:**
- `BookingCommand` (Abstract base class)
- `BookingCommandQueue` - Queue with retry logic (max 3 retries)
- `BookingCommandInvoker` - Execute commands immediately or queued

**Usage:**
```python
from patterns.command_booking import (
    CreateBookingCommand,
    CancelBookingCommand,
    BookingCommandInvoker
)
import datetime

# Create a booking immediately
command = CreateBookingCommand(
    customer_id=user_id,
    service_id=service_id,
    booking_time=datetime.datetime(2024, 12, 25, 14, 0),
    notes='Please arrive on time'
)

invoker = BookingCommandInvoker()
booking = invoker.execute_immediately(command)

# Queue a command for later execution
invoker.queue_command(command)
# Process queue
invoker.process_queue()

# Undo last command
invoker.undo_last_command()

# Cancel a booking
cancel_command = CancelBookingCommand(booking_id, user_id)
cancelled_booking = invoker.execute_immediately(cancel_command)
```

**Queue Features:**
- Automatic retry on failure (max 3 attempts)
- Command history tracking
- Failed command tracking
- Bulk processing

## 3. Adapter Pattern

### Cloudinary Adapter (`backend/patterns/cloudinary_adapter.py`)

**Purpose:** Abstract image storage behind a common interface

**Interface:** `ImageStorageAdapter`
- `upload(file, folder=None, public_id=None)` → returns URL
- `delete(public_id)` → returns bool
- `get_url(public_id, transformations=None)` → returns URL
- `get_thumbnail_url(public_id, width=150, height=150)` → returns URL

**Implementation:** `CloudinaryAdapter`
- Lazy loading (only initializes when first used)
- Supports image transformations
- Handles multiple uploads
- URL extraction from Cloudinary responses

**Usage:**
```python
from patterns.cloudinary_adapter import get_cloudinary_adapter

adapter = get_cloudinary_adapter()

# Upload image
url = adapter.upload(file_object, folder='businesses')

# Get thumbnail
thumb_url = adapter.get_thumbnail_url('business/profile123', width=200, height=200)

# Delete image
success = adapter.delete('business/profile123')
```

### Email Adapter (`backend/patterns/email_adapter.py`)

**Purpose:** Abstract email services behind a common interface

**Interface:** `EmailServiceAdapter`
- `send_email(to, subject, body, html=None)` → returns bool
- `send_verification_code(to, code)` → returns bool
- `send_password_reset(to, reset_link)` → returns bool

**Implementations:**
1. `FlaskMailAdapter` - Production email via Flask-Mail
2. `MockEmailAdapter` - Development/testing (prints to console)
3. `HardcodedVerificationAdapter` - Always uses PIN "123456"

**Usage:**
```python
from patterns.email_adapter import (
    get_email_adapter,
    send_booking_notification
)

# Send verification code
adapter = get_email_adapter()
adapter.send_verification_code('user@example.com', '123456')

# Send booking notification (helper function)
send_booking_notification(
    to_email='customer@example.com',
    customer_name='John Doe',
    business_name='Sparkle Clean',
    service_name='Deep Cleaning',
    booking_date='2024-12-25',
    booking_time='14:00'
)
```

### SMS Adapter (`backend/patterns/sms_adapter.py`)

**Purpose:** Abstract SMS services behind a common interface

**Interface:** `SMSServiceAdapter`
- `send_sms(to, message)` → returns bool
- `send_verification_code(to, code)` → returns bool
- `send_booking_notification(to, booking_details)` → returns bool

**Implementations:**
1. `TwilioAdapter` - Production SMS via Twilio API
2. `MockSMSAdapter` - Development/testing (prints to console)
3. `HardcodedVerificationAdapter` - Always uses PIN "123456"

**Hardcoded PIN:**
```python
# In backend/patterns/sms_adapter.py
class HardcodedVerificationAdapter(SMSServiceAdapter):
    HARDCODED_PIN = "123456"  # ← Always returns this PIN
    
    def send_verification_code(self, to: str, code: str) -> bool:
        print(f"[HARDCODED SMS] Verification code for {to}: {self.HARDCODED_PIN}")
        return True
```

**Usage:**
```python
from patterns.sms_adapter import get_sms_adapter

adapter = get_sms_adapter()

# Send verification code (always returns "123456")
adapter.send_verification_code('+1234567890', '123456')

# Send booking notification
adapter.send_booking_notification(
    to='+1234567890',
    booking_details={
        'business_name': 'Sparkle Clean',
        'service_name': 'Deep Cleaning',
        'booking_date': '2024-12-25',
        'booking_time': '14:00'
    }
)
```

## Integration with Existing Code

### Utils.py Integration
The `backend/utils.py` file has been refactored to use adapters:

```python
from patterns.cloudinary_adapter import get_cloudinary_adapter
from patterns.email_adapter import get_email_adapter
from patterns.sms_adapter import get_sms_adapter

def upload_image_to_cloudinary(file, folder=None):
    """Upload image using adapter"""
    adapter = get_cloudinary_adapter()
    return adapter.upload(file, folder=folder)

def send_verification_email(to, code):
    """Send verification email using adapter"""
    adapter = get_email_adapter()
    return adapter.send_verification_code(to, code)

def send_verification_sms(to, code):
    """Send verification SMS using adapter (hardcoded PIN)"""
    adapter = get_sms_adapter()
    return adapter.send_verification_code(to, code)
```

## Configuration

### Environment Variables
```bash
# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Email (Flask-Mail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_password

# SMS (Twilio)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

### Mock Mode (Development)
Set `FLASK_ENV=development` to automatically use mock adapters:
- MockEmailAdapter - prints emails to console
- MockSMSAdapter - prints SMS to console
- Cloudinary still works normally

## Benefits Summary

### Factory Pattern
✅ Centralized business/category/service creation logic
✅ Category-specific defaults (built-in or custom)
✅ Consistent structure across objects
✅ Easy to add new types without modifying existing code
✅ DB-aware: merges built-in and dynamic categories

### Repository Pattern
✅ Decouples storage from business logic
✅ Single source of truth for DB categories
✅ Easy to swap storage backend (MongoDB → PostgreSQL, Redis, etc.)
✅ Domain models (Category) stay pure; Repository (CategoryModel) handles persistence

### Proxy Pattern
✅ Centralized access control logic (single point of change)
✅ Early interception prevents unauthorized access
✅ Easy to extend with new rules (subscriptions, feature flags, etc.)
✅ Separation of concerns: routing vs. access policy

### Command Pattern
✅ Booking actions can be queued and retried
✅ Automatic retry on failure (max 3 attempts)
✅ Undo capability via command history
✅ Separates request from execution (flexibility)
✅ Command history tracking for auditing

### Observer Pattern
✅ Decouples booking actions from notifications
✅ Multiple observers can listen to same event
✅ Easy to add new notification types (SMS, email, push, etc.)
✅ Notification logic doesn't clutter command handlers

### Adapter Pattern
✅ Swap implementations without changing client code (Cloudinary → AWS S3)
✅ Easy testing with mock adapters
✅ Consistent interface across services (email, SMS, storage)
✅ External dependency isolation
✅ Configuration-based switching

## Testing Examples

### Test Factory Pattern
```python
def test_business_factory():
    business = BusinessFactory.create_business(
        owner_id='test_user',
        category='cleaning',
        data={...}
    )
    assert business.category == 'cleaning'
    assert len(business.default_services) > 0

def test_category_search():
    results = CategoryFactory.search_categories('clean')
    assert len(results) > 0
    assert any('clean' in cat['name'].lower() for cat in results)
```

### Test Command Pattern
```python
def test_create_booking_command():
    command = CreateBookingCommand(
        customer_id='test_user',
        service_id='test_service',
        booking_time=datetime.datetime.now() + datetime.timedelta(days=1)
    )
    invoker = BookingCommandInvoker()
    booking = invoker.execute_immediately(command)
    assert booking is not None
    
def test_command_queue():
    queue = BookingCommandQueue()
    command = CreateBookingCommand(...)
    queue.add_command(command)
    queue.process_all()
    assert len(queue.failed_commands) == 0
```

### Test Adapter Pattern
```python
def test_cloudinary_adapter():
    adapter = get_cloudinary_adapter()
    url = adapter.upload(test_image, folder='test')
    assert url is not None
    assert 'cloudinary' in url
    
def test_mock_email_adapter():
    adapter = MockEmailAdapter()
    result = adapter.send_verification_code('test@example.com', '123456')
    assert result is True
    
def test_hardcoded_sms():
    adapter = HardcodedVerificationAdapter()
    result = adapter.send_verification_code('+1234567890', 'ignored')
    assert result is True
    # Adapter always uses "123456" internally
```

## Troubleshooting

### Cloudinary Issues
- Check environment variables are set
- Verify cloud name, API key, and secret
- Ensure cloudinary package is installed: `pip install cloudinary`

### Email Issues
- Check SMTP settings
- For Gmail: enable "Less secure apps" or use app password
- Use MockEmailAdapter for development

### SMS Issues
- Verify Twilio credentials
- Check phone number format (+1234567890)
- Use MockSMSAdapter or HardcodedVerificationAdapter for development

### Command Pattern Issues
- Check command queue size: `queue.get_queue_size()`
- View failed commands: `queue.failed_commands`
- Check max retries setting

## File Locations

```
backend/
├── patterns/
│   ├── factory_business.py      # Business type factory
│   ├── factory_category.py      # Category management (Factory + Repository merge)
│   ├── factory_service.py       # Service templates
│   ├── command_booking.py       # Booking commands
│   ├── proxy_access.py          # Access control proxy (NEW)
│   ├── cloudinary_adapter.py    # Image storage adapter
│   ├── decorator_auth.py        # Role-based route decorators
│   ├── observer_booking.py      # Booking notifications
│   └── captcha_factory.py       # Captcha generation
├── models/
│   ├── user.py
│   ├── business.py
│   ├── booking.py
│   ├── category.py              # CategoryModel (Repository) (NEW)
│   └── service.py
├── views/
│   ├── home.py                  # Home/landing with Proxy gating
│   ├── admin.py                 # Admin routes (categories, users, businesses, bookings)
│   ├── auth.py
│   ├── booking.py
│   ├── business.py
│   └── owner_business.py
└── app.py                       # Main app with session/path security
```

## Pattern Combinations

### Factory + Repository (Category Management)
- Built-in categories come from `CategoryFactory._categories` (code)
- Custom categories come from `CategoryModel` (database)
- `CategoryFactory._db_categories_map()` merges both at read time
- Admin CRUD affects only DB-backed categories; built-ins remain immutable

### Proxy + Decorator (Access Control)
- `@admin_required` decorator blocks non-admins
- `AccessProxy` gates business owners from public home
- `app.before_request` provides early interception for path attacks
- Separation: decorators for route entry; proxy for business logic

### Command + Observer (Booking Workflow)
- Command wraps booking actions (create, accept, cancel, etc.)
- Observer is triggered on command execution to send notifications
- Observer decouples notification logic from command execution

### Adapter (External Services)
- Cloudinary for image storage
- Email for verification and notifications
- SMS for verification and notifications
- All implement common interfaces for easy testing/mocking
