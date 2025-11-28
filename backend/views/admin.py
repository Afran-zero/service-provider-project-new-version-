# views/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from models.user import User
from models.business import Business, Service
from models.booking import Booking
from controllers.business_controller import get_all_businesses
from controllers.booking_controller import get_bookings_by_customer
from patterns.factory_category import CategoryFactory
from patterns.builder_business import BusinessBuilder
import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='../../frontend')

# Hardcoded admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in as admin', 'danger')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
def index():
    """Base admin route — redirect to dashboard when logged in, otherwise to login."""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.login'))


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'GET':
        return render_template('admin/login.html')
    
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        session['admin_username'] = username
        flash('Welcome, Admin!', 'success')
        return redirect(url_for('admin.dashboard'))
    else:
        flash('Invalid credentials', 'danger')
        return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin.login'))


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    # Get statistics with error handling for index issues
    try:
        total_users = User.objects.count()
        # Convert to list to catch field errors before template rendering
        recent_users = list(User.objects().order_by('-created_at').limit(10))
    except Exception as e:
        print(f"Warning: User query failed: {e}")
        total_users = 0
        recent_users = []
    
    try:
        total_businesses = Business.objects.count()
        active_businesses = Business.objects(is_active=True).count()
    except Exception as e:
        print(f"Warning: Business query failed: {e}")
        total_businesses = 0
        active_businesses = 0
    
    try:
        total_bookings = Booking.objects.count()
        pending_bookings = Booking.objects(status='pending').count()
        accepted_bookings = Booking.objects(status='accepted').count()
        completed_bookings = Booking.objects(status='completed').count()
        cancelled_bookings = Booking.objects(status='cancelled').count()
        # Convert to list to catch errors before template rendering
        recent_bookings = list(Booking.objects().order_by('-created_at').limit(10))
    except Exception as e:
        print(f"Warning: Booking query failed: {e}")
        total_bookings = 0
        pending_bookings = 0
        accepted_bookings = 0
        completed_bookings = 0
        cancelled_bookings = 0
        recent_bookings = []
    
    stats = {
        'total_users': total_users,
        'total_businesses': total_businesses,
        'total_bookings': total_bookings,
        'active_businesses': active_businesses,
        'pending_bookings': pending_bookings,
        'accepted_bookings': accepted_bookings,
        'completed_bookings': completed_bookings,
        'cancelled_bookings': cancelled_bookings
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_bookings=recent_bookings,
                         recent_users=recent_users)


@admin_bp.route('/users')
@admin_required
def users():
    """List all users"""
    search = request.args.get('search', '')
    
    if search:
        users_list = User.objects(name__icontains=search)
    else:
        users_list = User.objects().order_by('-created_at')
    
    return render_template('admin/users.html', users=users_list, search=search)


@admin_bp.route('/users/<user_id>')
@admin_required
def user_detail(user_id):
    """View user details"""
    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        flash('User not found', 'danger')
        return redirect(url_for('admin.users'))
    
    # Get user's bookings
    bookings = get_bookings_by_customer(user_id)
    
    # Get user's businesses if they own any
    businesses = Business.objects(owner_id=user_id)
    
    return render_template('admin/user_detail.html', 
                         user=user, 
                         bookings=bookings,
                         businesses=businesses)


@admin_bp.route('/users/<user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """Activate/deactivate a user"""
    try:
        user = User.objects.get(user_id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User {user.name} {status} successfully', 'success')
    except User.DoesNotExist:
        flash('User not found', 'danger')
    
    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/businesses')
@admin_required
def businesses():
    """List all businesses"""
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = {}
    if category:
        query['category'] = category
    if search:
        query['name__icontains'] = search
    
    if query:
        businesses_list = Business.objects(**query).order_by('-created_at')
    else:
        businesses_list = Business.objects().order_by('-created_at')
    
    categories = CategoryFactory.get_all_categories()
    
    return render_template('admin/businesses.html', 
                         businesses=businesses_list,
                         categories=categories,
                         selected_category=category,
                         search=search)


@admin_bp.route('/businesses/create', methods=['GET', 'POST'])
@admin_required
def create_business():
    """Create a new business using the Builder pattern"""
    if request.method == 'GET':
        # Show create business form
        categories = CategoryFactory.get_all_categories()
        return render_template('admin/create_business.html', categories=categories)
    
    # POST: Create business from form data
    try:
        # Use BusinessBuilder to construct and save the business
        builder = (BusinessBuilder()
                   .set_name(request.form.get('name'))
                   .set_email(request.form.get('email'))
                   .set_phone(request.form.get('phone'))
                   .set_street_house(request.form.get('street_house'))
                   .set_city(request.form.get('city'))
                   .set_district(request.form.get('district'))
                   .set_category(request.form.get('category')))
        
        # Optional fields
        if request.form.get('description'):
            builder.set_description(request.form.get('description'))
        if request.form.get('owner_name'):
            builder.set_owner_name(request.form.get('owner_name'))
        
        # Build and save
        business = builder.build_and_save()

        # Create any services provided in the form
        try:
            service_names = request.form.getlist('service_name[]')
            service_prices = request.form.getlist('service_price[]')
            service_durations = request.form.getlist('service_duration[]')
            service_descriptions = request.form.getlist('service_description[]')

            for i, name in enumerate(service_names):
                if not name or not name.strip():
                    continue
                price = 0.0
                duration = 60
                description = None
                try:
                    if i < len(service_prices) and service_prices[i].strip():
                        price = float(service_prices[i])
                except Exception:
                    price = 0.0
                try:
                    if i < len(service_durations) and service_durations[i].strip():
                        duration = int(service_durations[i])
                except Exception:
                    duration = 60
                if i < len(service_descriptions) and service_descriptions[i].strip():
                    description = service_descriptions[i].strip()

                svc = Service(
                    business_id=business.business_id,
                    name=name.strip(),
                    description=description,
                    price=price,
                    duration_minutes=duration
                )
                svc.save()
        except Exception as e:
            # Non-fatal: log and continue; show flash so admin knows
            flash(f'Warning: some services could not be saved: {str(e)}', 'danger')
        
        flash(f'Business "{business.name}" created successfully!', 'success')
        return redirect(url_for('admin.business_detail', business_id=business.business_id))
    
    except ValueError as e:
        # Validation error from builder
        flash(f'Error creating business: {str(e)}', 'danger')
        categories = CategoryFactory.get_all_categories()
        return render_template('admin/create_business.html', 
                             categories=categories,
                             form_data=request.form.to_dict()), 400
    except Exception as e:
        # Other unexpected errors
        flash(f'Unexpected error: {str(e)}', 'danger')
        categories = CategoryFactory.get_all_categories()
        return render_template('admin/create_business.html', categories=categories), 500


@admin_bp.route('/businesses/<business_id>')
@admin_required
def business_detail(business_id):
    """View business details"""
    try:
        business = Business.objects.get(business_id=business_id)
    except Business.DoesNotExist:
        flash('Business not found', 'danger')
        return redirect(url_for('admin.businesses'))
    
    # Get business owner
    try:
        owner = User.objects.get(user_id=business.owner_id)
    except User.DoesNotExist:
        owner = None
    
    # Get business bookings
    bookings = Booking.objects(business_id=business_id).order_by('-created_at')
    
    return render_template('admin/business_detail.html',
                         business=business,
                         owner=owner,
                         bookings=bookings)


@admin_bp.route('/businesses/<business_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_business_status(business_id):
    """Activate/deactivate a business"""
    try:
        business = Business.objects.get(business_id=business_id)
        business.is_active = not business.is_active
        business.save()
        
        status = 'activated' if business.is_active else 'deactivated'
        flash(f'Business {business.name} {status} successfully', 'success')
    except Business.DoesNotExist:
        flash('Business not found', 'danger')
    
    return redirect(url_for('admin.business_detail', business_id=business_id))


@admin_bp.route('/bookings')
@admin_required
def bookings():
    """List all bookings"""
    status = request.args.get('status', '')
    
    if status:
        bookings_list = Booking.objects(status=status).order_by('-created_at')
    else:
        bookings_list = Booking.objects().order_by('-created_at')
    
    return render_template('admin/bookings.html', 
                         bookings=bookings_list,
                         selected_status=status)


@admin_bp.route('/bookings/<booking_id>')
@admin_required
def booking_detail(booking_id):
    """View booking details"""
    try:
        booking = Booking.objects.get(booking_id=booking_id)
    except Booking.DoesNotExist:
        flash('Booking not found', 'danger')
        return redirect(url_for('admin.bookings'))
    
    # Get customer info
    try:
        customer = User.objects.get(user_id=booking.customer_id)
    except User.DoesNotExist:
        customer = None
    
    # Get business info
    try:
        business = Business.objects.get(business_id=booking.business_id)
    except Business.DoesNotExist:
        business = None
    
    return render_template('admin/booking_detail.html',
                         booking=booking,
                         customer=customer,
                         business=business)


@admin_bp.route('/bookings/<booking_id>/update-status', methods=['POST'])
@admin_required
def update_booking_status(booking_id):
    """Update booking status"""
    try:
        booking = Booking.objects.get(booking_id=booking_id)
        new_status = request.form.get('status')
        
        if new_status in ['requested', 'accepted', 'rejected', 'completed', 'cancelled']:
            # Update status using the model's update_status method
            booking.update_status(new_status)
            
            flash(f'Booking status updated to {new_status}', 'success')
        else:
            flash('Invalid status', 'danger')
    except Booking.DoesNotExist:
        flash('Booking not found', 'danger')
    
    return redirect(url_for('admin.booking_detail', booking_id=booking_id))


@admin_bp.route('/categories')
@admin_required
def categories():
    """List all categories"""
    categories_list = CategoryFactory.get_all_categories()
    
    # Count businesses per category and add Bootstrap icon class
    for category in categories_list:
        try:
            setattr(category, 'id', category.name)
            setattr(category, 'count', Business.objects(category=category.name).count())
            # Add Bootstrap icon class (e.g., 'bi-broom') for template rendering
            setattr(category, 'bootstrap_icon', CategoryFactory.get_bootstrap_icon(category.name))
        except Exception:
            # Defensive fallback: ensure attributes exist even if query fails
            setattr(category, 'id', getattr(category, 'name', None))
            setattr(category, 'count', 0)
            setattr(category, 'bootstrap_icon', 'bi-grid')
    
    return render_template('admin/categories.html', categories=categories_list)


@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """API endpoint for dashboard statistics"""
    stats = {
        'users': {
            'total': User.objects.count(),
            'active': User.objects(is_active=True).count()
        },
        'businesses': {
            'total': Business.objects.count(),
            'active': Business.objects(is_active=True).count()
        },
        'bookings': {
            'total': Booking.objects.count(),
            'pending': Booking.objects(status='pending').count(),
            'accepted': Booking.objects(status='accepted').count(),
            'completed': Booking.objects(status='completed').count(),
            'cancelled': Booking.objects(status='cancelled').count()
        }
    }
    
    return jsonify(stats)
