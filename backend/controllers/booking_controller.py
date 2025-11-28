# controllers/booking_controller.py
from models.booking import Booking
from models.business import Service
from patterns.observer_booking import notify_booking_status_change
import datetime


def create_booking(customer_id, service_id, booking_time, staff_id=None):
    """Create a new booking with 'requested' status"""
    # Get service details for price and duration
    try:
        service = Service.objects.get(service_id=service_id)
    except Service.DoesNotExist:
        raise ValueError("Service not found")

    if not service.is_active:
        raise ValueError("Service is not active")

    # Check for booking conflicts
    end_time = booking_time + datetime.timedelta(minutes=service.duration_minutes)
    conflict = Booking.objects(
        business_id=service.business_id,
        booking_time__lt=end_time,
        status__in=['requested', 'accepted']
    ).first()

    # Calculate actual conflict by checking if existing booking end time overlaps
    if conflict:
        conflict_end = conflict.booking_time + datetime.timedelta(minutes=conflict.duration_minutes)
        if conflict_end > booking_time:
            raise ValueError("Booking time conflict")

    booking = Booking(
        business_id=service.business_id,
        service_id=service_id,
        customer_id=customer_id,
        staff_id=staff_id,
        booking_time=booking_time,
        duration_minutes=service.duration_minutes,
        price=service.price,
        status='requested',
        timestamps={'requested_at': datetime.datetime.utcnow()}
    )
    booking.save()

    # Notify observers
    notify_booking_status_change(booking, 'requested')

    return booking


def get_booking(booking_id):
    """Get a single booking by ID"""
    try:
        booking = Booking.objects.get(booking_id=booking_id)
        return booking
    except Booking.DoesNotExist:
        return None


def update_booking_status(booking_id, new_status, actor_id):
    """Update booking status with state machine validation"""
    booking = get_booking(booking_id)
    if not booking:
        raise ValueError("Booking not found")

    # State machine validation
    valid_transitions = {
        'requested': ['accepted', 'rejected', 'cancelled'],
        'accepted': ['completed', 'cancelled'],
        'rejected': [],  # Terminal state
        'cancelled': [],  # Terminal state
        'completed': []  # Terminal state
    }

    current_status = booking.status
    if new_status not in valid_transitions.get(current_status, []):
        raise ValueError(f"Invalid status transition from {current_status} to {new_status}")

    # Authorization check
    # Business owner can accept/reject/complete
    # Customer can cancel
    # (This requires getting business owner_id - simplified here)
    if new_status == 'cancelled' and actor_id != booking.customer_id:
        # Allow business to cancel too
        pass

    # Update status using model method
    booking.update_status(new_status)

    # Notify observers
    notify_booking_status_change(booking, new_status)

    return booking


def get_bookings_by_customer(customer_id, status=None):
    """Get all bookings for a customer with optional status filter"""
    query = {'customer_id': customer_id}
    if status:
        query['status'] = status

    bookings = Booking.objects(**query).order_by('-booking_time')
    return bookings


def get_bookings_by_business(business_id, status=None, start_date=None, end_date=None):
    """Get all bookings for a business with optional filters"""
    query = {'business_id': business_id}
    if status:
        query['status'] = status
    if start_date:
        query['booking_time__gte'] = start_date
    if end_date:
        query['booking_time__lte'] = end_date

    bookings = Booking.objects(**query).order_by('-booking_time')
    return bookings


def cancel_booking(booking_id, user_id):
    """Cancel a booking (customer or business can cancel)"""
    booking = get_booking(booking_id)
    if not booking:
        raise ValueError("Booking not found")

    # Only allow cancellation if in cancellable state
    if booking.status not in ['requested', 'accepted']:
        raise ValueError(f"Cannot cancel booking with status: {booking.status}")

    # Verify user authorization
    # (In production, also check if user is business owner)
    if booking.customer_id != user_id:
        # Could add business owner check here
        pass

    booking.update_status('cancelled')
    notify_booking_status_change(booking, 'cancelled')

    return booking


def get_booking_details(booking_id):
    """Get detailed booking information with related data"""
    booking = get_booking(booking_id)
    if not booking:
        return None

    # Get service details
    try:
        service = Service.objects.get(service_id=booking.service_id)
        service_data = {
            'service_id': service.service_id,
            'name': service.name,
            'description': service.description
        }
    except Service.DoesNotExist:
        service_data = None

    result = {
        'booking_id': booking.booking_id,
        'business_id': booking.business_id,
        'service': service_data,
        'customer_id': booking.customer_id,
        'staff_id': booking.staff_id,
        'booking_time': booking.booking_time,
        'duration_minutes': booking.duration_minutes,
        'price': booking.price,
        'status': booking.status,
        'timestamps': booking.timestamps,
        'created_at': booking.created_at,
        'updated_at': booking.updated_at
    }
    return result


# Wrapper functions for frontend views
def get_user_bookings(customer_id, status=None):
    """Get all bookings for a user - wrapper for get_bookings_by_customer"""
    return get_bookings_by_customer(customer_id, status)


def get_business_bookings(business_id, status=None):
    """Get all bookings for a business - wrapper for get_bookings_by_business"""
    return get_bookings_by_business(business_id, status)