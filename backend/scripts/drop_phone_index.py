"""Quick script to drop the phone_1 index from users collection.

Run this with the Flask server STOPPED:
    python scripts/drop_phone_index.py
"""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.singleton_db import SingletonDB
from mongoengine.connection import get_db

print("Connecting to database...")
SingletonDB()
db = get_db()

try:
    print("Dropping phone_1 index...")
    db.users.drop_index('phone_1')
    print("✓ phone_1 index dropped successfully")
except Exception as e:
    print(f"Index drop error (may not exist): {e}")

print("\nDone. Now restart your Flask app (python app.py)")
