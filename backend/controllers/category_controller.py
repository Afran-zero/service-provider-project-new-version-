# controllers/category_controller.py
"""
Category Controller with Factory Pattern

Manages category operations using CategoryFactory pattern
for consistent category handling and validation.
"""

from patterns.factory_category import CategoryFactory, Category


def get_category(name):
    """
    Get a category by name using Factory Pattern.
    
    Design Pattern: Factory Pattern
    - Retrieves category from factory registry
    - Merges static and database categories
    """
    return CategoryFactory.get_category(name)


def get_all_categories():
    """
    Get all available categories using Factory Pattern.
    
    Design Pattern: Factory Pattern
    - Returns all registered categories
    - Includes both static and dynamic categories
    """
    return CategoryFactory.get_all_categories()


def get_categories_dict():
    """
    Get all categories as dictionaries for API/templates.
    
    Design Pattern: Factory Pattern
    - Converts category objects to dict format
    """
    return CategoryFactory.get_categories_dict()


def search_categories(query):
    """
    Search categories by query string.
    
    Design Pattern: Factory Pattern
    - Searches across category names, tags, and descriptions
    """
    if not query or not query.strip():
        return []
    return CategoryFactory.search_categories(query)


def validate_category(name):
    """
    Validate if a category exists.
    
    Design Pattern: Factory Pattern
    - Checks factory registry for category existence
    """
    return CategoryFactory.validate_category(name)


def get_category_suggestions(partial_query):
    """
    Get category autocomplete suggestions.
    
    Design Pattern: Factory Pattern
    - Returns matching categories for autocomplete
    """
    if not partial_query or not partial_query.strip():
        return []
    return CategoryFactory.get_category_suggestions(partial_query)


def register_category(name, display_name, description, icon, tags):
    """
    Register a new category dynamically.
    
    Design Pattern: Factory Pattern
    - Adds new category to factory registry
    - Validates category structure
    
    Args:
        name: Unique category identifier
        display_name: User-friendly category name
        description: Category description
        icon: Category icon (emoji or class)
        tags: List of searchable tags
        
    Returns:
        Category object
        
    Raises:
        ValueError: If category data is invalid
    """
    if not name or not name.strip():
        raise ValueError("Category name is required")
    
    if not display_name or not display_name.strip():
        raise ValueError("Category display name is required")
    
    if CategoryFactory.validate_category(name):
        raise ValueError(f"Category '{name}' already exists")
    
    # Create and register category
    category = Category(
        name=name.strip().lower(),
        display_name=display_name.strip(),
        description=description.strip() if description else '',
        icon=icon.strip() if icon else '📦',
        tags=tags if tags else []
    )
    
    CategoryFactory.register_category(category)
    return category


def get_bootstrap_icon(category_name):
    """
    Get Bootstrap icon class for a category.
    
    Design Pattern: Factory Pattern
    - Returns appropriate icon from factory mapping
    """
    return CategoryFactory.get_bootstrap_icon(category_name)


def get_category_stats():
    """
    Get statistics about categories.
    
    Returns:
        Dict with category statistics
    """
    categories = get_all_categories()
    return {
        'total_categories': len(categories),
        'category_names': [cat.name for cat in categories],
        'categories_with_tags': sum(1 for cat in categories if cat.tags)
    }
