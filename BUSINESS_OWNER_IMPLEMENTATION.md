# Business Owner Implementation Guide

## Overview

This document details the implementation of a dedicated **Business Owner** actor in the Service Provider application. Business Owners are users who manage service businesses, create service listings, and handle booking requests from customers.

**Status:** ✅ Fully Implemented  
**Version:** 1.0.0  
**Last Updated:** November 28, 2025

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Design Patterns Used](#design-patterns-used)
3. [Database Schema Changes](#database-schema-changes)
4. [User Model Updates](#user-model-updates)
5. [Decorator Pattern Implementation](#decorator-pattern-implementation)
6. [Command Pattern Integration](#command-pattern-integration)
7. [Route Structure](#route-structure)
8. [Authentication & Authorization Flow](#authentication--authorization-flow)
9. [Testing Guide](#testing-guide)
10. [API Reference](#api-reference)

---

## Architecture Overview

### Actor Model

The system now supports three distinct user roles:

```
┌─────────────────────────────────────────────────────────────┐
│                      User (Base Class)                      │
│  - role: 'customer' | 'business_owner' | 'admin'            │
│  - Authentication via email/phone + password                │
└─────────────────────────────────────────────────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│    Customer      │  │ Business Owner   │  │      Admin       │
│                  │  │                  │  │                  │
│ - Browse/Search  │  │ - Create Business│  │ - Manage All     │
│ - Book Services  │  │ - List Services  │  │ - View Reports   │
│ - View Profile   │  │ - Accept/Reject  │  │ - User Management│
│                  │  │ - View Bookings  │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

### Data Flow

```
┌─────────────────────────────────────────────────────────┐
│ User Registration / Login                               │
│ - Email / Phone + Password                              │
│ - Select Role: Customer or Business Owner               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │   @business_owner_required │  (Decorator Pattern)
        │   Verifies Role = 'bo'     │
        └────────────────────────────┘
                     │
        ┌────────────┴────────────────────────┐
        ▼                                      ▼
   Business Owner          Regular User/Customer
   Dashboard Routes        Standard Routes
   └─ /owner/dashboard     └─ /
   └─ /owner/business/*    └─ /business/list
   └─ /owner/bookings/*    └─ /booking/create
```

---

## Design Patterns Used

### 1. **Decorator Pattern** (Role-Based Access Control)

**Location:** `backend/patterns/decorator_auth.py`

#### New Decorators Added:

```python
@business_owner_required
def protected_route():
    """Only accessible by business owners"""
    pass

@admin_required
def admin_route():
    """Only accessible by admins"""
    pass

@customer_required
def customer_route():
    """Only accessible by customers"""
    pass
```

#### Implementation Details:

```python
def business_owner_required(f):
    """
    Decorator to restrict access to Business Owners only.

    Flow:
    1. Check if user is authenticated
    2. Verify user.role == 'business_owner'
    3. Redirect to login/home if not authorized

    Why Decorator Pattern?
    - Separates authorization logic from route handlers
    - Reusable across multiple routes
    - Centralized policy management
    - Non-invasive (doesn't modify original functions)
    """
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in first.", "warning")
            return redirect(url_for('auth.login'))

        if not hasattr(current_user, 'role') or current_user.role != 'business_owner':
            flash("Access denied. Only business owners can access this page.", "danger")
            return redirect(url_for('home.index'))

        return f(*args, **kwargs)
    return decorated_view
```

**Usage Example:**

```python
@owner_business_bp.route('/dashboard')
@business_owner_required  # Decorator applied here
def dashboard():
    # Only business owners reach this code
    pass
```

**Benefits:**

- ✅ Clean separation of concerns
- ✅ Reusable authorization logic
- ✅ Easy to add/modify permissions
- ✅ No code duplication across routes

---

### 2. **Command Pattern** (Booking Operations)

**Location:** `backend/patterns/command_booking.py`

#### Enhanced Commands:

##### AcceptBookingCommand

```python
class AcceptBookingCommand(BookingCommand):
    """
    Command to accept a booking with ownership verification.

    Implementation:
    1. Fetch booking by ID
    2. Verify business ownership (owner_id matches current_user)
    3. Validate booking status is 'requested'
    4. Update status to 'accepted'
    5. Trigger observer notifications

    Ownership Check (Security Layer):
    - Prevents unauthorized users from accepting bookings
    - Double-checks even if decorator is bypassed
    """

    def execute(self):
        """Accept the booking"""
        # Get booking and business
        self.booking = Booking.objects.get(booking_id=self.booking_id)
        business = Business.objects.get(business_id=self.booking.business_id)

        # OWNERSHIP VERIFICATION
        if business.owner_id != self.business_owner_id:
            raise ValueError(
                f"Unauthorized: User {self.business_owner_id} is not the owner"
            )

        # Validate state
        if self.booking.status != 'requested':
            raise ValueError(f"Cannot accept: current status is {self.booking.status}")

        # Update status with timestamp
        self.booking.update_status('accepted')

        # Notify all observers (email, SMS, business)
        notify_booking_status_change(self.booking, 'accepted')

        return self.booking
```

##### RejectBookingCommand

```python
class RejectBookingCommand(BookingCommand):
    """
    Command to reject a booking with optional reason and ownership verification.

    Similar to AcceptBookingCommand but:
    - Accepts optional rejection reason
    - Sets status to 'rejected' (terminal state)
    """

    def execute(self):
        """Reject the booking"""
        # Same ownership verification as AcceptBookingCommand
        self.booking = Booking.objects.get(booking_id=self.booking_id)
        business = Business.objects.get(business_id=self.booking.business_id)

        if business.owner_id != self.business_owner_id:
            raise ValueError(f"Unauthorized: Not business owner")

        if self.booking.status != 'requested':
            raise ValueError(f"Cannot reject: current status is {self.booking.status}")

        # Update status and notify
        self.booking.update_status('rejected')
        notify_booking_status_change(self.booking, 'rejected')

        return self.booking
```

**Design Pattern Principles:**

- ✅ **Encapsulation:** Booking logic isolated in command objects
- ✅ **Undo/Redo:** Commands can be undone (partially implemented)
- ✅ **Queuing:** Commands can be queued for batch processing
- ✅ **Logging:** Commands are logged with execution details
- ✅ **Observer Integration:** Commands trigger notifications

### 3. **Strategy Pattern** (Profile Image Resolution + Lazy Loading)

**Location:** `backend/controllers/business_controller.py#get_business_details`

**Details:**

- Source selection: prefer `Business.profile_pic_url`; fallback to owner `User.profile_pic_url` if missing.
- Transformation: produce `profile_pic_lazy` (small, blurred) and `profile_pic_full` (optimized) URLs for progressive loading.
- Frontend usage: `frontend/owner/view_business.html` starts with lazy src and swaps to full via IntersectionObserver.

**Benefit:**

- Keeps image display reliable even when business image is absent.
- Improves perceived performance with progressive loading.

---

## Database Schema Changes

### User Model Update

**File:** `backend/models/user.py`

```python
class User(me.Document, UserMixin):
    ROLES = ('customer', 'business_owner', 'admin')

    # Existing fields...
    user_id = me.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    name = me.StringField(required=True)
    email = me.EmailField(unique=True, required=True)
    phone = me.StringField(required=False)
    password_hash = me.StringField(required=True)
    street_house = me.StringField(required=True)
    city = me.StringField(required=True)
    district = me.StringField(required=True)
    profile_pic_url = me.StringField(default=None)

    # NEW FIELD: Role-based access control
    role = me.StringField(
        default='customer',
        choices=ROLES,
        required=True
    )

    is_verified = me.BooleanField(default=False)
    created_at = me.DateTimeField(default=datetime.datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.datetime.utcnow)
```

**Migration for Existing Users:**

If you have existing users without the `role` field, they will default to `'customer'`. To update existing records:

```javascript
// MongoDB console
db.users.updateMany(
  { role: { $exists: false } },
  { $set: { role: "customer" } }
);
```

### Business Model (No Changes Required)

The existing `Business` model already supports owner linking:

```python
class Business(me.Document):
    business_id = me.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = me.StringField(required=False, default=None)  # Links to User.user_id
    name = me.StringField(required=True)
    # ... other fields ...
    is_active = me.BooleanField(default=True)
```

---

## User Model Updates

### Role Field Details

| Role               | Access                                          | Responsibilities                  |
| ------------------ | ----------------------------------------------- | --------------------------------- |
| `'customer'`       | Browse, search, book services                   | Use platform as service consumer  |
| `'business_owner'` | Create business, list services, manage bookings | Provide services, handle requests |
| `'admin'`          | Full system access                              | System administration             |

### Default Values

- **New registrations:** Default to `'customer'`
- **Existing users (pre-migration):** Will get `'customer'` role
- **Explicit selection:** Provided during registration form

### Registration Flow with Role

```python
# User selects role during registration
user, error = register_user(data, role='business_owner')

# In controller:
def register_user(data, role='customer'):
    """Register with explicit role"""
    valid_roles = ('customer', 'business_owner')
    if role not in valid_roles:
        return None, f"Invalid role: {role}"

    user = User(
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        # ... other fields ...
        role=role  # Set role here
    )
    user.set_password(data['password'])
    user.save()
    return user, None
```

---

## Decorator Pattern Implementation

### Core Decorator Architecture

**File:** `backend/patterns/decorator_auth.py`

```python
def business_owner_required(f):
    """
    Decorator implementing role-based access control.

    Pattern Benefits:
    1. Cross-cutting concern: Authorization is separate from business logic
    2. Reusable: Applied to any route that needs protection
    3. Maintainable: Change in one place affects all decorated routes
    4. Testable: Can test authorization independently
    """
    @wraps(f)
    def decorated_view(*args, **kwargs):
        # Step 1: Check authentication
        if not current_user.is_authenticated:
            flash("Please log in first.", "warning")
            return redirect(url_for('auth.login'))

        # Step 2: Check role
        if not hasattr(current_user, 'role') or current_user.role != 'business_owner':
            flash("Access denied. Only business owners can access this page.", "danger")
            return redirect(url_for('home.index'))

        # Step 3: Proceed to protected route
        return f(*args, **kwargs)

    return decorated_view
```

### Applied to Routes

```python
# File: backend/views/owner_business.py

from patterns.decorator_auth import business_owner_required

@owner_business_bp.route('/dashboard')
@business_owner_required  # Protection applied here
def dashboard():
    """Business owner can only access their own dashboard"""
    owner_businesses = Business.objects(owner_id=current_user.user_id)
    return render_template('owner/dashboard.html', businesses=owner_businesses)

@owner_business_bp.route('/business/create', methods=['GET', 'POST'])
@business_owner_required
def create_business():
    """Only business owners can create businesses"""
    if request.method == 'POST':
        # Create business logic
        pass

@owner_business_bp.route('/booking/<booking_id>/accept', methods=['POST'])
@business_owner_required
def accept_booking(booking_id):
    """Only business owners can accept bookings"""
    # Accept booking logic
    pass
```

### Decorator Execution Flow

```
Request → @business_owner_required Decorator
         ↓
    ┌─────────────────┐
    │ Is Authenticated?│
    └────────┬────────┘
             │ No
             ├─→ Flash warning
             └─→ Redirect to login

             │ Yes
             ├─→ Check role == 'business_owner'?
                    │ No
                    ├─→ Flash danger
                    └─→ Redirect to home

                    │ Yes
                    ├─→ Execute route handler
                    └─→ Return response
```

---

## Command Pattern Integration

### Booking Command Flow

#### 1. Accept Booking Flow

```
Business Owner Action:
  ├─ Clicks "Accept Booking" button
  ├─ HTTP POST to /owner/booking/<booking_id>/accept
  ├─ Route handler executes:
  │  └─ command = AcceptBookingCommand(booking_id, owner_id)
  │  └─ command.execute()  // Triggers ownership check
  │  └─ Returns result
  └─ Flash success/error message

Command Execution Steps:
  1. Fetch booking from database
  2. Fetch associated business
  3. Verify: business.owner_id == current_user.user_id
  4. Verify: booking.status == 'requested'
  5. Update: booking.status = 'accepted'
  6. Record: booking.timestamps['accepted_at'] = now()
  7. Notify: All observers (email, SMS, business)
  8. Log: Command execution details
  9. Return: Updated booking object
```

#### 2. Reject Booking Flow

```
Business Owner Action:
  ├─ Clicks "Reject Booking" button
  ├─ Opens modal for rejection reason
  ├─ HTTP POST to /owner/booking/<booking_id>/reject
  ├─ Route handler executes:
  │  └─ reason = request.form.get('reason')
  │  └─ command = RejectBookingCommand(booking_id, owner_id, reason)
  │  └─ command.execute()  // Triggers ownership check
  │  └─ Returns result
  └─ Flash success/error message

Command Execution Steps:
  1-7. Same as Accept flow
  7.  Update: booking.status = 'rejected' (terminal state)
  8.  Record: rejection timestamp
  9.  Include reason in notification if provided
```

### Ownership Verification (Security)

The Command Pattern includes a critical security check:

```python
# In AcceptBookingCommand.execute()
business = Business.objects.get(business_id=self.booking.business_id)

# AUTHORIZATION CHECK: Prevent privilege escalation
if business.owner_id != self.business_owner_id:
    raise ValueError(
        f"Unauthorized: User {self.business_owner_id} is not the owner of {business.business_id}"
    )
```

**Why Double-Check?**

- Decorator protects the route (client-level)
- Command verifies business ownership (server-level)
- Defense in depth: Even if decorator is somehow bypassed, command prevents unauthorized action
- Prevents direct API abuse

### Error Handling

```python
try:
    command = AcceptBookingCommand(booking_id, current_user.user_id)
    result = command.execute()

    flash(f'Booking {booking_id} accepted successfully!', 'success')
    logger.info(f"Booking accepted: {command.get_description()}")

except ValueError as e:
    # Status errors (invalid state, unauthorized owner)
    flash(f'Cannot accept booking: {str(e)}', 'danger')
    logger.error(f"Command error: {str(e)}")

except Exception as e:
    # Unexpected errors
    flash(f'Error accepting booking: {str(e)}', 'danger')
    logger.error(f"Unexpected error: {str(e)}")
```

---

## Route Structure

### Base URL: `/owner`

All business owner routes are prefixed with `/owner` (defined in `owner_business_bp`).

### Routes Overview

| Method | Route                        | Handler                 | Purpose                        |
| ------ | ---------------------------- | ----------------------- | ------------------------------ |
| `GET`  | `/owner/dashboard`           | `dashboard()`           | View pending bookings & stats  |
| `GET`  | `/owner/business/create`     | `create_business()`     | Show create business form      |
| `POST` | `/owner/business/create`     | `create_business()`     | Submit new business            |
| `GET`  | `/owner/business/<id>`       | `view_business()`       | View specific business         |
| `GET`  | `/owner/bookings`            | `view_bookings()`       | List all bookings (filterable) |
| `GET`  | `/owner/booking/<id>`        | `view_booking_detail()` | View booking details           |
| `POST` | `/owner/booking/<id>/accept` | `accept_booking()`      | Accept booking (Command)       |
| `POST` | `/owner/booking/<id>/reject` | `reject_booking()`      | Reject booking (Command)       |
| `GET`  | `/owner/booking/<id>/stats`  | `booking_stats_api()`   | JSON stats endpoint            |

### Detailed Route Documentation

#### 1. Dashboard - `/owner/dashboard`

**Decorators:** `@business_owner_required`

**Purpose:** Main landing page for business owners

**Template:** `owner/dashboard.html`

**Displays:**

- Summary statistics (pending, accepted, completed bookings)
- List of owned businesses
- Recent pending bookings (limited to 5)

**Data Context:**

```python
{
    'businesses': [Business, ...],
    'pending_bookings': [Booking, ...],
    'stats': {
        'total_bookings': int,
        'pending_bookings': int,
        'accepted_bookings': int,
        'completed_bookings': int,
        'businesses_count': int
    }
}
```

#### 2. Create Business - `/owner/business/create`

**Decorators:** `@business_owner_required`

**Methods:** `GET`, `POST`

**Purpose:** Register a new business

**Form Fields:**

- name (required)
- category (required) - dropdown
- description (optional)
- email (required)
- phone (required)
- street_house (required)
- city (required)
- district (required)
- profile_pic (optional) - file upload
- gallery_pics (optional) - multiple files

**Business Logic:**

```python
def create_business():
    if request.method == 'POST':
        # Validate form data
        # Upload images to Cloudinary (if provided)
        # Create Business with owner_id = current_user.user_id
        # Redirect to view_business
```

#### 3. View Bookings - `/owner/bookings`

**Decorators:** `@business_owner_required`

**Query Parameters:**

- `status` (optional): 'all', 'requested', 'accepted', 'rejected', 'completed', 'cancelled'

**Purpose:** List all bookings for all owned businesses

**Template:** `owner/bookings.html`

**Features:**
#### 3a. Public Business View - `/business/<id>`

Owner-view protection:

- Backend flags owner view (`is_owner_viewing`) when `current_user.user_id == business.owner_id`.
- Template (`frontend/business_detail.html`) hides booking UI for owners and shows a link back to the owner dashboard.

Navigation rules:

- Services page Back button points to `owner_business.view_business`.
- Create Service Cancel points to `owner_business.view_business`.
- Navbar/Footers: hide “Home” for business owners.

- Filter by status
- Display booking summary table
- Quick action buttons

#### 4. Booking Detail - `/owner/booking/<booking_id>`

**Decorators:** `@business_owner_required`

**Purpose:** View complete booking information and manage

**Ownership Check:**

```python
# Verify user owns the business associated with booking
business = Business.objects(business_id=booking.business_id)
if business.owner_id != current_user.user_id:
    # Deny access
```

**Template:** `owner/booking_detail.html`

**Actions Available (if status == 'requested'):**

- Accept Booking button
- Reject Booking button (with modal for reason)

**Displays:**

- Booking details (ID, time, price, duration)
- Customer information
- Service information
- Status timeline with timestamps

#### 5. Accept Booking - `/owner/booking/<booking_id>/accept`

**Decorators:** `@business_owner_required`

**Method:** `POST`

**Implementation:**

```python
def accept_booking(booking_id):
    # Execute Command Pattern
    command = AcceptBookingCommand(booking_id, current_user.user_id)
    result = command.execute()
    # Handle success/error
```

**Triggers:**

- Command execution (ownership verification)
- Observer notifications (email, SMS, business)
- Booking status update
- Timestamp recording

#### 6. Reject Booking - `/owner/booking/<booking_id>/reject`

**Decorators:** `@business_owner_required`

**Method:** `POST`

**Form Parameters:**

- `reason` (optional): Rejection reason

**Implementation:** Similar to accept_booking but with rejection reason handling

---

## Authentication & Authorization Flow

### 1. Registration Flow (New Business Owner)

```
Step 1: User navigates to /auth/register
        ↓
Step 2: Selects "Business Owner" role in form
        ↓
Step 3: Fills registration form:
        - Name, Email, Phone
        - Password
        - Address (street, city, district)
        ↓
Step 4: Selects verification method (captcha or email)
        ↓
Step 5: If CAPTCHA:
        - Verify captcha answer
        - Call register_user(data, role='business_owner')
        - Create User with role='business_owner'
        ↓
Step 6: Redirect to login page
        ↓
Step 7: Success flash message
```

### 2. Login Flow (Business Owner)

```
Step 1: User navigates to /auth/login
        ↓
Step 2: Enters email/phone and password
        ↓
Step 3: Solves CAPTCHA
        ↓
Step 4: Backend validates credentials
        - Find user by email/phone
        - Verify password hash
        ↓
Step 5: Flask-Login authenticates user
        - login_user(user, remember=False)
        ↓
Step 6: Role-based redirection:
        if user.role == 'business_owner':
            → Redirect to /owner/dashboard
        elif user.role == 'admin':
            → Redirect to /admin/dashboard
        else:
            → Redirect to /  (home)
        ↓
Step 7: User lands on appropriate dashboard
```

### 3. Protected Route Access

```
Request to /owner/dashboard
        ↓
@business_owner_required decorator
        ↓
Is user authenticated? (Session/JWT)
        ├─ NO → Redirect to /auth/login
        └─ YES
           ↓
        Is user.role == 'business_owner'?
           ├─ NO → Flash error, redirect to /
           └─ YES
              ↓
           Route handler executes
           ↓
           Return response
```

### 4. Booking Operation Authorization

```
User clicks "Accept Booking" button
        ↓
POST to /owner/booking/<booking_id>/accept
        ↓
@business_owner_required decorator checks role
        ├─ Not authorized → Reject
        └─ Authorized
           ↓
        Route handler creates command:
        command = AcceptBookingCommand(booking_id, current_user.user_id)
           ↓
        Command.execute() performs:
        1. Fetch booking
        2. Fetch business
        3. Verify: business.owner_id == current_user.user_id
           ├─ Mismatch → Raise ValueError (unauthorized)
           └─ Match
              ↓
        4. Verify booking status == 'requested'
           ├─ Not 'requested' → Raise ValueError
           └─ Is 'requested'
              ↓
        5. Update booking status to 'accepted'
        6. Record timestamp
        7. Notify observers
           ↓
        Return success response
```

---

## Testing Guide

### Prerequisites

- Ensure MongoDB is running
- Have test user account ready
- Virtual environment activated

### Test Scenario 1: Business Owner Registration

**Steps:**

1. Navigate to `http://localhost:5000/auth/register`
2. Select "Business Owner" from role dropdown
3. Fill in registration form:
   - Name: "John's Plumbing"
   - Email: "john@plumbing.com"
   - Phone: "555-1234567"
   - Password: "TestPass123!"
   - Address: "123 Main St, New York, NY"
4. Select CAPTCHA verification
5. Solve CAPTCHA and submit
6. Verify success message and redirect to login

**Expected Result:**

- User created with `role='business_owner'`
- Account ready for login

### Test Scenario 2: Business Owner Login & Redirection

**Steps:**

1. Navigate to `http://localhost:5000/auth/login`
2. Enter credentials from Scenario 1
3. Solve CAPTCHA
4. Submit

**Expected Result:**

- Login successful
- Redirected to `/owner/dashboard` (not `/` home page)
- Dashboard displays statistics and pending bookings

### Test Scenario 3: Create Business

**Steps:**

1. Logged in as business owner
2. Click "New Business" button on dashboard
3. Fill business creation form:
   - Name: "Smith Plumbing Services"
   - Category: "Plumbing"
   - Description: "Professional plumbing..."
   - Contact: "contact@smith.com" / "555-9999999"
   - Address: "456 Oak St, New York, NY"
4. Upload profile picture (optional)
5. Submit form

**Expected Result:**

- Business created with owner_id = current user's user_id
- Redirected to view_business page
- Business appears in dashboard's "Your Businesses" section

### Test Scenario 4: Accept Booking (Command Pattern)

**Prerequisites:**

- Business created with at least one service
- Customer has created a booking in 'requested' status

**Steps:**

1. From owner dashboard, click "View Pending" or navigate to `/owner/bookings?status=requested`
2. Click "View" on a pending booking
3. Click "Accept Booking" button
4. Verify booking detail page shows "Booking Accepted" message

**Expected Result:**

- Booking status changed to 'accepted'
- Timestamp recorded: `timestamps['accepted_at']`
- Observers notified (check logs)
- Success flash message displayed

**Command Pattern Verification:**

```python
# Check in Python console
from models.booking import Booking
booking = Booking.objects(booking_id='<id>').first()
print(booking.status)  # Should be 'accepted'
print(booking.timestamps)  # Should contain 'accepted_at'
```

### Test Scenario 5: Reject Booking (With Reason)

**Prerequisites:**

- Another pending booking available

**Steps:**

1. From bookings list, click "View" on pending booking
2. Click "Reject Booking" button
3. In modal, enter reason: "Already scheduled for that time"
4. Click "Reject" in modal

**Expected Result:**

- Booking status changed to 'rejected'
- Reason logged in system
- Timestamp recorded: `timestamps['rejected_at']`
- Success flash message displayed

### Test Scenario 6: Authorization Tests

**Test 6A: Non-Business Owner Cannot Access Dashboard**

**Steps:**

1. Login as regular customer (role='customer')
2. Try to access `/owner/dashboard`

**Expected Result:**

- Decorator intercepts request
- Flash error: "Access denied. Only business owners..."
- Redirected to home page

**Test 6B: Prevent Unauthorized Booking Acceptance**

**Steps:**

1. Login as Business Owner A
2. Get booking ID for Business B (owned by Business Owner B)
3. Manually POST to `/owner/booking/<business_b_booking>/accept`

**Expected Result:**

- Command verifies ownership
- Raises ValueError: "Not the owner of this business"
- Flash error: "Cannot accept booking: Unauthorized"
- Booking remains in 'requested' state

### Test Scenario 7: Database Verification

**After completing Scenarios 1-5:**

```javascript
// MongoDB Console
use serviceDB

// Check user role
db.users.findOne({ email: 'john@plumbing.com' }).role
// Should output: "business_owner"

// Check business owner_id
db.businesses.findOne({ name: 'Smith Plumbing Services' }).owner_id
// Should match the user's user_id

// Check booking status history
db.bookings.findOne({ _id: '<booking_id>' }).timestamps
// Should contain: { requested_at: ..., accepted_at: ... }
```

---

## API Reference

### Authentication Endpoints

#### Register as Business Owner

```
POST /auth/register
Content-Type: application/x-www-form-urlencoded

Parameters:
  name=John Doe
  email=john@example.com
  phone=5551234567
  password=SecurePass123!
  street_house=123 Main St
  city=New York
  district=Manhattan
  role=business_owner
  verification_method=captcha
  captcha_answer=<answered_color>

Response: 302 Redirect to /auth/login
```

#### Login

```
POST /auth/login
Content-Type: application/x-www-form-urlencoded

Parameters:
  identifier=john@example.com  (email or phone)
  password=SecurePass123!
  captcha_answer=<answered_color>

Response: 302 Redirect to /owner/dashboard (for business owners)
```

### Business Owner Routes

#### Get Dashboard

```
GET /owner/dashboard
Authorization: Required (business_owner role)

Response: HTML (owner/dashboard.html)
{
  businesses: [...],
  pending_bookings: [...],
  stats: { total_bookings, pending_bookings, ... }
}
```

#### Create Business

```
GET /owner/business/create
Authorization: Required (business_owner role)

Response: HTML (owner/create_business.html) - form

---

POST /owner/business/create
Authorization: Required (business_owner role)
Content-Type: multipart/form-data

Parameters:
  name=Business Name
  email=business@email.com
  phone=5559999999
  street_house=789 Service Blvd
  city=Boston
  district=Downtown
  category=plumbing
  description=Description text
  profile_pic=<file>
  gallery_pics=<files>

Response: 302 Redirect to /owner/business/<business_id>
```

#### List Bookings

```
GET /owner/bookings?status=requested
Authorization: Required (business_owner role)

Query Parameters:
  status: 'all' | 'requested' | 'accepted' | 'rejected' | 'completed' | 'cancelled'

Response: HTML (owner/bookings.html)
{
  bookings: [Booking, ...],
  status_filter: 'requested'
}
```

#### View Booking Detail

```
GET /owner/booking/<booking_id>
Authorization: Required (business_owner role)
Ownership: Must own associated business

Response: HTML (owner/booking_detail.html)
{
  booking: Booking,
  business: Business,
  customer: User,
  service: Service
}
```

#### Accept Booking (Command Pattern)

```
POST /owner/booking/<booking_id>/accept
Authorization: Required (business_owner role)
Ownership: Must own associated business

Response: 302 Redirect to referrer or /owner/bookings
Side Effects:
  - Updates booking.status = 'accepted'
  - Records booking.timestamps['accepted_at']
  - Triggers observer notifications
  - Logs command execution
```

#### Reject Booking (Command Pattern)

```
POST /owner/booking/<booking_id>/reject
Authorization: Required (business_owner role)
Ownership: Must own associated business
Content-Type: application/x-www-form-urlencoded

Parameters:
  reason=Optional rejection reason

Response: 302 Redirect to referrer or /owner/bookings
Side Effects:
  - Updates booking.status = 'rejected'
  - Records booking.timestamps['rejected_at']
  - Includes reason in observer notifications
  - Logs command execution with reason
```

#### Get Booking Stats (JSON API)

```
GET /owner/booking/<booking_id>/stats
Authorization: Required (business_owner role)
Ownership: Must own associated business

Response: application/json
{
  "booking_id": "uuid",
  "status": "accepted",
  "customer_name": "John Customer",
  "customer_phone": "555-1111111",
  "price": 99.99,
  "duration_minutes": 60,
  "booking_time": "2025-01-20T14:00:00",
  "created_at": "2025-01-15T10:00:00",
  "timestamps": {
    "requested_at": "2025-01-15T10:00:00",
    "accepted_at": "2025-01-15T10:30:00"
  }
}
```

---

## Implementation Checklist

### Backend

- [x] Update User model with role field
- [x] Create @business_owner_required decorator
- [x] Create @admin_required decorator
- [x] Create @customer_required decorator
- [x] Update register_user controller for role parameter
- [x] Update login flow for role-based redirection
- [x] Enhance AcceptBookingCommand with ownership check
- [x] Enhance RejectBookingCommand with ownership check
- [x] Create owner_business.py views file
- [x] Register owner_business blueprint in app.py
- [x] Add error handling and logging

### Frontend

- [x] Create owner/dashboard.html template
- [x] Create owner/bookings.html template
- [x] Create owner/booking_detail.html template
- [x] Create owner/create_business.html template
- [x] Create owner/view_business.html template
- [x] Add role selection to registration form
- [x] Update login flow for dashboard routing

### Documentation

- [x] Create BUSINESS_OWNER_IMPLEMENTATION.md
- [x] Document all design patterns used
- [x] Document route structure
- [x] Document testing procedures
- [x] Document API reference
- [x] Add code examples

### Testing

- [ ] Test business owner registration
- [ ] Test business owner login with redirection
- [ ] Test business creation
- [ ] Test booking acceptance (Command Pattern)
- [ ] Test booking rejection (Command Pattern)
- [ ] Test unauthorized access prevention
- [ ] Test ownership verification in commands

---

## Troubleshooting

### Issue: User registered as business owner but doesn't redirect to dashboard

**Solution:**

- Verify `user.role == 'business_owner'` in database
- Check login route for role-based redirection logic
- Ensure Flask-Login is properly initialized

### Issue: Decorator shows "Only business owners" for authenticated user

**Solution:**

- Verify user's role field is set correctly
- Check decorator hasattr check for role attribute
- Ensure current_user is properly loaded by Flask-Login

### Issue: Command raises "Unauthorized" even for correct owner

**Solution:**

- Verify `business.owner_id` matches `current_user.user_id`
- Check that owner_id is being set correctly when creating business
- Ensure both IDs are same data type (should be string UUID)

### Issue: Booking not changing status after accept/reject

**Solution:**

- Check MongoDB connection
- Verify booking.update_status() is being called
- Check for exceptions in try/catch block
- Enable debug logging

---

## Future Enhancements

### Planned Features

- [ ] Multiple users per business (staff management)
- [ ] Business performance analytics
- [ ] Booking confirmation templates
- [ ] Scheduled booking notifications
- [ ] Rating/review system for bookings
- [ ] Payment processing for services
- [ ] Subscription tiers for businesses

### Performance Optimizations

- [ ] Cache pending bookings count
- [ ] Implement database indexes for owner queries
- [ ] Add pagination to booking lists
- [ ] Lazy load business details

---

## References

### Design Patterns

- **Decorator Pattern:** Flask request wrapping for authorization
- **Command Pattern:** Booking operations (Accept/Reject) as encapsulated commands
- **Observer Pattern:** Booking status change notifications
- **Builder Pattern:** Business creation (existing in system)
- **Singleton Pattern:** Database connection (existing in system)

### Technologies Used

- **Flask 2.3.3:** Web framework
- **MongoEngine 0.27.0:** MongoDB ODM
- **Flask-Login 0.6.2:** User session management
- **Werkzeug 2.3.6:** WSGI utilities

### Files Modified

1. `backend/models/user.py` - Added role field
2. `backend/patterns/decorator_auth.py` - New decorators
3. `backend/patterns/command_booking.py` - Ownership verification in commands
4. `backend/controllers/user_controller.py` - Role parameter in register_user
5. `backend/views/auth.py` - Role selection and redirection
6. `backend/views/owner_business.py` - New routes file
7. `backend/app.py` - Blueprint registration
8. `frontend/owner/dashboard.html` - New template
9. `frontend/owner/bookings.html` - New template
10. `frontend/owner/booking_detail.html` - New template
11. `frontend/owner/create_business.html` - New template
12. `frontend/owner/view_business.html` - New template

---

## Support & Questions

For issues or questions about the Business Owner implementation:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review test scenarios in [Testing Guide](#testing-guide)
3. Refer to code examples in [Design Patterns](#design-patterns-used)
4. Check logs for error messages
5. Enable Flask debug mode: `app.run(debug=True)`

---

**Last Updated:** November 28, 2025  
**Implementation Status:** ✅ Complete  
**Test Coverage:** 7 scenarios documented
