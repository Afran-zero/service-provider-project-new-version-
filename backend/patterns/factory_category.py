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
        'electric': 'lightning-charge-fill',
        'painting': 'palette2',
        'carpentry': 'hammer',
        'gardening': 'flower2',
        'hvac': 'snow2',
        'roofing': 'house',
        'pest_control': 'bug-fill',
        'appliance_repair': 'tools',
        'locksmith': 'key-fill',
        'moving': 'box-seam'
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
        'electric': Category(
            name='electric',
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
        'gardening': Category(
            name='gardening',
            display_name='Gardening & Landscaping',
            description='Expert gardeners for lawn care and landscape design',
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
        'roofing': Category(
            name='roofing',
            display_name='Roofing Services',
            description='Professional roofers for repairs and installations',
            icon='🏠',
            tags=['roof repair', 'roof installation', 'gutter cleaning', 'leak repair']
        ),
        'pest_control': Category(
            name='pest_control',
            display_name='Pest Control',
            description='Effective pest elimination and prevention services',
            icon='🐜',
            tags=['pest removal', 'termite control', 'rodent control', 'fumigation']
        ),
        'appliance_repair': Category(
            name='appliance_repair',
            display_name='Appliance Repair',
            description='Repair services for home and kitchen appliances',
            icon='🔨',
            tags=['refrigerator repair', 'washing machine', 'dishwasher', 'oven repair']
        ),
        'locksmith': Category(
            name='locksmith',
            display_name='Locksmith Services',
            description='Emergency lockout service and lock installations',
            icon='🔑',
            tags=['lock change', 'key duplication', 'emergency lockout', 'security locks']
        ),
        'moving': Category(
            name='moving',
            display_name='Moving Services',
            description='Professional movers for residential and commercial relocations',
            icon='📦',
            tags=['house moving', 'packing', 'furniture moving', 'storage']
        )
    }
    
    @staticmethod
    def get_category(name):
        """
        Get category by name
        
        Args:
            name: Category name
            
        Returns:
            Category object or None
        """
        return CategoryFactory._categories.get(name)
    
    @staticmethod
    def get_all_categories():
        """
        Get all available categories
        
        Returns:
            List of Category objects
        """
        return list(CategoryFactory._categories.values())
    
    @staticmethod
    def get_categories_dict():
        """
        Get all categories as dictionaries
        
        Returns:
            List of category dicts
        """
        return [cat.to_dict() for cat in CategoryFactory._categories.values()]
    
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
        
        for category in CategoryFactory._categories.values():
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
        return name in CategoryFactory._categories
    
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
        
        for category in CategoryFactory._categories.values():
            if query_lower in category.display_name.lower():
                suggestions.append({
                    'name': category.name,
                    'display_name': category.display_name,
                    'icon': category.icon
                })
        
        return suggestions
