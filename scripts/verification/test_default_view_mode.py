#!/usr/bin/env python3
"""
测试默认视图模式问题
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_view_mode_initialization():
    """测试视图模式初始化"""
    print("🔍 测试默认视图模式\n")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeCenterVisualizationPanel
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # 创建中心面板
        panel = NativeCenterVisualizationPanel()
        
        print("1. 初始化后的状态:")
        print(f"   - current_view_mode: {panel.current_view_mode}")
        print(f"   - micro_view_btn.isChecked(): {panel.micro_view_btn.isChecked()}")
        print(f"   - macro_view_btn.isChecked(): {panel.macro_view_btn.isChecked()}")
        
        # 检查graphics_view
        if hasattr(panel, 'graphics_view'):
            print(f"\n2. graphics_view状态:")
            print(f"   - 存在: 是")
            
            if hasattr(panel.graphics_view, 'current_view_mode'):
                print(f"   - current_view_mode: {panel.graphics_view.current_view_mode}")
            else:
                print(f"   - current_view_mode: 未设置")
                
            if hasattr(panel.graphics_view, 'disable_auto_fit'):
                print(f"   - disable_auto_fit: {panel.graphics_view.disable_auto_fit}")
            else:
                print(f"   - disable_auto_fit: 未设置")
        else:
            print(f"\n2. graphics_view状态: 不存在")
            
        print("\n3. 结论:")
        if panel.current_view_mode == "micro" and panel.micro_view_btn.isChecked():
            print("   ✅ 中心面板默认为微观视图模式")
        else:
            print("   ❌ 中心面板未正确设置为微观视图模式")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_dxf_loading():
    """测试DXF加载时的视图模式"""
    print("\n" + "="*60)
    print("测试DXF加载时的视图模式")
    print("="*60)
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.pages.main_detection_p1.native_main_detection_view_p1 import MainDetectionViewP1
        from src.core_business.dxf_parser import DXFParser
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # 创建主视图
        view = MainDetectionViewP1()
        
        print("\n1. 加载DXF前的状态:")
        if view.center_panel:
            print(f"   - center_panel.current_view_mode: {view.center_panel.current_view_mode}")
            print(f"   - micro_view_btn.isChecked(): {view.center_panel.micro_view_btn.isChecked()}")
            
            if hasattr(view.center_panel, 'graphics_view') and view.center_panel.graphics_view:
                gv = view.center_panel.graphics_view
                print(f"   - graphics_view.current_view_mode: {getattr(gv, 'current_view_mode', '未设置')}")
                print(f"   - graphics_view.disable_auto_fit: {getattr(gv, 'disable_auto_fit', '未设置')}")
        
        # 加载DXF文件
        print("\n2. 加载DXF文件...")
        parser = DXFParser()
        hole_collection = parser.parse_file("Data/Products/CAP1000/dxf/CAP1000.dxf")
        
        if hole_collection:
            print(f"   ✅ DXF解析成功: {len(hole_collection.holes)} 个孔位")
            
            # 模拟加载到视图
            view.load_hole_collection(hole_collection)
            
            print("\n3. 加载DXF后的状态:")
            if view.center_panel:
                print(f"   - center_panel.current_view_mode: {view.center_panel.current_view_mode}")
                print(f"   - micro_view_btn.isChecked(): {view.center_panel.micro_view_btn.isChecked()}")
                
                if hasattr(view.center_panel, 'graphics_view') and view.center_panel.graphics_view:
                    gv = view.center_panel.graphics_view
                    print(f"   - graphics_view.current_view_mode: {getattr(gv, 'current_view_mode', '未设置')}")
                    print(f"   - graphics_view.disable_auto_fit: {getattr(gv, 'disable_auto_fit', '未设置')}")
                    
                    # 检查场景内容
                    if hasattr(gv, 'scene'):
                        scene = gv.scene() if callable(gv.scene) else gv.scene
                        if scene:
                            items = scene.items()
                            visible_count = sum(1 for item in items if item.isVisible())
                            print(f"   - 场景项总数: {len(items)}")
                            print(f"   - 可见项数量: {visible_count}")
                            
                            if visible_count == 0:
                                print("   ⚠️  所有项都被隐藏了（等待扇形选择）")
                            elif visible_count == len(items):
                                print("   ⚠️  所有项都可见（显示全景）")
                            else:
                                print(f"   ✅ 部分项可见（显示扇形）")
            
            # 检查是否调用了_load_default_sector1
            print("\n4. 检查默认扇形加载:")
            print(f"   - _initial_sector_loaded: {view._initial_sector_loaded}")
            if view.coordinator and hasattr(view.coordinator, 'current_sector'):
                print(f"   - coordinator.current_sector: {view.coordinator.current_sector}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    test_view_mode_initialization()
    test_dxf_loading()


if __name__ == "__main__":
    main()