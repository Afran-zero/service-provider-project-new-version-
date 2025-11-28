# patterns/observer_booking.py
"""
Observer Pattern Implementation for Booking Notifications

This module implements the Observer pattern to notify users about booking status changes.
Observers (EmailNotifier, SMSNotifier) are notified when bookings change state.
"""

from mongoengine import signals
from models.booking import Booking
from models.business import Business
from models.user import User
from flask import flash
import logging

logger = logging.getLogger(__name__)


class BookingObserver:
    """Abstract base class for booking observers"""
    
    def update(self, booking, status):
        """Override this method in concrete observers"""
        raise NotImplementedError("Subclasses must implement update()")


class EmailNotifier(BookingObserver):
    """Observer that sends email notifications for booking status changes"""
    
    def update(self, booking, status):
        """Send email notification based on booking status"""
        try:
            # Get customer and business details
            customer = User.objects.get(user_id=booking.customer_id)
            business = Business.objects.get(business_id=booking.business_id)
            
            subject = f"Booking {status.capitalize()}"
            
            # Create status-specific messages
            messages = {
                'requested': f"Your booking request at {business.name} has been submitted.",
                'accepted': f"Great news! Your booking at {business.name} has been accepted.",
                'rejected': f"Unfortunately, your booking at {business.name} has been rejected.",
                'cancelled': f"Your booking at {business.name} has been cancelled.",
                'completed': f"Thank you! Your service at {business.name} is complete."
            }
            
            message = messages.get(status, f"Booking status updated to {status}")
            
            # In production, send actual email using utils.send_email
            logger.info(f"[EMAIL] To: {customer.email}, Subject: {subject}, Message: {message}")
            
            # For development, use flash messages
            flash(f"Email notification: {message}", "info")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")


class SMSNotifier(BookingObserver):
    """Observer that sends SMS notifications for booking status changes"""
    
    def update(self, booking, status):
        """Send SMS notification based on booking status"""
        try:
            # Get customer details
            customer = User.objects.get(user_id=booking.customer_id)
            business = Business.objects.get(business_id=booking.business_id)
            
            # Create status-specific messages
            messages = {
                'requested': f"Booking request submitted at {business.name}",
                'accepted': f"Booking accepted at {business.name}! Time: {booking.booking_time.strftime('%Y-%m-%d %H:%M')}",
                'rejected': f"Booking rejected at {business.name}",
                'cancelled': f"Booking cancelled at {business.name}",
                'completed': f"Service completed at {business.name}. Thank you!"
            }
            
            message = messages.get(status, f"Booking status: {status}")
            
            # In production, integrate with SMS gateway (Twilio, etc.)
            logger.info(f"[SMS] To: {customer.phone}, Message: {message}")
            
            # For development, use flash messages
            flash(f"SMS notification: {message}", "info")
            
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {str(e)}")


class BusinessNotifier(BookingObserver):
    """Observer that notifies business owners about booking requests"""
    
    def update(self, booking, status):
        """Notify business owner about booking status changes"""
        try:
            business = Business.objects.get(business_id=booking.business_id)
            owner = User.objects.get(user_id=business.owner_id)
            customer = User.objects.get(user_id=booking.customer_id)
            
            # Only notify business for specific statuses
            if status == 'requested':
                subject = "New Booking Request"
                message = f"New booking request from {customer.name} for {booking.booking_time.strftime('%Y-%m-%d %H:%M')}"
            elif status == 'cancelled':
                subject = "Booking Cancelled"
                message = f"Customer {customer.name} cancelled booking for {booking.booking_time.strftime('%Y-%m-%d %H:%M')}"
            else:
                return  # Don't notify for other statuses
            
            # In production, send email to business owner
            logger.info(f"[BUSINESS EMAIL] To: {owner.email}, Subject: {subject}, Message: {message}")
            
        except Exception as e:
            logger.error(f"Failed to notify business: {str(e)}")


# Registry of active observers
_observers = [
    EmailNotifier(),
    SMSNotifier(),
    BusinessNotifier()
]


def notify_booking_status_change(booking, status):
    """Notify all registered observers about booking status change"""
    for observer in _observers:
        try:
            observer.update(booking, status)
        except Exception as e:
            logger.error(f"Observer {observer.__class__.__name__} failed: {str(e)}")


def register_observer(observer):
    """Register a new observer to receive booking notifications"""
    if observer not in _observers:
        _observers.append(observer)


def unregister_observer(observer):
    """Unregister an observer from receiving notifications"""
    if observer in _observers:
        _observers.remove(observer)


# MongoEngine signal handlers (alternative approach)
def on_booking_post_save(sender, document, created):
    """Signal handler for booking creation"""
    if created:
        notify_booking_status_change(document, 'requested')


def setup_observers():
    """Initialize MongoEngine signal connections"""
    signals.post_save.connect(on_booking_post_save, sender=Booking)