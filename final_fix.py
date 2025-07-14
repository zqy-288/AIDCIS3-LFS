#!/usr/bin/env python3
"""
AIDCIS 渲染问题最终修复方案
基于日志分析的精确修复
"""

import os
import re
from datetime import datetime

def fix_mini_panorama_data_consistency():
    """修复小型全景图数据一致性问题"""
    print("\n🔧 修复小型全景图数据一致性...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份
    backup = f"{filepath}.final_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 修复1: 在 _setup_mini_panorama 中确保使用正确的数据访问方式
    old_setup = """# 添加所有孔位到小型全景图
        hole_count = 0
        for hole in hole_collection.holes.values():"""
    
    new_setup = """# 添加所有孔位到小型全景图
        hole_count = 0
        # 确保正确遍历hole_collection
        if hasattr(hole_collection, 'holes') and isinstance(hole_collection.holes, dict):
            holes_to_add = hole_collection.holes.values()
        else:
            # 如果是可迭代对象，直接使用
            holes_to_add = hole_collection
            
        for hole in holes_to_add:"""
    
    content = content.replace(old_setup, new_setup)
    
    # 修复2: 改进查找逻辑，处理类型转换
    old_find = """item_hole_id = item.data(0)
                        if item_hole_id and item_hole_id == hole_id:"""
    
    new_find = """item_hole_id = item.data(0)
                        # 转换为字符串比较，避免类型不匹配
                        if item_hole_id and str(item_hole_id) == str(hole_id):"""
    
    content = content.replace(old_find, new_find)
    
    # 修复3: 在 _initialize_mini_panorama_data 中也做同样修改
    old_init_loop = """hole_count = 0
        for hole in hole_collection:"""
    
    new_init_loop = """hole_count = 0
        # 确保正确遍历hole_collection
        if hasattr(hole_collection, 'holes') and isinstance(hole_collection.holes, dict):
            holes_to_add = hole_collection.holes.values()
        else:
            holes_to_add = hole_collection
            
        for hole in holes_to_add:"""
    
    content = content.replace(old_init_loop, new_init_loop)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 小型全景图数据一致性修复完成")

def fix_offset_visual_effect():
    """修复中间列偏移视觉效果"""
    print("\n🔧 修复中间列偏移视觉效果...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 完全重写偏移应用逻辑
    old_offset_logic = """# 应用偏移效果而不使用fitInView（避免强制居中）
        # 设置变换以显示偏移后的视图区域
        transform = QTransform()
        transform.scale(scale, scale)
        transform.translate(-visual_center_x, -visual_center_y)
        self.graphics_view.setTransform(transform)"""
    
    new_offset_logic = """# 应用偏移效果 - 使用正确的方法
        # 首先重置所有变换
        self.graphics_view.resetTransform()
        
        # 应用缩放
        self.graphics_view.scale(scale, scale)
        
        # 计算偏移量（在视图坐标系中）
        if self.sector_offset_enabled and self.sector_offset_ratio > 0:
            # 获取视口尺寸
            viewport_width = self.graphics_view.viewport().width()
            
            # 计算需要的偏移量（向左移动内容，相当于向右移动视图）
            offset_pixels = viewport_width * self.sector_offset_ratio
            
            # 获取当前的视觉中心在视图坐标中的位置
            visual_center_view = self.graphics_view.mapFromScene(visual_center)
            
            # 调整视觉中心的x坐标（向左移动）
            adjusted_x = visual_center_view.x() - offset_pixels
            adjusted_center_view = QPointF(adjusted_x, visual_center_view.y())
            
            # 将调整后的点转回场景坐标
            adjusted_center_scene = self.graphics_view.mapToScene(adjusted_center_view.toPoint())
            
            # 使用调整后的中心
            self.graphics_view.centerOn(adjusted_center_scene)
            
            print(f"📏 [偏移应用] 偏移量: {offset_pixels:.1f}px ({self.sector_offset_ratio:.1%})")
            print(f"📍 [偏移应用] 原始中心: ({visual_center.x():.1f}, {visual_center.y():.1f})")
            print(f"📍 [偏移应用] 调整后中心: ({adjusted_center_scene.x():.1f}, {adjusted_center_scene.y():.1f})")
        else:
            # 没有偏移，直接居中
            self.graphics_view.centerOn(visual_center)
        
        # 立即设置标志防止被覆盖
        self.graphics_view.disable_auto_center = True
        self.graphics_view.disable_auto_fit = True"""
    
    content = content.replace(old_offset_logic, new_offset_logic)
    
    # 同时修复验证逻辑
    old_verify_end = """if diff_x > 10 or diff_y > 10:
                print(f"⚠️ [变换验证] 偏差较大: X偏差={diff_x}, Y偏差={diff_y}")
                # 如果偏差大，返回False表示需要重新应用
                return False
            else:
                print(f"✅ [变换验证] 变换成功应用")
                return True"""
    
    new_verify_end = """# 考虑偏移的验证
            expected_offset = 0
            if hasattr(self, 'sector_offset_enabled') and self.sector_offset_enabled:
                viewport_width = self.graphics_view.viewport().width()
                expected_offset = viewport_width * self.sector_offset_ratio
            
            # 允许一定的误差范围
            tolerance = 5.0
            
            if diff_x > tolerance or diff_y > tolerance:
                print(f"⚠️ [变换验证] 偏差较大: X偏差={diff_x:.1f}, Y偏差={diff_y:.1f}")
                if expected_offset > 0:
                    print(f"   (期望偏移: {expected_offset:.1f}px)")
                return False
            else:
                print(f"✅ [变换验证] 变换成功应用")
                return True"""
    
    content = content.replace(old_verify_end, new_verify_end)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 偏移视觉效果修复完成")

def fix_synchronization_signal():
    """修复信号同步问题"""
    print("\n🔧 修复信号同步问题...")
    
    filepath = "src/main_window.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在 _update_simulation_progress 中添加直接调用
    # 查找函数定义
    pattern = r'def _update_simulation_progress\(self\):.*?(?=\n    def|\n\nclass|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        func_content = match.group(0)
        
        # 在状态更新后添加直接同步
        if "_synchronize_panorama_status" not in func_content:
            # 找到 status_updated.emit 的位置
            emit_pattern = r'self\.status_updated\.emit\(hole_id, "qualified"\)'
            
            replacement = '''self.status_updated.emit(hole_id, "qualified")
                
                # 直接调用同步函数以确保实时更新
                try:
                    if hasattr(self, '_synchronize_panorama_status'):
                        from PySide6.QtGui import QColor
                        color = QColor(76, 175, 80)  # 绿色
                        self._synchronize_panorama_status(hole_id, "qualified", color)
                        print(f"✅ [模拟] 直接同步了孔位 {hole_id}")
                except Exception as e:
                    print(f"⚠️ [模拟] 直接同步失败: {e}")'''
            
            func_content = re.sub(emit_pattern, replacement, func_content)
            content = content[:match.start()] + func_content + content[match.end():]
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 信号同步修复完成")

def add_final_debugging():
    """添加最终调试信息"""
    print("\n🔧 添加最终调试信息...")
    
    # 在 graphics_view.py 中添加偏移保护
    filepath = "src/aidcis2/graphics/graphics_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在所有可能触发居中的地方添加检查
    places_to_check = [
        ("def resizeEvent", "super().resizeEvent(event)", 
         """super().resizeEvent(event)
        
        # 检查是否应该跳过自动调整
        if getattr(self, 'disable_auto_center', False) or getattr(self, 'disable_auto_fit', False):
            self.logger.info("resizeEvent: 跳过自动调整（标志已设置）")
            return"""),
        
        ("def showEvent", "super().showEvent(event)",
         """super().showEvent(event)
        
        # 检查是否应该跳过自动调整
        if getattr(self, 'disable_auto_center', False):
            self.logger.info("showEvent: 跳过自动调整（disable_auto_center=True）")
            return""")
    ]
    
    for func_name, after_line, insert_code in places_to_check:
        if func_name not in content and after_line in content:
            content = content.replace(after_line, insert_code)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 最终调试信息添加完成")

def main():
    print("=" * 80)
    print("AIDCIS 渲染问题最终修复")
    print("基于日志分析的精确解决方案")
    print("=" * 80)
    
    fix_mini_panorama_data_consistency()
    fix_offset_visual_effect()
    fix_synchronization_signal()
    add_final_debugging()
    
    print("\n" + "=" * 80)
    print("✅ 所有修复已完成！")
    print("\n关键改进:")
    print("1. 统一了小型全景图的数据访问方式")
    print("2. 重写了偏移应用逻辑，使用视口坐标计算")
    print("3. 添加了直接同步调用确保实时更新")
    print("4. 增强了防覆盖保护机制")
    print("\n请重启程序测试效果！")
    print("=" * 80)

if __name__ == "__main__":
    main()