"""
File service implementation for business logic layer.

This module handles all file operations including DXF loading, 
product management, and file-related business logic.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from PySide6.QtCore import QObject, Signal

from ...core.exceptions.main_exceptions import BusinessControllerError


class FileService(QObject):
    """
    Service for handling file operations and product management.
    
    This service provides file loading, product management,
    and related business operations.
    """
    
    # Signals for file operations
    file_loaded = Signal(str, dict)  # file_path, file_info
    file_load_failed = Signal(str)  # error_message
    product_loaded = Signal(str, dict)  # product_name, product_info
    product_load_failed = Signal(str)  # error_message
    
    def __init__(self):
        """Initialize the file service."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # File state
        self.current_file_path: Optional[str] = None
        self.current_product: Optional[str] = None
        self._loaded_files: Dict[str, Any] = {}
        
        # Business service integration
        self._business_service: Optional[Any] = None
        
        self.logger.debug("File service initialized")
    
    @property
    def business_service(self):
        """Get business service (lazy loading)"""
        if self._business_service is None:
            from .business_service import get_business_service
            self._business_service = get_business_service()
        return self._business_service
    
    def load_dxf_file(self, file_path: str) -> None:
        """
        Load a DXF file.
        
        Args:
            file_path: Path to the DXF file
        """
        try:
            if not file_path or not Path(file_path).exists():
                error_msg = f"File not found: {file_path}"
                self.logger.error(error_msg)
                self.file_load_failed.emit(error_msg)
                return
            
            # Use business service to parse DXF
            hole_collection = self.business_service.parse_dxf_file(file_path)
            
            if not hole_collection:
                error_msg = f"Failed to parse DXF file: {file_path}"
                self.logger.error(error_msg)
                self.file_load_failed.emit(error_msg)
                return
            
            # Apply hole numbering
            hole_collection = self.business_service.apply_hole_numbering(
                hole_collection, strategy="grid"
            )
            
            # Set to shared data manager
            if not self.business_service.set_hole_collection(hole_collection):
                error_msg = f"Failed to set hole collection: {file_path}"
                self.logger.error(error_msg)
                self.file_load_failed.emit(error_msg)
                return
            
            # Update state
            self.current_file_path = file_path
            self._loaded_files[file_path] = hole_collection
            
            # Create file info
            file_info = {
                'file_path': file_path,
                'hole_collection': hole_collection,
                'hole_count': len(hole_collection.holes) if hole_collection else 0,
                'file_size': Path(file_path).stat().st_size
            }
            
            self.logger.info(f"Successfully loaded DXF file: {file_path}")
            self.file_loaded.emit(file_path, file_info)
            
        except Exception as e:
            error_msg = f"Failed to load DXF file {file_path}: {e}"
            self.logger.error(error_msg)
            self.file_load_failed.emit(error_msg)
    
    def load_product(self, product_name: str) -> None:
        """
        Load a product configuration.
        
        Args:
            product_name: Name of the product to load
        """
        try:
            # Use business service to select product
            if not self.business_service.select_product(product_name):
                error_msg = f"Failed to select product: {product_name}"
                self.logger.error(error_msg)
                self.product_load_failed.emit(error_msg)
                return
            
            # Update state
            self.current_product = product_name
            
            # Get product info
            current_product = self.business_service.current_product
            product_info = {
                'product_name': product_name,
                'product_object': current_product,
                'has_dxf': hasattr(current_product, 'dxf_file_path') and current_product.dxf_file_path
            }
            
            self.logger.info(f"Successfully loaded product: {product_name}")
            self.product_loaded.emit(product_name, product_info)
            
        except Exception as e:
            error_msg = f"Failed to load product {product_name}: {e}"
            self.logger.error(error_msg)
            self.product_load_failed.emit(error_msg)
    
    def get_available_products(self) -> List[str]:
        """
        Get list of available products.
        
        Returns:
            List of available product names
        """
        try:
            return self.business_service.get_product_list()
            
        except Exception as e:
            self.logger.error(f"Failed to get available products: {e}")
            return []
    
    def get_current_file_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently loaded file.
        
        Returns:
            Dictionary with file information or None
        """
        if not self.current_file_path or self.current_file_path not in self._loaded_files:
            return None
        
        try:
            file_path = Path(self.current_file_path)
            hole_collection = self._loaded_files[self.current_file_path]
            
            return {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': file_path.stat().st_size,
                'hole_count': len(hole_collection.holes) if hole_collection else 0,
                'hole_collection': hole_collection
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get current file info: {e}")
            return None
    
    def get_current_product_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently loaded product.
        
        Returns:
            Dictionary with product information or None
        """
        if not self.current_product:
            return None
        
        try:
            current_product = self.business_service.current_product
            if not current_product:
                return None
            
            return {
                'product_name': self.current_product,
                'product_id': getattr(current_product, 'id', None),
                'model_name': getattr(current_product, 'model_name', self.current_product),
                'dxf_file_path': getattr(current_product, 'dxf_file_path', None),
                'description': getattr(current_product, 'description', ''),
                'product_object': current_product
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get current product info: {e}")
            return None
    
    def reload_current_file(self) -> None:
        """Reload the currently loaded file."""
        if self.current_file_path:
            self.load_dxf_file(self.current_file_path)
    
    def clear_current_file(self) -> None:
        """Clear the currently loaded file."""
        if self.current_file_path:
            self._loaded_files.pop(self.current_file_path, None)
        
        self.current_file_path = None
        self.logger.debug("Current file cleared")
    
    def clear_current_product(self) -> None:
        """Clear the currently loaded product."""
        self.current_product = None
        self.business_service.current_product = None
        self.logger.debug("Current product cleared")
    
    def get_file_history(self) -> List[str]:
        """
        Get list of previously loaded files.
        
        Returns:
            List of file paths
        """
        return list(self._loaded_files.keys())
    
    def cleanup(self) -> None:
        """Clean up resources when shutting down."""
        try:
            self._loaded_files.clear()
            self.current_file_path = None
            self.current_product = None
            
            self.logger.debug("File service cleaned up")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup file service: {e}")