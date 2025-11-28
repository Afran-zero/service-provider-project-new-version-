import mongoengine
from config import Config
import threading


class SingletonDB:
    _instance = None
    _lock = threading.Lock()  # Thread-safe lock

    def __new__(cls):
        # Double-checked locking pattern for thread safety
        if cls._instance is None:
            with cls._lock:
                # Double-check: another thread might have created instance
                # while this thread was waiting for the lock
                if cls._instance is None:
                    cls._instance = super(SingletonDB, cls).__new__(cls)
                    config = Config.get_instance()
                    mongoengine.connect(db=config.DB_NAME, host=config.MONGO_URI)
        return cls._instance
    
 
 