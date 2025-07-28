#!/usr/bin/env python3
"""
加载测试数据并验证全景图显示
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

def main():
    """加载测试数据"""
    print("🚀 启动程序并加载测试数据...")
    
    try:
        # 导入Qt
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        
        # 创建应用
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # 导入并创建主窗口
        from src.main_window import MainWindow
        window = MainWindow()
        
        # 显示窗口
        window.show()
        window.raise_()
        
        print("✅ GUI已启动")
        
        # 定义加载测试数据的函数
        def load_test_data():
            print("\n🔄 开始加载测试数据...")
            try:
                # 调用test_load_default_dxf方法
                if hasattr(window, 'test_load_default_dxf'):
                    print("📂 调用 test_load_default_dxf...")
                    window.test_load_default_dxf()
                    print("✅ test_load_default_dxf 调用完成")
                    
                    # 延迟检查加载结果
                    QTimer.singleShot(8000, check_data_loaded)
                else:
                    print("❌ test_load_default_dxf 方法不存在")
                    
                    # 尝试其他可能的加载方法
                    print("🔍 尝试查找其他数据加载方法...")
                    methods = [attr for attr in dir(window) if 'load' in attr.lower() or 'dxf' in attr.lower()]
                    print(f"可能的方法: {methods}")
                    
            except Exception as e:
                print(f"❌ 加载失败: {e}")
                import traceback
                traceback.print_exc()
        
        def check_data_loaded():
            print("\n🔍 检查数据加载结果...")
            try:
                # 检查主窗口数据
                if hasattr(window, 'hole_collection') and window.hole_collection:
                    hole_count = len(window.hole_collection)
                    print(f"✅ 主窗口孔位数据: {hole_count} 个")
                    
                    # 检查全景图数据
                    if hasattr(window, 'sidebar_panorama') and window.sidebar_panorama:
                        panorama = window.sidebar_panorama
                        if hasattr(panorama, 'hole_collection') and panorama.hole_collection:
                            panorama_holes = len(panorama.hole_collection)
                            print(f"✅ 全景图孔位数据: {panorama_holes} 个")
                            
                            # 检查图形视图项
                            if hasattr(panorama, 'panorama_view') and panorama.panorama_view:
                                view = panorama.panorama_view
                                if hasattr(view, 'hole_items') and view.hole_items:
                                    view_items = len(view.hole_items)
                                    print(f"✅ 全景图图形项: {view_items} 个")
                                    
                                    if view_items > 0:
                                        print("\n🎉 数据加载成功！全景图应该显示孔位数据")
                                        
                                        # 增强孔位可见性
                                        enhance_hole_visibility()
                                    else:
                                        print("❌ 全景图没有图形项")
                                else:
                                    print("❌ 全景图视图没有hole_items")
                            else:
                                print("❌ 全景图没有panorama_view")
                        else:
                            print("❌ 全景图组件没有孔位数据")
                    else:
                        print("❌ 没有sidebar_panorama组件")
                else:
                    print("❌ 主窗口没有孔位数据")
                    print("💡 可能需要手动从菜单加载DXF文件")
                    
            except Exception as e:
                print(f"❌ 检查失败: {e}")
                import traceback
                traceback.print_exc()
        
        def enhance_hole_visibility():
            """增强孔位可见性"""
            print("\n🔧 增强孔位可见性...")
            try:
                panorama = window.sidebar_panorama
                view = panorama.panorama_view
                
                if hasattr(view, 'hole_items') and view.hole_items:
                    # 使用较大的半径确保可见
                    test_radius = 8.0  
                    updated_count = 0
                    
                    from PySide6.QtCore import QRectF
                    
                    for hole_item in view.hole_items.values():
                        if hasattr(hole_item, 'setRect'):
                            new_rect = QRectF(-test_radius, -test_radius, 
                                            test_radius * 2, test_radius * 2)
                            hole_item.setRect(new_rect)
                            updated_count += 1
                    
                    print(f"✅ 已将 {updated_count} 个孔位调整为 {test_radius}px 半径")
                    
                    # 强制更新视图
                    view.scene.update()
                    view.update()
                    panorama.update()
                    
                    print("✅ 视图已更新，孔位应该现在可见")
                    print("\n🎯 请检查GUI中的全景图区域是否显示孔位")
                    
            except Exception as e:
                print(f"❌ 可见性增强失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 3秒后开始加载数据
        QTimer.singleShot(3000, load_test_data)
        
        print("🚀 进入事件循环...")
        print("程序将在3秒后自动加载测试数据...")
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())