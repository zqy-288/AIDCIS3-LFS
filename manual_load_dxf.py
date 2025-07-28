#!/usr/bin/env python3
"""
手动加载DXF文件并验证全景图显示
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
    """直接加载DXF文件"""
    print("🚀 启动程序并直接加载DXF文件...")
    
    try:
        # 导入Qt
        from PySide6.QtWidgets import QApplication, QFileDialog
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
        
        # 查找DXF文件
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        if os.path.exists(dxf_path):
            print(f"✅ 找到DXF文件: {dxf_path}")
        else:
            print(f"❌ DXF文件不存在: {dxf_path}")
            # 尝试查找其他DXF文件
            dxf_dir = Path("/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf")
            if dxf_dir.exists():
                dxf_files = list(dxf_dir.rglob("*.dxf"))
                if dxf_files:
                    dxf_path = str(dxf_files[0])
                    print(f"🔍 使用找到的DXF文件: {dxf_path}")
                else:
                    print("❌ 没有找到任何DXF文件")
                    return 1
            else:
                print("❌ DXF目录不存在")
                return 1
        
        def load_dxf():
            print(f"\n🔄 开始加载DXF文件: {dxf_path}")
            try:
                # 检查MainWindow是否有load_dxf_file方法
                if hasattr(window, 'load_dxf_file'):
                    print("📂 调用 load_dxf_file...")
                    window.load_dxf_file(dxf_path)
                    print("✅ load_dxf_file 调用完成")
                elif hasattr(window, 'on_load_dxf'):
                    print("📂 调用 on_load_dxf...")
                    window.on_load_dxf(dxf_path)
                    print("✅ on_load_dxf 调用完成")
                else:
                    # 查找所有可能的DXF加载方法
                    print("🔍 查找DXF加载方法...")
                    methods = [attr for attr in dir(window) if ('dxf' in attr.lower() or 'load' in attr.lower()) and callable(getattr(window, attr))]
                    print(f"可能的方法: {methods}")
                    
                    # 尝试手动调用DXF解析器
                    print("🔧 尝试直接调用DXF解析器...")
                    from src.core_business.dxf_parser import DXFParser
                    
                    parser = DXFParser()
                    holes = parser.parse_file(dxf_path)
                    print(f"✅ DXF解析完成，获得 {len(holes)} 个孔位")
                    
                    # 手动设置数据到主窗口
                    if hasattr(window, 'set_hole_collection'):
                        window.set_hole_collection(holes)
                        print("✅ 数据已设置到主窗口")
                    elif hasattr(window, 'hole_collection'):
                        window.hole_collection = holes
                        print("✅ 数据已直接赋值到hole_collection")
                    
                    # 手动分发数据到全景图
                    if hasattr(window, 'sidebar_panorama') and window.sidebar_panorama:
                        window.sidebar_panorama.load_complete_view(holes)
                        print("✅ 数据已加载到全景图")
                
                # 延迟检查结果
                QTimer.singleShot(3000, check_loading_result)
                
            except Exception as e:
                print(f"❌ DXF加载失败: {e}")
                import traceback
                traceback.print_exc()
        
        def check_loading_result():
            print("\n🔍 检查加载结果...")
            try:
                # 检查主窗口数据
                if hasattr(window, 'hole_collection') and window.hole_collection:
                    hole_count = len(window.hole_collection)
                    print(f"✅ 主窗口孔位数据: {hole_count} 个")
                    
                    # 检查全景图数据
                    check_panorama_display()
                else:
                    print("❌ 主窗口没有孔位数据")
                    
            except Exception as e:
                print(f"❌ 检查失败: {e}")
                import traceback
                traceback.print_exc()
        
        def check_panorama_display():
            print("\n🔍 检查全景图显示...")
            try:
                if hasattr(window, 'sidebar_panorama') and window.sidebar_panorama:
                    panorama = window.sidebar_panorama
                    print("✅ 全景图组件存在")
                    
                    # 检查全景图数据
                    if hasattr(panorama, 'hole_collection') and panorama.hole_collection:
                        panorama_holes = len(panorama.hole_collection)
                        print(f"✅ 全景图孔位数据: {panorama_holes} 个")
                        
                        # 检查图形视图
                        if hasattr(panorama, 'panorama_view') and panorama.panorama_view:
                            view = panorama.panorama_view
                            print("✅ 全景图视图存在")
                            
                            # 检查hole_items
                            if hasattr(view, 'hole_items') and view.hole_items:
                                view_items = len(view.hole_items)
                                print(f"✅ 全景图图形项: {view_items} 个")
                                
                                # 强制更新孔位可见性
                                enhance_visibility(view)
                                
                            else:
                                print("❌ 全景图视图没有hole_items")
                        else:
                            print("❌ 全景图没有panorama_view")
                    else:
                        print("❌ 全景图组件没有孔位数据")
                else:
                    print("❌ 没有sidebar_panorama组件")
                    
            except Exception as e:
                print(f"❌ 全景图检查失败: {e}")
                import traceback
                traceback.print_exc()
        
        def enhance_visibility(view):
            print("\n🔧 强制增强孔位可见性...")
            try:
                if hasattr(view, 'hole_items') and view.hole_items:
                    from PySide6.QtCore import QRectF
                    from PySide6.QtGui import QBrush, QColor, QPen
                    
                    # 使用更大的半径和明显的颜色
                    radius = 15.0  # 使用更大的半径
                    updated_count = 0
                    
                    for hole_id, hole_item in view.hole_items.items():
                        if hasattr(hole_item, 'setRect'):
                            # 设置新的矩形大小
                            new_rect = QRectF(-radius, -radius, radius * 2, radius * 2)
                            hole_item.setRect(new_rect)
                            
                            # 设置明显的颜色
                            if hasattr(hole_item, 'setBrush'):
                                hole_item.setBrush(QBrush(QColor(255, 0, 0)))  # 红色
                            if hasattr(hole_item, 'setPen'):
                                hole_item.setPen(QPen(QColor(255, 255, 255), 2))  # 白色边框
                            
                            updated_count += 1
                    
                    print(f"✅ 已将 {updated_count} 个孔位调整为 {radius}px 半径，红色显示")
                    
                    # 强制更新所有相关视图
                    if hasattr(view, 'scene') and view.scene:
                        view.scene.update()
                        print("✅ 场景已更新")
                    
                    view.update()
                    view.viewport().update()
                    
                    if hasattr(view.parent(), 'update'):
                        view.parent().update()
                    
                    print("✅ 所有视图已强制更新")
                    print("\n🎯 现在全景图应该显示大号红色孔位，请检查GUI！")
                
            except Exception as e:
                print(f"❌ 可见性增强失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 3秒后开始加载
        QTimer.singleShot(3000, load_dxf)
        
        print("🚀 进入事件循环...")
        print("程序将在3秒后自动加载DXF文件...")
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())