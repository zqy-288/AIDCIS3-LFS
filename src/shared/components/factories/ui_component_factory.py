"""
UI组件工厂
集中管理所有UI组件的创建，减少MainWindow的导入依赖
"""

from typing import Optional, Any
from PySide6.QtWidgets import QWidget

# 延迟导入，只在需要时加载
_component_modules = {
    'realtime_chart': 'src.pages.realtime_monitoring_p2.components.chart.chart_widget',
    'worker_thread': 'src.shared.services.threading.worker_thread',
    'history_viewer': 'src.pages.history_analytics_p3.components.history.history_viewer',
    'report_interface': 'src.pages.report_generation_p4.generators.report_output_interface',
    'product_selection': 'src.pages.main_detection_p1.modules.product_selection',
    'panorama_controller': 'src.modules.panorama_controller'
}

_component_classes = {
    'realtime_chart': 'EnhancedChartWidget',
    'worker_thread': 'WorkerThread',
    'history_viewer': 'HistoryViewer',
    'report_interface': 'ReportOutputInterface',
    'product_selection': 'ProductSelectionDialog',
    'panorama_controller': 'PanoramaController'
}


class UIComponentFactory:
    """
    UI组件工厂类
    使用延迟加载和缓存机制优化性能
    """
    
    def __init__(self):
        self._loaded_modules = {}
        self._component_cache = {}
        
    def create_realtime_chart(self, parent: Optional[QWidget] = None) -> Any:
        """创建实时图表组件"""
        return self._create_component('realtime_chart', parent)
        
    def create_worker_thread(self) -> Any:
        """创建工作线程"""
        return self._create_component('worker_thread')
        
    def create_history_viewer(self, parent: Optional[QWidget] = None) -> Any:
        """创建历史数据查看器"""
        return self._create_component('history_viewer', parent)
        
    def create_report_interface(self, parent: Optional[QWidget] = None) -> Any:
        """创建报告输出界面"""
        return self._create_component('report_interface', parent)
        
    def create_product_selection_dialog(self, parent: Optional[QWidget] = None) -> Any:
        """创建产品选择对话框"""
        return self._create_component('product_selection', parent)
        
    def create_panorama_controller(self) -> Any:
        """创建全景图控制器"""
        return self._create_component('panorama_controller')
        
    def _create_component(self, component_type: str, *args, **kwargs) -> Any:
        """
        通用组件创建方法
        使用延迟加载减少启动时间
        """
        # 如果模块未加载，先加载模块
        if component_type not in self._loaded_modules:
            module_name = _component_modules.get(component_type)
            class_name = _component_classes.get(component_type)
            
            if not module_name or not class_name:
                raise ValueError(f"Unknown component type: {component_type}")
                
            # 动态导入模块
            import importlib
            module = importlib.import_module(module_name)
            component_class = getattr(module, class_name)
            
            self._loaded_modules[component_type] = component_class
            
        # 创建组件实例
        component_class = self._loaded_modules[component_type]
        return component_class(*args, **kwargs)
        
    def preload_components(self, component_types: list):
        """
        预加载指定的组件模块
        用于优化关键组件的加载性能
        """
        for component_type in component_types:
            if component_type not in self._loaded_modules:
                # 只加载模块，不创建实例
                module_name = _component_modules.get(component_type)
                class_name = _component_classes.get(component_type)
                
                if not module_name or not class_name:
                    continue
                    
                # 动态导入模块
                import importlib
                module = importlib.import_module(module_name)
                component_class = getattr(module, class_name)
                
                # 保存类引用，但不创建实例
                self._loaded_modules[component_type] = component_class
                
                
# 全局工厂实例
_global_factory = None


def get_ui_factory() -> UIComponentFactory:
    """获取全局UI工厂实例"""
    global _global_factory
    if _global_factory is None:
        _global_factory = UIComponentFactory()
    return _global_factory