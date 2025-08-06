"""
统一共享服务模块
提供跨页面的通用服务功能
"""

from .csv_processing_service import CSVProcessingService, get_csv_processing_service
from .statistics_service import UnifiedStatisticsService, get_statistics_service
from .chart_generation_service import ChartGenerationService, get_chart_generation_service
from .archive_manager import ArchiveManager
from ..utilities.product_import_service import ProductImportService
from .business_service import BusinessService, get_business_service
from .detection_service import DetectionService, get_detection_service
from .graphics_service import GraphicsService, get_graphics_service
from .data_service import DataService, get_data_service
from .product_management_service import ProductManagementDialog

__all__ = [
    'CSVProcessingService',
    'get_csv_processing_service', 
    'UnifiedStatisticsService',
    'get_statistics_service',
    'ChartGenerationService', 
    'get_chart_generation_service',
    'ArchiveManager',
    'ProductImportService',
    'ProductManagementDialog',
    'BusinessService',
    'get_business_service',
    'DetectionService',
    'get_detection_service',
    'GraphicsService',
    'get_graphics_service',
    'DataService',
    'get_data_service'
]