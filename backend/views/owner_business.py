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


def is_ajax_request(req=None):
    """Return True if the request appears to be an AJAX/JS fetch requesting JSON."""
    if req is None:
        from flask import request as _r
        req = _r
    # Old Flask had request.is_xhr; replace with header check
    try:
        if req.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return True
    except Exception:
        pass
    # Also treat JSON requests or Accept: application/json as AJAX
    try:
        if req.is_json:
            return True
    except Exception:
        pass
    try:
        accept = req.headers.get('Accept', '')
        if 'application/json' in accept:
            return True
    except Exception:
        pass
    return False


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
        # Enrich pending bookings with service and customer lookups for display
        from models.user import User
        from models.business import Service

        service_ids = [b.service_id for b in pending_bookings]
        customer_ids = [b.customer_id for b in pending_bookings]

        services = {s.service_id: s for s in Service.objects(service_id__in=service_ids)}
        customers = {u.user_id: u for u in User.objects(user_id__in=customer_ids)}
        
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
            stats=stats,
            services_map=services,
            customers_map=customers
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
        from patterns.factory_category import CategoryFactory
        categories = CategoryFactory.get_all_categories()
        return render_template('owner/create_business.html', categories=categories)
    
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


@owner_business_bp.route('/business/<business_id>/gallery/add', methods=['POST'])
@business_owner_required
def add_gallery(business_id):
    """Upload additional gallery images for this business (owner only)."""
    try:
        business = business_controller.get_business(business_id)
        if not business or business.owner_id != current_user.user_id:
            flash('Unauthorized', 'danger')
            return redirect(url_for('owner_business.view_business', business_id=business_id))
        gallery_pics = request.files.getlist('gallery_pics')
        added = business_controller.add_gallery_images(business_id, gallery_pics)
        if added:
            flash(f'Added {len(added)} image(s) to gallery.', 'success')
        else:
            flash('No images were added.', 'warning')
    except Exception as e:
        flash(f'Error adding gallery images: {str(e)}', 'danger')
    return redirect(url_for('owner_business.view_business', business_id=business_id))


@owner_business_bp.route('/business/<business_id>/gallery/delete', methods=['POST'])
@business_owner_required
def delete_gallery(business_id):
    """Delete a gallery image for this business (owner only)."""
    try:
        business = business_controller.get_business(business_id)
        if not business or business.owner_id != current_user.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        gallery_url = request.form.get('gallery_url') or (request.json.get('gallery_url') if request.is_json else None)
        if not gallery_url:
            return jsonify({'error': 'gallery_url required'}), 400
        updated = business_controller.delete_gallery_image(business_id, gallery_url)
        if not updated:
            return jsonify({'error': 'Image not found'}), 404
        return jsonify({'success': True, 'gallery_url': gallery_url}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
            
        # Enrich bookings with Service and Customer data
        from models.user import User
        from models.business import Service
        
        # Collect IDs
        service_ids = [b.service_id for b in bookings]
        customer_ids = [b.customer_id for b in bookings]
        
        # Fetch objects
        services = {s.service_id: s for s in Service.objects(service_id__in=service_ids)}
        customers = {u.user_id: u for u in User.objects(user_id__in=customer_ids)}
        
        # Create a list of enriched booking objects (or just pass the lookups)
        # Passing lookups is cleaner for the template
        
        return render_template(
            'owner/bookings.html',
            bookings=bookings,
            status_filter=status_filter,
            business_ids=business_ids,
            services_map=services,
            customers_map=customers
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
        try:
            booking = Booking.objects.get(booking_id=booking_id)
        except Booking.DoesNotExist:
            booking = None
        
        if not booking:
            flash('Booking not found', 'danger')
            return redirect(url_for('owner_business.view_bookings'))
        
        # Verify ownership of the business
        try:
            business = Business.objects.get(business_id=booking.business_id)
        except Business.DoesNotExist:
            business = None
        if not business or business.owner_id != current_user.user_id:
            flash('You are not authorized to view this booking', 'danger')
            return redirect(url_for('owner_business.view_bookings'))
        
        # Get related data
        from models.user import User
        from models.business import Service
        
        try:
            customer = User.objects.get(user_id=booking.customer_id)
        except User.DoesNotExist:
            customer = None
        try:
            service = Service.objects.get(service_id=booking.service_id)
        except Service.DoesNotExist:
            service = None
        
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
        try:
            booking = Booking.objects.get(booking_id=booking_id)
        except Booking.DoesNotExist:
            booking = None
        
        if not booking:
            if is_ajax_request(request):
                return jsonify({'success': False, 'error': 'Booking not found'}), 404
            flash('Booking not found', 'danger')
            return redirect(url_for('owner_business.view_bookings'))
        
        # Verify business ownership (double-check before command)
        try:
            business = Business.objects.get(business_id=booking.business_id)
        except Business.DoesNotExist:
            business = None
        if not business or business.owner_id != current_user.user_id:
            if is_ajax_request(request):
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403
            flash('You are not authorized to accept this booking', 'danger')
            logger.warning(
                f"Unauthorized accept attempt by {current_user.user_id} on booking {booking_id}"
            )
            return redirect(url_for('owner_business.view_bookings'))
        
        # Execute Command Pattern
        try:
            command = AcceptBookingCommand(booking_id, current_user.user_id)
            result = command.execute()
            
            logger.info(
                f"Booking {booking_id} accepted by owner {current_user.user_id}. "
                f"Command: {command.get_description()}"
            )
            
            # Check if AJAX request
            if is_ajax_request(request):
                return jsonify({
                    'success': True,
                    'message': 'Booking accepted successfully! Customer will be notified.',
                    'booking_id': booking_id,
                    'status': result.status,
                    'redirect_url': url_for('owner_business.view_bookings')
                })
            
            flash(
                f'Booking {booking_id} accepted successfully! Customer will be notified.',
                'success'
            )
            
            # Redirect back to booking detail or bookings list
            next_page = request.referrer or url_for('owner_business.view_bookings')
            return redirect(next_page)
            
        except ValueError as e:
            if request.is_xhr or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': str(e)}), 400
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
    logger.info(f"=== REJECT BOOKING START: {booking_id} ===")
    
    try:
        # Step 1: Fetch booking
        logger.info(f"Step 1: Fetching booking {booking_id}")
        try:
            booking = Booking.objects.get(booking_id=booking_id)
            logger.info(f"  ✓ Booking found: status={booking.status}")
        except Booking.DoesNotExist:
            booking = None
            logger.warning(f"  ✗ Booking not found")
        
        if not booking:
            logger.warning(f"Booking {booking_id} not found, redirecting")
            if is_ajax_request(request):
                return jsonify({'success': False, 'error': 'Booking not found'}), 404
            flash('Booking not found', 'danger')
            return redirect(url_for('owner_business.view_bookings'))
        
        # Step 2: Verify business ownership
        logger.info(f"Step 2: Verifying business ownership for {booking.business_id}")
        try:
            business = Business.objects.get(business_id=booking.business_id)
            logger.info(f"  ✓ Business found: owner={business.owner_id}, current_user={current_user.user_id}")
        except Business.DoesNotExist:
            business = None
            logger.warning(f"  ✗ Business not found")
        
        if not business or business.owner_id != current_user.user_id:
            logger.warning(f"Unauthorized reject attempt by {current_user.user_id} on booking {booking_id}")
            if is_ajax_request(request):
                return jsonify({'success': False, 'error': 'Unauthorized'}), 403
            flash('You are not authorized to reject this booking', 'danger')
            return redirect(url_for('owner_business.view_bookings'))
        
        # Step 3: Get rejection reason from form
        logger.info(f"Step 3: Getting rejection reason from form")
        reason = request.form.get('reason', '')
        logger.info(f"  ✓ Reason: {reason or '(none)'}")
        
        # Step 4: Execute Command Pattern
        logger.info(f"Step 4: Creating and executing RejectBookingCommand")
        try:
            command = RejectBookingCommand(booking_id, current_user.user_id, reason=reason)
            logger.info(f"  ✓ Command created, executing...")
            result = command.execute()
            logger.info(f"  ✓ Command executed successfully, new status={result.status}")
            
            logger.info(f"Booking {booking_id} rejected successfully by owner {current_user.user_id}")
            
            # Step 5: Check if AJAX request
            if is_ajax_request(request):
                logger.info(f"Step 5: AJAX request detected, returning JSON")
                return jsonify({
                    'success': True,
                    'message': 'Booking rejected successfully!',
                    'booking_id': booking_id,
                    'status': result.status,
                    'redirect_url': url_for('owner_business.view_booking_detail', booking_id=booking_id)
                })
            
            # Step 5: Flash success message (after command completes)
            logger.info(f"Step 5: Flashing success message")
            flash(f'Booking rejected successfully!', 'success')
            
            # Step 6: Redirect
            logger.info(f"Step 6: Redirecting")
            next_page = request.referrer or url_for('owner_business.view_booking_detail', booking_id=booking_id)
            logger.info(f"  ✓ Redirecting to {next_page}")
            return redirect(next_page)
            
        except ValueError as e:
            logger.error(f"ValueError in command execution: {str(e)}")
            if is_ajax_request(request):
                return jsonify({'success': False, 'error': str(e)}), 400
            flash(f'Cannot reject booking: {str(e)}', 'danger')
            return redirect(url_for('owner_business.view_booking_detail', booking_id=booking_id))
        except Exception as e:
            logger.error(f"Unexpected error in command execution: {str(e)}", exc_info=True)
            if is_ajax_request(request):
                return jsonify({'success': False, 'error': str(e)}), 500
            flash(f'Error executing command: {str(e)}', 'danger')
            return redirect(url_for('owner_business.view_booking_detail', booking_id=booking_id))
        
    except Exception as e:
        logger.error(f"Outer exception in reject_booking: {str(e)}", exc_info=True)
        if is_ajax_request(request):
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error rejecting booking: {str(e)}', 'danger')
        return redirect(url_for('owner_business.view_bookings'))
    finally:
        logger.info(f"=== REJECT BOOKING END: {booking_id} ===")



@owner_business_bp.route('/booking/<booking_id>/mark-payment', methods=['POST'])
@business_owner_required
def mark_payment_received(booking_id):
    """Mark a booking as payment received (prototype) by the business owner.

    This toggles the `payment_received` flag to True and records timestamp and owner id.
    """
    try:
        try:
            booking = Booking.objects.get(booking_id=booking_id)
        except Booking.DoesNotExist:
            return jsonify({'success': False, 'error': 'Booking not found'}), 404

        # Verify owner owns the business for this booking
        try:
            business = Business.objects.get(business_id=booking.business_id)
        except Business.DoesNotExist:
            return jsonify({'success': False, 'error': 'Business not found'}), 404

        if business.owner_id != current_user.user_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403

        # Mark payment received
        import datetime
        booking.payment_received = True
        booking.payment_received_at = datetime.datetime.utcnow()
        booking.payment_received_by = current_user.user_id
        booking.updated_at = datetime.datetime.utcnow()
        booking.save()

        # Audit log entry
        try:
            from models.audit_log import AuditLog
            AuditLog(
                action='payment_marked_received',
                actor_id=current_user.user_id,
                actor_role='business_owner',
                target_type='booking',
                target_id=booking.booking_id,
                details={
                    'business_id': booking.business_id,
                    'amount': booking.price,
                }
            ).save()
        except Exception:
            logger.exception('Failed to write audit log for payment marking')

        return jsonify({'success': True, 'message': 'Payment marked as received'}), 200

    except Exception as e:
        logger.error(f"Error marking payment for booking {booking_id}: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@owner_business_bp.route('/booking/<booking_id>/stats', methods=['GET'])
@business_owner_required
def booking_stats_api(booking_id):
    """
    API endpoint to get booking statistics (for AJAX calls).
    
    Returns JSON with booking details and status information.
    """
    try:
        try:
            booking = Booking.objects.get(booking_id=booking_id)
        except Booking.DoesNotExist:
            booking = None
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        # Verify ownership
        try:
            business = Business.objects.get(business_id=booking.business_id)
        except Business.DoesNotExist:
            business = None
        if not business or business.owner_id != current_user.user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        from models.user import User
        try:
            customer = User.objects.get(user_id=booking.customer_id)
        except User.DoesNotExist:
            customer = None
        
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
