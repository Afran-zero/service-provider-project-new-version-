# models/business.py
import mongoengine as me
import datetime
import uuid


class Business(me.Document):
    business_id = me.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    # Owner may be a registered user or an external contact.
    # Make `owner_id` optional so businesses can be created without a linked user.
    owner_id = me.StringField(required=False, default=None)
    # Optional human-readable owner name (for businesses without a user account)
    owner_name = me.StringField(default=None)

    name = me.StringField(required=True)
    email = me.EmailField(required=True)
    phone = me.StringField(required=True)

    street_house = me.StringField(required=True)
    city = me.StringField(required=True)
    district = me.StringField(required=True)

    description = me.StringField()
    profile_pic_url = me.StringField(default=None)
    gallery_urls = me.ListField(me.StringField(), default=list)

    category = me.StringField(required=True)  
    # ex: "cleaning", "plumbing", "electric", "painting", etc.

    is_active = me.BooleanField(default=True)

    created_at = me.DateTimeField(default=datetime.datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "businesses",
        "indexes": ["owner_id", "category", "city", "district", "is_active"]
    }


class Service(me.Document):
    service_id = me.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = me.StringField(required=True)  # reference to Business.business_id

    name = me.StringField(required=True)
    description = me.StringField()
    price = me.FloatField(required=True)
    duration_minutes = me.IntField(required=True, default=60)

    is_active = me.BooleanField(default=True)

    created_at = me.DateTimeField(default=datetime.datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "services",
        "indexes": ["business_id", "is_active"]
    }