# patterns/auth_strategy.py
# No changes needed, but it's not used in login anymore
from patterns.captcha_factory import CaptchaFactory
from utils import email_verification
from flask import session

class AuthStrategy:
    def __init__(self, strategy='captcha_or_email'):
        self.strategy = strategy

    def verify(self, request_data):
        """
        Verify using the chosen strategy.
        """
        if self.strategy == 'captcha_or_email':
            if 'captcha_answer' in request_data:
                # compare against the answer stored in session when captcha was rendered
                expected = session.get('captcha_answer')
                return request_data.get('captcha_answer') == expected
            elif 'email' in request_data and 'code' in request_data:
                return email_verification(request_data['email'], request_data['code'])
        return False