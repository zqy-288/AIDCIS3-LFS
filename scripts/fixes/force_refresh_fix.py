#!/usr/bin/env python3
"""
添加强制刷新机制的修复脚本
"""

import os

def add_force_refresh():
    """添加强制刷新机制"""
    
    # 在 simulation_controller.py 中添加强制刷新
    file_path = 'src/pages/main_detection_p1/components/simulation_controller.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找 _force_refresh_graphics_view 方法
    if '_force_refresh_graphics_view' in content:
        print(f"✅ {file_path} 已包含强制刷新方法")
    else:
        print(f"❌ {file_path} 缺少强制刷新方法")
    
    # 检查是否在清除颜色后调用强制刷新
    if 'self._force_refresh_graphics_view()' in content:
        print(f"✅ 正确调用强制刷新")
    else:
        print(f"⚠️  可能未调用强制刷新")
    
    print("\n建议的额外修复:")
    print("1. 在 _finalize_current_pair_status 末尾添加:")
    print("   QApplication.processEvents()  # 强制处理所有待处理的事件")
    print("\n2. 在 _update_hole_status 中添加:")
    print("   if color_override is None:")
    print("       # 清除蓝色时额外强制刷新")
    print("       QTimer.singleShot(10, self._force_refresh_all_views)")
    print("\n3. 考虑添加一个全局刷新方法:")
    print("   def _force_refresh_all_views(self):")
    print("       if self.graphics_view:")
    print("           self.graphics_view.viewport().repaint()")
    print("       if self.panorama_widget:")
    print("           self.panorama_widget.repaint()")

if __name__ == "__main__":
    add_force_refresh()