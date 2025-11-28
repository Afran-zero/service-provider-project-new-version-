from flask import Flask
from flask_login import LoginManager, current_user, logout_user
from flask import session, request, redirect, url_for
import uuid
from config import Config
from database.singleton_db import SingletonDB
from views.home import home_bp
from views.auth import auth_bp
from views.booking import booking_bp
from views.business import business_bp
from views.admin import admin_bp
from views.owner_business import owner_business_bp
from patterns.observer_booking import setup_observers
from models.user import User
import os

app = Flask(
    __name__,
    template_folder='../frontend',   # point Flask to frontend templates
    static_folder='../frontend/static'
)

config = Config.get_instance()
app.config.from_object(config)
app.config.update({
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',  # consider 'Strict' if cross-site usage not needed
    'SESSION_COOKIE_SECURE': not getattr(config, 'DEBUG', False)  # secure only in non-debug
})

# In development, append a random suffix to SECRET_KEY each run so old cookies become invalid
if getattr(config, 'DEBUG', False):
    app.secret_key = f"{config.SECRET_KEY}_{uuid.uuid4().hex[:8]}"
else:
    app.secret_key = config.SECRET_KEY

# Boot identifier: used to detect server restarts and force session cleanup
app.config['APP_BOOT_ID'] = uuid.uuid4().hex

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    try:
        return User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return None

# Initialize DB (Singleton)
db = SingletonDB()

# Register blueprints
app.register_blueprint(home_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(booking_bp, url_prefix='/booking')
app.register_blueprint(business_bp, url_prefix='/business')
app.register_blueprint(admin_bp)
app.register_blueprint(owner_business_bp)  # Business Owner routes

# Setup observers for booking notifications
setup_observers()

# Context processor: inject primary business ID for business owner navigation
from models.business import Business

@app.context_processor
def inject_owner_business():
    if current_user.is_authenticated and getattr(current_user, 'role', None) == 'business_owner':
        business = Business.objects(owner_id=current_user.user_id).first()
        if business:
            return {'owner_primary_business_id': business.business_id}
    return {}


@app.before_request
def enforce_fresh_session_on_restart():
    """If the server was restarted, clear any existing session to ensure user must log in again.

    This prevents a previously authenticated user remaining logged in across restarts in development.
    """
    boot_id = session.get('APP_BOOT_ID')
    current_boot = app.config.get('APP_BOOT_ID')
    if boot_id is None:
        # First visit this boot cycle: stamp boot id
        session['APP_BOOT_ID'] = current_boot
    elif boot_id != current_boot:
        # Server reboot detected; clear session & logout
        session.clear()
        try:
            if current_user.is_authenticated:
                logout_user()
        except Exception:
            pass
        session['APP_BOOT_ID'] = current_boot

@app.before_request
def canonicalize_and_role_gate():
    """Security hardening: normalize // paths + gate business owners from public home.

    Implements Proxy pattern indirectly (home route also uses AccessProxy) but adds early
    interception for variants like //home or /// which Flask may still route.
    """
    try:
        # Collapse multiple leading slashes
        if '//' in request.path:
            import re
            cleaned = re.sub(r'/+', '/', request.path)
            if cleaned != request.path:
                return redirect(cleaned if cleaned != '' else '/')
        # Additional guard: if business owner hits root paths, redirect earlier
        if current_user.is_authenticated and getattr(current_user, 'role', None) == 'business_owner':
            if request.path in ['/', '/home']:
                # Defer to proxy decision: send to dashboard or create business
                from patterns.proxy_access import AccessProxy
                proxy = AccessProxy(current_user)
                return redirect(proxy.destination_for_owner())
    except Exception:
        # Fail closed by allowing normal flow if something unexpected occurs
        pass

if __name__ == '__main__':
    app.run(debug=True)