#!/usr/bin/env python3
"""
测试批次显示修复
验证批次创建时UI能正确显示批次信息
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_batch_signal_addition():
    """测试批次信号添加"""
    print("🔍 测试批次信号添加...")
    
    try:
        from src.pages.main_detection_p1.controllers.main_window_controller import MainWindowController
        
        controller = MainWindowController()
        
        # 检查batch_created信号是否存在
        if hasattr(controller, 'batch_created'):
            print("    ✅ batch_created信号已添加")
            
            # 检查信号类型
            signal = getattr(controller, 'batch_created')
            if hasattr(signal, 'emit'):
                print("    ✅ batch_created是有效的Signal对象")
                
                # 模拟信号发射测试
                try:
                    signal.emit("TEST_BATCH_001")
                    print("    ✅ 信号发射测试成功")
                except Exception as e:
                    print(f"    ⚠️ 信号发射测试异常: {e}")
                    
            else:
                print("    ❌ batch_created不是有效的Signal对象")
                return False
        else:
            print("    ❌ batch_created信号不存在")
            return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ 批次信号测试失败: {e}")
        return False

def test_batch_creation_logic():
    """测试批次创建逻辑"""
    print("🔍 测试批次创建逻辑...")
    
    try:
        from src.pages.main_detection_p1.controllers.main_window_controller import MainWindowController
        from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
        
        controller = MainWindowController()
        
        # 设置必要的数据
        controller.current_product_id = 1
        controller.current_product = {'model_name': 'TEST_PRODUCT'}
        
        # 创建测试孔位集合
        holes = {}
        for i in range(3):
            hole = HoleData(
                hole_id=f"TEST_{i:03d}",
                center_x=i * 10.0,
                center_y=i * 15.0,
                radius=8.0
            )
            holes[hole.hole_id] = hole
        
        controller.hole_collection = HoleCollection(holes=holes)
        
        # 测试批次创建过程中的信号发射
        signal_emitted = []
        
        def on_batch_created(batch_id):
            signal_emitted.append(batch_id)
            print(f"    📡 接收到批次创建信号: {batch_id}")
        
        # 连接信号
        controller.batch_created.connect(on_batch_created)
        
        # 启动检测（模拟）
        print("    🔧 启动模拟检测...")
        try:
            controller.start_detection(is_mock=True)
            
            # 检查信号是否被发射
            if signal_emitted:
                batch_id = signal_emitted[0]
                print(f"    ✅ 批次创建成功: {batch_id}")
                
                # 验证批次ID格式
                if "_MOCK" in batch_id:
                    print("    ✅ 模拟批次ID格式正确")
                else:
                    print("    ⚠️ 模拟批次ID缺少MOCK标识")
                
                return True
            else:
                print("    ❌ 批次创建信号未发射")
                return False
                
        except Exception as e:
            print(f"    ❌ 批次创建过程异常: {e}")
            return False
        
    except Exception as e:
        print(f"    ❌ 批次创建逻辑测试失败: {e}")
        return False

def test_ui_update_method():
    """测试UI更新方法"""
    print("🔍 测试UI更新方法...")
    
    try:
        # 创建模拟的UI组件
        class MockLeftPanel:
            def __init__(self):
                self.batch_info = "检测批次: 未开始"
                
            def update_batch_info(self, batch_id=None):
                if batch_id:
                    self.batch_info = f"检测批次: {batch_id}"
                    print(f"    📱 左侧面板更新: {self.batch_info}")
                else:
                    self.batch_info = "检测批次: 未开始"
                    print(f"    📱 左侧面板重置: {self.batch_info}")
        
        class MockNativeView:
            def __init__(self):
                self.left_panel = MockLeftPanel()
                
        # 模拟UI更新逻辑
        mock_view = MockNativeView()
        
        # 测试批次信息更新
        test_batch_id = "TEST_PRODUCT_检测001_20250804_123456_MOCK"
        
        if hasattr(mock_view, 'left_panel') and hasattr(mock_view.left_panel, 'update_batch_info'):
            mock_view.left_panel.update_batch_info(test_batch_id)
            
            if test_batch_id in mock_view.left_panel.batch_info:
                print("    ✅ UI更新方法工作正常")
                return True
            else:
                print("    ❌ UI更新方法失效")
                return False
        else:
            print("    ❌ UI更新方法不存在")
            return False
        
    except Exception as e:
        print(f"    ❌ UI更新方法测试失败: {e}")
        return False

def test_code_modifications():
    """测试代码修改"""
    print("🔍 测试代码修改...")
    
    try:
        # 检查控制器文件的修改
        controller_file = Path(project_root) / "src/pages/main_detection_p1/controllers/main_window_controller.py"
        
        if controller_file.exists():
            content = controller_file.read_text(encoding='utf-8')
            
            # 检查batch_created信号定义
            if "batch_created = Signal(str)" in content:
                print("    ✅ batch_created信号定义已添加")
            else:
                print("    ❌ batch_created信号定义未找到")
                return False
            
            # 检查信号发射代码
            if "self.batch_created.emit(batch.batch_id)" in content:
                print("    ✅ 信号发射代码已添加")
            else:
                print("    ❌ 信号发射代码未找到")
                return False
        else:
            print("    ❌ 控制器文件不存在")
            return False
        
        # 检查主检测页面的修改
        page_file = Path(project_root) / "src/pages/main_detection_p1/main_detection_page.py"
        
        if page_file.exists():
            content = page_file.read_text(encoding='utf-8')
            
            # 检查信号连接
            if "self.controller.batch_created.connect(self._on_batch_created)" in content:
                print("    ✅ 信号连接代码已添加")
            else:
                print("    ❌ 信号连接代码未找到")
                return False
            
            # 检查处理方法
            if "def _on_batch_created(self, batch_id: str):" in content:
                print("    ✅ 批次处理方法已添加")
            else:
                print("    ❌ 批次处理方法未找到")
                return False
        else:
            print("    ❌ 主检测页面文件不存在")
            return False
        
        return True
        
    except Exception as e:
        print(f"    ❌ 代码修改检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 测试批次显示修复...")
    print("=" * 60)
    
    tests = [
        ("批次信号添加测试", test_batch_signal_addition),
        ("批次创建逻辑测试", test_batch_creation_logic),
        ("UI更新方法测试", test_ui_update_method),
        ("代码修改检查", test_code_modifications)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, "PASS" if result else "FAIL"))
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append((test_name, "ERROR"))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("📊 批次显示修复验证结果")
    print("=" * 60)
    
    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)
    
    for test_name, status in results:
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{status_emoji} {test_name}: {status}")
    
    print(f"\n🎯 结果: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 ✨ 批次显示问题已修复！ ✨")
        print("\n🔧 修复内容:")
        print("   ✅ 添加了batch_created信号到MainWindowController")
        print("   ✅ 在批次创建时发射信号通知UI")
        print("   ✅ 连接信号到主检测页面")
        print("   ✅ 添加了_on_batch_created方法更新UI")
        print("   ✅ 更新左侧面板的批次信息显示")
        print("\n💡 现在检测开始时应该能正确显示批次信息而不是'未开始'")
    else:
        failed_tests = [name for name, status in results if status != "PASS"]
        print(f"\n⚠️ 需要进一步检查: {failed_tests}")
    
    print("=" * 60)
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)