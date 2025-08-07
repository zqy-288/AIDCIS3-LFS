#!/usr/bin/env python3
"""
调试左侧全景显示问题
检查左侧全景组件是否正确显示数据
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_left_panorama_rendering():
    """测试左侧全景组件渲染"""
    app = QApplication(sys.argv)
    
    try:
        # 创建主窗口
        main_window = QMainWindow()
        main_window.setWindowTitle("左侧全景测试")
        main_window.resize(800, 600)
        
        # 创建主视图
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeMainDetectionView
        main_view = NativeMainDetectionView()
        main_window.setCentralWidget(main_view)
        
        print("✅ 主视图创建成功")
        
        # 检查左侧面板和全景组件
        if hasattr(main_view, 'left_panel'):
            print("✅ 左侧面板存在")
            
            if hasattr(main_view.left_panel, 'sidebar_panorama'):
                panorama = main_view.left_panel.sidebar_panorama
                print(f"✅ 全景组件存在: {type(panorama)}")
                
                # 加载测试数据
                dxf_file = project_root / "Data/Products/CAP1000/dxf/CAP1000.dxf"
                if dxf_file.exists():
                    print(f"✅ 找到DXF文件: {dxf_file}")
                    
                    # 手动触发数据加载
                    def load_data():
                        try:
                            from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
                            loader = DXFLoaderService()
                            hole_collection = loader.load_dxf_file(str(dxf_file))
                            
                            if hole_collection and len(hole_collection) > 0:
                                print(f"✅ 加载了 {len(hole_collection)} 个孔位")
                                
                                # 直接加载到左侧全景
                                main_view.load_hole_collection(hole_collection)
                                print("✅ 数据已加载到主视图")
                                
                                # 检查全景组件状态
                                if hasattr(panorama, 'hole_collection'):
                                    if panorama.hole_collection:
                                        print(f"✅ 全景组件有数据: {len(panorama.hole_collection)} 个孔位")
                                    else:
                                        print("❌ 全景组件没有数据")
                                        
                                        # 强制刷新全景组件
                                        if hasattr(panorama, 'load_hole_collection'):
                                            panorama.load_hole_collection(hole_collection)
                                            print("✅ 强制刷新全景组件")
                                
                            else:
                                print("❌ 没有加载到孔位数据")
                                
                        except Exception as e:
                            print(f"❌ 数据加载失败: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # 延迟执行数据加载
                    QTimer.singleShot(1000, load_data)
        
        # 显示主窗口
        main_window.show()
        print("✅ 主窗口已显示")
        
        # 运行10秒后退出
        QTimer.singleShot(10000, app.quit)
        app.exec()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_left_panorama_rendering()