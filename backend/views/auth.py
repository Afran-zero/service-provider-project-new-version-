# routes/auth.py
"""
Authentication Routes with Design Patterns Implementation

Design Patterns Used:
====================

1. FACTORY PATTERN (Captcha Generation - Login)
   - Factory: CaptchaFactory
   - Products: ColorBallCaptcha, MathCaptcha
   - Usage: Creates different captcha types based on user preference
   - Extensibility: Add new captcha types by creating new Captcha classes
   
2. STRATEGY PATTERN (Verification Methods)
   a) Registration Verification:
      - Context: VerificationContext
      - Strategies: EmailVerificationStrategy, PhoneVerificationStrategy
      - Factory: VerificationStrategyFactory
      - Usage: Handles email/phone verification for registration
      
   b) Login Authentication:
      - Context: LoginAuthContext
      - Strategy: CaptchaAuthStrategy
      - Usage: Verifies captcha challenges during login
      
3. OBSERVER PATTERN (Notifications)
   - Subject: auth_notifier
   - Usage: Broadcasts authentication events (success, errors)
   
Benefits:
- Open/Closed Principle: Add new verification methods without modifying existing code
- Single Responsibility: Each strategy/product handles one specific task
- Easy to test: Each component can be unit tested independently
- Maintainable: Clear separation of concerns
"""
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
        verification_method = data.get('verification_method', 'email')
        role = data.get('role', 'customer')
        
        # Register user with role
        user, error = register_user(data, role=role)
        if error:
            auth_notifier.notify(error, 'danger')
            return render_template('register_v2.html', role=role)
        
        # ===== Strategy Pattern Implementation =====
        from patterns.auth_strategy import VerificationStrategyFactory, VerificationContext
        
        # 1. Create appropriate strategy based on verification method
        strategy = VerificationStrategyFactory.create_strategy(verification_method)
        
        # 2. Create context with the strategy
        verification_context = VerificationContext(strategy)
        
        # 3. Get contact field name from strategy
        contact_field = verification_context.get_contact_field()
        contact = data.get(contact_field)
        
        # 4. Validate contact exists
        if not contact:
            auth_notifier.notify(f'No {contact_field} provided for verification.', 'danger')
            return render_template('register_v2.html', role=role)
        
        # 5. Send verification using strategy
        try:
            code = verification_context.send_verification(contact, user_data=data)
            auth_notifier.notify(f"Registration successful! Verification code sent to your {contact_field}: {code}", "success")
            return redirect(url_for('auth.verify_register'))
        except Exception as e:
            auth_notifier.notify(f'Failed to send verification: {str(e)}', 'danger')
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
        
        # ===== Strategy Pattern Implementation =====
        from patterns.auth_strategy import VerificationStrategyFactory, VerificationContext
        
        # 1. Create appropriate strategy based on stored method
        strategy = VerificationStrategyFactory.create_strategy(method)
        
        # 2. Create context with the strategy
        verification_context = VerificationContext(strategy)
        
        # 3. Verify code using strategy
        is_valid = verification_context.verify_code(contact, code_entered)
        
        if is_valid:
            # Mark user as verified
            from models.user import User
            contact_field = verification_context.get_contact_field()
            
            # Find user by appropriate field
            if contact_field == 'email':
                user = User.objects(email=contact).first()
            elif contact_field == 'phone':
                user = User.objects(phone=contact).first()
            else:
                user = None
            
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
        identifier = request.form.get('identifier')
        password = request.form.get('password')
        login_as = request.form.get('login_as', 'customer')
        user_captcha = request.form.get('captcha_answer')
        
        # ===== Strategy Pattern for Captcha Verification =====
        from patterns.auth_strategy import LoginAuthContext, CaptchaAuthStrategy
        
        # 1. Create authentication context with captcha strategy
        auth_context = LoginAuthContext(CaptchaAuthStrategy())
        
        # 2. Verify captcha using strategy
        is_captcha_valid = auth_context.authenticate(user_captcha, session)
        
        if not is_captcha_valid:
            auth_notifier.notify("Captcha incorrect. Try again.", "danger")
            return redirect(url_for('auth.login'))
        
        # 3. Proceed with user authentication
        user, error = controller_login(identifier, password)
        if user:
            # ===== Role Validation Before Login =====
            user_role = getattr(user, 'role', 'customer')  # Default to customer if no role
            
            # Validate that user's role matches their login intent
            if login_as == 'business_owner':
                if user_role != 'business_owner':
                    # User tried to login as business owner but doesn't have that role
                    auth_notifier.notify(
                        f"Login failed: Your account is registered as '{user_role}', not 'business_owner'. "
                        f"Please select the correct account type or register a new business owner account.",
                        'danger'
                    )
                    return redirect(url_for('auth.login'))
            
            elif login_as == 'customer':
                if user_role not in ['customer', None]:
                    # User tried to login as customer but has a different role
                    auth_notifier.notify(
                        f"Login failed: Your account is registered as '{user_role}', not 'customer'. "
                        f"Please select the correct account type to login.",
                        'danger'
                    )
                    return redirect(url_for('auth.login'))
            
            # Role validation passed - proceed with login
            login_user(user, remember=False)
            auth_notifier.notify(f"Login successful! Welcome, {user.name}", "success")
            
            # Role-based redirection (Admin takes precedence)
            if user_role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user_role == 'business_owner':
                return redirect(url_for('owner_business.dashboard'))
            else:
                # Default: customer home
                return redirect(url_for('home.index'))
        else:
            auth_notifier.notify(error or "Invalid credentials.", "danger")
            return redirect(url_for('auth.login'))
    
    # ===== Factory Pattern for Captcha Generation =====
    # GET request - allow requesting different captcha types
    captcha_type = request.args.get('type', 'color_ball')  # Supports: 'color_ball', 'math'
    
    # Use Factory to create appropriate captcha
    captcha = CaptchaFactory.create_captcha(type=captcha_type)
    
    # Store answer in session for verification
    session['captcha_answer'] = captcha['answer']
    
    # Get available captcha types for template (to show type switcher)
    available_types = CaptchaFactory.get_available_types()
    
    return render_template('login.html', 
                         captcha=captcha, 
                         captcha_type=captcha_type,
                         available_captcha_types=available_types)

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