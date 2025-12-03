# patterns/captcha_factory.py
# Factory Pattern for Captcha Generation
from abc import ABC, abstractmethod
import random

# ============================================
# Product Interface (Captcha)
# ============================================
class Captcha(ABC):
    """Abstract base class for all captcha types"""
    
    @abstractmethod
    def generate_challenge(self):
        """Generate and return captcha challenge data"""
        pass
    
    @abstractmethod
    def get_answer(self):
        """Get the correct answer for this captcha"""
        pass
    
    @abstractmethod
    def get_type(self):
        """Get the captcha type identifier"""
        pass


# ============================================
# Concrete Products (Captcha Types)
# ============================================
class ColorBallCaptcha(Captcha):
    """Color ball selection captcha"""
    
    def __init__(self):
        self.colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange']
        self.correct_color = random.choice(self.colors)
        self.options = random.sample(self.colors, 3)  # Show 3 random colors
        if self.correct_color not in self.options:
            self.options[0] = self.correct_color  # Ensure correct color is in options
        random.shuffle(self.options)
    
    def generate_challenge(self):
        """Generate color ball challenge"""
        return {
            'type': self.get_type(),
            'challenge': f'Select the {self.correct_color} ball',
            'answer': self.correct_color,
            'options': self.options
        }
    
    def get_answer(self):
        return self.correct_color
    
    def get_type(self):
        return 'color_ball'


class MathCaptcha(Captcha):
    """Simple math problem captcha"""
    
    def __init__(self):
        self.num1 = random.randint(1, 10)
        self.num2 = random.randint(1, 10)
        self.operation = random.choice(['+', '-', '*'])
        self.correct_answer = self._calculate_answer()
    
    def _calculate_answer(self):
        """Calculate the correct answer based on operation"""
        if self.operation == '+':
            return str(self.num1 + self.num2)
        elif self.operation == '-':
            return str(self.num1 - self.num2)
        elif self.operation == '*':
            return str(self.num1 * self.num2)
        return '0'
    
    def generate_challenge(self):
        """Generate math challenge"""
        return {
            'type': self.get_type(),
            'challenge': f'What is {self.num1} {self.operation} {self.num2}?',
            'answer': self.correct_answer,
            'options': None  # Math captcha doesn't need pre-defined options
        }
    
    def get_answer(self):
        return self.correct_answer
    
    def get_type(self):
        return 'math'


# ============================================
# Factory (Creator)
# ============================================
class CaptchaFactory:
    """Factory class for creating different types of captchas"""
    
    # Registry of available captcha types
    _captcha_types = {
        'color_ball': ColorBallCaptcha,
        'math': MathCaptcha,
    }
    
    @staticmethod
    def create_captcha(type='color_ball'):
        """
        Factory method to create captcha instances
        
        Args:
            type: Type of captcha to create ('color_ball', 'math')
            
        Returns:
            dict: Captcha challenge data
        """
        captcha_class = CaptchaFactory._captcha_types.get(type.lower())
        
        if not captcha_class:
            # Default to color_ball if unknown type
            captcha_class = ColorBallCaptcha
        
        # Create captcha instance and generate challenge
        captcha_instance = captcha_class()
        return captcha_instance.generate_challenge()
    
    @staticmethod
    def get_available_types():
        """Get list of available captcha types"""
        return list(CaptchaFactory._captcha_types.keys())
    
    @staticmethod
    def register_captcha_type(type_name: str, captcha_class: type):
        """
        Register a new captcha type (for extensibility)
        
        Args:
            type_name: Identifier for the captcha type
            captcha_class: Class that implements Captcha interface
        """
        if not issubclass(captcha_class, Captcha):
            raise TypeError(f"{captcha_class} must inherit from Captcha")
        CaptchaFactory._captcha_types[type_name.lower()] = captcha_class