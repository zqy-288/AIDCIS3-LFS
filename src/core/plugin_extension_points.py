"""
核心插件扩展点定义
定义应用程序中可以被插件扩展的核心功能点
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Type, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

from .interfaces.plugin_interfaces import IPluginExtension


class ExtensionPointType(Enum):
    """扩展点类型"""
    DATA_PROCESSOR = "data_processor"        # 数据处理扩展
    UI_WIDGET = "ui_widget"                  # UI组件扩展
    COMMAND_HANDLER = "command_handler"      # 命令处理器扩展
    MENU_ITEM = "menu_item"                  # 菜单项扩展
    TOOLBAR_BUTTON = "toolbar_button"        # 工具栏按钮扩展
    FILE_HANDLER = "file_handler"            # 文件处理器扩展
    EXPORT_FORMAT = "export_format"          # 导出格式扩展
    IMPORT_FORMAT = "import_format"          # 导入格式扩展
    ALGORITHM = "algorithm"                  # 算法扩展
    VALIDATOR = "validator"                  # 验证器扩展
    FILTER = "filter"                        # 过滤器扩展
    THEME = "theme"                          # 主题扩展


@dataclass
class ExtensionPoint:
    """扩展点定义"""
    name: str
    type: ExtensionPointType
    description: str
    interface: Type
    required: bool = False
    multiple: bool = True
    priority: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'interface': str(self.interface),
            'required': self.required,
            'multiple': self.multiple,
            'priority': self.priority,
            'metadata': self.metadata
        }


# 数据处理扩展点接口
class IDataProcessor(IPluginExtension):
    """数据处理器接口"""
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的数据格式"""
        pass
    
    @abstractmethod
    def process_data(self, data: Any, format_type: str, options: Dict[str, Any] = None) -> Any:
        """处理数据"""
        pass
    
    @abstractmethod
    def validate_data(self, data: Any, format_type: str) -> bool:
        """验证数据"""
        pass


class IDXFDataProcessor(IDataProcessor):
    """DXF数据处理器接口"""
    
    @abstractmethod
    def parse_dxf_entities(self, dxf_content: str) -> List[Dict[str, Any]]:
        """解析DXF实体"""
        pass
    
    @abstractmethod
    def extract_hole_data(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取孔数据"""
        pass
    
    @abstractmethod
    def calculate_statistics(self, hole_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算统计信息"""
        pass


# UI扩展点接口
class IUIWidget(IPluginExtension):
    """UI组件接口"""
    
    @abstractmethod
    def get_widget_info(self) -> Dict[str, Any]:
        """获取组件信息"""
        pass
    
    @abstractmethod
    def create_widget(self, parent=None) -> Any:
        """创建组件实例"""
        pass
    
    @abstractmethod
    def get_widget_config(self) -> Dict[str, Any]:
        """获取组件配置"""
        pass


class IToolbarButton(IPluginExtension):
    """工具栏按钮接口"""
    
    @abstractmethod
    def get_button_info(self) -> Dict[str, str]:
        """获取按钮信息（text, icon, tooltip等）"""
        pass
    
    @abstractmethod
    def get_action_handler(self) -> Callable:
        """获取按钮点击处理器"""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """检查按钮是否启用"""
        pass


class IMenuItem(IPluginExtension):
    """菜单项接口"""
    
    @abstractmethod
    def get_menu_path(self) -> str:
        """获取菜单路径（如：'文件/导入/DXF文件'）"""
        pass
    
    @abstractmethod
    def get_menu_info(self) -> Dict[str, str]:
        """获取菜单信息"""
        pass
    
    @abstractmethod
    def get_action_handler(self) -> Callable:
        """获取菜单点击处理器"""
        pass


# 文件处理扩展点接口
class IFileHandler(IPluginExtension):
    """文件处理器接口"""
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名"""
        pass
    
    @abstractmethod
    def can_handle_file(self, file_path: str) -> bool:
        """检查是否可以处理指定文件"""
        pass
    
    @abstractmethod
    def handle_file(self, file_path: str, options: Dict[str, Any] = None) -> Any:
        """处理文件"""
        pass


class IExportFormat(IPluginExtension):
    """导出格式接口"""
    
    @abstractmethod
    def get_format_info(self) -> Dict[str, str]:
        """获取格式信息（名称、扩展名、描述等）"""
        pass
    
    @abstractmethod
    def export_data(self, data: Any, output_path: str, options: Dict[str, Any] = None) -> bool:
        """导出数据"""
        pass
    
    @abstractmethod
    def get_export_options(self) -> Dict[str, Any]:
        """获取导出选项配置"""
        pass


class IImportFormat(IPluginExtension):
    """导入格式接口"""
    
    @abstractmethod
    def get_format_info(self) -> Dict[str, str]:
        """获取格式信息"""
        pass
    
    @abstractmethod
    def import_data(self, file_path: str, options: Dict[str, Any] = None) -> Any:
        """导入数据"""
        pass
    
    @abstractmethod
    def validate_file(self, file_path: str) -> bool:
        """验证文件格式"""
        pass


# 算法扩展点接口
class IAlgorithm(IPluginExtension):
    """算法接口"""
    
    @abstractmethod
    def get_algorithm_info(self) -> Dict[str, Any]:
        """获取算法信息"""
        pass
    
    @abstractmethod
    def execute_algorithm(self, input_data: Any, parameters: Dict[str, Any] = None) -> Any:
        """执行算法"""
        pass
    
    @abstractmethod
    def get_parameter_schema(self) -> Dict[str, Any]:
        """获取参数配置模式"""
        pass


class IHoleDetectionAlgorithm(IAlgorithm):
    """孔检测算法接口"""
    
    @abstractmethod
    def detect_holes(self, image_data: Any, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """检测孔位"""
        pass
    
    @abstractmethod
    def get_detection_confidence(self, detection_result: Dict[str, Any]) -> float:
        """获取检测置信度"""
        pass


# 验证器扩展点接口
class IValidator(IPluginExtension):
    """验证器接口"""
    
    @abstractmethod
    def get_validator_info(self) -> Dict[str, str]:
        """获取验证器信息"""
        pass
    
    @abstractmethod
    def validate(self, data: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行验证，返回验证结果"""
        pass
    
    @abstractmethod
    def get_validation_rules(self) -> List[Dict[str, Any]]:
        """获取验证规则列表"""
        pass


# 过滤器扩展点接口  
class IFilter(IPluginExtension):
    """过滤器接口"""
    
    @abstractmethod
    def get_filter_info(self) -> Dict[str, str]:
        """获取过滤器信息"""
        pass
    
    @abstractmethod
    def apply_filter(self, data: Any, criteria: Dict[str, Any] = None) -> Any:
        """应用过滤器"""
        pass
    
    @abstractmethod
    def get_filter_criteria_schema(self) -> Dict[str, Any]:
        """获取过滤条件配置模式"""
        pass


# 主题扩展点接口
class ITheme(IPluginExtension):
    """主题接口"""
    
    @abstractmethod
    def get_theme_info(self) -> Dict[str, str]:
        """获取主题信息"""
        pass
    
    @abstractmethod
    def get_style_sheet(self) -> str:
        """获取样式表"""
        pass
    
    @abstractmethod
    def get_color_scheme(self) -> Dict[str, str]:
        """获取颜色方案"""
        pass
    
    @abstractmethod
    def get_icons(self) -> Dict[str, str]:
        """获取图标映射"""
        pass


class ExtensionPointRegistry:
    """扩展点注册表"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)
        self._extension_points: Dict[str, ExtensionPoint] = {}
        self._extensions: Dict[str, List[IPluginExtension]] = {}
        
        # 注册核心扩展点
        self._register_core_extension_points()
    
    def _register_core_extension_points(self):
        """注册核心扩展点"""
        core_points = [
            # 数据处理扩展点
            ExtensionPoint(
                name="dxf_data_processor",
                type=ExtensionPointType.DATA_PROCESSOR,
                description="DXF数据处理器扩展点",
                interface=IDXFDataProcessor,
                multiple=True
            ),
            ExtensionPoint(
                name="general_data_processor", 
                type=ExtensionPointType.DATA_PROCESSOR,
                description="通用数据处理器扩展点",
                interface=IDataProcessor,
                multiple=True
            ),
            
            # UI扩展点
            ExtensionPoint(
                name="main_toolbar_button",
                type=ExtensionPointType.TOOLBAR_BUTTON,
                description="主工具栏按钮扩展点",
                interface=IToolbarButton,
                multiple=True
            ),
            ExtensionPoint(
                name="main_menu_item",
                type=ExtensionPointType.MENU_ITEM,
                description="主菜单项扩展点",
                interface=IMenuItem,
                multiple=True
            ),
            ExtensionPoint(
                name="custom_widget",
                type=ExtensionPointType.UI_WIDGET,
                description="自定义UI组件扩展点",
                interface=IUIWidget,
                multiple=True
            ),
            
            # 文件处理扩展点
            ExtensionPoint(
                name="file_handler",
                type=ExtensionPointType.FILE_HANDLER,
                description="文件处理器扩展点",
                interface=IFileHandler,
                multiple=True
            ),
            ExtensionPoint(
                name="export_format",
                type=ExtensionPointType.EXPORT_FORMAT,
                description="导出格式扩展点",
                interface=IExportFormat,
                multiple=True
            ),
            ExtensionPoint(
                name="import_format",
                type=ExtensionPointType.IMPORT_FORMAT,
                description="导入格式扩展点",
                interface=IImportFormat,
                multiple=True
            ),
            
            # 算法扩展点
            ExtensionPoint(
                name="hole_detection_algorithm",
                type=ExtensionPointType.ALGORITHM,
                description="孔检测算法扩展点",
                interface=IHoleDetectionAlgorithm,
                multiple=True
            ),
            ExtensionPoint(
                name="general_algorithm",
                type=ExtensionPointType.ALGORITHM,
                description="通用算法扩展点",
                interface=IAlgorithm,
                multiple=True
            ),
            
            # 验证和过滤扩展点
            ExtensionPoint(
                name="data_validator",
                type=ExtensionPointType.VALIDATOR,
                description="数据验证器扩展点",
                interface=IValidator,
                multiple=True
            ),
            ExtensionPoint(
                name="data_filter",
                type=ExtensionPointType.FILTER,
                description="数据过滤器扩展点",
                interface=IFilter,
                multiple=True
            ),
            
            # 主题扩展点
            ExtensionPoint(
                name="application_theme",
                type=ExtensionPointType.THEME,
                description="应用程序主题扩展点",
                interface=ITheme,
                multiple=True
            )
        ]
        
        for point in core_points:
            self._extension_points[point.name] = point
            self._extensions[point.name] = []
        
        if self._logger:
            self._logger.info(f"注册了 {len(core_points)} 个核心扩展点")
    
    def register_extension_point(self, extension_point: ExtensionPoint):
        """注册扩展点"""
        self._extension_points[extension_point.name] = extension_point
        if extension_point.name not in self._extensions:
            self._extensions[extension_point.name] = []
        
        if self._logger:
            self._logger.info(f"注册扩展点: {extension_point.name}")
    
    def register_extension(self, extension_point_name: str, extension: IPluginExtension) -> bool:
        """注册扩展实现"""
        if extension_point_name not in self._extension_points:
            if self._logger:
                self._logger.error(f"扩展点 {extension_point_name} 不存在")
            return False
        
        point = self._extension_points[extension_point_name]
        
        # 检查接口兼容性
        if not isinstance(extension, point.interface):
            if self._logger:
                self._logger.error(f"扩展 {extension} 不实现接口 {point.interface}")
            return False
        
        # 检查是否允许多个扩展
        if not point.multiple and len(self._extensions[extension_point_name]) > 0:
            if self._logger:
                self._logger.error(f"扩展点 {extension_point_name} 不允许多个扩展")
            return False
        
        self._extensions[extension_point_name].append(extension)
        
        if self._logger:
            self._logger.info(f"注册扩展到 {extension_point_name}: {extension}")
        
        return True
    
    def unregister_extension(self, extension_point_name: str, extension: IPluginExtension) -> bool:
        """注销扩展实现"""
        if extension_point_name not in self._extensions:
            return False
        
        try:
            self._extensions[extension_point_name].remove(extension)
            if self._logger:
                self._logger.info(f"注销扩展 {extension} 从 {extension_point_name}")
            return True
        except ValueError:
            return False
    
    def get_extensions(self, extension_point_name: str) -> List[IPluginExtension]:
        """获取扩展点的所有扩展"""
        return self._extensions.get(extension_point_name, []).copy()
    
    def get_extension_point(self, name: str) -> Optional[ExtensionPoint]:
        """获取扩展点定义"""
        return self._extension_points.get(name)
    
    def list_extension_points(self) -> List[ExtensionPoint]:
        """列出所有扩展点"""
        return list(self._extension_points.values())
    
    def get_extensions_by_type(self, extension_type: ExtensionPointType) -> Dict[str, List[IPluginExtension]]:
        """按类型获取扩展"""
        result = {}
        for name, point in self._extension_points.items():
            if point.type == extension_type:
                result[name] = self._extensions.get(name, [])
        return result
    
    def clear_extensions(self, extension_point_name: str):
        """清除扩展点的所有扩展"""
        if extension_point_name in self._extensions:
            self._extensions[extension_point_name].clear()
    
    def get_registry_statistics(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        total_points = len(self._extension_points)
        total_extensions = sum(len(extensions) for extensions in self._extensions.values())
        
        by_type = {}
        for point in self._extension_points.values():
            type_name = point.type.value
            if type_name not in by_type:
                by_type[type_name] = {'points': 0, 'extensions': 0}
            by_type[type_name]['points'] += 1
            by_type[type_name]['extensions'] += len(self._extensions.get(point.name, []))
        
        return {
            'total_extension_points': total_points,
            'total_extensions': total_extensions,
            'by_type': by_type,
            'extension_points': {name: len(self._extensions.get(name, [])) 
                               for name in self._extension_points.keys()}
        }


# 全局扩展点注册表实例
_extension_registry = None

def get_extension_registry() -> ExtensionPointRegistry:
    """获取全局扩展点注册表"""
    global _extension_registry
    if _extension_registry is None:
        _extension_registry = ExtensionPointRegistry()
    return _extension_registry


# 便捷函数
def register_extension(extension_point_name: str, extension: IPluginExtension) -> bool:
    """注册扩展（便捷函数）"""
    return get_extension_registry().register_extension(extension_point_name, extension)


def get_extensions(extension_point_name: str) -> List[IPluginExtension]:
    """获取扩展（便捷函数）"""
    return get_extension_registry().get_extensions(extension_point_name)


def unregister_extension(extension_point_name: str, extension: IPluginExtension) -> bool:
    """注销扩展（便捷函数）"""
    return get_extension_registry().unregister_extension(extension_point_name, extension)