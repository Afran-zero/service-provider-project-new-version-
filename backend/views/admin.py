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
        recent = list(Booking.objects().order_by('-created_at').limit(10))
        # Enrich recent bookings with customer and business owner names
        enriched_recent = []
        for bk in recent:
            cust_name = None
            owner_name = None
            try:
                cust = User.objects.get(user_id=bk.customer_id)
                cust_name = cust.name
            except Exception:
                cust_name = None
            try:
                biz = Business.objects.get(business_id=bk.business_id)
                if getattr(biz, 'owner_id', None):
                    try:
                        owner = User.objects.get(user_id=biz.owner_id)
                        owner_name = owner.name
                    except Exception:
                        owner_name = getattr(biz, 'owner_name', None)
                else:
                    owner_name = getattr(biz, 'owner_name', None)
            except Exception:
                owner_name = None
            enriched_recent.append({
                'booking_id': bk.booking_id,
                'status': bk.status,
                'created_at': bk.created_at,
                'customer_id': bk.customer_id,
                'business_id': bk.business_id,
                'customer_name': cust_name,
                'owner_name': owner_name
            })
        recent_bookings = enriched_recent
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

    # Enrich with owner display name resolved from User where possible
    enriched = []
    for b in businesses_list:
        owner_display = None
        try:
            if getattr(b, 'owner_id', None):
                u = User.objects.get(user_id=b.owner_id)
                owner_display = u.name
            elif getattr(b, 'owner_name', None):
                owner_display = b.owner_name
        except Exception:
            owner_display = getattr(b, 'owner_name', None)
        # Attach attribute for template usage
        try:
            setattr(b, 'owner_display_name', owner_display)
        except Exception:
            pass
        enriched.append(b)
    
    categories = CategoryFactory.get_all_categories()
    
    return render_template('admin/businesses.html', 
                         businesses=enriched,
                         categories=categories,
                         selected_category=category,
                         search=search)


@admin_bp.route('/businesses/create', methods=['GET', 'POST'])
@admin_required
def create_business():
    """Admins are not allowed to create businesses via UI; redirect with message."""
    flash('Admins cannot create businesses. Please ask the business owner to create their own profile.', 'warning')
    return redirect(url_for('admin.businesses'))


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
        raw = Booking.objects(status=status).order_by('-created_at')
    else:
        raw = Booking.objects().order_by('-created_at')

    # Enrich with customer name, business name, and owner name
    bookings_list = []
    for bk in raw:
        cust_name = None
        biz_name = None
        owner_name = None
        payment_received = False
        payment_received_by = None
        payment_received_at = None
        try:
            cust = User.objects.get(user_id=bk.customer_id)
            cust_name = cust.name
        except Exception:
            pass
        try:
            biz = Business.objects.get(business_id=bk.business_id)
            biz_name = getattr(biz, 'name', None)
            if getattr(biz, 'owner_id', None):
                try:
                    owner = User.objects.get(user_id=biz.owner_id)
                    owner_name = owner.name
                except Exception:
                    owner_name = getattr(biz, 'owner_name', None)
            else:
                owner_name = getattr(biz, 'owner_name', None)
        except Exception:
            pass
        # Attach attributes dynamically for template rendering
        try:
            setattr(bk, 'customer_name', cust_name)
            setattr(bk, 'business_name', biz_name)
            setattr(bk, 'owner_name', owner_name)
            setattr(bk, 'payment_received', getattr(bk, 'payment_received', False))
            setattr(bk, 'payment_received_by', getattr(bk, 'payment_received_by', None))
            setattr(bk, 'payment_received_at', getattr(bk, 'payment_received_at', None))
        except Exception:
            pass
        bookings_list.append(bk)

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
        # Admin restriction: only allow setting to completed or cancelled
        if new_status not in ['completed', 'cancelled']:
            flash('Admins can only set a booking to Completed or Cancelled.', 'danger')
            return redirect(url_for('admin.booking_detail', booking_id=booking_id))
        # If admin is attempting to mark completed, require business owner to mark payment received first
        if new_status == 'completed' and not getattr(booking, 'payment_received', False):
            flash('Cannot mark Completed: payment has not been marked received by the business owner.', 'danger')
            return redirect(url_for('admin.booking_detail', booking_id=booking_id))
        # Update status using the model's update_status method
        booking.update_status(new_status)
        flash(f'Booking status updated to {new_status}', 'success')
    except Booking.DoesNotExist:
        flash('Booking not found', 'danger')
    
    return redirect(url_for('admin.booking_detail', booking_id=booking_id))


@admin_bp.route('/categories')
@admin_required
def categories():
    """List all categories"""
    categories_list = CategoryFactory.get_all_categories()

    # Determine which categories are DB-backed so we can allow deletion only for those
    try:
        from models.category import CategoryModel
        db_names = set([c.name for c in CategoryModel.objects()])
    except Exception:
        db_names = set()

    # Count businesses per category and attach id/count; icon comes from category.icon
    for category in categories_list:
        try:
            setattr(category, 'id', category.name)
            setattr(category, 'count', Business.objects(category=category.name).count())
            setattr(category, 'is_db', category.name in db_names)
        except Exception:
            setattr(category, 'id', getattr(category, 'name', None))
            setattr(category, 'count', 0)
            try:
                setattr(category, 'is_db', category.name in db_names)
            except Exception:
                setattr(category, 'is_db', False)

    return render_template('admin/categories.html', categories=categories_list)

@admin_bp.route('/categories/create', methods=['POST'])
@admin_required
def create_category():
    """Create a new service category (Factory + Repository).

    Uses Factory pattern at read time; persists via CategoryModel (Repository) so new
    categories appear dynamically across the app.
    """
    from models.category import CategoryModel
    import re
    display_name = (request.form.get('display_name') or '').strip()
    name = (request.form.get('name') or '').strip()
    description = (request.form.get('description') or '').strip()
    icon = (request.form.get('icon') or '').strip()
    tags_raw = (request.form.get('tags') or '').strip()
    if not display_name and not name:
        flash('Please provide at least a Display Name for the category.', 'danger')
        return redirect(url_for('admin.categories'))
    # Slugify name if not provided
    if not name:
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', display_name).strip().lower()
        slug = re.sub(r'\s+', '-', slug)
        name = slug or 'category'
    # Normalize icon: allow emoji; if starts with 'bi-' keep; if looks like bootstrap suffix keep as-is
    if icon.startswith('bi-'):
        icon = icon  # stored with bi- prefix; frontends will handle both
    # Parse tags
    tags = [t.strip() for t in tags_raw.split(',') if t.strip()] if tags_raw else []
    try:
        if CategoryModel.objects(name=name).first():
            flash('A category with this name already exists.', 'warning')
            return redirect(url_for('admin.categories'))
        CategoryModel(
            name=name,
            display_name=display_name or name,
            description=description,
            icon=icon,
            tags=tags
        ).save()
        flash(f'Category "{display_name or name}" created successfully.', 'success')
    except Exception as e:
        flash(f'Error creating category: {str(e)}', 'danger')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/<name>/delete', methods=['POST'])
@admin_required
def delete_category(name):
    """Delete a DB-backed category if unused by any business.

    Built-in categories are not deletable. If any Business references the
    category by name, deletion is blocked to avoid orphaned references.
    """
    try:
        from models.category import CategoryModel
        cat = CategoryModel.objects(name=name).first()
        if not cat:
            flash('This category is built-in or does not exist in the database and cannot be deleted.', 'warning')
            return redirect(url_for('admin.categories'))
        usage = Business.objects(category=name).count()
        if usage > 0:
            flash(f'Cannot delete "{name}": it is used by {usage} business(es).', 'danger')
            return redirect(url_for('admin.categories'))
        cat.delete()
        flash(f'Category "{name}" deleted successfully.', 'success')
    except Exception as e:
        flash(f'Error deleting category: {str(e)}', 'danger')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/categories/<name>/edit', methods=['POST'])
@admin_required
def edit_category(name):
    """Edit a DB-backed category's metadata (display_name, description, icon, tags)."""
    try:
        from models.category import CategoryModel
        cat = CategoryModel.objects(name=name).first()
        if not cat:
            flash('Built-in categories cannot be edited here.', 'warning')
            return redirect(url_for('admin.categories'))
        display_name = (request.form.get('display_name') or '').strip()
        description = (request.form.get('description') or '').strip()
        icon = (request.form.get('icon') or '').strip()
        tags_raw = (request.form.get('tags') or '').strip()
        tags = [t.strip() for t in tags_raw.split(',') if t.strip()] if tags_raw else []
        if display_name:
            cat.display_name = display_name
        cat.description = description
        cat.icon = icon
        cat.tags = tags
        cat.save()
        flash(f'Category "{cat.name}" updated successfully.', 'success')
    except Exception as e:
        flash(f'Error updating category: {str(e)}', 'danger')
    return redirect(url_for('admin.categories'))


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
