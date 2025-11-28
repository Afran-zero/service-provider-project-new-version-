# Booking Command Pattern Fix

## Error

```
Unexpected error: CreateBookingCommand.__init__() got an unexpected keyword argument 'notes'
```

## Root Cause

The booking form in the frontend was sending a `notes` parameter when creating a booking, but the `CreateBookingCommand` class didn't accept this parameter. This caused the booking command to fail.

## Changes Made

### 1. Updated `backend/patterns/command_booking.py`

**Added `notes` parameter to `CreateBookingCommand.__init__()`:**

```python
# Before
def __init__(self, customer_id, service_id, booking_time, staff_id=None):
    self.customer_id = customer_id
    self.service_id = service_id
    self.booking_time = booking_time
    self.staff_id = staff_id
    self.booking = None

# After
def __init__(self, customer_id, service_id, booking_time, staff_id=None, notes=None):
    self.customer_id = customer_id
    self.service_id = service_id
    self.booking_time = booking_time
    self.staff_id = staff_id
    self.notes = notes  # New parameter
    self.booking = None
```

**Updated `execute()` method to save notes:**

```python
# Added notes parameter when creating Booking
self.booking = Booking(
    ...
    notes=self.notes,  # New line
    ...
)
```

### 2. Updated `backend/models/booking.py`

**Added `notes` field to Booking model:**

```python
notes = me.StringField(default=None)  # Optional customer notes/special requirements
```

This allows storing customer notes/special requirements with each booking.

## Flow After Fix

1. User fills out booking form with service, date, time, and optional notes
2. Frontend sends data with `notes` parameter to `/booking/create` endpoint
3. Backend creates `CreateBookingCommand` with all parameters including `notes`
4. Command creates `Booking` document with the notes field populated
5. Booking is saved successfully
6. User receives success message

## Database Update

Existing bookings in MongoDB won't have the `notes` field - that's fine as it has `default=None`. Any new bookings will include the notes field.

## Testing

1. Navigate to a business detail page
2. Select a service
3. Pick a date and time
4. Add some notes in "Additional Notes" field (or leave blank)
5. Click "Confirm Booking"
6. Confirm the booking
7. ✅ Booking should be created successfully without the "Unexpected error" message

## Files Modified

- `backend/patterns/command_booking.py` - Added notes parameter to CreateBookingCommand
- `backend/models/booking.py` - Added notes field to Booking model

## Related Components

**Frontend (`business_detail.html`):**

- Already sending notes via AJAX: `notes: notes`
- Works correctly after backend fixes

**Backend Controller (`views/booking.py`):**

- Already passing notes to CreateBookingCommand: `notes=notes`
- Works correctly after pattern updates

**Booking Controller (`controllers/booking_controller.py`):**

- Can be updated later to retrieve and display notes in booking details
