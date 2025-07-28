"""
全局状态重构示例
展示如何逐步移除SharedDataManager的全局依赖
"""

from typing import Optional
from src.core.data_service_interface import IDataService, get_service
from src.core.simple_di_container import get_service_container, register_service
from src.core_business.models.hole_data import HoleCollection


class RefactoredComponent:
    """重构后的组件示例 - 使用依赖注入"""
    
    def __init__(self, data_service: Optional[IDataService] = None):
        # 优先使用注入的服务，fallback到容器获取
        self._data_service = data_service or get_service(IDataService)
    
    def load_data(self, hole_collection: HoleCollection):
        """加载数据 - 不直接访问全局状态"""
        self._data_service.set_hole_collection(hole_collection)
    
    def get_current_data(self) -> Optional[HoleCollection]:
        """获取当前数据 - 通过服务接口"""
        return self._data_service.get_hole_collection()


class LegacyComponent:
    """遗留组件示例 - 仍使用全局状态"""
    
    def __init__(self):
        from src.core.shared_data_manager import SharedDataManager
        self._shared_data_manager = SharedDataManager()  # 全局状态依赖
    
    def load_data(self, hole_collection: HoleCollection):
        """加载数据 - 直接访问全局状态"""
        self._shared_data_manager.set_data('hole_collection', hole_collection)


class HybridComponent:
    """混合组件示例 - 逐步迁移"""
    
    def __init__(self, data_service: Optional[IDataService] = None):
        if data_service:
            # 新方式：使用依赖注入
            self._data_service = data_service
            self._use_legacy = False
        else:
            # 旧方式：全局状态 fallback
            from src.core.shared_data_manager import SharedDataManager
            self._shared_data_manager = SharedDataManager()
            self._use_legacy = True
    
    def load_data(self, hole_collection: HoleCollection):
        """加载数据 - 支持两种模式"""
        if self._use_legacy:
            self._shared_data_manager.set_data('hole_collection', hole_collection)
        else:
            self._data_service.set_hole_collection(hole_collection)


def example_refactor_main_window():
    """MainWindow重构示例"""
    
    # 错误的方式：UI层直接创建数据管理器
    # class MainWindow:
    #     def __init__(self):
    #         self.shared_data_manager = SharedDataManager()  # ❌ 全局状态滥用
    
    # 正确的方式：通过依赖注入
    class RefactoredMainWindow:
        def __init__(self, data_service: Optional[IDataService] = None):
            # 使用服务接口，而不是具体实现
            self._data_service = data_service or get_service(IDataService)
            
        def setup_components(self):
            """设置子组件 - 传递服务依赖"""
            from src.core_business.graphics.dynamic_sector_display_refactored import DynamicSectorDisplayRefactored
            
            # 传递服务依赖，而不是让组件自己获取
            # self.sector_display = DynamicSectorDisplayRefactored(data_service=self._data_service)
            pass


def example_dependency_injection_setup():
    """依赖注入设置示例"""
    
    # 在应用启动时配置依赖
    container = get_service_container()
    
    # 可以注册不同的实现用于测试
    def create_test_data_service():
        from src.core.data_service_interface import DataServiceAdapter
        from src.core.shared_data_manager import SharedDataManager
        return DataServiceAdapter(SharedDataManager())
    
    # 注册测试服务
    # register_service(IDataService, create_test_data_service, singleton=True)


# 重构步骤说明
"""
重构步骤（按优先级）：

1. ✅ 创建数据服务接口层
   - IDataService 抽象接口
   - DataServiceAdapter 适配现有实现
   
2. ✅ 实现简单依赖注入容器
   - 避免手动传递依赖
   - 支持单例和瞬时服务
   
3. 🔄 修复错误调用
   - 修复 get_instance() 调用错误
   - 统一实例获取方式
   
4. ⏳ 重构 MainWindow
   - 移除直接 SharedDataManager 创建
   - 使用服务接口
   
5. ⏳ 移除循环依赖
   - UnifiedSectorAdapter 不应反向依赖 SharedDataManager
   - 使用事件或回调机制
   
6. ⏳ 逐步迁移组件
   - 从 SharedDataManager 迁移到 IDataService
   - 使用 HybridComponent 模式过渡

优势：
- 📝 可测试性：可以注入 mock 服务
- 🔧 可维护性：清晰的依赖关系
- 🎯 单一职责：组件专注自己的逻辑
- 🏗️ 松耦合：通过接口而不是具体实现依赖
"""