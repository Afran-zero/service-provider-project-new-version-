from flask import Flask
from flask_login import LoginManager
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
app.secret_key = config.SECRET_KEY

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

if __name__ == '__main__':
    app.run(debug=True)