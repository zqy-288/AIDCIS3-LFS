#!/usr/bin/env python3
"""
修复重复初始化和缺失属性问题的脚本
解决组件被初始化三次和属性错误的问题
"""

import os
import re
from pathlib import Path

class InitializationFixer:
    """修复初始化问题的工具类"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        
    def fix_all_issues(self):
        """修复所有问题"""
        print("🔧 开始修复重复初始化和缺失属性问题...")
        
        # 1. 修复缺失的属性问题
        self.fix_missing_attributes()
        
        # 2. 创建单例管理器
        self.create_singleton_manager()
        
        # 3. 修复TabManager的RightSide属性问题
        self.fix_tab_manager_rightside()
        
        # 4. 修复RealtimeChart的data_point_selected信号
        self.fix_realtime_chart_signal()
        
        # 5. 修复ApplicationModel的data_loaded信号
        self.fix_application_model_signal()
        
        # 6. 重构MainWindow初始化逻辑
        self.refactor_main_window_initialization()
        
        # 7. 创建统一的启动入口
        self.create_unified_startup()
        
        print("✅ 修复完成！")
    
    def fix_missing_attributes(self):
        """修复缺失的属性"""
        print("📝 修复缺失的属性...")
        
        # 修复TabManager的RightSide问题
        tab_manager_path = self.src_dir / "ui" / "tab_manager.py"
        if tab_manager_path.exists():
            content = tab_manager_path.read_text(encoding='utf-8')
            
            # 替换RightSide为正确的Qt常量
            content = re.sub(
                r'self\._tab_widget\.tabBar\(\)\.RightSide',
                'self._tab_widget.tabBar().RightSide if hasattr(self._tab_widget.tabBar(), "RightSide") else 1',
                content
            )
            
            # 更正确的做法是使用QTabBar的枚举
            content = re.sub(
                r'self\._tab_widget\.tabBar\(\)\.RightSide',
                'QTabBar.RightSide',
                content
            )
            
            # 确保导入QTabBar
            if 'from PySide6.QtWidgets import' in content and 'QTabBar' not in content:
                content = re.sub(
                    r'from PySide6\.QtWidgets import ([^)]+)',
                    r'from PySide6.QtWidgets import \1, QTabBar',
                    content
                )
            
            tab_manager_path.write_text(content, encoding='utf-8')
            print("  ✅ 修复TabManager RightSide属性")
    
    def create_singleton_manager(self):
        """创建单例管理器"""
        print("🏗️ 创建单例管理器...")
        
        singleton_manager_path = self.src_dir / "core" / "singleton_manager.py"
        singleton_manager_content = '''"""
单例管理器
确保关键组件只被初始化一次
"""

import logging
from typing import Dict, Type, Any, Optional
from threading import Lock
import weakref

class SingletonManager:
    """单例管理器 - 确保组件只被初始化一次"""
    
    _instance = None
    _lock = Lock()
    _singletons: Dict[Type, Any] = {}
    _logger = logging.getLogger(__name__)
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._logger.info("SingletonManager initialized")
    
    @classmethod
    def get_or_create(cls, component_type: Type, factory_func=None, *args, **kwargs) -> Any:
        """获取或创建单例组件"""
        if component_type in cls._singletons:
            instance = cls._singletons[component_type]
            # 检查弱引用是否仍然有效
            if isinstance(instance, weakref.ref):
                actual_instance = instance()
                if actual_instance is not None:
                    cls._logger.debug(f"返回现有单例: {component_type.__name__}")
                    return actual_instance
                else:
                    # 弱引用已失效，移除并重新创建
                    del cls._singletons[component_type]
            else:
                cls._logger.debug(f"返回现有单例: {component_type.__name__}")
                return instance
        
        # 创建新实例
        try:
            if factory_func:
                instance = factory_func(*args, **kwargs)
            else:
                instance = component_type(*args, **kwargs)
            
            # 对于QObject子类，使用弱引用以避免循环引用
            from PySide6.QtCore import QObject
            if isinstance(instance, QObject):
                cls._singletons[component_type] = weakref.ref(instance)
            else:
                cls._singletons[component_type] = instance
            
            cls._logger.info(f"创建新单例: {component_type.__name__}")
            return instance
            
        except Exception as e:
            cls._logger.error(f"创建单例失败 {component_type.__name__}: {e}")
            raise
    
    @classmethod
    def register_instance(cls, component_type: Type, instance: Any):
        """注册现有实例为单例"""
        from PySide6.QtCore import QObject
        if isinstance(instance, QObject):
            cls._singletons[component_type] = weakref.ref(instance)
        else:
            cls._singletons[component_type] = instance
        cls._logger.info(f"注册现有实例为单例: {component_type.__name__}")
    
    @classmethod
    def has_instance(cls, component_type: Type) -> bool:
        """检查是否已有实例"""
        if component_type not in cls._singletons:
            return False
        
        instance = cls._singletons[component_type]
        if isinstance(instance, weakref.ref):
            return instance() is not None
        return True
    
    @classmethod
    def clear_instance(cls, component_type: Type):
        """清除指定类型的实例"""
        if component_type in cls._singletons:
            del cls._singletons[component_type]
            cls._logger.info(f"清除单例: {component_type.__name__}")
    
    @classmethod
    def clear_all(cls):
        """清除所有单例"""
        cls._singletons.clear()
        cls._logger.info("清除所有单例")
    
    @classmethod
    def get_active_singletons(cls) -> Dict[str, Any]:
        """获取所有活跃的单例"""
        active = {}
        for component_type, instance in cls._singletons.items():
            if isinstance(instance, weakref.ref):
                actual_instance = instance()
                if actual_instance is not None:
                    active[component_type.__name__] = actual_instance
            else:
                active[component_type.__name__] = instance
        return active


# 便捷函数
def get_singleton(component_type: Type, factory_func=None, *args, **kwargs):
    """获取单例实例的便捷函数"""
    return SingletonManager.get_or_create(component_type, factory_func, *args, **kwargs)


def register_singleton(component_type: Type, instance: Any):
    """注册单例实例的便捷函数"""
    SingletonManager.register_instance(component_type, instance)


def clear_singleton(component_type: Type):
    """清除单例实例的便捷函数"""
    SingletonManager.clear_instance(component_type)
'''
        
        singleton_manager_path.write_text(singleton_manager_content, encoding='utf-8')
        print("  ✅ 创建SingletonManager")
    
    def fix_tab_manager_rightside(self):
        """修复TabManager的RightSide属性问题"""
        print("🔧 修复TabManager RightSide属性...")
        
        tab_manager_path = self.src_dir / "ui" / "tab_manager.py"
        if not tab_manager_path.exists():
            print("  ❌ tab_manager.py 不存在")
            return
        
        content = tab_manager_path.read_text(encoding='utf-8')
        
        # 修复RightSide属性问题
        fixes = [
            # 添加正确的导入
            (
                r'from PySide6\.QtWidgets import[^\\n]*',
                lambda m: m.group(0) + '\nfrom PySide6.QtWidgets import QTabBar' if 'QTabBar' not in m.group(0) else m.group(0)
            ),
            # 修复RightSide引用
            (
                r'self\._tab_widget\.tabBar\(\)\.RightSide',
                'QTabBar.ButtonPosition.RightSide'
            ),
            # 备用修复方案
            (
                r'QTabBar\.ButtonPosition\.RightSide',
                'QTabBar.RightSide'
            )
        ]
        
        for pattern, replacement in fixes:
            if callable(replacement):
                content = re.sub(pattern, replacement, content)
            else:
                content = re.sub(pattern, replacement, content)
        
        tab_manager_path.write_text(content, encoding='utf-8')
        print("  ✅ 修复TabManager RightSide属性")
    
    def fix_realtime_chart_signal(self):
        """修复RealtimeChart的data_point_selected信号"""
        print("🔧 修复RealtimeChart data_point_selected信号...")
        
        realtime_chart_path = self.src_dir / "modules" / "realtime_chart.py"
        if not realtime_chart_path.exists():
            print("  ❌ realtime_chart.py 不存在")
            return
        
        content = realtime_chart_path.read_text(encoding='utf-8')
        
        # 查找是否已经定义了data_point_selected信号
        if 'data_point_selected = Signal' not in content:
            # 在类定义后添加信号
            class_match = re.search(r'class RealtimeChart\([^)]+\):', content)
            if class_match:
                insert_pos = class_match.end()
                signal_definition = '''
    
    # 信号定义
    data_point_selected = Signal(dict)  # 数据点选择信号
'''
                content = content[:insert_pos] + signal_definition + content[insert_pos:]
                print("  ✅ 添加data_point_selected信号")
        
        realtime_chart_path.write_text(content, encoding='utf-8')
    
    def fix_application_model_signal(self):
        """修复ApplicationModel的data_loaded信号"""
        print("🔧 修复ApplicationModel data_loaded信号...")
        
        app_model_path = self.src_dir / "models" / "application_model.py"
        if not app_model_path.exists():
            print("  ❌ application_model.py 不存在")
            return
        
        content = app_model_path.read_text(encoding='utf-8')
        
        # 查找是否已经定义了data_loaded信号
        if 'data_loaded = Signal' not in content:
            # 在类定义后添加信号
            class_match = re.search(r'class ApplicationModel\([^)]*\):', content)
            if class_match:
                insert_pos = class_match.end()
                signal_definition = '''
    
    # 信号定义
    data_loaded = Signal(str, object)  # 数据加载信号 (file_path, hole_collection)
'''
                content = content[:insert_pos] + signal_definition + content[insert_pos:]
                print("  ✅ 添加data_loaded信号")
        
        app_model_path.write_text(content, encoding='utf-8')
    
    def refactor_main_window_initialization(self):
        """重构MainWindow初始化逻辑"""
        print("🔧 重构MainWindow初始化逻辑...")
        
        # 创建新的初始化逻辑
        new_init_content = '''    def _init_core_components(self):
        """初始化核心组件 - 使用单例模式避免重复创建"""
        # 导入单例管理器
        from core.singleton_manager import get_singleton
        
        # 获取ApplicationCore实例
        try:
            from core.application import get_application
            app = get_application()
            self.app_core = app.core
            
            if self.app_core is None:
                # 如果核心还未初始化，创建临时的组件
                self.event_bus = EventBus()
                self.container = DependencyContainer()
                self.logger.warning("ApplicationCore未初始化，使用临时组件")
            else:
                # 获取事件总线和依赖注入容器
                self.event_bus: EventBus = self.app_core.event_bus
                self.container: DependencyContainer = self.app_core.container
        except Exception as e:
            # 回退处理：创建本地组件
            self.logger.warning(f"无法获取ApplicationCore: {e}，创建本地组件")
            self.app_core = None
            self.event_bus = EventBus()
            self.container = DependencyContainer()
        
        # 使用单例模式初始化数据模型 - 避免重复创建
        self.app_model = get_singleton(ApplicationModel)
        self.detection_state_manager = get_singleton(DetectionStateManager)
        
        # 使用单例模式初始化管理器 - 避免重复创建
        self.tab_manager = get_singleton(TabManager, lambda: TabManager(self))
        self.ui_state_manager = get_singleton(UIStateManager, lambda: UIStateManager("AIDCIS3-LFS", self))
        
        # 初始化核心业务组件
        self.dxf_parser = DXFParser()
        self.hole_collection: Optional[HoleCollection] = None
        
        # 只有在容器中没有实例时才注册
        if not self.container.has_registration(ApplicationModel):
            self.container.register_instance(ApplicationModel, self.app_model)
        if not self.container.has_registration(DetectionStateManager):
            self.container.register_instance(DetectionStateManager, self.detection_state_manager)
        if not self.container.has_registration(TabManager):
            self.container.register_instance(TabManager, self.tab_manager)
        if not self.container.has_registration(UIStateManager):
            self.container.register_instance(UIStateManager, self.ui_state_manager)
'''
        
        main_window_path = self.src_dir / "main_window.py"
        if main_window_path.exists():
            content = main_window_path.read_text(encoding='utf-8')
            
            # 替换_init_core_components方法
            pattern = r'def _init_core_components\(self\):.*?(?=def|\Z)'
            content = re.sub(pattern, new_init_content + '\n    ', content, flags=re.DOTALL)
            
            main_window_path.write_text(content, encoding='utf-8')
            print("  ✅ 重构MainWindow初始化逻辑")
    
    def create_unified_startup(self):
        """创建统一的启动入口"""
        print("🚀 创建统一启动入口...")
        
        startup_script = self.project_root / "startup_fixed.py"
        startup_content = '''#!/usr/bin/env python3
"""
修复后的统一启动脚本
解决重复初始化问题，确保组件只被创建一次
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def setup_logging():
    """设置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """主启动函数 - 确保只有一个初始化路径"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🚀 启动AIDCIS3-LFS (修复版)")
    print("🔧 使用单例模式避免重复初始化")
    
    try:
        # 清理可能的重复实例
        from core.singleton_manager import SingletonManager
        SingletonManager.clear_all()
        
        # 使用ApplicationCore作为唯一入口
        from core.application import get_application
        
        app = get_application()
        
        # 初始化应用程序
        if not app.initialize():
            logger.error("应用程序初始化失败")
            return 1
        
        logger.info("✅ 应用程序初始化成功")
        
        # 运行应用程序
        exit_code = app.run()
        
        # 清理单例
        SingletonManager.clear_all()
        
        return exit_code
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
'''
        
        startup_script.write_text(startup_content, encoding='utf-8')
        print(f"  ✅ 创建统一启动脚本: {startup_script}")
        
        # 修改run_project.py以使用新的启动逻辑
        run_project_path = self.project_root / "run_project.py"
        if run_project_path.exists():
            new_run_project = '''#!/usr/bin/env python3
"""
AIDCIS3-LFS 主启动脚本 v3.0.0 (修复版)
重定向到修复后的统一启动入口
"""

import sys
import os
from pathlib import Path

print("🔄 重定向到修复后的启动入口...")
print("📍 使用统一的ApplicationCore启动方式")
print("🔧 避免重复初始化问题")
print("")

# 添加src目录到Python路径
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

if __name__ == "__main__":
    # 导入并运行修复后的启动脚本
    try:
        import startup_fixed
        exit_code = startup_fixed.main()
        sys.exit(exit_code)
    except ImportError:
        print("❌ 修复后的启动脚本不存在，回退到原始方式")
        # 回退到原始启动方式
        from main_window import main
        exit_code = main()
        sys.exit(exit_code)
'''
            
            run_project_path.write_text(new_run_project, encoding='utf-8')
            print("  ✅ 更新run_project.py")

def main():
    """主函数"""
    import sys
    
    # 获取项目根目录
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = "/Users/vsiyo/Desktop/AIDCIS/AIDCIS3-LFS"
    
    # 创建修复器并执行修复
    fixer = InitializationFixer(project_root)
    fixer.fix_all_issues()
    
    print("\n🎉 修复完成！")
    print("📋 修复内容:")
    print("  ✅ 修复TabManager RightSide属性问题")
    print("  ✅ 修复RealtimeChart data_point_selected信号")
    print("  ✅ 修复ApplicationModel data_loaded信号")
    print("  ✅ 创建SingletonManager避免重复初始化")
    print("  ✅ 重构MainWindow初始化逻辑")
    print("  ✅ 创建统一启动入口")
    print("\n🚀 现在可以使用以下命令启动应用程序:")
    print("  python startup_fixed.py")
    print("  或")
    print("  python run_project.py")

if __name__ == "__main__":
    main()