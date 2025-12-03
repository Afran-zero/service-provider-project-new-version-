"""
Database Connection Singleton Pattern Implementation

Design Pattern: Singleton
- Ensures only one database connection instance exists
- Thread-safe using double-checked locking pattern
- Prevents multiple database connections
- Lazy initialization: connection created on first access
"""
import mongoengine
from config import Config
import threading
import logging

logger = logging.getLogger(__name__)


class SingletonDB:
    """
    Singleton class for MongoDB database connection.
    
    Thread-safe implementation using double-checked locking.
    Ensures only one database connection is created and shared across the application.
    """
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False  # Track if database has been connected
    _connection = None  # Store connection reference

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
                    cls._instance = super(SingletonDB, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Initialize database connection only once.
        Subsequent calls do nothing (singleton behavior).
        """
        # Prevent re-initialization
        if SingletonDB._initialized:
            return
        
        with SingletonDB._lock:
            # Double-check initialization flag
            if SingletonDB._initialized:
                return
            
            # Get config singleton
            config = Config.get_instance()
            
            try:
                # Connect to MongoDB
                SingletonDB._connection = mongoengine.connect(
                    db=config.DB_NAME,
                    host=config.MONGO_URI,
                    alias='default'
                )
                logger.info(f"✓ MongoDB connected: {config.DB_NAME}")
                
                # Mark as initialized
                SingletonDB._initialized = True
                
            except Exception as e:
                logger.error(f"✗ MongoDB connection failed: {str(e)}")
                raise
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of database connection.
        
        Returns:
            SingletonDB: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_connection(cls):
        """
        Get the MongoDB connection object.
        
        Returns:
            MongoClient: The MongoDB connection
        """
        instance = cls.get_instance()
        return cls._connection
    
    @classmethod
    def is_connected(cls):
        """
        Check if database is connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return cls._initialized and cls._connection is not None
    
    def __repr__(self):
        """String representation showing this is a singleton"""
        status = "connected" if SingletonDB.is_connected() else "not connected"
        return f"<SingletonDB Singleton at {hex(id(self))} - {status}>"
    
 
 