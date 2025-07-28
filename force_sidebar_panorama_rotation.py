#!/usr/bin/env python3
"""
强制应用侧边栏全景图旋转
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from src.core_business.graphics.rotation_config import get_rotation_manager


def force_sidebar_panorama_rotation():
    """强制应用侧边栏全景图旋转"""
    print("🔧 强制侧边栏全景图旋转")
    print("=" * 40)
    
    # 获取应用实例
    app = QApplication.instance()
    if not app:
        print("❌ 没有找到运行中的应用")
        return
    
    # 查找主窗口
    main_window = None
    for widget in app.topLevelWidgets():
        if hasattr(widget, 'sidebar_panorama'):
            main_window = widget
            break
    
    if not main_window:
        print("❌ 没有找到主窗口")
        return
    
    print("✅ 找到主窗口")
    
    # 检查侧边栏全景图
    if hasattr(main_window, 'sidebar_panorama') and main_window.sidebar_panorama:
        sidebar_panorama = main_window.sidebar_panorama
        print("✅ 找到侧边栏全景图组件")
        
        if hasattr(sidebar_panorama, 'panorama_view'):
            panorama_view = sidebar_panorama.panorama_view
            
            # 获取当前变换
            current_transform = panorama_view.transform()
            print(f"📊 当前变换: m11={current_transform.m11():.3f}, m12={current_transform.m12():.3f}")
            
            # 获取旋转配置
            rotation_manager = get_rotation_manager()
            if rotation_manager.is_rotation_enabled("scale_manager"):
                angle = rotation_manager.get_rotation_angle("scale_manager")
                print(f"🔄 应用 {angle}° 旋转...")
                
                # 应用旋转
                current_transform.rotate(angle)
                panorama_view.setTransform(current_transform)
                
                # 强制更新
                panorama_view.viewport().update()
                panorama_view.repaint()
                
                # 再次检查
                new_transform = panorama_view.transform()
                print(f"📊 新变换: m11={new_transform.m11():.3f}, m12={new_transform.m12():.3f}")
                
                if abs(new_transform.m12()) > 0.01:
                    print("✅ 旋转成功应用！")
                else:
                    print("❌ 旋转未生效")
            else:
                print("❌ scale_manager 旋转未启用")
        else:
            print("❌ 侧边栏全景图没有 panorama_view 属性")
    else:
        print("❌ 没有找到侧边栏全景图组件")


if __name__ == "__main__":
    print("⚠️ 此脚本需要在主程序运行时执行")
    print("   请在主程序加载数据后运行此脚本")
    
    # 如果作为独立脚本运行，尝试连接到运行中的应用
    force_sidebar_panorama_rotation()