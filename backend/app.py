from flask import Flask
from flask_login import LoginManager, current_user, logout_user
from flask import session, request, redirect, url_for
from flask_mail import Mail
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

@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access requests"""
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from flask import jsonify
        return jsonify({'success': False, 'error': 'Unauthorized', 'message': 'Please log in to continue.'}), 401
    return redirect(url_for('auth.login', next=request.path))

# Initialize Flask-Mail extension so it is available via current_app.extensions['mail']
try:
    mail = Mail(app)
except Exception:
    # If initialization fails (e.g., missing config), we continue; utils will handle runtime errors
    mail = None


@app.route('/send-test-email')
def send_test_email():
    """Send a simple test email to verify SMTP configuration.

    Query params:
      - to: recipient email address (optional; defaults to MAIL_DEFAULT_SENDER or MAIL_USERNAME)

    Returns JSON {success: bool, message: str}
    """
    from flask import request, jsonify, current_app
    try:
        # Prefer the Mail() instance initialized at app start; otherwise create a temporary Mail wrapper
        mail_instance = None
        try:
            if 'mail' in globals() and globals().get('mail') is not None:
                mail_instance = globals().get('mail')
            else:
                mail_instance = Mail(current_app)
        except Exception:
            mail_instance = None

        if not mail_instance:
            return jsonify(success=False, message='Mail extension not initialized'), 500

        to = request.args.get('to') or current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
        if not to:
            return jsonify(success=False, message='No recipient configured (pass ?to= or set MAIL_DEFAULT_SENDER)'), 400

        from flask_mail import Message
        msg = Message(
            subject='ServiceProvider - SMTP Test',
            recipients=[to],
            body='This is a test email sent from the ServiceProvider application to verify SMTP settings.'
        )
        # Try Flask-Mail first, but fall back to direct SMTP sender in utils
        try:
            mail_instance.send(msg)
        except Exception:
            # Fallback: use direct smtplib sender
            try:
                import utils
                utils.send_email_smtp(to, msg.subject, msg.body, sender=msg.sender)
            except Exception as e:
                return jsonify(success=False, message=f'Error sending email: {str(e)}'), 500
        return jsonify(success=True, message=f'Test email sent to {to}')

    except Exception as e:
        return jsonify(success=False, message=f'Error sending email: {str(e)}'), 500

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