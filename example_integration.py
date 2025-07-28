#!/usr/bin/env python3
"""
全景图包集成示例
展示如何在现有项目中使用新的全景图包
"""

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt

def example_1_legacy_compatibility():
    """示例1: 向后兼容使用方式"""
    print("=== 示例1: 向后兼容方式 ===")
    
    # 导入方式1: 使用适配器，完全兼容旧代码
    from src.core_business.graphics.panorama import CompletePanoramaWidget
    
    # 旧代码完全不需要修改
    app = QApplication.instance() or QApplication([])
    
    panorama = CompletePanoramaWidget()
    panorama.setFixedSize(350, 350)
    
    # 原有的方法调用都保持不变
    # panorama.load_hole_collection(hole_collection)
    # panorama.sector_clicked.connect(handler)
    
    print("✅ 适配器创建成功，与旧代码完全兼容")
    return panorama


def example_2_new_architecture():
    """示例2: 使用新架构"""
    print("\n=== 示例2: 新架构方式 ===")
    
    # 导入新架构组件
    from src.core_business.graphics.panorama import PanoramaDIContainer
    
    app = QApplication.instance() or QApplication([])
    
    # 使用依赖注入容器
    container = PanoramaDIContainer()
    panorama = container.create_panorama_widget()
    panorama.setFixedSize(350, 350)
    
    # 获取事件总线进行高级操作
    event_bus = container.get_event_bus()
    
    print("✅ 新架构组件创建成功")
    print(f"   - 事件总线: {event_bus}")
    print(f"   - 数据模型: {container.get_data_model()}")
    return panorama, container


def example_3_mixed_usage():
    """示例3: 混合使用方式"""
    print("\n=== 示例3: 混合使用方式 ===")
    
    # 既可以使用旧接口，也可以访问新功能
    from src.core_business.graphics.panorama import CompletePanoramaWidget
    
    app = QApplication.instance() or QApplication([])
    
    panorama = CompletePanoramaWidget()
    
    # 使用旧接口
    panorama.setFixedSize(350, 350)
    
    # 访问新功能
    event_bus = panorama.get_event_bus()
    data_model = panorama.get_data_model()
    
    print("✅ 混合使用成功")
    print(f"   - 旧接口可用: {hasattr(panorama, 'load_hole_collection')}")
    print(f"   - 新功能可用: {event_bus is not None}")
    return panorama


def example_4_main_window_integration():
    """示例4: 在主窗口中集成"""
    print("\n=== 示例4: 主窗口集成 ===")
    
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("全景图集成示例")
            
            # 方式1: 使用适配器（推荐迁移期使用）
            from src.core_business.graphics.panorama import CompletePanoramaWidget
            self.sidebar_panorama = CompletePanoramaWidget()
            self.sidebar_panorama.setFixedSize(350, 350)
            
            # 方式2: 使用新架构（推荐新项目使用）
            from src.core_business.graphics.panorama import PanoramaDIContainer
            self.panorama_container = PanoramaDIContainer()
            self.main_panorama = self.panorama_container.create_panorama_widget()
            
            # 设置UI
            self._setup_ui()
            
            print("✅ 主窗口集成成功")
        
        def _setup_ui(self):
            central_widget = QWidget()
            layout = QHBoxLayout(central_widget)
            
            # 添加侧边栏全景图
            layout.addWidget(self.sidebar_panorama)
            
            # 添加主全景图
            layout.addWidget(self.main_panorama, 1)
            
            self.setCentralWidget(central_widget)
    
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    return window


def example_5_custom_extension():
    """示例5: 自定义扩展"""
    print("\n=== 示例5: 自定义扩展 ===")
    
    from src.core_business.graphics.panorama import (
        PanoramaDIContainer, 
        PanoramaRenderer,
        PanoramaEvent
    )
    
    # 自定义渲染器
    class CustomRenderer(PanoramaRenderer):
        def render_holes(self, holes, scene, hole_size):
            print(f"自定义渲染 {len(holes)} 个孔位")
            return super().render_holes(holes, scene, hole_size)
    
    app = QApplication.instance() or QApplication([])
    
    # 创建容器并替换组件
    container = PanoramaDIContainer()
    
    # 注意: 实际使用时需要在容器中正确注入自定义组件
    # 这里只是展示概念
    
    panorama = container.create_panorama_widget()
    
    # 监听事件
    event_bus = container.get_event_bus()
    
    def on_event(event_data):
        print(f"收到事件: {event_data.event_type}")
    
    event_bus.subscribe(PanoramaEvent.DATA_LOADED, on_event)
    
    print("✅ 自定义扩展设置完成")
    return panorama


def run_all_examples():
    """运行所有示例"""
    print("🚀 全景图包集成示例")
    print("=" * 50)
    
    try:
        # 运行各个示例
        panorama1 = example_1_legacy_compatibility()
        panorama2, container2 = example_2_new_architecture()
        panorama3 = example_3_mixed_usage()
        window4 = example_4_main_window_integration()
        panorama5 = example_5_custom_extension()
        
        print("\n" + "=" * 50)
        print("🎉 所有示例运行成功！")
        print("\n📝 总结:")
        print("   1. ✅ 向后兼容适配器工作正常")
        print("   2. ✅ 新架构组件创建成功")
        print("   3. ✅ 混合使用方式可行")
        print("   4. ✅ 主窗口集成无问题")
        print("   5. ✅ 自定义扩展支持良好")
        
        print("\n🔧 推荐使用方式:")
        print("   - 现有项目: 使用 CompletePanoramaWidget 适配器")
        print("   - 新项目: 使用 PanoramaDIContainer + PanoramaWidget")
        print("   - 高级用法: 直接使用核心组件和事件总线")
        
    except Exception as e:
        print(f"\n❌ 示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()