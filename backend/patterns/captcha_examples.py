# patterns/captcha_examples.py
"""
Examples of how to extend the Captcha Factory with new captcha types
This demonstrates the extensibility of the Factory Pattern
"""

from patterns.captcha_factory import Captcha, CaptchaFactory
import random


# ============================================
# Example 1: Image-based Captcha
# ============================================
class ImageCaptcha(Captcha):
    """Example: Select images containing specific objects"""
    
    def __init__(self):
        self.objects = ['car', 'bicycle', 'traffic light', 'crosswalk', 'bus']
        self.target_object = random.choice(self.objects)
        # In real implementation, you'd have actual image URLs
        self.images = [f'image_{i}.jpg' for i in range(9)]
        self.correct_indices = random.sample(range(9), k=random.randint(2, 4))
    
    def generate_challenge(self):
        return {
            'type': self.get_type(),
            'challenge': f'Select all images containing a {self.target_object}',
            'answer': ','.join(map(str, sorted(self.correct_indices))),
            'options': self.images,
            'correct_indices': self.correct_indices
        }
    
    def get_answer(self):
        return ','.join(map(str, sorted(self.correct_indices)))
    
    def get_type(self):
        return 'image'


# ============================================
# Example 2: Slider Captcha
# ============================================
class SliderCaptcha(Captcha):
    """Example: Slide puzzle piece to correct position"""
    
    def __init__(self):
        self.correct_position = random.randint(50, 250)  # Pixel position
        self.tolerance = 10  # Acceptable margin of error
    
    def generate_challenge(self):
        return {
            'type': self.get_type(),
            'challenge': 'Slide the puzzle piece to complete the image',
            'answer': str(self.correct_position),
            'options': None,
            'tolerance': self.tolerance
        }
    
    def get_answer(self):
        return str(self.correct_position)
    
    def get_type(self):
        return 'slider'


# ============================================
# Example 3: Logic Puzzle Captcha
# ============================================
class LogicCaptcha(Captcha):
    """Example: Simple logic puzzles"""
    
    def __init__(self):
        puzzles = [
            {
                'question': 'If all roses are flowers and some flowers fade quickly, can all roses fade quickly?',
                'options': ['Yes', 'No', 'Cannot be determined'],
                'answer': 'Cannot be determined'
            },
            {
                'question': 'What comes next in the sequence: 2, 4, 8, 16, __?',
                'options': ['20', '24', '32', '64'],
                'answer': '32'
            },
            {
                'question': 'If 5 cats catch 5 mice in 5 minutes, how many cats catch 100 mice in 100 minutes?',
                'options': ['5', '20', '100', '500'],
                'answer': '5'
            }
        ]
        self.puzzle = random.choice(puzzles)
    
    def generate_challenge(self):
        return {
            'type': self.get_type(),
            'challenge': self.puzzle['question'],
            'answer': self.puzzle['answer'],
            'options': self.puzzle['options']
        }
    
    def get_answer(self):
        return self.puzzle['answer']
    
    def get_type(self):
        return 'logic'


# ============================================
# Example 4: Audio Captcha (Accessibility)
# ============================================
class AudioCaptcha(Captcha):
    """Example: Listen to audio and type what you hear"""
    
    def __init__(self):
        self.code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        # In real implementation, you'd generate actual audio file
        self.audio_url = f'/static/audio/captcha_{self.code}.mp3'
    
    def generate_challenge(self):
        return {
            'type': self.get_type(),
            'challenge': 'Listen to the audio and type the numbers you hear',
            'answer': self.code,
            'options': None,
            'audio_url': self.audio_url
        }
    
    def get_answer(self):
        return self.code
    
    def get_type(self):
        return 'audio'


# ============================================
# HOW TO REGISTER NEW CAPTCHA TYPES
# ============================================
def register_custom_captchas():
    """
    Register all custom captcha types with the factory.
    Call this function during application initialization.
    
    Example usage in app initialization:
        from patterns.captcha_examples import register_custom_captchas
        register_custom_captchas()
    """
    CaptchaFactory.register_captcha_type('image', ImageCaptcha)
    CaptchaFactory.register_captcha_type('slider', SliderCaptcha)
    CaptchaFactory.register_captcha_type('logic', LogicCaptcha)
    CaptchaFactory.register_captcha_type('audio', AudioCaptcha)
    
    print("✓ Custom captcha types registered successfully!")
    print(f"Available types: {CaptchaFactory.get_available_types()}")


# ============================================
# USAGE EXAMPLES
# ============================================
if __name__ == "__main__":
    # Example 1: Use built-in captcha types
    print("=== Built-in Captcha Types ===")
    color_captcha = CaptchaFactory.create_captcha('color_ball')
    print(f"Color Ball: {color_captcha}")
    
    math_captcha = CaptchaFactory.create_captcha('math')
    print(f"Math: {math_captcha}")
    
    # Example 2: Register and use custom captcha types
    print("\n=== Custom Captcha Types ===")
    register_custom_captchas()
    
    image_captcha = CaptchaFactory.create_captcha('image')
    print(f"Image: {image_captcha['challenge']}")
    
    logic_captcha = CaptchaFactory.create_captcha('logic')
    print(f"Logic: {logic_captcha['challenge']}")
    
    audio_captcha = CaptchaFactory.create_captcha('audio')
    print(f"Audio: {audio_captcha['challenge']}")
    
    # Example 3: List all available types
    print(f"\nAll available captcha types: {CaptchaFactory.get_available_types()}")
