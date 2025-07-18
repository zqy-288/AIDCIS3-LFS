"""
核心插件扩展点定义
为DXF处理、图形渲染、业务规则等核心功能提供插件扩展点
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

from src.core.interfaces.plugin_interfaces import IAsyncPlugin, PluginMetadata


class ExtensionPointType(Enum):
    """扩展点类型"""
    DXF_PARSER = "dxf_parser"
    DXF_PROCESSOR = "dxf_processor"
    GRAPHICS_RENDERER = "graphics_renderer"
    GRAPHICS_FILTER = "graphics_filter"
    BUSINESS_RULE = "business_rule"
    DATA_VALIDATOR = "data_validator"
    REPORT_GENERATOR = "report_generator"
    UI_COMPONENT = "ui_component"


@dataclass
class ExtensionPoint:
    """扩展点定义"""
    id: str
    name: str
    description: str
    extension_type: ExtensionPointType
    interface_class: type
    priority: int = 100
    required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


# DXF处理扩展点
class IDXFParserExtension(ABC):
    """DXF解析器扩展接口"""
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """检查是否可以解析指定文件"""
        pass
    
    @abstractmethod
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """解析DXF文件"""
        pass
    
    @abstractmethod
    def get_supported_versions(self) -> List[str]:
        """获取支持的DXF版本"""
        pass


class IDXFProcessorExtension(ABC):
    """DXF处理器扩展接口"""
    
    @abstractmethod
    def process_entities(self, entities: List[Any]) -> List[Any]:
        """处理DXF实体"""
        pass
    
    @abstractmethod
    def extract_holes(self, entities: List[Any]) -> List[Dict[str, Any]]:
        """从实体中提取孔位信息"""
        pass
    
    @abstractmethod
    def validate_geometry(self, geometry: Dict[str, Any]) -> bool:
        """验证几何数据"""
        pass


# 图形渲染扩展点
class IGraphicsRendererExtension(ABC):
    """图形渲染器扩展接口"""
    
    @abstractmethod
    def render_hole(self, hole_data: Dict[str, Any], context: Any) -> Any:
        """渲染孔位"""
        pass
    
    @abstractmethod
    def render_background(self, context: Any) -> Any:
        """渲染背景"""
        pass
    
    @abstractmethod
    def apply_style(self, item: Any, style: Dict[str, Any]) -> Any:
        """应用样式"""
        pass


class IGraphicsFilterExtension(ABC):
    """图形过滤器扩展接口"""
    
    @abstractmethod
    def filter_holes(self, holes: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """过滤孔位"""
        pass
    
    @abstractmethod
    def transform_coordinates(self, points: List[tuple], transformation: Dict[str, Any]) -> List[tuple]:
        """坐标变换"""
        pass


# 业务规则扩展点
class IBusinessRuleExtension(ABC):
    """业务规则扩展接口"""
    
    @abstractmethod
    def validate_hole_data(self, hole_data: Dict[str, Any]) -> List[str]:
        """验证孔位数据，返回错误信息列表"""
        pass
    
    @abstractmethod
    def calculate_metrics(self, holes: List[Dict[str, Any]]) -> Dict[str, float]:
        """计算指标"""
        pass
    
    @abstractmethod
    def apply_business_logic(self, data: Any, context: Dict[str, Any]) -> Any:
        """应用业务逻辑"""
        pass


# 数据验证扩展点
class IDataValidatorExtension(ABC):
    """数据验证器扩展接口"""
    
    @abstractmethod
    def validate_format(self, data: Any) -> bool:
        """验证数据格式"""
        pass
    
    @abstractmethod
    def validate_constraints(self, data: Any, constraints: Dict[str, Any]) -> List[str]:
        """验证约束条件"""
        pass
    
    @abstractmethod
    def sanitize_data(self, data: Any) -> Any:
        """清理数据"""
        pass


# 报告生成扩展点
class IReportGeneratorExtension(ABC):
    """报告生成器扩展接口"""
    
    @abstractmethod
    def generate_report(self, data: Dict[str, Any], template: str) -> bytes:
        """生成报告"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的格式"""
        pass
    
    @abstractmethod
    def get_template_variables(self) -> List[str]:
        """获取模板变量"""
        pass


# UI组件扩展点
class IUIComponentExtension(ABC):
    """UI组件扩展接口"""
    
    @abstractmethod
    def create_widget(self, parent=None, **kwargs) -> Any:
        """创建UI组件"""
        pass
    
    @abstractmethod
    def handle_event(self, event_type: str, data: Any) -> None:
        """处理事件"""
        pass
    
    @abstractmethod
    def get_widget_info(self) -> Dict[str, Any]:
        """获取组件信息"""
        pass


# 核心扩展点注册表
CORE_EXTENSION_POINTS = [
    ExtensionPoint(
        id="dxf_parser",
        name="DXF解析器",
        description="扩展DXF文件解析功能",
        extension_type=ExtensionPointType.DXF_PARSER,
        interface_class=IDXFParserExtension,
        priority=10,
        required=True
    ),
    ExtensionPoint(
        id="dxf_processor",
        name="DXF处理器",
        description="扩展DXF数据处理功能",
        extension_type=ExtensionPointType.DXF_PROCESSOR,
        interface_class=IDXFProcessorExtension,
        priority=20
    ),
    ExtensionPoint(
        id="graphics_renderer",
        name="图形渲染器",
        description="扩展图形渲染功能",
        extension_type=ExtensionPointType.GRAPHICS_RENDERER,
        interface_class=IGraphicsRendererExtension,
        priority=30
    ),
    ExtensionPoint(
        id="graphics_filter",
        name="图形过滤器",
        description="扩展图形过滤和变换功能",
        extension_type=ExtensionPointType.GRAPHICS_FILTER,
        interface_class=IGraphicsFilterExtension,
        priority=40
    ),
    ExtensionPoint(
        id="business_rule",
        name="业务规则",
        description="扩展业务规则和验证功能",
        extension_type=ExtensionPointType.BUSINESS_RULE,
        interface_class=IBusinessRuleExtension,
        priority=50
    ),
    ExtensionPoint(
        id="data_validator",
        name="数据验证器",
        description="扩展数据验证功能",
        extension_type=ExtensionPointType.DATA_VALIDATOR,
        interface_class=IDataValidatorExtension,
        priority=60
    ),
    ExtensionPoint(
        id="report_generator",
        name="报告生成器",
        description="扩展报告生成功能",
        extension_type=ExtensionPointType.REPORT_GENERATOR,
        interface_class=IReportGeneratorExtension,
        priority=70
    ),
    ExtensionPoint(
        id="ui_component",
        name="UI组件",
        description="扩展用户界面组件",
        extension_type=ExtensionPointType.UI_COMPONENT,
        interface_class=IUIComponentExtension,
        priority=80
    )
]


class CoreExtensionManager:
    """核心扩展管理器"""
    
    def __init__(self):
        self._extension_points: Dict[str, ExtensionPoint] = {}
        self._extensions: Dict[str, List[Any]] = {}
        
        # 注册核心扩展点
        self._register_core_extensions()
    
    def _register_core_extensions(self):
        """注册核心扩展点"""
        for ext_point in CORE_EXTENSION_POINTS:
            self._extension_points[ext_point.id] = ext_point
            self._extensions[ext_point.id] = []
    
    def register_extension(self, extension_point_id: str, extension: Any, plugin_id: str = "") -> bool:
        """注册扩展"""
        if extension_point_id not in self._extension_points:
            return False
        
        ext_point = self._extension_points[extension_point_id]
        
        # 验证扩展是否实现了正确的接口
        if not isinstance(extension, ext_point.interface_class):
            return False
        
        # 添加插件ID信息
        extension._plugin_id = plugin_id
        
        self._extensions[extension_point_id].append(extension)
        return True
    
    def unregister_extension(self, extension_point_id: str, extension: Any) -> bool:
        """注销扩展"""
        if extension_point_id not in self._extensions:
            return False
        
        try:
            self._extensions[extension_point_id].remove(extension)
            return True
        except ValueError:
            return False
    
    def get_extensions(self, extension_point_id: str) -> List[Any]:
        """获取扩展点的所有扩展"""
        return self._extensions.get(extension_point_id, []).copy()
    
    def get_extension_points(self) -> List[ExtensionPoint]:
        """获取所有扩展点"""
        return list(self._extension_points.values())
    
    def execute_extensions(self, extension_point_id: str, method: str, *args, **kwargs) -> List[Any]:
        """执行扩展点的所有扩展"""
        results = []
        extensions = self.get_extensions(extension_point_id)
        
        for extension in extensions:
            if hasattr(extension, method):
                try:
                    result = getattr(extension, method)(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    # 记录错误但继续执行其他扩展
                    results.append({"error": str(e), "extension": str(extension)})
        
        return results


# 全局扩展管理器实例
_core_extension_manager = CoreExtensionManager()


def get_core_extension_manager() -> CoreExtensionManager:
    """获取核心扩展管理器实例"""
    return _core_extension_manager