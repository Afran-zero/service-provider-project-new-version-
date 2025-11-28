"""Fix user phone values so a unique index on `phone` can be built.

Actions performed:
- Set unique placeholders for users with phone == null or missing.
- For duplicate non-null phones, keep the first and append a suffix to others.
- Drop the existing `phone_1` index if present and call `ensure_indexes()`
  to rebuild the unique index.

Run from backend/ with the venv active:
    python scripts/fix_user_phones.py

This script modifies user documents. Back up your DB before running.
"""
import sys
import os
from bson.objectid import ObjectId

# Ensure backend package imports resolve when run from backend/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.singleton_db import SingletonDB
from models.user import User
from mongoengine import connect


def main():
    print("Connecting to DB...")
    # initialize DB connection
    SingletonDB()

    # 1) Fix null or missing phones
    null_count = User.objects(__raw__={"phone": None}).count()
    missing_count = User.objects(__raw__={"phone": {"$exists": False}}).count()
    print(f"Users with phone null: {null_count}, missing: {missing_count}")

    # Update null phones to a unique placeholder
    for u in User.objects(__raw__={"phone": None}):
        placeholder = f"no-phone-{u.user_id}"
        print(f"Setting phone placeholder for user {u.user_id}: {placeholder}")
        u.phone = placeholder
        u.save()

    # Update missing phone field similarly
    for u in User.objects(__raw__={"phone": {"$exists": False}}):
        placeholder = f"no-phone-{u.user_id}"
        print(f"Adding phone placeholder for user {u.user_id}: {placeholder}")
        u.phone = placeholder
        u.save()

    # 2) Detect duplicate phone values (non-null)
    print("Checking for duplicate phones...")
    pipeline = [
        {"$match": {"phone": {"$ne": None}}},
        {"$group": {"_id": "$phone", "count": {"$sum": 1}, "ids": {"$push": "$_id"}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    dupes = list(User.objects.aggregate(*pipeline))
    if not dupes:
        print("No duplicate phone values found.")
    else:
        print(f"Found {len(dupes)} duplicate phone groups. Fixing...")
        for group in dupes:
            phone = group['_id']
            ids = group['ids']
            # keep the first id as canonical, change others
            for oid in ids[1:]:
                u = User.objects.get(__raw__={"_id": oid})
                new_phone = f"{u.phone}-dup-{u.user_id[:8]}"
                print(f"Updating user {u.user_id} phone {phone} -> {new_phone}")
                u.phone = new_phone
                u.save()

    # 3) Drop old index if present, then ensure indexes
    from mongoengine.connection import get_db
    db = get_db()
    try:
        indexes = db.users.index_information()
        if 'phone_1' in indexes:
            print('Dropping existing index phone_1...')
            db.users.drop_index('phone_1')
    except Exception as e:
        print('Could not inspect/drop phone index:', e)

    print('Ensuring indexes via mongoengine...')
    try:
        User.ensure_indexes()
        print('Index ensure complete.')
    except Exception as e:
        print('Error ensuring indexes:', e)

    print('Done. Please restart your Flask app and check /admin/dashboard')


if __name__ == '__main__':
    main()
