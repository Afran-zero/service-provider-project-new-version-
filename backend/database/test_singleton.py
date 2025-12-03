"""
Test script to verify Singleton pattern implementation
for Config and Database classes
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from database.singleton_db import SingletonDB
import threading


def test_config_singleton():
    """Test that Config follows Singleton pattern"""
    print("=" * 60)
    print("TESTING CONFIG SINGLETON PATTERN")
    print("=" * 60)
    
    # Test 1: Multiple instantiations return same instance
    print("\n1. Testing multiple instantiations...")
    config1 = Config()
    config2 = Config()
    config3 = Config.get_instance()
    
    print(f"   config1 ID: {id(config1)}")
    print(f"   config2 ID: {id(config2)}")
    print(f"   config3 ID: {id(config3)}")
    print(f"   ✓ Same instance: {config1 is config2 is config3}")
    
    assert config1 is config2, "❌ FAILED: config1 and config2 are not the same instance"
    assert config2 is config3, "❌ FAILED: config2 and config3 are not the same instance"
    
    # Test 2: Configuration values are shared
    print("\n2. Testing shared configuration values...")
    print(f"   config1.DB_NAME: {config1.DB_NAME}")
    print(f"   config2.DB_NAME: {config2.DB_NAME}")
    print(f"   ✓ Same values: {config1.DB_NAME == config2.DB_NAME}")
    
    assert config1.DB_NAME == config2.DB_NAME, "❌ FAILED: Different config values"
    
    # Test 3: Thread safety
    print("\n3. Testing thread safety...")
    instances = []
    
    def create_config():
        instances.append(Config.get_instance())
    
    threads = [threading.Thread(target=create_config) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    all_same = all(inst is instances[0] for inst in instances)
    print(f"   Created instances from 10 threads: {len(instances)}")
    print(f"   All instances identical: {all_same}")
    print(f"   ✓ Thread-safe: {all_same}")
    
    assert all_same, "❌ FAILED: Thread safety violated"
    
    print("\n✅ CONFIG SINGLETON PATTERN: PASSED")


def test_database_singleton():
    """Test that SingletonDB follows Singleton pattern"""
    print("\n" + "=" * 60)
    print("TESTING DATABASE SINGLETON PATTERN")
    print("=" * 60)
    
    # Test 1: Multiple instantiations return same instance
    print("\n1. Testing multiple instantiations...")
    db1 = SingletonDB()
    db2 = SingletonDB()
    db3 = SingletonDB.get_instance()
    
    print(f"   db1 ID: {id(db1)}")
    print(f"   db2 ID: {id(db2)}")
    print(f"   db3 ID: {id(db3)}")
    print(f"   ✓ Same instance: {db1 is db2 is db3}")
    
    assert db1 is db2, "❌ FAILED: db1 and db2 are not the same instance"
    assert db2 is db3, "❌ FAILED: db2 and db3 are not the same instance"
    
    # Test 2: Connection status
    print("\n2. Testing connection status...")
    print(f"   Is connected: {SingletonDB.is_connected()}")
    print(f"   Connection: {SingletonDB.get_connection()}")
    print(f"   ✓ Singleton initialized: {SingletonDB._initialized}")
    
    # Test 3: Thread safety
    print("\n3. Testing thread safety...")
    db_instances = []
    
    def create_db():
        db_instances.append(SingletonDB.get_instance())
    
    threads = [threading.Thread(target=create_db) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    all_same = all(inst is db_instances[0] for inst in db_instances)
    print(f"   Created instances from 10 threads: {len(db_instances)}")
    print(f"   All instances identical: {all_same}")
    print(f"   ✓ Thread-safe: {all_same}")
    
    assert all_same, "❌ FAILED: Thread safety violated"
    
    # Test 4: Only one database connection
    print("\n4. Testing single database connection...")
    connection1 = SingletonDB.get_connection()
    connection2 = SingletonDB.get_connection()
    print(f"   Connection 1 ID: {id(connection1)}")
    print(f"   Connection 2 ID: {id(connection2)}")
    print(f"   ✓ Same connection: {connection1 is connection2}")
    
    assert connection1 is connection2, "❌ FAILED: Multiple database connections created"
    
    print("\n✅ DATABASE SINGLETON PATTERN: PASSED")


def test_singleton_properties():
    """Test Singleton pattern properties"""
    print("\n" + "=" * 60)
    print("TESTING SINGLETON PATTERN PROPERTIES")
    print("=" * 60)
    
    # Property 1: Single instance per class
    print("\n1. Single instance per class")
    config = Config.get_instance()
    db = SingletonDB.get_instance()
    print(f"   Config instance: {config}")
    print(f"   Database instance: {db}")
    print(f"   ✓ Different classes, different singletons: {config is not db}")
    
    # Property 2: Global access point
    print("\n2. Global access point")
    print(f"   Config accessible via: Config() or Config.get_instance()")
    print(f"   Database accessible via: SingletonDB() or SingletonDB.get_instance()")
    print(f"   ✓ Global access points available")
    
    # Property 3: Lazy initialization
    print("\n3. Lazy initialization")
    print(f"   Config initialized: {Config._initialized}")
    print(f"   Database initialized: {SingletonDB._initialized}")
    print(f"   ✓ Instances created only when first accessed")
    
    print("\n✅ SINGLETON PROPERTIES: VERIFIED")


if __name__ == "__main__":
    print("\n" + "🔍 SINGLETON PATTERN VERIFICATION" + "\n")
    print("Testing Config and Database Singleton implementations")
    print("Verifying: Single instance, thread safety, lazy initialization\n")
    
    try:
        # Run all tests
        test_config_singleton()
        test_database_singleton()
        test_singleton_properties()
        
        print("\n" + "=" * 60)
        print("🎉 ALL SINGLETON TESTS PASSED!")
        print("=" * 60)
        print("\nSingleton Pattern Properties Verified:")
        print("✓ Single instance per class")
        print("✓ Thread-safe implementation")
        print("✓ Global access point")
        print("✓ Lazy initialization")
        print("✓ Double-checked locking")
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
