#!/usr/bin/env python3
"""
简化的全景图测试
仅测试包的导入和基本功能
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

def test_package_import():
    """测试包导入"""
    print("🔍 测试包导入...")
    
    try:
        # 测试主要组件导入
        from src.core_business.graphics.panorama import PanoramaDIContainer
        from src.core_business.graphics.panorama import PanoramaWidget
        from src.core_business.graphics.panorama import CompletePanoramaWidget
        
        # 测试事件系统导入
        from src.core_business.graphics.panorama import PanoramaEventBus, PanoramaEvent
        
        # 测试核心组件导入
        from src.core_business.graphics.panorama import (
            PanoramaDataModel,
            PanoramaGeometryCalculator,
            PanoramaStatusManager,
            PanoramaRenderer
        )
        
        print("✅ 所有组件导入成功")
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_container_creation():
    """测试容器创建"""
    print("🔍 测试容器创建...")
    
    try:
        from src.core_business.graphics.panorama import PanoramaDIContainer
        from PySide6.QtWidgets import QApplication
        
        # 确保有Qt应用
        app = QApplication.instance() or QApplication([])
        
        # 创建容器
        container = PanoramaDIContainer()
        
        # 获取核心组件
        event_bus = container.get_event_bus()
        data_model = container.get_data_model()
        status_manager = container.get_status_manager()
        
        assert event_bus is not None
        assert data_model is not None
        assert status_manager is not None
        
        print("✅ 容器创建成功")
        return True
        
    except Exception as e:
        print(f"❌ 容器创建失败: {e}")
        return False


def test_widget_creation():
    """测试组件创建"""
    print("🔍 测试组件创建...")
    
    try:
        from src.core_business.graphics.panorama import PanoramaDIContainer
        from PySide6.QtWidgets import QApplication
        
        # 确保有Qt应用
        app = QApplication.instance() or QApplication([])
        
        # 创建组件
        container = PanoramaDIContainer()
        widget = container.create_panorama_widget()
        
        assert widget is not None
        assert hasattr(widget, 'sector_clicked')
        assert hasattr(widget, 'status_update_completed')
        
        print("✅ 组件创建成功")
        return True
        
    except Exception as e:
        print(f"❌ 组件创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_legacy_adapter():
    """测试遗留适配器"""
    print("🔍 测试遗留适配器...")
    
    try:
        from src.core_business.graphics.panorama import CompletePanoramaWidget
        from PySide6.QtWidgets import QApplication
        
        # 确保有Qt应用
        app = QApplication.instance() or QApplication([])
        
        # 创建适配器
        panorama = CompletePanoramaWidget()
        
        # 检查接口
        assert hasattr(panorama, 'load_hole_collection')
        assert hasattr(panorama, 'update_hole_status')
        assert hasattr(panorama, 'highlight_sector')
        assert hasattr(panorama, 'sector_clicked')
        
        # 检查新功能访问
        event_bus = panorama.get_event_bus()
        data_model = panorama.get_data_model()
        
        assert event_bus is not None
        assert data_model is not None
        
        print("✅ 遗留适配器测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 遗留适配器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_event_bus():
    """测试事件总线"""
    print("🔍 测试事件总线...")
    
    try:
        from src.core_business.graphics.panorama import PanoramaEventBus, PanoramaEvent
        from PySide6.QtWidgets import QApplication
        
        # 确保有Qt应用
        app = QApplication.instance() or QApplication([])
        
        # 创建事件总线
        event_bus = PanoramaEventBus()
        
        # 测试事件发布订阅
        received_events = []
        
        def callback(event_data):
            received_events.append(event_data)
        
        # 订阅事件
        event_bus.subscribe(PanoramaEvent.DATA_LOADED, callback)
        
        # 发布事件
        event_bus.publish(PanoramaEvent.DATA_LOADED, "test_data")
        
        # 处理Qt事件循环
        app.processEvents()
        
        # 验证结果
        assert len(received_events) == 1
        assert received_events[0].event_type == PanoramaEvent.DATA_LOADED
        assert received_events[0].data == "test_data"
        
        print("✅ 事件总线测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 事件总线测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_simple_tests():
    """运行简化测试"""
    print("🚀 全景图包简化测试")
    print("=" * 50)
    
    tests = [
        ("包导入", test_package_import),
        ("容器创建", test_container_creation),
        ("组件创建", test_widget_creation),
        ("遗留适配器", test_legacy_adapter),
        ("事件总线", test_event_bus)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {name}测试异常: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"   ✅ 通过: {passed}")
    print(f"   ❌ 失败: {failed}")
    print(f"   📈 成功率: {(passed / len(tests) * 100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有基础功能测试通过！")
        print("📝 包的核心功能正常工作:")
        print("   - ✅ 包结构正确，所有组件可以正常导入")
        print("   - ✅ 依赖注入容器工作正常")
        print("   - ✅ 全景图组件可以正常创建")
        print("   - ✅ 向后兼容适配器功能完整")
        print("   - ✅ 事件总线通信正常")
        print("\n🔧 可以安全使用新的全景图包！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")
    
    return failed == 0


if __name__ == "__main__":
    success = run_simple_tests()
    
    if success:
        print("\n💡 使用方式提醒:")
        print("   现有项目: from src.core_business.graphics.panorama import CompletePanoramaWidget")
        print("   新项目:   from src.core_business.graphics.panorama import PanoramaDIContainer")
    
    sys.exit(0 if success else 1)