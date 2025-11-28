# patterns/captcha_factory.py
# Changes: Add 'math' type explicitly, randomize the math question
import random

class CaptchaFactory:
    @staticmethod
    def create_captcha(type='color_ball'):
        if type == 'color_ball':
            colors = ['red', 'blue', 'green']
            correct = random.choice(colors)
            return {
                'challenge': f'Select the {correct} ball',
                'answer': correct,
                'options': colors  # Pass options to template
            }
        elif type == 'math':
            a = random.randint(1, 10)
            b = random.randint(1, 10)
            return {
                'challenge': f'What is {a} + {b}?',
                'answer': str(a + b),
                'options': None
            }
        # Fallback to color_ball
        return CaptchaFactory.create_captcha('color_ball')