
import random
import os
from dotenv import load_dotenv
from patterns.cloudinary_adapter import get_cloudinary_adapter
from flask_mail import Mail, Message
from flask import current_app
import threading
import smtplib
from email.mime.text import MIMEText

# Load environment variables from project root .env (one level above backend)
try:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    dotenv_path = os.path.join(base_dir, '.env')
    load_dotenv(dotenv_path)
except Exception:
    # Fallback to default loader
    load_dotenv()

# Hardcoded PIN for verification (email/phone)
HARDCODED_PIN = "12345"  # kept for backward-compatibility fallback (not used by default)

# In-memory store for verification (for demo)
verification_codes = {}


# Adapter instances
_cloudinary_adapter = None
_mail_adapter = None
_mail_lock = threading.Lock()


def _get_cloudinary():
    """Get Cloudinary adapter instance (lazy loaded)"""
    global _cloudinary_adapter
    if _cloudinary_adapter is None:
        _cloudinary_adapter = get_cloudinary_adapter()
    return _cloudinary_adapter


def generate_verification_code():
    """Generate a random 5-digit verification code as a string.

    Returns:
        str: 5-digit code, e.g. '03421'
    """
    return "{:05d}".format(random.randint(0, 99999))



def _get_mail_adapter():
    """Get or initialize Flask-Mail adapter (singleton, thread-safe)"""
    global _mail_adapter
    if _mail_adapter is None:
        with _mail_lock:
            if _mail_adapter is None:
                try:
                    # Prefer the already-initialized extension registered on app
                    mail_ext = None
                    try:
                        mail_ext = current_app.extensions.get('mail')
                    except Exception:
                        mail_ext = None

                    if mail_ext:
                        _mail_adapter = mail_ext
                    else:
                        _mail_adapter = Mail(current_app)
                except Exception as e:
                    # If mail cannot be initialized, leave None and raise at send time
                    print(f"[MAIL INIT ERROR] {str(e)}")
                    _mail_adapter = None
    return _mail_adapter

def send_verification_email(email, code=None):
    """
    Send verification email using Flask-Mail (Adapter pattern).

    If `code` is not provided, a new 5-digit code will be generated and stored
    in the in-memory `verification_codes` map keyed by recipient.
    """
    if not code:
        code = generate_verification_code()
    # Store the code against the recipient so it can be verified later
    verification_codes[email] = code
    try:
        mail = _get_mail_adapter()
        if mail:
            msg = Message(
                subject="Your Verification Code",
                recipients=[email],
                body=f"Your verification code is: {code}"
            )
            mail.send(msg)
            print(f"[VERIFICATION EMAIL SENT] To: {email} | Code: {code}")
        else:
            # Fallback to direct SMTP send if Flask-Mail not available
            send_email_smtp(email, "Your Verification Code", f"Your verification code is: {code}")
            print(f"[VERIFICATION EMAIL SENT VIA SMTP] To: {email} | Code: {code}")
    except Exception as e:
        print(f"[EMAIL ERROR] Could not send verification email: {str(e)}")
    return code


def send_verification_sms(phone, code=None):
    """
    Mock send verification SMS (prints to console).

    If `code` is not provided, a new 5-digit code will be generated and stored
    in the in-memory `verification_codes` map keyed by the phone number.
    """
    if not code:
        code = generate_verification_code()
    verification_codes[phone] = code
    # For demo purposes we just print the SMS to console
    print(f"[VERIFICATION SMS] To: {phone}")
    print(f"[VERIFICATION SMS] Code: {code}")
    return code


def email_verification(email, code):
    """Verify the provided `code` against the stored code for `email`.

    Returns True if matches, False otherwise.
    """
    stored = verification_codes.get(email)
    if stored:
        return str(code) == str(stored)
    # Fallback to legacy hardcoded PIN for compatibility
    return str(code) == HARDCODED_PIN


def phone_verification(phone, code):
    """Verify the provided `code` against the stored code for `phone`.

    Returns True if matches, False otherwise.
    """
    stored = verification_codes.get(phone)
    if stored:
        return str(code) == str(stored)
    # Fallback to legacy hardcoded PIN for compatibility
    return str(code) == HARDCODED_PIN


def upload_image_to_cloudinary(file, folder="uploads", public_id=None):
    """
    Upload an image file to Cloudinary using adapter.
    
    Args:
        file: FileStorage object from Flask request.files
        folder: Cloudinary folder name (default: "uploads")
        public_id: Custom public ID for the image (optional)
    
    Returns:
        Secure URL string, or None on failure
    """
    adapter = _get_cloudinary()
    
    try:
        transformations = {
            "width": 500,
            "height": 500,
            "quality": "auto:good",
            "crop": "limit"
        }
        
        result = adapter.upload(file, folder, public_id, transformations)
        return result.get('url') if result else None
        
    except Exception as e:
        print(f"[ERROR] Image upload failed: {str(e)}")
        return None


def delete_image_from_cloudinary(public_id_or_url):
    """
    Delete an image from Cloudinary using adapter.
    
    Args:
        public_id_or_url: The public ID or URL of the image to delete
    
    Returns:
        True if successful, False otherwise
    """
    adapter = _get_cloudinary()
    return adapter.delete(public_id_or_url)


def get_cloudinary_url(public_id_or_url, width=None, height=None, quality="auto:good", lazy=False):
    """
    Generate optimized Cloudinary URL using adapter.
    
    Args:
        public_id_or_url: Cloudinary public_id or full URL
        width: Target width (optional)
        height: Target height (optional)
        quality: Image quality ('auto', 'auto:low', 'auto:good', 'auto:best', or 1-100)
        lazy: Enable lazy loading optimization (default: False)
    
    Returns:
        Optimized Cloudinary URL with transformations
    """
    adapter = _get_cloudinary()
    
    transformations = {}
    if width:
        transformations['width'] = width
    if height:
        transformations['height'] = height
    if quality:
        transformations['quality'] = quality
    if lazy:
        transformations['effect'] = 'blur:100'
    
    url = adapter.get_url(public_id_or_url, transformations)
    return url if url else public_id_or_url


def get_cloudinary_thumbnail_url(public_id_or_url, size=150):
    """
    Generate thumbnail URL using adapter.
    
    Args:
        public_id_or_url: Cloudinary public_id or full URL
        size: Thumbnail size (square, default: 150px)
    
    Returns:
        Optimized thumbnail URL
    """
    adapter = _get_cloudinary()
    return adapter.get_thumbnail_url(public_id_or_url, size)


def send_email_smtp(to_address, subject, body, sender=None):
    """Send an email using smtplib directly using MAIL_* settings.

    This function is a lightweight fallback to verify SMTP settings and
    will be used by the `/send-test-email` endpoint when Flask-Mail
    is unreliable in the current environment.
    """
    config = current_app.config
    server = config.get('MAIL_SERVER')
    port = int(config.get('MAIL_PORT') or 0)
    username = config.get('MAIL_USERNAME')
    password = config.get('MAIL_PASSWORD')
    use_tls = config.get('MAIL_USE_TLS', False)
    use_ssl = config.get('MAIL_USE_SSL', False)

    sender = sender or config.get('MAIL_DEFAULT_SENDER') or username
    if not sender:
        raise RuntimeError('No sender configured (MAIL_DEFAULT_SENDER or MAIL_USERNAME)')

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to_address

    if use_ssl:
        smtp = smtplib.SMTP_SSL(server, port, timeout=30)
    else:
        smtp = smtplib.SMTP(server, port, timeout=30)

    try:
        smtp.set_debuglevel(0)
        if use_tls and not use_ssl:
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.sendmail(sender, [to_address], msg.as_string())
    finally:
        try:
            smtp.quit()
        except Exception:
            pass

    return True
