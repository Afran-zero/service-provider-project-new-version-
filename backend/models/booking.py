# models/booking.py
import mongoengine as me
import datetime
import uuid


class Booking(me.Document):
    BOOKING_STATUSES = (
        'requested',
        'accepted',
        'rejected',
        'cancelled',
        'completed'
    )

    booking_id = me.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    business_id = me.StringField(required=True)  # reference to Business.business_id
    service_id = me.StringField(required=True)  # reference to Service.service_id
    customer_id = me.StringField(required=True)  # reference to User.user_id
    staff_id = me.StringField(default=None)  # optional reference to User.user_id

    booking_time = me.DateTimeField(required=True)
    duration_minutes = me.IntField(required=True)
    price = me.FloatField(required=True)

    status = me.StringField(
        required=True,
        default='requested',
        choices=BOOKING_STATUSES
    )

    notes = me.StringField(default=None)  # Optional customer notes/special requirements

    # State transition timestamps
    timestamps = me.DictField(default=dict)
    # Structure: {
    #   "requested_at": datetime,
    #   "accepted_at": datetime,
    #   "rejected_at": datetime,
    #   "cancelled_at": datetime,
    #   "completed_at": datetime
    # }

    created_at = me.DateTimeField(default=datetime.datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "bookings",
        "indexes": [
            "business_id",
            "service_id",
            "customer_id",
            "booking_time",
            "status"
        ]
    }

    def update_status(self, new_status):
        """Update booking status with timestamp tracking"""
        if new_status not in self.BOOKING_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")

        self.status = new_status
        timestamp_key = f"{new_status}_at"
        if self.timestamps is None:
            self.timestamps = {}
        self.timestamps[timestamp_key] = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()
        self.save()