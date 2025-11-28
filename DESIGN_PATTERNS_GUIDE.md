# Design Patterns Implementation Guide

## Overview
This document details the Factory, Command, and Adapter design patterns implemented in the backend.

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

**Purpose:** Manage service categories with icons, tags, and search

**Categories (12 total):**
- cleaning, plumbing, electric, painting, carpentry, gardening
- hvac, roofing, pest_control, appliance_repair, locksmith, moving

**Usage:**
```python
from patterns.factory_category import CategoryFactory

# Get all categories
categories = CategoryFactory.get_all_categories()

# Get specific category
category = CategoryFactory.get_category('cleaning')
# Returns: {'id': 'cleaning', 'name': 'Cleaning', 'icon': 'brush', 'tags': [...]}

# Search categories
results = CategoryFactory.search_categories('electric')

# Get suggestions
suggestions = CategoryFactory.get_category_suggestions('clean', limit=3)
```

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

## 2. Command Pattern

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

## Benefits

### Factory Pattern
✅ Centralized business creation logic
✅ Category-specific defaults
✅ Consistent service structure
✅ Easy to add new business types

### Command Pattern
✅ Booking actions can be queued
✅ Automatic retry on failure
✅ Undo capability
✅ Command history tracking
✅ Separates request from execution

### Adapter Pattern
✅ Swap implementations without changing code
✅ Easy testing with mock adapters
✅ Consistent interface across services
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
backend/patterns/
├── factory_business.py      # Business type factory
├── factory_category.py      # Category management
├── factory_service.py       # Service templates
├── command_booking.py       # Booking commands
├── cloudinary_adapter.py    # Image storage adapter
├── email_adapter.py         # Email service adapter
└── sms_adapter.py          # SMS service adapter (PIN: 123456)
```
