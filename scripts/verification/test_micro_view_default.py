#!/usr/bin/env python3
"""
测试默认微观视图是否正确显示
"""

import sys
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_micro_view_default():
    """测试默认微观视图"""
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    print("=" * 80)
    print("测试默认微观视图")
    print("=" * 80)
    
    try:
        # 导入必要的模块
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
        from src.core_business.hole_numbering_service import HoleNumberingService
        
        # 创建主视图
        view = NativeMainDetectionView()
        view.show()
        
        # 检查初始状态
        print("\n1. 检查初始状态...")
        if hasattr(view, 'center_panel') and view.center_panel:
            if hasattr(view.center_panel, 'micro_view_btn'):
                is_micro_checked = view.center_panel.micro_view_btn.isChecked()
                current_mode = getattr(view.center_panel, 'current_view_mode', None)
                
                print(f"   微观视图按钮选中: {is_micro_checked}")
                print(f"   当前视图模式: {current_mode}")
                print(f"   _initial_sector_loaded: {getattr(view, '_initial_sector_loaded', 'Not found')}")
        
        # 加载测试数据
        print("\n2. 加载测试数据...")
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/Data/Products/CAP1000/dxf/CAP1000.dxf"
        
        if Path(dxf_path).exists():
            loader = DXFLoaderService()
            hole_collection = loader.load_dxf_file(dxf_path)
            
            if hole_collection:
                # 应用编号
                numbering_service = HoleNumberingService()
                numbered_collection = numbering_service.apply_numbering(hole_collection)
                
                if numbered_collection:
                    print(f"   ✅ 加载了 {len(numbered_collection.holes)} 个孔位")
                    
                    # 加载到视图
                    view.load_hole_collection(numbered_collection)
                else:
                    print(f"   ✅ 加载了 {len(hole_collection.holes)} 个孔位（未编号）")
                    # 直接使用未编号的数据
                    view.load_hole_collection(hole_collection)
                
                # 等待加载完成
                def check_after_load():
                    print("\n3. 加载后检查...")
                    
                    # 检查coordinator状态
                    if view.coordinator:
                        current_sector = view.coordinator.current_sector
                        print(f"   当前扇形: {current_sector}")
                        
                        if current_sector:
                            sector_holes = view.coordinator.get_current_sector_holes()
                            print(f"   扇形孔位数: {len(sector_holes) if sector_holes else 0}")
                    
                    # 检查graphics_view状态
                    if hasattr(view.center_panel, 'graphics_view'):
                        gv = view.center_panel.graphics_view
                        if hasattr(gv, 'current_view_mode'):
                            print(f"   graphics_view模式: {gv.current_view_mode}")
                        
                        # 检查场景中的可见项
                        if hasattr(gv, 'scene') and callable(gv.scene):
                            scene = gv.scene()
                            if scene:
                                all_items = scene.items()
                                visible_items = [item for item in all_items if item.isVisible()]
                                print(f"   场景总项数: {len(all_items)}")
                                print(f"   可见项数: {len(visible_items)}")
                    
                    print(f"   _initial_sector_loaded: {getattr(view, '_initial_sector_loaded', 'Not found')}")
                    
                    # 手动触发微观视图
                    print("\n4. 手动触发微观视图...")
                    if view.center_panel:
                        view.center_panel._on_view_mode_changed("micro")
                        view._on_view_mode_changed("micro")
                    
                    # 再次检查
                    QTimer.singleShot(1000, final_check)
                
                def final_check():
                    print("\n5. 最终检查...")
                    if hasattr(view.center_panel, 'graphics_view'):
                        gv = view.center_panel.graphics_view
                        if hasattr(gv, 'scene') and callable(gv.scene):
                            scene = gv.scene()
                            if scene:
                                visible_items = [item for item in scene.items() if item.isVisible()]
                                print(f"   最终可见项数: {len(visible_items)}")
                                
                                if visible_items:
                                    print("   ✅ 微观视图正确显示扇形")
                                else:
                                    print("   ❌ 微观视图未能显示扇形")
                    
                    app.quit()
                
                # 延迟检查
                QTimer.singleShot(2000, check_after_load)
                
                # 运行事件循环
                app.exec()
        
        else:
            print(f"   ❌ DXF文件不存在: {dxf_path}")
    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_micro_view_default()