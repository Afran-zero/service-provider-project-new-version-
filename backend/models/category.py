from mongoengine import Document, StringField, ListField

class CategoryModel(Document):
    meta = {'collection': 'categories'}
    # Unique machine-readable name (slug)
    name = StringField(required=True, unique=True)
    # Human-friendly display name
    display_name = StringField(required=True)
    # Optional description
    description = StringField(default='')
    # Icon string: emoji (e.g., "🧹") or bootstrap suffix/full (e.g., "brush-fill" or "bi-brush-fill")
    icon = StringField(default='')
    # Tags for search/autocomplete
    tags = ListField(StringField(), default=list)
