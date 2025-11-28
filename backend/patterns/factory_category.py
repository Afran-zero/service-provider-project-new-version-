# patterns/factory_category.py
"""
Factory Pattern for Category Management

Provides category information, icons, validation rules,
and search filters for different service categories.
"""


class Category:
    """Base category class with common properties"""
    
    def __init__(self, name, display_name, description, icon, tags):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.icon = icon
        self.tags = tags
    
    def to_dict(self):
        """Convert category to dictionary"""
        return {
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'icon': self.icon,
            'tags': self.tags
        }


class CategoryFactory:
    """
    Factory for creating and managing service categories
    """
    
    # Map category names to Bootstrap icon classes
    _icon_map = {
        'cleaning': 'brush-fill',
        'plumbing': 'wrench-adjustable-circle-fill',
        'electrical': 'lightning-charge-fill',
        'painting': 'palette2',
        'carpentry': 'hammer',
        'landscaping': 'flower2',
        'hvac': 'snow2',
        'other': 'three-dots'
    }
    
    _categories = {
        'cleaning': Category(
            name='cleaning',
            display_name='Cleaning Services',
            description='Professional cleaning for homes, offices, and commercial spaces',
            icon='🧹',
            tags=['house cleaning', 'office cleaning', 'deep cleaning', 'maid service']
        ),
        'plumbing': Category(
            name='plumbing',
            display_name='Plumbing Services',
            description='Licensed plumbers for repairs, installations, and maintenance',
            icon='🔧',
            tags=['pipe repair', 'leak fixing', 'drain cleaning', 'water heater']
        ),
        'electrical': Category(
            name='electrical',
            display_name='Electrical Services',
            description='Certified electricians for wiring, repairs, and installations',
            icon='⚡',
            tags=['wiring', 'lighting', 'circuit breaker', 'electrical repair']
        ),
        'painting': Category(
            name='painting',
            display_name='Painting Services',
            description='Professional painters for interior and exterior projects',
            icon='🎨',
            tags=['interior painting', 'exterior painting', 'wall painting', 'house painter']
        ),
        'carpentry': Category(
            name='carpentry',
            display_name='Carpentry Services',
            description='Skilled carpenters for custom woodwork and furniture',
            icon='🪚',
            tags=['furniture assembly', 'cabinet installation', 'wood repair', 'custom woodwork']
        ),
        'landscaping': Category(
            name='landscaping',
            display_name='Landscaping',
            description='Landscape design and lawn care',
            icon='🌱',
            tags=['lawn mowing', 'landscaping', 'tree trimming', 'garden maintenance']
        ),
        'hvac': Category(
            name='hvac',
            display_name='HVAC Services',
            description='Heating, ventilation, and air conditioning experts',
            icon='❄️',
            tags=['ac repair', 'heating', 'ventilation', 'hvac maintenance']
        ),
        'other': Category(
            name='other',
            display_name='Other Services',
            description='Miscellaneous services not listed',
            icon='⋯',
            tags=['misc', 'general']
        )
    }
    
    @staticmethod
    def _db_categories_map():
        """Fetch categories from DB and return a mapping name->Category."""
        try:
            from models.category import CategoryModel
            items = CategoryModel.objects()
            db_map = {}
            for c in items:
                db_map[c.name] = Category(
                    name=c.name,
                    display_name=c.display_name or c.name,
                    description=c.description or '',
                    icon=c.icon or '',
                    tags=c.tags or []
                )
            return db_map
        except Exception:
            return {}

    @staticmethod
    def get_category(name):
        """
        Get category by name
        
        Args:
            name: Category name
            
        Returns:
            Category object or None
        """
        db_map = CategoryFactory._db_categories_map()
        return db_map.get(name) or CategoryFactory._categories.get(name)
    
    @staticmethod
    def get_all_categories():
        """
        Get all available categories
        
        Returns:
            List of Category objects
        """
        merged = dict(CategoryFactory._categories)
        db_map = CategoryFactory._db_categories_map()
        merged.update(db_map)
        return list(merged.values())
    
    @staticmethod
    def get_categories_dict():
        """
        Get all categories as dictionaries
        
        Returns:
            List of category dicts
        """
        merged = dict(CategoryFactory._categories)
        merged.update(CategoryFactory._db_categories_map())
        return [cat.to_dict() for cat in merged.values()]
    
    @staticmethod
    def search_categories(query):
        """
        Search categories by query string (matches name, tags, description)
        
        Args:
            query: Search query string
            
        Returns:
            List of matching Category objects
        """
        query_lower = query.lower()
        matches = []
        
        merged = dict(CategoryFactory._categories)
        merged.update(CategoryFactory._db_categories_map())
        for category in merged.values():
            # Search in name, display_name, description, and tags
            if (query_lower in category.name.lower() or
                query_lower in category.display_name.lower() or
                query_lower in category.description.lower() or
                any(query_lower in tag.lower() for tag in category.tags)):
                matches.append(category)
        
        return matches
    
    @staticmethod
    def validate_category(name):
        """
        Validate if category exists
        
        Args:
            name: Category name
            
        Returns:
            Boolean indicating validity
        """
        if not name:
            return False
        if name in CategoryFactory._categories:
            return True
        try:
            from models.category import CategoryModel
            return CategoryModel.objects(name=name).first() is not None
        except Exception:
            return False
    
    @staticmethod
    def get_bootstrap_icon(category_name):
        """
        Get Bootstrap icon class name for a category.
        
        Args:
            category_name: Category name (e.g., 'cleaning', 'plumbing')
            
        Returns:
            Bootstrap icon class name (e.g., 'bi-broom') or default 'bi-grid'
        """
        icon = CategoryFactory._icon_map.get(category_name, 'grid')
        return f'bi-{icon}'
    
    @staticmethod
    def register_category(category):
        """
        Register a new category
        
        Args:
            category: Category object
        """
        if not isinstance(category, Category):
            raise ValueError("category must be a Category instance")
        CategoryFactory._categories[category.name] = category
    
    @staticmethod
    def get_category_suggestions(partial_query):
        """
        Get category suggestions for autocomplete
        
        Args:
            partial_query: Partial search query
            
        Returns:
            List of category names matching the query
        """
        query_lower = partial_query.lower()
        suggestions = []
        
        merged = dict(CategoryFactory._categories)
        merged.update(CategoryFactory._db_categories_map())
        for category in merged.values():
            if query_lower in category.display_name.lower():
                suggestions.append({
                    'name': category.name,
                    'display_name': category.display_name,
                    'icon': category.icon
                })
        
        return suggestions
