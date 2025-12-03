# Adapter Pattern: Cloudinary Image Storage

## Overview

The Cloudinary image storage implementation uses the **Adapter Design Pattern** to provide a uniform interface for image operations while abstracting away the Cloudinary-specific implementation details.

## Pattern Structure

### Abstract Interface: `ImageStorageAdapter`

```python
class ImageStorageAdapter(ABC):
    """Abstract interface for image storage services"""
    
    @abstractmethod
    def upload(self, file, folder, public_id=None, transformations=None):
        """Upload an image and return metadata"""
        pass
    
    @abstractmethod
    def delete(self, public_id_or_url):
        """Delete an image by ID or URL"""
        pass
    
    @abstractmethod
    def get_url(self, public_id, transformations=None):
        """Get image URL with optional transformations"""
        pass
    
    @abstractmethod
    def get_thumbnail_url(self, public_id, size=150):
        """Get thumbnail URL"""
        pass
```

### Concrete Adapter: `CloudinaryAdapter`

Located in `backend/patterns/cloudinary_adapter.py`, this class implements the abstract interface and wraps all Cloudinary-specific API calls.

```python
class CloudinaryAdapter(ImageStorageAdapter):
    """Adapter for Cloudinary image storage service"""
    
    def __init__(self):
        self._configured = False
        self._config = None
    
    def _ensure_configured(self):
        """Lazy load Cloudinary configuration"""
        # Configures cloudinary.config() only when first needed
        
    def upload(self, file, folder, public_id=None, transformations=None):
        """Implements upload using cloudinary.uploader.upload()"""
        
    def delete(self, public_id_or_url):
        """Implements delete using cloudinary.uploader.destroy()"""
        
    def get_url(self, public_id, transformations=None):
        """Implements URL generation using cloudinary.utils.cloudinary_url()"""
        
    def get_thumbnail_url(self, public_id, size=150):
        """Implements thumbnail URL generation"""
```

## Architecture Layers

### Layer 1: Adapter Pattern (Abstraction)
**File**: `backend/patterns/cloudinary_adapter.py`
- Only file that imports `cloudinary.uploader` and `cloudinary.api`
- Implements abstract interface
- Handles Cloudinary-specific logic
- Manages configuration and authentication

### Layer 2: Utility Wrapper Functions
**File**: `backend/utils.py`
- Provides convenient wrapper functions
- Delegates all operations to the adapter
- Simplifies common operations

```python
def upload_image_to_cloudinary(file, folder="uploads", public_id=None):
    adapter = _get_cloudinary()
    transformations = {
        "width": 500,
        "height": 500,
        "quality": "auto:good",
        "crop": "limit"
    }
    result = adapter.upload(file, folder, public_id, transformations)
    return result.get('url') if result else None

def delete_image_from_cloudinary(public_id_or_url):
    adapter = _get_cloudinary()
    return adapter.delete(public_id_or_url)

def get_cloudinary_url(public_id_or_url, width=None, height=None, quality="auto:good", lazy=False):
    adapter = _get_cloudinary()
    transformations = {...}
    return adapter.get_url(public_id_or_url, transformations)

def get_cloudinary_thumbnail_url(public_id_or_url, size=150):
    adapter = _get_cloudinary()
    return adapter.get_thumbnail_url(public_id_or_url, size)
```

### Layer 3: Controllers (Business Logic)
**Files**: `backend/controllers/business_controller.py`, `backend/controllers/user_controller.py`
- Import utility functions from `utils.py`
- Never import cloudinary directly
- Handle business logic for image operations

```python
from utils import upload_image_to_cloudinary, delete_image_from_cloudinary

def create_business(owner_id, data, profile_pic=None, gallery_pics=None):
    if profile_pic:
        folder = f"businesses/{owner_key}"
        public_id = f"profile_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        profile_pic_url = upload_image_to_cloudinary(profile_pic, folder, public_id)
    
    # Create business with uploaded image URL
```

### Layer 4: Views (Request Handling)
**Files**: `backend/views/business.py`, `backend/views/home.py`
- Extract files from `request.files`
- Pass files to controller functions
- No direct image handling

```python
@business_bp.route('/create', methods=['POST'])
def create_business():
    profile_pic = request.files.get('profile_pic')
    gallery_pics = request.files.getlist('gallery_pics')
    
    business = business_controller.create_business(
        owner_id=current_user.user_id,
        data=data,
        profile_pic=profile_pic if profile_pic and profile_pic.filename else None,
        gallery_pics=[pic for pic in gallery_pics if pic and pic.filename]
    )
```

## Complete Data Flow

```
┌─────────────────┐
│  View Layer     │  Extract files from request.files
│  (business.py)  │
└────────┬────────┘
         │ profile_pic, gallery_pics
         ↓
┌─────────────────┐
│  Controller     │  Business logic, generate folder/public_id
│  (business_     │
│   controller)   │
└────────┬────────┘
         │ file, folder, public_id
         ↓
┌─────────────────┐
│  Utils Layer    │  Apply default transformations
│  (utils.py)     │
└────────┬────────┘
         │ file, folder, public_id, transformations
         ↓
┌─────────────────┐
│  Adapter        │  Configure Cloudinary, execute upload
│  (cloudinary_   │
│   adapter.py)   │
└────────┬────────┘
         │ cloudinary.uploader.upload()
         ↓
┌─────────────────┐
│  Cloudinary API │  Cloud storage
└─────────────────┘
```

## Key Features

### 1. Lazy Configuration
The adapter only configures Cloudinary when first used, not at import time:

```python
def _ensure_configured(self):
    if not self._configured:
        self._config = Config.get_instance()
        cloudinary.config(
            cloud_name=self._config.CLOUDINARY_CLOUD_NAME,
            api_key=self._config.CLOUDINARY_API_KEY,
            api_secret=self._config.CLOUDINARY_API_SECRET,
            secure=True
        )
        self._configured = True
```

### 2. Singleton Pattern
The adapter uses a singleton pattern to ensure only one instance exists:

```python
_cloudinary_adapter_instance = None

def get_cloudinary_adapter():
    global _cloudinary_adapter_instance
    if _cloudinary_adapter_instance is None:
        _cloudinary_adapter_instance = CloudinaryAdapter()
    return _cloudinary_adapter_instance
```

### 3. Transformation Support
Images can be transformed during upload or URL generation:

```python
transformations = {
    'width': 500,
    'height': 500,
    'crop': 'limit',      # limit, fill, scale, fit, etc.
    'quality': 'auto:good',
    'format': 'auto'
}

result = adapter.upload(file, folder, public_id, transformations)
```

### 4. URL Extraction
The adapter can extract public_id from full Cloudinary URLs:

```python
def _extract_public_id(self, public_id_or_url):
    # Extracts: "businesses/user_123/profile_20231203"
    # From: "https://res.cloudinary.com/cloud/image/upload/v123/businesses/user_123/profile_20231203.jpg"
```

## Benefits of the Adapter Pattern

### 1. **Easy Provider Switching**
To switch from Cloudinary to AWS S3 or Azure Blob Storage:
```python
class S3Adapter(ImageStorageAdapter):
    def upload(self, file, folder, public_id=None, transformations=None):
        # AWS S3 implementation
        pass
```

Then update `utils.py` to use the new adapter. No changes needed in controllers or views!

### 2. **Centralized Configuration**
All Cloudinary-specific code is in one file. API credentials, transformation defaults, and error handling are managed in a single location.

### 3. **Consistent Interface**
All image operations use the same methods regardless of storage backend:
```python
adapter.upload()      # Same interface for Cloudinary, S3, Azure, etc.
adapter.delete()
adapter.get_url()
adapter.get_thumbnail_url()
```

### 4. **Testability**
Easy to create mock adapters for testing:
```python
class MockAdapter(ImageStorageAdapter):
    def upload(self, file, folder, public_id=None, transformations=None):
        return {'url': 'http://mock.url/test.jpg', 'public_id': 'test'}
```

### 5. **Separation of Concerns**
- **Views**: Handle HTTP requests and responses
- **Controllers**: Handle business logic
- **Utils**: Provide convenient operations
- **Adapter**: Handle external service integration
- **Cloudinary API**: Cloud storage

## Usage Examples

### Upload Profile Picture
```python
# In controller
def create_business(owner_id, data, profile_pic=None):
    if profile_pic:
        folder = f"businesses/{owner_id}"
        public_id = f"profile_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        profile_pic_url = upload_image_to_cloudinary(profile_pic, folder, public_id)
        # Use profile_pic_url in business model
```

### Upload Gallery Images
```python
# In controller
gallery_urls = []
if gallery_pics:
    folder = f"businesses/{owner_id}/gallery"
    for idx, gallery_pic in enumerate(gallery_pics):
        public_id = f"gallery_{idx}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        gallery_url = upload_image_to_cloudinary(gallery_pic, folder, public_id)
        if gallery_url:
            gallery_urls.append(gallery_url)
```

### Delete Image
```python
# In controller
def update_business(business_id, data, profile_pic=None):
    business = get_business(business_id)
    
    if profile_pic and business.profile_pic_url:
        # Delete old image before uploading new one
        delete_image_from_cloudinary(business.profile_pic_url)
        
    # Upload new image
    profile_pic_url = upload_image_to_cloudinary(profile_pic, folder, public_id)
```

### Get Optimized URL
```python
# In view or template helper
from utils import get_cloudinary_url

# Get optimized URL for display
optimized_url = get_cloudinary_url(
    business.profile_pic_url,
    width=300,
    height=300,
    quality='auto:good'
)
```

### Get Thumbnail
```python
# In view or template helper
from utils import get_cloudinary_thumbnail_url

thumbnail_url = get_cloudinary_thumbnail_url(business.profile_pic_url, size=150)
```

## Error Handling

The adapter includes comprehensive error handling:

```python
def upload(self, file, folder, public_id=None, transformations=None):
    self._ensure_configured()
    
    try:
        result = cloudinary.uploader.upload(file, **upload_options)
        logger.info(f"Image uploaded successfully: {result.get('public_id')}")
        return {
            'url': result.get('secure_url'),
            'public_id': result.get('public_id'),
            'width': result.get('width'),
            'height': result.get('height')
        }
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {str(e)}")
        raise
```

## Verification Checklist

✅ **Pattern Implementation**
- Abstract interface defines contract
- Concrete adapter implements all methods
- Singleton pattern for adapter instance

✅ **Separation of Concerns**
- Only adapter file imports cloudinary
- Controllers use utility functions
- Views pass files to controllers

✅ **Features**
- Upload with transformations
- Delete images
- Generate URLs with transformations
- Generate thumbnails
- Extract public_id from URLs
- Lazy configuration loading
- Error handling and logging

✅ **Benefits**
- Easy to switch storage providers
- Centralized configuration
- Consistent interface
- Testable with mocks
- Follows SOLID principles

## Related Patterns

This implementation combines multiple design patterns:

1. **Adapter Pattern**: Wraps Cloudinary API with uniform interface
2. **Singleton Pattern**: Ensures single adapter instance
3. **Lazy Initialization**: Configures only when first used
4. **Facade Pattern**: Utils layer simplifies common operations

## Conclusion

The Cloudinary adapter pattern implementation strictly follows design pattern principles and provides a clean, maintainable abstraction layer for image storage operations. The architecture ensures:

- **Maintainability**: Changes to image storage logic are isolated
- **Flexibility**: Easy to switch storage providers
- **Testability**: Can mock the adapter interface
- **Consistency**: Uniform interface across the application
- **Separation**: Clear boundaries between layers

This design makes the codebase more robust and easier to extend with new image storage providers or features.
