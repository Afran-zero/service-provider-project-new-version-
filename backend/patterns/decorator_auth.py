from flask import redirect, url_for, flash
from flask_login import current_user, LoginManager
from functools import wraps

login_manager = LoginManager()

def login_required(f):
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_view


def business_owner_required(f):
    """
    Decorator to restrict access to Business Owners only.
    
    Implements the Decorator Design Pattern to add authorization checks
    without modifying the route handler directly.
    
    Usage:
        @app.route('/business/dashboard')
        @business_owner_required
        def owner_dashboard():
            # Only accessible by business owners
            pass
    
    Returns:
        - Redirect to login if user not authenticated
        - Redirect to home with warning if user is not a business owner
    """
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in first.", "warning")
            return redirect(url_for('auth.login'))
        
        # Check if user has business_owner role
        if not hasattr(current_user, 'role') or current_user.role != 'business_owner':
            flash("Access denied. Only business owners can access this page.", "danger")
            return redirect(url_for('home.index'))
        
        return f(*args, **kwargs)
    return decorated_view


def admin_required(f):
    """
    Decorator to restrict access to Admins only.
    
    Implements the Decorator Design Pattern for admin-only routes.
    
    Usage:
        @app.route('/admin/dashboard')
        @admin_required
        def admin_dashboard():
            # Only accessible by admins
            pass
    """
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in first.", "warning")
            return redirect(url_for('auth.login'))
        
        # Check if user has admin role
        if not hasattr(current_user, 'role') or current_user.role != 'admin':
            flash("Access denied. Only administrators can access this page.", "danger")
            return redirect(url_for('home.index'))
        
        return f(*args, **kwargs)
    return decorated_view


def customer_required(f):
    """
    Decorator to restrict access to Customers only.
    
    Implements the Decorator Design Pattern for customer-only routes.
    
    Usage:
        @app.route('/booking/my-bookings')
        @customer_required
        def my_bookings():
            # Only accessible by customers
            pass
    """
    @wraps(f)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in first.", "warning")
            return redirect(url_for('auth.login'))
        
        # Check if user has customer role
        if not hasattr(current_user, 'role') or current_user.role != 'customer':
            flash("This page is only for customers.", "warning")
            return redirect(url_for('home.index'))
        
        return f(*args, **kwargs)
    return decorated_view
