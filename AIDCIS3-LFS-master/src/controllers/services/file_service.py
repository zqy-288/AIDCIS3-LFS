"""
File service implementation for business logic layer.

This module handles all file-related operations including DXF loading,
product management, and file I/O operations.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from PySide6.QtCore import QObject, Signal

from ...exceptions.main_exceptions import BusinessControllerError


class FileService(QObject):
    """
    Service for handling file operations and product management.
    
    This service manages DXF file loading, product selection,
    and related file I/O operations.
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
        
        # Current file state
        self._current_file_path: Optional[str] = None
        self._current_file_info: Dict[str, Any] = {}
        self._current_product: Optional[str] = None
        self._current_product_info: Dict[str, Any] = {}
        
        # Supported file formats
        self._supported_formats = {'.dxf', '.dwg'}
        
        self.logger.debug("File service initialized")
    
    @property
    def current_file_path(self) -> Optional[str]:
        """Get the currently loaded file path."""
        return self._current_file_path
    
    @property
    def current_file_info(self) -> Dict[str, Any]:
        """Get information about the currently loaded file."""
        return self._current_file_info.copy()
    
    @property
    def current_product(self) -> Optional[str]:
        """Get the currently selected product."""
        return self._current_product
    
    @property
    def current_product_info(self) -> Dict[str, Any]:
        """Get information about the currently selected product."""
        return self._current_product_info.copy()
    
    def load_dxf_file(self, file_path: str) -> None:
        """
        Load a DXF file and extract information.
        
        Args:
            file_path: Path to the DXF file to load
        """
        try:
            # Validate file path
            if not file_path:
                raise BusinessControllerError("File path cannot be empty")
            
            path = Path(file_path)
            if not path.exists():
                raise BusinessControllerError(f"File does not exist: {file_path}")
            
            if path.suffix.lower() not in self._supported_formats:
                raise BusinessControllerError(f"Unsupported file format: {path.suffix}")
            
            # Get file information
            file_info = self._get_file_info(path)
            
            # Try to load with existing DXF parser if available
            hole_collection = None
            try:
                # Import here to avoid circular dependencies
                from src.core_business.dxf_parser import DXFParser
                dxf_parser = DXFParser()
                hole_collection = dxf_parser.parse_dxf(file_path)
                
                if hole_collection:
                    hole_count = len(hole_collection.holes) if hasattr(hole_collection, 'holes') else 0
                    file_info['hole_count'] = hole_count
                    file_info['has_data'] = hole_count > 0
                
            except Exception as e:
                self.logger.warning(f"Failed to parse DXF with existing parser: {e}")
                file_info['parse_error'] = str(e)
                file_info['has_data'] = False
            
            # Update current state
            self._current_file_path = file_path
            self._current_file_info = file_info
            
            # Emit success signal
            self.file_loaded.emit(file_path, file_info)
            self.logger.info(f"DXF file loaded successfully: {file_path}")
            
        except Exception as e:
            error_msg = f"Failed to load DXF file: {e}"
            self.logger.error(error_msg)
            self.file_load_failed.emit(error_msg)
            raise BusinessControllerError(error_msg)
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract information about a file.
        
        Args:
            file_path: Path object for the file
            
        Returns:
            Dictionary containing file information
        """
        try:
            stat = file_path.stat()
            
            return {
                'name': file_path.name,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified_time': stat.st_mtime,
                'extension': file_path.suffix.lower(),
                'directory': str(file_path.parent),
                'absolute_path': str(file_path.absolute()),
                'is_readable': os.access(file_path, os.R_OK),
                'is_writable': os.access(file_path, os.W_OK)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get file info: {e}")
            return {'name': file_path.name, 'error': str(e)}
    
    def load_product(self, product_name: str) -> None:
        """
        Load a product configuration.
        
        Args:
            product_name: Name of the product to load
        """
        try:
            if not product_name:
                raise BusinessControllerError("Product name cannot be empty")
            
            # Try to load with existing product manager if available
            product_info = {}
            try:
                # Import here to avoid circular dependencies
                from src.models.product_model import get_product_manager
                product_manager = get_product_manager()
                
                # Get product information
                if hasattr(product_manager, 'get_product_info'):
                    product_info = product_manager.get_product_info(product_name)
                elif hasattr(product_manager, 'products'):
                    products = product_manager.products
                    if product_name in products:
                        product_info = products[product_name]
                
                if not product_info:
                    raise BusinessControllerError(f"Product not found: {product_name}")
                
            except Exception as e:
                self.logger.warning(f"Failed to load product with existing manager: {e}")
                # Create basic product info
                product_info = {
                    'name': product_name,
                    'loaded_time': None,
                    'error': str(e)
                }
            
            # Update current state
            self._current_product = product_name
            self._current_product_info = product_info
            
            # Emit success signal
            self.product_loaded.emit(product_name, product_info)
            self.logger.info(f"Product loaded successfully: {product_name}")
            
        except Exception as e:
            error_msg = f"Failed to load product: {e}"
            self.logger.error(error_msg)
            self.product_load_failed.emit(error_msg)
            raise BusinessControllerError(error_msg)
    
    def get_available_products(self) -> List[str]:
        """
        Get list of available products.
        
        Returns:
            List of available product names
        """
        try:
            # Try to get from existing product manager
            try:
                from src.models.product_model import get_product_manager
                product_manager = get_product_manager()
                
                if hasattr(product_manager, 'get_available_products'):
                    return product_manager.get_available_products()
                elif hasattr(product_manager, 'products'):
                    return list(product_manager.products.keys())
                
            except Exception as e:
                self.logger.warning(f"Failed to get products from manager: {e}")
            
            # Return default products if manager not available
            return ["东重管板", "测试管板", "标准管板"]
            
        except Exception as e:
            self.logger.error(f"Failed to get available products: {e}")
            return []
    
    def validate_file_path(self, file_path: str) -> Dict[str, Any]:
        """
        Validate a file path without loading it.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            if not file_path:
                return {'valid': False, 'error': 'File path is empty'}
            
            path = Path(file_path)
            
            if not path.exists():
                return {'valid': False, 'error': 'File does not exist'}
            
            if not path.is_file():
                return {'valid': False, 'error': 'Path is not a file'}
            
            if path.suffix.lower() not in self._supported_formats:
                return {
                    'valid': False, 
                    'error': f'Unsupported format: {path.suffix}',
                    'supported_formats': list(self._supported_formats)
                }
            
            if not os.access(path, os.R_OK):
                return {'valid': False, 'error': 'File is not readable'}
            
            file_info = self._get_file_info(path)
            return {
                'valid': True,
                'file_info': file_info
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def cleanup(self) -> None:
        """Clean up resources when shutting down."""
        try:
            self._current_file_path = None
            self._current_file_info = {}
            self._current_product = None
            self._current_product_info = {}
            self.logger.debug("File service cleaned up")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup file service: {e}")