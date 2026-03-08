import mongoengine as me
import datetime
import uuid

class AuditLog(me.Document):
    audit_id = me.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    action = me.StringField(required=True)
    actor_id = me.StringField(required=True)
    actor_role = me.StringField(required=False)
    target_type = me.StringField(required=False)
    target_id = me.StringField(required=False)
    details = me.DictField(default=dict)
    timestamp = me.DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        'collection': 'audit_logs',
        'indexes': ['actor_id', 'target_id', 'action', 'timestamp']
    }
