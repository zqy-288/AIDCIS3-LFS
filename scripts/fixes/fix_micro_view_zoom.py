#!/usr/bin/env python3
"""
修复微观视图初始缩放过大的问题

问题原因：
1. _show_sector_in_view 中调用 fitInView 后，又在 switch_to_micro_view 中调用 set_micro_view_scale
2. 导致双重缩放，使得视图过度放大
3. set_micro_view_scale 的最小缩放比例 1.2 在已经 fitInView 的基础上太大

解决方案：
1. 在 set_micro_view_scale 中添加缩放锁检查
2. 调整微观视图的缩放范围
3. 在 _show_sector_in_view 中设置标志，跳过额外的缩放
"""

import sys
import os
from pathlib import Path

def fix_graphics_view():
    """修复 graphics_view.py 中的缩放逻辑"""
    file_path = Path("src/core_business/graphics/graphics_view.py")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复1：在 set_micro_view_scale 方法开始处添加缩放锁检查
    old_micro_scale = '''    def set_micro_view_scale(self):
        """设置微观视图的适当缩放比例"""
        # 微观视图需要更大的缩放比例以显示细节
        current_scale = self.transform().m11()'''
    
    new_micro_scale = '''    def set_micro_view_scale(self):
        """设置微观视图的适当缩放比例"""
        # 如果正在进行 fitInView 操作，跳过额外缩放
        if getattr(self, '_is_fitting', False):
            self.logger.info("跳过 set_micro_view_scale（正在进行 fitInView）")
            return
            
        # 如果已经通过 fitInView 设置了合适的缩放，跳过
        if getattr(self, '_fitted_to_sector', False):
            self.logger.info("跳过 set_micro_view_scale（已适配到扇形）")
            # 重置标志
            self._fitted_to_sector = False
            return
            
        # 微观视图需要更大的缩放比例以显示细节
        current_scale = self.transform().m11()'''
    
    content = content.replace(old_micro_scale, new_micro_scale)
    
    # 修复2：调整微观视图的缩放范围（降低最小值）
    old_scale_range = '''        # 微观视图的缩放范围
        min_micro_scale = 1.2
        max_micro_scale = 4.0'''
    
    new_scale_range = '''        # 微观视图的缩放范围（调整后）
        min_micro_scale = 0.8  # 降低最小值，因为可能已经通过 fitInView 放大
        max_micro_scale = 3.0  # 降低最大值，避免过度放大'''
    
    content = content.replace(old_scale_range, new_scale_range)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 修复了 graphics_view.py 中的微观视图缩放逻辑")

def fix_native_view():
    """修复 native_main_detection_view_p1.py 中的缩放逻辑"""
    file_path = Path("src/pages/main_detection_p1/native_main_detection_view_p1.py")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在 fitInView 后设置标志，告诉后续方法已经适配过了
    old_fit_code = '''                        # 适配视图到扇形区域（只调用一次）
                        graphics_view.fitInView(bounding_rect, Qt.KeepAspectRatio)
                        
                        self.logger.info(f"✅ 视图已适配到扇形区域，边界: ({min_x:.1f}, {min_y:.1f}) - ({max_x:.1f}, {max_y:.1f})")'''
    
    new_fit_code = '''                        # 适配视图到扇形区域（只调用一次）
                        graphics_view.fitInView(bounding_rect, Qt.KeepAspectRatio)
                        
                        # 设置标志，告诉 set_micro_view_scale 跳过额外缩放
                        graphics_view._fitted_to_sector = True
                        
                        self.logger.info(f"✅ 视图已适配到扇形区域，边界: ({min_x:.1f}, {min_y:.1f}) - ({max_x:.1f}, {max_y:.1f})")'''
    
    content = content.replace(old_fit_code, new_fit_code)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 修复了 native_main_detection_view_p1.py 中的缩放标志设置")

def main():
    """主函数"""
    print("开始修复微观视图初始缩放过大的问题...")
    
    # 修复 graphics_view.py
    fix_graphics_view()
    
    # 修复 native_main_detection_view_p1.py
    fix_native_view()
    
    print("\n✅ 所有修复已完成！")
    print("\n修复内容：")
    print("1. 在 set_micro_view_scale 中添加了缩放锁检查")
    print("2. 调整了微观视图的缩放范围（min: 1.2->0.8, max: 4.0->3.0）")
    print("3. 在 fitInView 后设置标志，避免重复缩放")
    print("\n请重新运行程序测试微观视图的初始缩放是否正常。")

if __name__ == "__main__":
    main()