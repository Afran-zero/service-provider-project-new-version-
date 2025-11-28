"""
Command Pattern for Booking Operations

Encapsulates booking actions (create, cancel, accept, reject, complete)
as command objects that can be queued, retried, logged, and undone.
"""

from abc import ABC, abstractmethod
from models.booking import Booking
from models.business import Service, Business
from patterns.observer_booking import notify_booking_status_change
import datetime
import logging

logger = logging.getLogger(__name__)


class BookingCommand(ABC):
    """Abstract base class for booking commands"""
    
    def __init__(self):
        self.executed = False
        self.timestamp = None
        self.error = None
    
    @abstractmethod
    def execute(self):
        """Execute the command"""
        pass
    
    @abstractmethod
    def undo(self):
        """Undo the command (if possible)"""
        pass
    
    @abstractmethod
    def get_description(self):
        """Get human-readable description of command"""
        pass
    
    def log_execution(self, success=True):
        """Log command execution"""
        self.timestamp = datetime.datetime.utcnow()
        self.executed = True
        
        if success:
            logger.info(f"Command executed: {self.get_description()}")
        else:
            logger.error(f"Command failed: {self.get_description()} - {self.error}")


class CreateBookingCommand(BookingCommand):
    """Command to create a new booking"""
    
    def __init__(self, customer_id, service_id, booking_time, staff_id=None, notes=None):
        super().__init__()
        self.customer_id = customer_id
        self.service_id = service_id
        self.booking_time = booking_time
        self.staff_id = staff_id
        self.notes = notes
        self.booking = None
    
    def execute(self):
        """Create the booking"""
        try:
            # Get service details
            service = Service.objects.get(service_id=self.service_id)
            
            if not service.is_active:
                raise ValueError("Service is not active")
            
            # Check for conflicts
            end_time = self.booking_time + datetime.timedelta(minutes=service.duration_minutes)
            conflict = Booking.objects(
                business_id=service.business_id,
                booking_time__lt=end_time,
                status__in=['requested', 'accepted']
            ).first()
            
            if conflict:
                conflict_end = conflict.booking_time + datetime.timedelta(minutes=conflict.duration_minutes)
                if conflict_end > self.booking_time:
                    raise ValueError("Booking time conflict")
            
            # Create booking
            self.booking = Booking(
                business_id=service.business_id,
                service_id=self.service_id,
                customer_id=self.customer_id,
                staff_id=self.staff_id,
                booking_time=self.booking_time,
                duration_minutes=service.duration_minutes,
                price=service.price,
                notes=self.notes,
                status='requested',
                timestamps={'requested_at': datetime.datetime.utcnow()}
            )
            self.booking.save()
            
            # Notify observers
            notify_booking_status_change(self.booking, 'requested')
            
            self.log_execution(success=True)
            return self.booking
            
        except Exception as e:
            self.error = str(e)
            self.log_execution(success=False)
            raise
    
    def undo(self):
        """Cancel the created booking"""
        if self.booking and self.booking.status == 'requested':
            self.booking.update_status('cancelled')
            logger.info(f"Booking {self.booking.booking_id} cancelled (undo create)")
        else:
            raise ValueError("Cannot undo: booking not in 'requested' state")
    
    def get_description(self):
        return f"Create booking for service {self.service_id} at {self.booking_time}"


class CancelBookingCommand(BookingCommand):
    """Command to cancel a booking"""
    
    def __init__(self, booking_id, user_id, reason=None):
        super().__init__()
        self.booking_id = booking_id
        self.user_id = user_id
        self.reason = reason
        self.booking = None
        self.previous_status = None
    
    def execute(self):
        """Cancel the booking"""
        try:
            self.booking = Booking.objects.get(booking_id=self.booking_id)
            
            # Store previous status for undo
            self.previous_status = self.booking.status
            
            # Validate cancellation is allowed
            if self.booking.status not in ['requested', 'accepted']:
                raise ValueError(f"Cannot cancel booking with status: {self.booking.status}")
            
            # Update status
            self.booking.update_status('cancelled')
            
            # Notify observers
            notify_booking_status_change(self.booking, 'cancelled')
            
            self.log_execution(success=True)
            return self.booking
            
        except Exception as e:
            self.error = str(e)
            self.log_execution(success=False)
            raise
    
    def undo(self):
        """Restore previous booking status"""
        if self.booking and self.previous_status:
            self.booking.status = self.previous_status
            self.booking.timestamps.pop('cancelled_at', None)
            self.booking.save()
            logger.info(f"Booking {self.booking_id} restored to {self.previous_status} (undo cancel)")
        else:
            raise ValueError("Cannot undo: no previous state stored")
    
    def get_description(self):
        reason_str = f" (Reason: {self.reason})" if self.reason else ""
        return f"Cancel booking {self.booking_id}{reason_str}"


class AcceptBookingCommand(BookingCommand):
    """Command to accept a booking
    
    Verifies that the user executing the command is the business owner
    of the business associated with the booking.
    """
    
    def __init__(self, booking_id, business_owner_id):
        super().__init__()
        self.booking_id = booking_id
        self.business_owner_id = business_owner_id
        self.booking = None
    
    def execute(self):
        """Accept the booking"""
        try:
            self.booking = Booking.objects.get(booking_id=self.booking_id)
            
            # Verify business ownership (Decorator Pattern applied in views, but double-check here)
            business = Business.objects.get(business_id=self.booking.business_id)
            if business.owner_id != self.business_owner_id:
                raise ValueError(
                    f"Unauthorized: User {self.business_owner_id} is not the owner of business {business.business_id}"
                )
            
            if self.booking.status != 'requested':
                raise ValueError(f"Cannot accept booking with status: {self.booking.status}")
            
            self.booking.update_status('accepted')
            
            # Notify observers
            notify_booking_status_change(self.booking, 'accepted')
            
            self.log_execution(success=True)
            return self.booking
            
        except Exception as e:
            self.error = str(e)
            self.log_execution(success=False)
            raise
    
    def undo(self):
        """Revert to requested status"""
        if self.booking and self.booking.status == 'accepted':
            self.booking.status = 'requested'
            self.booking.timestamps.pop('accepted_at', None)
            self.booking.save()
            logger.info(f"Booking {self.booking_id} reverted to requested (undo accept)")
        else:
            raise ValueError("Cannot undo: booking not in 'accepted' state")
    
    def get_description(self):
        return f"Accept booking {self.booking_id} by owner {self.business_owner_id}"


class RejectBookingCommand(BookingCommand):
    """Command to reject a booking
    
    Verifies that the user executing the command is the business owner
    of the business associated with the booking.
    """
    
    def __init__(self, booking_id, business_owner_id, reason=None):
        super().__init__()
        self.booking_id = booking_id
        self.business_owner_id = business_owner_id
        self.reason = reason
        self.booking = None
    
    def execute(self):
        """Reject the booking"""
        try:
            self.booking = Booking.objects.get(booking_id=self.booking_id)
            
            # Verify business ownership (Decorator Pattern applied in views, but double-check here)
            business = Business.objects.get(business_id=self.booking.business_id)
            if business.owner_id != self.business_owner_id:
                raise ValueError(
                    f"Unauthorized: User {self.business_owner_id} is not the owner of business {business.business_id}"
                )
            
            if self.booking.status != 'requested':
                raise ValueError(f"Cannot reject booking with status: {self.booking.status}")
            
            self.booking.update_status('rejected')
            
            # Notify observers
            notify_booking_status_change(self.booking, 'rejected')
            
            self.log_execution(success=True)
            return self.booking
            
        except Exception as e:
            self.error = str(e)
            self.log_execution(success=False)
            raise
    
    def undo(self):
        """Revert to requested status"""
        if self.booking and self.booking.status == 'rejected':
            self.booking.status = 'requested'
            self.booking.timestamps.pop('rejected_at', None)
            self.booking.save()
            logger.info(f"Booking {self.booking_id} reverted to requested (undo reject)")
        else:
            raise ValueError("Cannot undo: booking not in 'rejected' state")
    
    def get_description(self):
        reason_str = f" (Reason: {self.reason})" if self.reason else ""
        return f"Reject booking {self.booking_id} by owner {self.business_owner_id}{reason_str}"
    
    def undo(self):
        """Cannot undo rejection (terminal state)"""
        raise ValueError("Cannot undo rejection - terminal state")
    
    def get_description(self):
        reason_str = f" (Reason: {self.reason})" if self.reason else ""
        return f"Reject booking {self.booking_id}{reason_str}"


class CompleteBookingCommand(BookingCommand):
    """Command to mark a booking as completed"""
    
    def __init__(self, booking_id, business_owner_id):
        super().__init__()
        self.booking_id = booking_id
        self.business_owner_id = business_owner_id
        self.booking = None
    
    def execute(self):
        """Complete the booking"""
        try:
            self.booking = Booking.objects.get(booking_id=self.booking_id)
            
            if self.booking.status != 'accepted':
                raise ValueError(f"Cannot complete booking with status: {self.booking.status}")
            
            self.booking.update_status('completed')
            
            # Notify observers
            notify_booking_status_change(self.booking, 'completed')
            
            self.log_execution(success=True)
            return self.booking
            
        except Exception as e:
            self.error = str(e)
            self.log_execution(success=False)
            raise
    
    def undo(self):
        """Cannot undo completion (terminal state)"""
        raise ValueError("Cannot undo completion - terminal state")
    
    def get_description(self):
        return f"Complete booking {self.booking_id}"


class BookingCommandQueue:
    """
    Queue for managing booking commands with retry logic
    """
    
    def __init__(self):
        self.queue = []
        self.history = []
        self.max_retries = 3
    
    def add_command(self, command):
        """Add command to queue"""
        self.queue.append({
            'command': command,
            'retries': 0,
            'added_at': datetime.datetime.utcnow()
        })
        logger.info(f"Command added to queue: {command.get_description()}")
    
    def execute_next(self):
        """Execute the next command in queue"""
        if not self.queue:
            return None
        
        item = self.queue.pop(0)
        command = item['command']
        
        try:
            result = command.execute()
            self.history.append({
                'command': command,
                'status': 'success',
                'executed_at': datetime.datetime.utcnow()
            })
            return result
        except Exception as e:
            item['retries'] += 1
            
            if item['retries'] < self.max_retries:
                # Re-add to queue for retry
                self.queue.append(item)
                logger.warning(f"Command failed, will retry ({item['retries']}/{self.max_retries}): {command.get_description()}")
            else:
                # Max retries reached
                self.history.append({
                    'command': command,
                    'status': 'failed',
                    'error': str(e),
                    'executed_at': datetime.datetime.utcnow()
                })
                logger.error(f"Command failed after {self.max_retries} retries: {command.get_description()}")
            
            raise
    
    def execute_all(self):
        """Execute all commands in queue"""
        results = []
        errors = []
        
        while self.queue:
            try:
                result = self.execute_next()
                results.append(result)
            except Exception as e:
                errors.append(str(e))
        
        return results, errors
    
    def get_queue_size(self):
        """Get number of commands in queue"""
        return len(self.queue)
    
    def get_history(self, limit=10):
        """Get command execution history"""
        return self.history[-limit:]
    
    def clear_queue(self):
        """Clear all pending commands"""
        self.queue.clear()
        logger.info("Command queue cleared")


class BookingCommandInvoker:
    """
    Invoker for executing booking commands with queue support
    """
    
    def __init__(self):
        self.queue = BookingCommandQueue()
    
    def execute_immediately(self, command):
        """Execute command immediately without queueing"""
        return command.execute()
    
    def queue_command(self, command):
        """Add command to queue for later execution"""
        self.queue.add_command(command)
    
    def process_queue(self):
        """Process all queued commands"""
        return self.queue.execute_all()
    
    def undo_last_command(self):
        """Undo the last successfully executed command"""
        history = self.queue.get_history(limit=1)
        if history and history[0]['status'] == 'success':
            command = history[0]['command']
            command.undo()
            logger.info(f"Undid command: {command.get_description()}")
        else:
            raise ValueError("No command to undo")
