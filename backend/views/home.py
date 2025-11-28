# routes/home.py
from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from controllers.user_controller import update_profile, get_user_profile
from controllers.business_controller import get_all_businesses, get_business_by_id
from models.user import User
from models.business import Business
from patterns.factory_category import CategoryFactory
from models.business import Service

# How many categories to show on the home page
MAX_CATEGORIES_DISPLAY = 5

home_bp = Blueprint('home', __name__, template_folder='../../frontend')

@home_bp.route('/')
@home_bp.route('/home')
def index():
    """Home page - marketing landing (proxied for business owners)."""
    # Use Proxy pattern to gate business owners away from public home.
    from patterns.proxy_access import AccessProxy

    def _render_home():
        categories = CategoryFactory.get_all_categories()
        businesses = get_all_businesses()
        raw_popular = businesses[:6] if businesses else []
        enriched_popular = []
        from models.user import User  # local import to avoid circular issues at module load
        from utils import get_cloudinary_url
        for b in raw_popular:
            original = getattr(b, 'profile_pic_url', None)
            if not original and getattr(b, 'owner_id', None):
                try:
                    owner = User.objects.get(user_id=b.owner_id)
                    if owner and getattr(owner, 'profile_pic_url', None):
                        original = owner.profile_pic_url
                except Exception:
                    pass
            full_img = None
            lazy_img = None
            if original:
                try:
                    full_img = get_cloudinary_url(original, width=600, height=250, quality="auto:good") or original
                    lazy_img = get_cloudinary_url(original, width=40, height=20, quality="auto:low", lazy=True) or original
                except Exception:
                    full_img = original
                    lazy_img = original
            address_parts = [p for p in [getattr(b, 'street_house', ''), getattr(b, 'city', ''), getattr(b, 'district', '')] if p]
            address = ', '.join(address_parts)
            enriched_popular.append({
                'id': getattr(b, 'business_id', None),
                'business_name': getattr(b, 'name', ''),
                'profile_image': original,
                'profile_image_full': full_img,
                'profile_image_lazy': lazy_img,
                'address': address,
                'phone': getattr(b, 'phone', ''),
                'category': getattr(b, 'category', '')
            })
        return render_template('Home/landing.html', categories=categories, popular_businesses=enriched_popular)

    proxy = AccessProxy(current_user)
    return proxy.render_or_redirect_home(_render_home)
@home_bp.route('/category/')
def category_root():
    """Redirect bare `/category/` requests back to home to avoid 404s."""
    return redirect(url_for('home.index'))


@home_bp.route('/services')
def services_list():
    """Browse all businesses with search and filter options"""
    # Get filter parameters
    category = request.args.get('category', '')
    city = request.args.get('city', '')
    search_query = request.args.get('q', '')
    
    # Get all businesses
    all_businesses = get_all_businesses()
    
    # Apply filters
    filtered_businesses = all_businesses
    
    if category:
        filtered_businesses = [b for b in filtered_businesses if b.category == category]
    
    if city:
        filtered_businesses = [b for b in filtered_businesses if b.city.lower() == city.lower()]
    
    if search_query:
        query_lower = search_query.lower()
        # Search by business name, category, and location (city/district). Do not search by service names.
        filtered_businesses = [
            b for b in filtered_businesses
            if (
                query_lower in b.name.lower()
                or (getattr(b, 'category', '') and query_lower in getattr(b, 'category', '').lower())
                or query_lower in b.city.lower()
                or query_lower in b.district.lower()
            )
        ]
    
    # Get all categories for filter dropdown
    categories = CategoryFactory.get_all_categories()
    
    # Get unique cities for filter dropdown
    cities = sorted(list(set(b.city for b in all_businesses)))
    
    return render_template('services.html',
                         businesses=filtered_businesses,
                         categories=categories,
                         cities=cities,
                         selected_category=category,
                         selected_city=city,
                         search_query=search_query)
@home_bp.route('/category/<category_id>')
def category_list(category_id):
    """Show all businesses in a specific category"""
    category = CategoryFactory.get_category(category_id)
    
    if not category:
        flash('Category not found', 'danger')
        return redirect(url_for('home.index'))
    
    # Filter businesses by category (match against category.name which is the ID)
    all_businesses = get_all_businesses()
    filtered_businesses = [b for b in all_businesses if b.category == category_id]

    # Enrich with fallback + lazy/full image URLs (reuse logic similar to home.index)
    from models.user import User  # local import to avoid circular issues
    from utils import get_cloudinary_url
    enriched = []
    for b in filtered_businesses:
        original = getattr(b, 'profile_pic_url', None)
        if not original and getattr(b, 'owner_id', None):
            try:
                owner = User.objects.get(user_id=b.owner_id)
                if owner and getattr(owner, 'profile_pic_url', None):
                    original = owner.profile_pic_url
            except Exception:
                pass
        full_img = None
        lazy_img = None
        if original:
            try:
                full_img = get_cloudinary_url(original, width=600, height=250, quality="auto:good") or original
                lazy_img = get_cloudinary_url(original, width=40, height=20, quality="auto:low", lazy=True) or original
            except Exception:
                full_img = original
                lazy_img = original
        address_parts = [p for p in [getattr(b, 'street_house', ''), getattr(b, 'city', ''), getattr(b, 'district', '')] if p]
        address = ', '.join(address_parts)
        enriched.append({
            'id': getattr(b, 'business_id', None),
            'business_name': getattr(b, 'name', ''),
            'profile_image': original,
            'profile_image_full': full_img,
            'profile_image_lazy': lazy_img,
            'address': address,
            'phone': getattr(b, 'phone', ''),
            'category': getattr(b, 'category', '')
        })

    return render_template('category_list.html',
                         category_name=category.display_name,
                         businesses=enriched)


@home_bp.route('/my-bookings')
@login_required
def my_bookings():
    """Show user's bookings with active and completed tabs"""
    from controllers.booking_controller import get_user_bookings
    
    bookings = get_user_bookings(current_user.user_id)
    # Enrich bookings with service and business details and format date/time
    active_bookings = []
    completed_bookings = []
    from controllers import business_controller

    for b in bookings:
        service = business_controller.get_service(b.service_id)
        business = business_controller.get_business(b.business_id)

        booking_date = ''
        booking_time = ''
        try:
            dt = b.booking_time
            if isinstance(dt, str):
                # try parsing
                import datetime as _dt
                dt = _dt.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
            booking_date = dt.strftime("%Y-%m-%d")
            booking_time = dt.strftime("%H:%M:%S")
        except Exception:
            booking_date = ''
            booking_time = ''

        item = {
            'id': getattr(b, 'booking_id', None) or getattr(b, 'id', None),
            'service_name': service.name if service else '',
            'business_name': business.name if business else '',
            'business_phone': business.phone if business else '',
            'booking_date': booking_date,
            'booking_time': booking_time,
            'status': b.status
        }

        if b.status in ['requested', 'accepted']:
            active_bookings.append(item)
        else:
            completed_bookings.append(item)

    return render_template('my_bookings.html',
                         active_bookings=active_bookings,
                         completed_bookings=completed_bookings)


@home_bp.route('/search')
def search():
    """Search for businesses and services"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('home.index'))
    
    # Search in businesses and categories
    all_businesses = get_all_businesses()
    
    # Simple text search in business name, category, and fields
    results = []
    for b in all_businesses:
        search_fields = [
            b.name.lower(),
            b.category.lower(),
            b.city.lower(),
            b.district.lower(),
            b.description.lower() if b.description else ''
        ]
        if any(query.lower() in field for field in search_fields):
            results.append(b)
    
    return render_template('category_list.html',
                         category_name=f'Search Results for "{query}"',
                         businesses=results)


@home_bp.route('/dashboard')
def dashboard():
    """Dashboard - requires login"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
   
    return render_template('dashboard.html', user_name=current_user.name)


@home_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    """View user profile with optimized lazy-loaded images"""
    # Use Flask-Login's current_user
    user_data = get_user_profile(current_user.user_id, thumbnail_size=150)
    if not user_data:
        flash('User not found', 'danger')
        return redirect(url_for('home.index'))
    
    return render_template('profile.html', user=user_data)


@home_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile_route():
    """Update user profile with optional profile picture upload"""
    user_id = current_user.user_id
    
    # Get form data
    data = {
        'name': request.form.get('name'),
        'phone': request.form.get('phone'),
        'street_house': request.form.get('street_house'),
        'city': request.form.get('city'),
        'district': request.form.get('district')
    }
    
    # Get profile picture file if uploaded
    profile_picture = request.files.get('profile_picture')
    
    # Update profile with Cloudinary upload
    user, error = update_profile(user_id, data, profile_picture)
    
    if error:
        flash(error, 'danger')
        return redirect(url_for('home.profile'))
    else:
        flash('Profile updated successfully!', 'success')

    # Role-aware post-update redirect: business owners go to dashboard or business
    if getattr(current_user, 'role', None) == 'business_owner':
        from models.business import Business
        biz = Business.objects(owner_id=current_user.user_id).first()
        if biz:
            return redirect(url_for('owner_business.view_business', business_id=biz.business_id))
        return redirect(url_for('owner_business.dashboard'))

    return redirect(url_for('home.profile'))


@home_bp.route('/about')
def about():
    """About Us page"""
    return render_template('about.html')