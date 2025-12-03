"""
Configuration Singleton Pattern Implementation

Design Pattern: Singleton
- Ensures only one Config instance exists throughout the application
- Thread-safe using double-checked locking pattern
- Lazy initialization: instance created on first access
"""
import os
from dotenv import load_dotenv
import threading


class Config:
    """
    Singleton class for application configuration.
    
    Thread-safe implementation using double-checked locking.
    Ensures configuration is loaded only once and shared across the application.
    """
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False  # Track if instance has been initialized

    def __new__(cls):
        """
        Control instance creation to ensure only one instance exists.
        Uses double-checked locking for thread safety.
        """
        # First check (without lock) - fast path for existing instance
        if cls._instance is None:
            with cls._lock:
                # Second check (with lock) - ensure thread safety
                if cls._instance is None:
                    cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Initialize configuration values only once.
        Subsequent calls do nothing (singleton behavior).
        """
        # Prevent re-initialization
        if Config._initialized:
            return
        
        with Config._lock:
            # Double-check initialization flag
            if Config._initialized:
                return
            
            # Load .env file
            load_dotenv()
            
            # Set config values from environment variables
            self.SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key_fallback')
            self.MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/default_db')
            self.DB_NAME = os.getenv('DB_NAME', 'default_db_name')
            
            # Cloudinary configuration (optional)
            self.CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
            self.CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
            self.CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
            
            # Validate critical configuration
            if not self.SECRET_KEY or self.SECRET_KEY == 'default_secret_key_fallback':
                raise ValueError("SECRET_KEY must be set in .env or environment variables.")
            if not self.MONGO_URI:
                raise ValueError("MONGO_URI must be set in .env or environment variables.")
            
            # Warn if Cloudinary credentials missing
            if not all([self.CLOUDINARY_CLOUD_NAME, self.CLOUDINARY_API_KEY, self.CLOUDINARY_API_SECRET]):
                print("[WARN] Cloudinary credentials missing; image uploads will fail.")
            
            # Mark as initialized
            Config._initialized = True

    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of Config.
        
        Returns:
            Config: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __repr__(self):
        """String representation showing this is a singleton"""
        return f"<Config Singleton at {hex(id(self))}>"