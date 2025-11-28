from models.booking import Booking
from mongoengine.queryset.visitor import Q

def check_booking_conflict(business_id, start_time, end_time):
    # Check for overlapping bookings
    overlapping = Booking.objects(
        Q(business_id=business_id) &
        Q(start_time__lt=end_time) &
        Q(end_time__gt=start_time)
    ).count()
    return overlapping == 0