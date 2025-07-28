#!/usr/bin/env python3
"""
进一步增强全景图孔位可见性
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
    """连接到正在运行的程序并增强可见性"""
    print("🔧 连接到运行中的程序，增强全景图可见性...")
    
    try:
        # 导入Qt
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QBrush, QColor, QPen
        
        # 获取现有应用实例
        app = QApplication.instance()
        if not app:
            print("❌ 没有找到运行中的Qt应用")
            return 1
        
        print("✅ 找到运行中的Qt应用")
        
        # 查找主窗口
        main_window = None
        for widget in app.topLevelWidgets():
            if hasattr(widget, 'sidebar_panorama'):
                main_window = widget
                break
        
        if not main_window:
            print("❌ 没有找到主窗口")
            return 1
        
        print("✅ 找到主窗口")
        
        def enhance_visibility():
            try:
                print("\n🎨 开始增强全景图可见性...")
                
                panorama = main_window.sidebar_panorama
                if not panorama:
                    print("❌ 全景图组件不存在")
                    return
                
                view = panorama.panorama_view
                if not view or not hasattr(view, 'hole_items') or not view.hole_items:
                    print("❌ 全景图视图或孔位项不存在")
                    return
                
                print(f"🔍 找到 {len(view.hole_items)} 个孔位项")
                
                # 使用非常大的半径和高对比度颜色
                large_radius = 25.0  # 更大的半径
                bright_colors = [
                    QColor(255, 0, 0),    # 红色
                    QColor(0, 255, 0),    # 绿色
                    QColor(0, 0, 255),    # 蓝色
                    QColor(255, 255, 0),  # 黄色
                    QColor(255, 0, 255),  # 品红
                    QColor(0, 255, 255),  # 青色
                ]
                
                updated_count = 0
                for i, (hole_id, hole_item) in enumerate(view.hole_items.items()):
                    if hasattr(hole_item, 'setRect'):
                        from PySide6.QtCore import QRectF
                        
                        # 设置大矩形
                        new_rect = QRectF(-large_radius, -large_radius, 
                                        large_radius * 2, large_radius * 2)
                        hole_item.setRect(new_rect)
                        
                        # 设置高对比度颜色（循环使用）
                        color = bright_colors[i % len(bright_colors)]
                        
                        if hasattr(hole_item, 'setBrush'):
                            hole_item.setBrush(QBrush(color))
                        
                        if hasattr(hole_item, 'setPen'):
                            # 白色粗边框
                            hole_item.setPen(QPen(QColor(255, 255, 255), 3))
                        
                        # 设置高Z值确保在顶层
                        if hasattr(hole_item, 'setZValue'):
                            hole_item.setZValue(100)
                        
                        updated_count += 1
                        
                        # 每更新1000个就打印一次进度
                        if updated_count % 1000 == 0:
                            print(f"  📊 已更新 {updated_count} 个孔位...")
                
                print(f"✅ 已将 {updated_count} 个孔位调整为 {large_radius}px 半径，彩色高对比度显示")
                
                # 强制更新场景和视图
                if hasattr(view, 'scene') and view.scene:
                    # 设置场景背景为深色以提高对比度
                    view.scene.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
                    view.scene.update()
                    print("✅ 场景背景设置为深色")
                
                view.update()
                view.viewport().update()
                panorama.update()
                main_window.update()
                
                print("✅ 所有视图已强制更新")
                print("\n🎯 全景图现在应该显示大号彩色孔位，对比度极高！")
                print("💡 如果还是看不清，可能需要调整全景图的缩放或窗口大小")
                
                # 打印一些调试信息
                if hasattr(view, 'scene') and view.scene:
                    scene_rect = view.scene.sceneRect()
                    print(f"📐 场景边界: {scene_rect}")
                    
                    items_count = len(view.scene.items())
                    print(f"🔢 场景中总图形项: {items_count}")
                
            except Exception as e:
                print(f"❌ 可见性增强失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 立即执行增强
        enhance_visibility()
        
        print("\n✅ 增强完成，程序继续运行...")
        return 0
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    result = main()
    if result == 0:
        print("🎉 可见性增强成功！请检查GUI中的全景图")
    else:
        print("❌ 可见性增强失败")
    sys.exit(result)