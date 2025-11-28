# views/booking.py
from flask import Blueprint, request, render_template, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from controllers import booking_controller, business_controller
from models.business import Business
import datetime

booking_bp = Blueprint('booking', __name__, url_prefix='/booking')


@booking_bp.route('/create', methods=['POST'])
@login_required
def create_booking():
    """Create a new booking with conflict detection"""
    try:
        # Get JSON data from AJAX request
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        business_id = data.get('business_id')
        service_id = data.get('service_id')
        booking_date = data.get('booking_date')
        booking_time = data.get('booking_time')
        notes = data.get('notes', '')
        
        # Validate required fields
        if not all([business_id, service_id, booking_date, booking_time]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Combine date and time
        booking_datetime = datetime.datetime.strptime(
            f"{booking_date} {booking_time}", 
            "%Y-%m-%d %H:%M"
        )
        
        # Check if booking time is in the future
        if booking_datetime <= datetime.datetime.now():
            return jsonify({'success': False, 'message': 'Booking time must be in the future'}), 400
        
        # CONFLICT DETECTION: Check if customer has another booking at the same time
        customer_bookings = booking_controller.get_user_bookings(current_user.user_id)
        for booking in customer_bookings:
            if booking.status in ['pending', 'accepted']:
                # Parse existing booking time
                existing_time = booking.booking_time
                if isinstance(existing_time, str):
                    existing_datetime = datetime.datetime.strptime(existing_time, "%Y-%m-%d %H:%M:%S")
                else:
                    existing_datetime = existing_time
                
                # Check if times conflict (same time)
                if existing_datetime == booking_datetime:
                    return jsonify({
                        'success': False, 
                        'message': 'You already have a booking at this time'
                    }), 400
        
        # CONFLICT DETECTION: Check if business has another booking at the same time
        business_bookings = booking_controller.get_business_bookings(business_id)
        for booking in business_bookings:
            if booking.status in ['pending', 'accepted']:
                existing_time = booking.booking_time
                if isinstance(existing_time, str):
                    existing_datetime = datetime.datetime.strptime(existing_time, "%Y-%m-%d %H:%M:%S")
                else:
                    existing_datetime = existing_time
                
                if existing_datetime == booking_datetime:
                    return jsonify({
                        'success': False, 
                        'message': 'This time slot is already booked'
                    }), 400
        
        # Create booking using Command pattern
        from patterns.command_booking import CreateBookingCommand, BookingCommandInvoker
        
        command = CreateBookingCommand(
            customer_id=current_user.user_id,
            service_id=service_id,
            booking_time=booking_datetime,
            notes=notes
        )
        
        invoker = BookingCommandInvoker()
        booking = invoker.execute_immediately(command)
        
        return jsonify({
            'success': True, 
            'message': 'Booking created successfully',
            'booking_id': booking.id
        }), 200
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Unexpected error: {str(e)}'}), 500


@booking_bp.route('/<booking_id>')
@login_required
def view_booking(booking_id):
    """View booking details"""
    booking_details = booking_controller.get_booking_details(booking_id)
    if not booking_details:
        flash('Booking not found', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    # Get business details
    business = business_controller.get_business(booking_details['business_id'])
    
    # Check authorization
    is_customer = booking_details['customer_id'] == current_user.user_id
    is_owner = business and business.owner_id == current_user.user_id
    
    if not (is_customer or is_owner):
        flash('You are not authorized to view this booking', 'danger')
        return redirect(url_for('home.dashboard'))
    
    return render_template('booking/view.html', 
                         booking=booking_details, 
                         business=business,
                         is_customer=is_customer,
                         is_owner=is_owner)


@booking_bp.route('/<booking_id>/status', methods=['POST'])
@login_required
def update_status(booking_id):
    """Update booking status (accept/reject/complete)"""
    try:
        new_status = request.form.get('status')
        if not new_status:
            return jsonify({'success': False, 'error': 'Status is required'}), 400
        
        # Update status
        booking = booking_controller.update_booking_status(
            booking_id=booking_id,
            new_status=new_status,
            actor_id=current_user.user_id
        )
        
        flash(f'Booking status updated to {new_status}', 'success')
        
        # Return JSON for AJAX requests
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'status': new_status})
        
        return redirect(url_for('booking.view_booking', booking_id=booking_id))
        
    except ValueError as e:
        flash(f'Error: {str(e)}', 'danger')
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 400
        return redirect(url_for('booking.view_booking', booking_id=booking_id))


@booking_bp.route('/my-bookings')
@login_required
def my_bookings():
    """View customer's bookings"""
    status_filter = request.args.get('status')
    
    bookings = booking_controller.get_bookings_by_customer(
        customer_id=current_user.user_id,
        status=status_filter
    )
    
    # Enrich with business and service details
    enriched_bookings = []
    for booking in bookings:
        business = business_controller.get_business(booking.business_id)
        service = business_controller.get_service(booking.service_id)
        
        enriched_bookings.append({
            'booking': booking,
            'business': business,
            'service': service
        })
    
    return render_template('booking/my_bookings.html', 
                         bookings=enriched_bookings,
                         status_filter=status_filter)


@booking_bp.route('/business-bookings/<business_id>')
@login_required
def business_bookings(business_id):
    """View bookings for a business (owner only)"""
    business = business_controller.get_business(business_id)
    if not business or business.owner_id != current_user.user_id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('home.dashboard'))
    
    status_filter = request.args.get('status')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Parse dates
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None
    
    bookings = booking_controller.get_bookings_by_business(
        business_id=business_id,
        status=status_filter,
        start_date=start_date,
        end_date=end_date
    )
    
    # Enrich with customer and service details
    enriched_bookings = []
    for booking in bookings:
        from models.user import User
        customer = User.objects.get(user_id=booking.customer_id)
        service = business_controller.get_service(booking.service_id)
        
        enriched_bookings.append({
            'booking': booking,
            'customer': customer,
            'service': service
        })
    
    return render_template('booking/business_bookings.html',
                         business=business,
                         bookings=enriched_bookings,
                         status_filter=status_filter,
                         start_date=start_date_str,
                         end_date=end_date_str)


@booking_bp.route('/cancel/<booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Cancel a booking - JSON response for AJAX"""
    try:
        # Use Command pattern for cancellation
        from patterns.command_booking import CancelBookingCommand, BookingCommandInvoker
        
        command = CancelBookingCommand(booking_id, current_user.user_id)
        invoker = BookingCommandInvoker()
        booking = invoker.execute_immediately(command)
        
        return jsonify({'success': True, 'message': 'Booking cancelled successfully'}), 200
        
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@booking_bp.route('/check-availability/<business_id>', methods=['GET'])
def check_availability(business_id):
    """Check available time slots for a business on a specific date"""
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({'error': 'Date is required'}), 400
    
    try:
        # Get all bookings for this business on this date
        bookings = booking_controller.get_business_bookings(business_id)
        
        # Filter bookings for the selected date and active statuses
        booked_slots = []
        for booking in bookings:
            if booking.status in ['pending', 'accepted']:
                # Parse booking time
                booking_time = booking.booking_time
                if isinstance(booking_time, str):
                    booking_datetime = datetime.datetime.strptime(booking_time, "%Y-%m-%d %H:%M:%S")
                else:
                    booking_datetime = booking_time
                
                # Check if booking is on the selected date
                if booking_datetime.strftime("%Y-%m-%d") == date_str:
                    booked_slots.append(booking_datetime.strftime("%H:%M"))
        
        return jsonify({'booked_slots': booked_slots}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@booking_bp.route('/api/available-slots', methods=['GET'])
def get_available_slots():
    """Get available booking slots for a service on a specific date (API endpoint)"""
    service_id = request.args.get('service_id')
    date_str = request.args.get('date')
    
    if not service_id or not date_str:
        return jsonify({'error': 'service_id and date are required'}), 400
    
    try:
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        service = business_controller.get_service(service_id)
        
        if not service:
            return jsonify({'error': 'Service not found'}), 404
        
        # Get all bookings for this business on this date
        start_of_day = date.replace(hour=0, minute=0, second=0)
        end_of_day = date.replace(hour=23, minute=59, second=59)
        
        bookings = booking_controller.get_bookings_by_business(
            business_id=service.business_id,
            status='accepted',
            start_date=start_of_day,
            end_date=end_of_day
        )
        
        # Calculate available slots (9 AM - 6 PM, 1-hour intervals)
        business_hours = list(range(9, 18))  # 9 AM to 5 PM
        booked_hours = set()
        
        for booking in bookings:
            booked_hours.add(booking.booking_time.hour)
        
        available_slots = [f"{hour:02d}:00" for hour in business_hours if hour not in booked_hours]
        
        return jsonify({'available_slots': available_slots})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500