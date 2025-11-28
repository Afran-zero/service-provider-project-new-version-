# views/owner_business.py
"""
Business Owner Dashboard and Management Routes

Provides routes for business owners to:
- View their dashboard with pending bookings
- Manage their business profile
- Accept/reject booking requests using the Command Pattern
"""

from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import current_user
from patterns.decorator_auth import business_owner_required, login_required
from controllers import business_controller
from models.booking import Booking
from models.business import Business
from patterns.command_booking import AcceptBookingCommand, RejectBookingCommand
import logging

logger = logging.getLogger(__name__)

owner_business_bp = Blueprint(
    'owner_business',
    __name__,
    url_prefix='/owner',
    template_folder='../../frontend'
)


@owner_business_bp.route('/dashboard', methods=['GET'])
@business_owner_required
def dashboard():
    """
    Business Owner Dashboard - displays summary and pending bookings.
    
    Accessible by: Business owners only (Decorator Pattern)
    Template shows:
    - List of pending booking requests
    - Quick stats (total bookings, accepted, pending)
    - Link to manage business
    """
    try:
        # Get all businesses owned by current user
        owner_businesses = Business.objects(owner_id=current_user.user_id)
        
        if not owner_businesses:
            flash(
                "You haven't created a business yet. Create one to start accepting bookings.",
                "info"
            )
            return redirect(url_for('owner_business.create_business'))
        
        # Get IDs of all owned businesses
        business_ids = [b.business_id for b in owner_businesses]
        
        # Get pending bookings for all owned businesses
        pending_bookings = Booking.objects(
            business_id__in=business_ids,
            status='requested'
        ).order_by('-created_at')
        
        # Get stats
        all_bookings = Booking.objects(business_id__in=business_ids)
        accepted_bookings = Booking.objects(
            business_id__in=business_ids,
            status='accepted'
        )
        completed_bookings = Booking.objects(
            business_id__in=business_ids,
            status='completed'
        )
        
        stats = {
            'total_bookings': len(all_bookings),
            'pending_bookings': len(pending_bookings),
            'accepted_bookings': len(accepted_bookings),
            'completed_bookings': len(completed_bookings),
            'businesses_count': len(owner_businesses)
        }
        
        return render_template(
            'owner/dashboard.html',
            businesses=owner_businesses,
            pending_bookings=pending_bookings,
            stats=stats
        )
        
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "danger")
        logger.error(f"Dashboard error for user {current_user.user_id}: {str(e)}")
        return redirect(url_for('home.index'))


@owner_business_bp.route('/business/create', methods=['GET', 'POST'])
@business_owner_required
def create_business():
    """
    Create a new business as a Business Owner.
    
    Accessible by: Business owners only (Decorator Pattern)
    Uses: BusinessBuilder pattern from controllers
    """
    if request.method == 'GET':
        return render_template('owner/create_business.html')
    
    try:
        # Get form data
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'street_house': request.form.get('street_house'),
            'city': request.form.get('city'),
            'district': request.form.get('district'),
            'description': request.form.get('description', ''),
            'category': request.form.get('category')
        }
        
        # Validate required fields
        required_fields = ['name', 'email', 'phone', 'street_house', 'city', 'district', 'category']
        missing_fields = [f for f in required_fields if not data.get(f)]
        
        if missing_fields:
            flash(f"Missing required fields: {', '.join(missing_fields)}", 'danger')
            return render_template('owner/create_business.html', data=data), 400
        
        # Get uploaded files
        profile_pic = request.files.get('profile_pic')
        gallery_pics = request.files.getlist('gallery_pics')
        
        # Create business with owner_id set to current user
        business = business_controller.create_business(
            owner_id=current_user.user_id,
            data=data,
            profile_pic=profile_pic if profile_pic and profile_pic.filename else None,
            gallery_pics=[pic for pic in gallery_pics if pic and pic.filename]
        )
        
        flash(f'Business "{business.name}" created successfully!', 'success')
        logger.info(f"Business {business.business_id} created by owner {current_user.user_id}")
        return redirect(url_for('owner_business.view_business', business_id=business.business_id))
        
    except Exception as e:
        flash(f'Error creating business: {str(e)}', 'danger')
        logger.error(f"Error creating business for user {current_user.user_id}: {str(e)}")
        return render_template('owner/create_business.html'), 500


@owner_business_bp.route('/business/<business_id>', methods=['GET'])
@business_owner_required
def view_business(business_id):
    """
    View a specific business managed by the owner.
    
    Accessible by: The owner of the business only (verified via decorator)
    """
    try:
        business = business_controller.get_business(business_id)
        
        if not business:
            flash('Business not found', 'danger')
            return redirect(url_for('owner_business.dashboard'))
        
        # Verify ownership
        if business.owner_id != current_user.user_id:
            flash('You are not authorized to view this business', 'danger')
            return redirect(url_for('owner_business.dashboard'))
        
        # Get services for this business
        services = business_controller.get_services_by_business(business_id)
        business_details = business_controller.get_business_details(business_id)
        
        return render_template(
            'owner/view_business.html',
            business=business_details,
            services=services
        )
        
    except Exception as e:
        flash(f'Error loading business: {str(e)}', 'danger')
        logger.error(f"Error viewing business {business_id}: {str(e)}")
        return redirect(url_for('owner_business.dashboard'))


@owner_business_bp.route('/bookings', methods=['GET'])
@business_owner_required
def view_bookings():
    """
    View all bookings for the owner's businesses.
    
    Accessible by: Business owners only (Decorator Pattern)
    Allows filtering by status: requested, accepted, rejected, completed, cancelled
    """
    try:
        # Get all businesses owned by current user
        owner_businesses = Business.objects(owner_id=current_user.user_id)
        business_ids = [b.business_id for b in owner_businesses]
        
        if not business_ids:
            flash("You don't have any businesses yet.", "info")
            return redirect(url_for('owner_business.create_business'))
        
        # Get filter parameter
        status_filter = request.args.get('status', 'all')
        
        # Build query
        if status_filter == 'all' or not status_filter:
            bookings = Booking.objects(business_id__in=business_ids).order_by('-created_at')
        else:
            bookings = Booking.objects(
                business_id__in=business_ids,
                status=status_filter
            ).order_by('-created_at')
        
        return render_template(
            'owner/bookings.html',
            bookings=bookings,
            status_filter=status_filter,
            business_ids=business_ids
        )
        
    except Exception as e:
        flash(f'Error loading bookings: {str(e)}', 'danger')
        logger.error(f"Error loading bookings for owner {current_user.user_id}: {str(e)}")
        return redirect(url_for('owner_business.dashboard'))


@owner_business_bp.route('/booking/<booking_id>', methods=['GET'])
@business_owner_required
def view_booking_detail(booking_id):
    """
    View details of a specific booking.
    
    Accessible by: The owner of the business associated with the booking
    """
    try:
        booking = Booking.objects(booking_id=booking_id).first()
        
        if not booking:
            flash('Booking not found', 'danger')
            return redirect(url_for('owner_business.view_bookings'))
        
        # Verify ownership of the business
        business = Business.objects(business_id=booking.business_id).first()
        if not business or business.owner_id != current_user.user_id:
            flash('You are not authorized to view this booking', 'danger')
            return redirect(url_for('owner_business.view_bookings'))
        
        # Get related data
        from models.user import User
        from models.business import Service
        
        customer = User.objects(user_id=booking.customer_id).first()
        service = Service.objects(service_id=booking.service_id).first()
        
        return render_template(
            'owner/booking_detail.html',
            booking=booking,
            business=business,
            customer=customer,
            service=service
        )
        
    except Exception as e:
        flash(f'Error loading booking: {str(e)}', 'danger')
        logger.error(f"Error loading booking {booking_id}: {str(e)}")
        return redirect(url_for('owner_business.view_bookings'))


@owner_business_bp.route('/booking/<booking_id>/accept', methods=['POST'])
@business_owner_required
def accept_booking(booking_id):
    """
    Accept a booking request using the Command Pattern.
    
    Implementation of Command Pattern:
    - Creates an AcceptBookingCommand
    - Command verifies business ownership
    - Command updates booking status
    - Command triggers observer notifications
    
    Accessible by: The owner of the business (verified by decorator and command)
    """
    try:
        booking = Booking.objects(booking_id=booking_id).first()
        
        if not booking:
            flash('Booking not found', 'danger')
            return redirect(url_for('owner_business.view_bookings'))
        
        # Verify business ownership (double-check before command)
        business = Business.objects(business_id=booking.business_id).first()
        if not business or business.owner_id != current_user.user_id:
            flash('You are not authorized to accept this booking', 'danger')
            logger.warning(
                f"Unauthorized accept attempt by {current_user.user_id} on booking {booking_id}"
            )
            return redirect(url_for('owner_business.view_bookings'))
        
        # Execute Command Pattern
        try:
            command = AcceptBookingCommand(booking_id, current_user.user_id)
            result = command.execute()
            
            flash(
                f'Booking {booking_id} accepted successfully! Customer will be notified.',
                'success'
            )
            logger.info(
                f"Booking {booking_id} accepted by owner {current_user.user_id}. "
                f"Command: {command.get_description()}"
            )
            
            # Redirect back to booking detail or bookings list
            next_page = request.referrer or url_for('owner_business.view_bookings')
            return redirect(next_page)
            
        except ValueError as e:
            flash(f'Cannot accept booking: {str(e)}', 'danger')
            logger.error(f"Command execution error for booking {booking_id}: {str(e)}")
            return redirect(url_for('owner_business.view_booking_detail', booking_id=booking_id))
        
    except Exception as e:
        flash(f'Error accepting booking: {str(e)}', 'danger')
        logger.error(f"Unexpected error accepting booking {booking_id}: {str(e)}")
        return redirect(url_for('owner_business.view_bookings'))


@owner_business_bp.route('/booking/<booking_id>/reject', methods=['POST'])
@business_owner_required
def reject_booking(booking_id):
    """
    Reject a booking request using the Command Pattern.
    
    Implementation of Command Pattern:
    - Creates a RejectBookingCommand
    - Command verifies business ownership
    - Command updates booking status
    - Command triggers observer notifications
    
    Accessible by: The owner of the business (verified by decorator and command)
    """
    try:
        booking = Booking.objects(booking_id=booking_id).first()
        
        if not booking:
            flash('Booking not found', 'danger')
            return redirect(url_for('owner_business.view_bookings'))
        
        # Verify business ownership (double-check before command)
        business = Business.objects(business_id=booking.business_id).first()
        if not business or business.owner_id != current_user.user_id:
            flash('You are not authorized to reject this booking', 'danger')
            logger.warning(
                f"Unauthorized reject attempt by {current_user.user_id} on booking {booking_id}"
            )
            return redirect(url_for('owner_business.view_bookings'))
        
        # Get rejection reason from form (optional)
        reason = request.form.get('reason', '')
        
        # Execute Command Pattern
        try:
            command = RejectBookingCommand(booking_id, current_user.user_id, reason=reason)
            result = command.execute()
            
            flash(
                f'Booking {booking_id} rejected successfully! Customer will be notified.',
                'success'
            )
            logger.info(
                f"Booking {booking_id} rejected by owner {current_user.user_id}. "
                f"Reason: {reason or 'None provided'}. Command: {command.get_description()}"
            )
            
            # Redirect back to booking detail or bookings list
            next_page = request.referrer or url_for('owner_business.view_bookings')
            return redirect(next_page)
            
        except ValueError as e:
            flash(f'Cannot reject booking: {str(e)}', 'danger')
            logger.error(f"Command execution error for booking {booking_id}: {str(e)}")
            return redirect(url_for('owner_business.view_booking_detail', booking_id=booking_id))
        
    except Exception as e:
        flash(f'Error rejecting booking: {str(e)}', 'danger')
        logger.error(f"Unexpected error rejecting booking {booking_id}: {str(e)}")
        return redirect(url_for('owner_business.view_bookings'))


@owner_business_bp.route('/booking/<booking_id>/stats', methods=['GET'])
@business_owner_required
def booking_stats_api(booking_id):
    """
    API endpoint to get booking statistics (for AJAX calls).
    
    Returns JSON with booking details and status information.
    """
    try:
        booking = Booking.objects(booking_id=booking_id).first()
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Verify ownership
        business = Business.objects(business_id=booking.business_id).first()
        if not business or business.owner_id != current_user.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        from models.user import User
        customer = User.objects(user_id=booking.customer_id).first()
        
        return jsonify({
            'booking_id': booking.booking_id,
            'status': booking.status,
            'customer_name': customer.name if customer else 'Unknown',
            'customer_phone': customer.phone if customer else 'Unknown',
            'price': booking.price,
            'duration_minutes': booking.duration_minutes,
            'booking_time': booking.booking_time.isoformat(),
            'created_at': booking.created_at.isoformat(),
            'timestamps': booking.timestamps or {}
        })
        
    except Exception as e:
        logger.error(f"Error getting booking stats: {str(e)}")
        return jsonify({'error': str(e)}), 500
