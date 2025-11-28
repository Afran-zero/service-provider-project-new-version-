# patterns/cloudinary_adapter.py
"""
Adapter Pattern for Cloudinary Image Service

Provides a common interface for image storage operations,
abstracting Cloudinary-specific implementation details.
"""

from abc import ABC, abstractmethod
import cloudinary
import cloudinary.uploader
import cloudinary.api
from config import Config
import logging

logger = logging.getLogger(__name__)


class ImageStorageAdapter(ABC):
    """Abstract interface for image storage services"""
    
    @abstractmethod
    def upload(self, file, folder, public_id=None, transformations=None):
        """
        Upload an image
        
        Args:
            file: File object or path
            folder: Destination folder
            public_id: Unique identifier (optional)
            transformations: Image transformations dict
            
        Returns:
            dict with 'url', 'public_id', 'width', 'height'
        """
        pass
    
    @abstractmethod
    def delete(self, public_id_or_url):
        """
        Delete an image
        
        Args:
            public_id_or_url: Image identifier or full URL
            
        Returns:
            Boolean indicating success
        """
        pass
    
    @abstractmethod
    def get_url(self, public_id, transformations=None):
        """
        Get image URL with optional transformations
        
        Args:
            public_id: Image identifier
            transformations: Image transformations dict
            
        Returns:
            Image URL string
        """
        pass
    
    @abstractmethod
    def get_thumbnail_url(self, public_id, size=150):
        """
        Get thumbnail URL
        
        Args:
            public_id: Image identifier
            size: Thumbnail size in pixels
            
        Returns:
            Thumbnail URL string
        """
        pass


class CloudinaryAdapter(ImageStorageAdapter):
    """
    Adapter for Cloudinary image storage service
    """
    
    def __init__(self):
        self._configured = False
        self._config = None
    
    def _ensure_configured(self):
        """Lazy load Cloudinary configuration"""
        if not self._configured:
            self._config = Config.get_instance()
            
            cloudinary.config(
                cloud_name=self._config.CLOUDINARY_CLOUD_NAME,
                api_key=self._config.CLOUDINARY_API_KEY,
                api_secret=self._config.CLOUDINARY_API_SECRET,
                secure=True
            )
            
            self._configured = True
            logger.info("Cloudinary adapter configured")
    
    def upload(self, file, folder, public_id=None, transformations=None):
        """
        Upload image to Cloudinary
        
        Args:
            file: File object or path
            folder: Cloudinary folder path
            public_id: Custom public ID (optional)
            transformations: dict with 'width', 'height', 'quality', 'crop', etc.
            
        Returns:
            dict with image details
        """
        self._ensure_configured()
        
        try:
            # Build upload options
            upload_options = {
                'folder': folder,
                'resource_type': 'image'
            }
            
            if public_id:
                upload_options['public_id'] = public_id
            
            # Apply transformations during upload
            if transformations:
                if 'width' in transformations or 'height' in transformations:
                    upload_options['transformation'] = {
                        'width': transformations.get('width', 500),
                        'height': transformations.get('height', 500),
                        'crop': transformations.get('crop', 'limit'),
                        'quality': transformations.get('quality', 'auto:good')
                    }
            else:
                # Default transformation
                upload_options['transformation'] = {
                    'width': 500,
                    'height': 500,
                    'crop': 'limit',
                    'quality': 'auto:good'
                }
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(file, **upload_options)
            
            logger.info(f"Image uploaded successfully: {result.get('public_id')}")
            
            return {
                'url': result.get('secure_url'),
                'public_id': result.get('public_id'),
                'width': result.get('width'),
                'height': result.get('height'),
                'format': result.get('format'),
                'bytes': result.get('bytes')
            }
            
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {str(e)}")
            raise
    
    def delete(self, public_id_or_url):
        """
        Delete image from Cloudinary
        
        Args:
            public_id_or_url: Cloudinary public ID or full URL
            
        Returns:
            Boolean indicating success
        """
        self._ensure_configured()
        
        try:
            # Extract public_id from URL if needed
            public_id = self._extract_public_id(public_id_or_url)
            
            if not public_id:
                logger.warning(f"Could not extract public_id from: {public_id_or_url}")
                return False
            
            result = cloudinary.uploader.destroy(public_id)
            
            success = result.get('result') == 'ok'
            if success:
                logger.info(f"Image deleted successfully: {public_id}")
            else:
                logger.warning(f"Image deletion failed: {public_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Cloudinary delete failed: {str(e)}")
            return False
    
    def get_url(self, public_id, transformations=None):
        """
        Generate Cloudinary URL with transformations
        
        Args:
            public_id: Cloudinary public ID or full URL
            transformations: dict with 'width', 'height', 'quality', 'effect', etc.
            
        Returns:
            Transformed image URL
        """
        self._ensure_configured()
        
        # If already a full URL, return as-is
        if isinstance(public_id, str) and public_id.startswith('http'):
            return public_id
        
        # Extract public_id from URL if needed
        public_id = self._extract_public_id(public_id)
        
        if not public_id:
            return None
        
        try:
            # Build transformation parameters
            transform_params = {}
            
            if transformations:
                if 'width' in transformations:
                    transform_params['width'] = transformations['width']
                if 'height' in transformations:
                    transform_params['height'] = transformations['height']
                if 'quality' in transformations:
                    transform_params['quality'] = transformations['quality']
                if 'crop' in transformations:
                    transform_params['crop'] = transformations['crop']
                if 'effect' in transformations:
                    transform_params['effect'] = transformations['effect']
                if 'format' in transformations:
                    transform_params['format'] = transformations['format']
            
            # Generate URL
            url, options = cloudinary.utils.cloudinary_url(
                public_id,
                secure=True,
                **transform_params
            )
            
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate Cloudinary URL: {str(e)}")
            return None
    
    def get_thumbnail_url(self, public_id, size=150):
        """
        Get thumbnail URL with square crop
        
        Args:
            public_id: Cloudinary public ID or URL
            size: Thumbnail size in pixels (default 150)
            
        Returns:
            Thumbnail URL
        """
        transformations = {
            'width': size,
            'height': size,
            'crop': 'fill',
            'gravity': 'auto',
            'quality': 'auto:good',
            'format': 'auto'
        }
        
        return self.get_url(public_id, transformations)
    
    def get_optimized_url(self, public_id, width=500, height=500, lazy=True):
        """
        Get optimized URL with lazy loading support
        
        Args:
            public_id: Cloudinary public ID or URL
            width: Maximum width
            height: Maximum height
            lazy: Enable lazy loading with blur placeholder
            
        Returns:
            Optimized image URL
        """
        transformations = {
            'width': width,
            'height': height,
            'crop': 'limit',
            'quality': 'auto:good',
            'format': 'auto',
            'fetch_format': 'auto'
        }
        
        if lazy:
            transformations['effect'] = 'blur:400'
            transformations['quality'] = 'auto:low'
        
        return self.get_url(public_id, transformations)
    
    def _extract_public_id(self, public_id_or_url):
        """
        Extract public_id from Cloudinary URL
        
        Args:
            public_id_or_url: Public ID or full Cloudinary URL
            
        Returns:
            Extracted public_id or original string
        """
        if not isinstance(public_id_or_url, str):
            return None
        
        # If it's already a public_id (no http), return as-is
        if not public_id_or_url.startswith('http'):
            return public_id_or_url
        
        try:
            # Extract from Cloudinary URL pattern
            # Example: https://res.cloudinary.com/cloud/image/upload/v123/folder/image.jpg
            parts = public_id_or_url.split('/upload/')
            if len(parts) == 2:
                # Remove version number (v123456/)
                path_parts = parts[1].split('/')
                if path_parts[0].startswith('v'):
                    path_parts = path_parts[1:]
                
                # Join folder and filename, remove extension
                public_id = '/'.join(path_parts)
                public_id = public_id.rsplit('.', 1)[0]  # Remove extension
                
                return public_id
        except Exception as e:
            logger.warning(f"Failed to extract public_id: {str(e)}")
        
        return None
    
    def upload_multiple(self, files, folder, transformations=None):
        """
        Upload multiple images at once
        
        Args:
            files: List of file objects
            folder: Destination folder
            transformations: Transformations to apply to all images
            
        Returns:
            List of upload results
        """
        results = []
        
        for idx, file in enumerate(files):
            try:
                result = self.upload(
                    file,
                    folder,
                    public_id=f"image_{idx}",
                    transformations=transformations
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to upload image {idx}: {str(e)}")
                results.append({'error': str(e)})
        
        return results


# Singleton instance
_cloudinary_adapter_instance = None


def get_cloudinary_adapter():
    """Get singleton instance of CloudinaryAdapter"""
    global _cloudinary_adapter_instance
    if _cloudinary_adapter_instance is None:
        _cloudinary_adapter_instance = CloudinaryAdapter()
    return _cloudinary_adapter_instance
