# routes/auth.py
# Changes: Update imports if needed; Handle phone in register; Hardcode code in forgot; Remove strategy from login_user call; Add captcha_type to login template; Update captcha creation
from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_user, logout_user, current_user
from controllers.user_controller import (
    register_user, login_user as controller_login,
    send_forgot_password_email, reset_password
)
from utils import generate_verification_code, send_verification_email  # Not used but keep
from patterns.captcha_factory import CaptchaFactory
from patterns.observer_auth import auth_notifier


auth_bp = Blueprint('auth', __name__, template_folder='../../frontend/Auth')

# -------- Register --------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form.to_dict()
        # Registration now supports only email or phone verification; captcha removed
        verification_method = data.get('verification_method', 'email')
        role = data.get('role', 'customer')  # Get role from form, default to customer
        
        # Register user with role
        user, error = register_user(data, role=role)
        if error:
            auth_notifier.notify(error, 'danger')
            return render_template('register_v2.html', role=role)
        
        # Handle verification method (email or phone only)
        if verification_method == 'email':
            # Send email verification code
            from utils import generate_verification_code, send_verification_email
            code = generate_verification_code()  # hardcoded to 12345 in utils
            send_verification_email(data['email'], code)  # Print to console
            session['reg_email'] = data['email']
            session['reg_code'] = code
            session['reg_method'] = 'email'
            auth_notifier.notify(f"Registration successful! Verification code: {code}", "success")
            return redirect(url_for('auth.verify_register'))
        elif verification_method == 'phone':
            # Send phone verification code
            from utils import generate_verification_code, send_verification_sms
            code = generate_verification_code()  # hardcoded to 12345 in utils
            send_verification_sms(data['phone'], code)  # Print to console
            session['reg_phone'] = data['phone']
            session['reg_code'] = code
            session['reg_method'] = 'phone'
            auth_notifier.notify(f"Registration successful! Verification code: {code}", "success")
            return redirect(url_for('auth.verify_register'))
        else:
            # Fallback to email verification if unknown method
            from utils import generate_verification_code, send_verification_email
            code = generate_verification_code()
            email = data.get('email')
            if email:
                send_verification_email(email, code)
                session['reg_email'] = email
                session['reg_code'] = code
                session['reg_method'] = 'email'
                auth_notifier.notify(f"Registration successful! Verification code: {code}", "success")
                return redirect(url_for('auth.verify_register'))
            auth_notifier.notify('Verification method not supported and no email provided.', 'danger')
            return render_template('register_v2.html', role=role)
    # GET request - show registration form
    return render_template('register_v2.html')

@auth_bp.route('/verify_register', methods=['GET', 'POST'])
def verify_register():
    """Page to enter verification code after registering with email/phone verification."""
    method = session.get('reg_method')
    contact = session.get('reg_email') or session.get('reg_phone')
    
    if not contact or not method:
        auth_notifier.notify("No verification pending.", "warning")
        return redirect(url_for('auth.register'))
    if request.method == 'POST':
        code_entered = request.form.get('code')
        real_code = session.get('reg_code')
        
        # Simple verification - compare entered code with stored code
        if code_entered == real_code:
            # Mark user as verified
            from models.user import User
            if method == 'email':
                user = User.objects(email=contact).first()
            else:
                user = User.objects(phone=contact).first()
            
            if user:
                user.is_verified = True
                user.save()
            
            # Clear session
            session.pop('reg_email', None)
            session.pop('reg_phone', None)
            session.pop('reg_code', None)
            session.pop('reg_method', None)
            
            auth_notifier.notify('Verification successful! You can now login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            auth_notifier.notify('Verification code incorrect. Try again.', 'danger')
    return render_template('verify_register.html', contact=contact, method=method)

# -------- Login --------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')  # Changed name to identifier for clarity
        password = request.form.get('password')
        login_as = request.form.get('login_as', 'customer')
        user_captcha = request.form.get('captcha_answer')
        correct_answer = session.get('captcha_answer')
        if user_captcha != correct_answer:
            auth_notifier.notify("Captcha incorrect. Try again.", "danger")
            return redirect(url_for('auth.login'))
        user, error = controller_login(identifier, password)  # Removed request.form
        if user:
            # Use Flask-Login's login_user() instead of manual session storage
            login_user(user, remember=False)
            auth_notifier.notify(f"Login successful! Welcome, {user.name}", "success")
            
            # Role + intent-based redirection (Decorator Pattern used in routes)
            # Admin takes precedence regardless of selected intent
            if hasattr(user, 'role') and user.role == 'admin':
                return redirect(url_for('admin.dashboard'))

            # If user selected business owner intent
            if login_as == 'business_owner':
                if hasattr(user, 'role') and user.role == 'business_owner':
                    return redirect(url_for('owner_business.dashboard'))
                else:
                    auth_notifier.notify('Your account is not a business owner. Redirected to home.', 'warning')
                    return redirect(url_for('home.index'))

            # Default: customer home
            return redirect(url_for('home.index'))
        else:
            auth_notifier.notify(error or "Invalid credentials.", "danger")
            return redirect(url_for('auth.login'))
    # GET request - allow requesting different captcha types
    captcha_type = request.args.get('type', 'color_ball')
    captcha = CaptchaFactory.create_captcha(type=captcha_type)
    session['captcha_answer'] = captcha['answer']
    return render_template('login.html', captcha=captcha, captcha_type=captcha_type)

# -------- Forgot Password --------
@auth_bp.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']
        code = send_forgot_password_email(email)
        if code:
            session['reset_email'] = email
            session['real_code'] = code
            auth_notifier.notify("Verification code sent to your email.", "success")
            return redirect(url_for('auth.reset'))
        else:
            auth_notifier.notify('No user with that email.', 'danger')
    return render_template('forgot.html')

# -------- Reset Password --------
@auth_bp.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        code = request.form['code']
        new_password = request.form['new_password']
        email = session.get('reset_email')
        real_code = session.get('real_code')
        success = reset_password(email, code, real_code, new_password)
        if success:
            auth_notifier.notify('Password reset successful! You can login now.', 'success')
            return redirect(url_for('auth.login'))
        else:
            auth_notifier.notify('Invalid verification code.', 'danger')
    return render_template('reset.html')

# -------- Logout --------
@auth_bp.route('/logout')
def logout():
    user_name = current_user.name if hasattr(current_user, 'name') and current_user.is_authenticated else 'Guest'
    logout_user()  # Use Flask-Login's logout_user()
    session.clear()
    auth_notifier.notify(f"Logged out successfully, {user_name}", "success")
    return redirect(url_for('auth.login'))
    return redirect(url_for('home.index'))