import os
from dotenv import load_dotenv
import threading


class Config:
    _instance = None
    _lock = threading.Lock()  # Thread-safe lock

    def __new__(cls):
        # Double-checked locking pattern for thread safety
        if cls._instance is None:
            with cls._lock:
                # Double-check inside lock
                if cls._instance is None:
                    cls._instance = super(Config, cls).__new__(cls)
            # Load .env file
            load_dotenv()
            
            # Set config values from environment variables (loaded from .env or actual env)
            cls._instance.SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key_fallback')  # Use a fallback for dev only
            cls._instance.MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/default_db')
            cls._instance.DB_NAME = os.getenv('DB_NAME', 'default_db_name')
            
            # Raise error if critical vars are missing (for production safety)
            if not cls._instance.SECRET_KEY or cls._instance.SECRET_KEY == 'default_secret_key_fallback':
                raise ValueError("SECRET_KEY must be set in .env or environment variables.")
            if not cls._instance.MONGO_URI:
                raise ValueError("MONGO_URI must be set in .env or environment variables.")
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls()  # Ensures singleton