# patterns/auth_strategy.py
# Strategy Pattern for Authentication/Verification
from abc import ABC, abstractmethod
from utils import generate_verification_code, send_verification_email, send_verification_sms
from flask import session

# ============================================
# Strategy Interface
# ============================================
class VerificationStrategy(ABC):
    """Abstract base class for verification strategies"""
    
    @abstractmethod
    def send_verification(self, contact, user_data=None):
        """Send verification code to the user"""
        pass
    
    @abstractmethod
    def verify_code(self, contact, code):
        """Verify the code entered by user"""
        pass
    
    @abstractmethod
    def get_contact_field(self):
        """Return the field name used for contact (email, phone, etc.)"""
        pass


# ============================================
# Concrete Strategies
# ============================================
class EmailVerificationStrategy(VerificationStrategy):
    """Strategy for email-based verification"""
    
    def send_verification(self, contact, user_data=None):
        """Send verification code via email"""
        code = generate_verification_code()
        send_verification_email(contact, code)
        
        # Store in session
        session['reg_email'] = contact
        session['reg_code'] = code
        session['reg_method'] = 'email'
        
        return code
    
    def verify_code(self, contact, code):
        """Verify email verification code"""
        stored_code = session.get('reg_code')
        stored_email = session.get('reg_email')
        stored_method = session.get('reg_method')
        
        return (stored_method == 'email' and 
                stored_email == contact and 
                stored_code == code)
    
    def get_contact_field(self):
        return 'email'


class PhoneVerificationStrategy(VerificationStrategy):
    """Strategy for phone-based verification"""
    
    def send_verification(self, contact, user_data=None):
        """Send verification code via SMS"""
        code = generate_verification_code()
        send_verification_sms(contact, code)
        
        # Store in session
        session['reg_phone'] = contact
        session['reg_code'] = code
        session['reg_method'] = 'phone'
        
        return code
    
    def verify_code(self, contact, code):
        """Verify phone verification code"""
        stored_code = session.get('reg_code')
        stored_phone = session.get('reg_phone')
        stored_method = session.get('reg_method')
        
        return (stored_method == 'phone' and 
                stored_phone == contact and 
                stored_code == code)
    
    def get_contact_field(self):
        return 'phone'


# ============================================
# Context Class (Manages Strategy)
# ============================================
class VerificationContext:
    """Context class that uses a verification strategy"""
    
    def __init__(self, strategy: VerificationStrategy):
        self._strategy = strategy
    
    @property
    def strategy(self):
        return self._strategy
    
    @strategy.setter
    def strategy(self, strategy: VerificationStrategy):
        self._strategy = strategy
    
    def send_verification(self, contact, user_data=None):
        """Delegate to strategy"""
        return self._strategy.send_verification(contact, user_data)
    
    def verify_code(self, contact, code):
        """Delegate to strategy"""
        return self._strategy.verify_code(contact, code)
    
    def get_contact_field(self):
        """Delegate to strategy"""
        return self._strategy.get_contact_field()


# ============================================
# Factory for Strategy Selection
# ============================================
class VerificationStrategyFactory:
    """Factory to create verification strategies"""
    
    @staticmethod
    def create_strategy(method: str) -> VerificationStrategy:
        """
        Create and return appropriate verification strategy
        
        Args:
            method: 'email', 'phone', or other verification method
            
        Returns:
            VerificationStrategy instance
        """
        strategies = {
            'email': EmailVerificationStrategy,
            'phone': PhoneVerificationStrategy,
        }
        
        strategy_class = strategies.get(method.lower())
        if not strategy_class:
            # Default to email if unknown method
            strategy_class = EmailVerificationStrategy
        
        return strategy_class()


# ============================================
# Login Authentication Strategy (Captcha)
# ============================================
class LoginAuthStrategy(ABC):
    """Abstract strategy for login authentication methods"""
    
    @abstractmethod
    def verify(self, user_input, session_data):
        """Verify the authentication challenge"""
        pass


class CaptchaAuthStrategy(LoginAuthStrategy):
    """Strategy for captcha-based login authentication"""
    
    def verify(self, user_input, session_data):
        """
        Verify captcha answer
        
        Args:
            user_input: User's captcha answer
            session_data: Session containing correct answer
            
        Returns:
            bool: True if captcha is correct
        """
        expected_answer = session_data.get('captcha_answer')
        return user_input == expected_answer


class LoginAuthContext:
    """Context class for managing login authentication strategies"""
    
    def __init__(self, strategy: LoginAuthStrategy = None):
        self._strategy = strategy or CaptchaAuthStrategy()
    
    @property
    def strategy(self):
        return self._strategy
    
    @strategy.setter
    def strategy(self, strategy: LoginAuthStrategy):
        self._strategy = strategy
    
    def authenticate(self, user_input, session_data):
        """Delegate authentication to strategy"""
        return self._strategy.verify(user_input, session_data)


# ============================================
# Legacy Support (backward compatibility)
# ============================================
class AuthStrategy:
    """Legacy class for backward compatibility"""
    
    def __init__(self, strategy='captcha_or_email'):
        self.strategy = strategy
        self._auth_context = LoginAuthContext(CaptchaAuthStrategy())

    def verify(self, request_data):
        """Verify using the chosen strategy (for login captcha)"""
        if self.strategy == 'captcha_or_email':
            if 'captcha_answer' in request_data:
                return self._auth_context.authenticate(
                    request_data.get('captcha_answer'),
                    session
                )
        return False