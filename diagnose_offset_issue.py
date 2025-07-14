#!/usr/bin/env python3
"""
诊断和修复偏移视觉效果问题
"""

import os
import re

def add_debug_logging():
    """添加更详细的调试日志"""
    print("🔧 添加偏移调试日志...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在 centerOn 调用后添加验证
    debug_code = '''
        # 立即验证 centerOn 是否生效
        actual_center = self.graphics_view.mapToScene(self.graphics_view.viewport().rect().center())
        print(f"🔍 [偏移调试] centerOn 后的实际中心: ({actual_center.x():.1f}, {actual_center.y():.1f})")
        print(f"🔍 [偏移调试] 期望与实际的差异: X={abs(adjusted_center_scene.x() - actual_center.x()):.1f}, Y={abs(adjusted_center_scene.y() - actual_center.y()):.1f}")
        
        # 强制更新视口
        self.graphics_view.viewport().update()
        self.graphics_view.scene.update()
        
        # 再次尝试 centerOn（如果第一次没生效）
        if abs(adjusted_center_scene.x() - actual_center.x()) > 5:
            print(f"⚠️ [偏移调试] centerOn 未生效，再次尝试...")
            self.graphics_view.centerOn(adjusted_center_scene)
            
            # 使用 QTimer 延迟再次尝试
            from PySide6.QtCore import QTimer
            QTimer.singleShot(10, lambda: self.graphics_view.centerOn(adjusted_center_scene))
            QTimer.singleShot(50, lambda: self.graphics_view.centerOn(adjusted_center_scene))'''
    
    # 在 centerOn(adjusted_center_scene) 之后插入调试代码
    pattern = r'self\.graphics_view\.centerOn\(adjusted_center_scene\)\s*\n\s*print\(f"📏 \[偏移应用\]'
    
    if re.search(pattern, content):
        # 找到位置并插入
        content = re.sub(
            r'(self\.graphics_view\.centerOn\(adjusted_center_scene\))\s*\n',
            r'\1' + debug_code + '\n',
            content
        )
        print("✅ 添加了 centerOn 调试代码")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_offset_mechanism():
    """修复偏移机制"""
    print("\n🔧 修复偏移机制...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 方案1：使用 setSceneRect 来强制视图范围
    new_offset_logic = '''# 应用偏移效果 - 使用更可靠的方法
        # 首先重置所有变换
        self.graphics_view.resetTransform()
        
        # 应用缩放
        self.graphics_view.scale(scale, scale)
        
        # 计算偏移量（在视图坐标系中）
        if self.sector_offset_enabled and self.sector_offset_ratio > 0:
            # 获取视口尺寸
            viewport_rect = self.graphics_view.viewport().rect()
            viewport_width = viewport_rect.width()
            viewport_height = viewport_rect.height()
            
            # 计算需要的偏移量（向左移动内容，相当于向右移动视图）
            offset_pixels = viewport_width * self.sector_offset_ratio
            
            print(f"📏 [偏移应用] 偏移量: {offset_pixels:.1f}px ({self.sector_offset_ratio:.1%})")
            print(f"📍 [偏移应用] 原始中心: ({visual_center.x():.1f}, {visual_center.y():.1f})")
            
            # 方法1：通过设置场景矩形来实现偏移
            # 计算偏移后的视图矩形（在场景坐标中）
            view_width_scene = viewport_width / scale
            view_height_scene = viewport_height / scale
            offset_scene = offset_pixels / scale
            
            # 创建偏移后的场景矩形
            offset_rect = QRectF(
                visual_center.x() - view_width_scene / 2 + offset_scene,
                visual_center.y() - view_height_scene / 2,
                view_width_scene,
                view_height_scene
            )
            
            # 设置场景矩形并适配
            self.graphics_view.setSceneRect(offset_rect)
            self.graphics_view.fitInView(offset_rect, Qt.KeepAspectRatio)
            
            print(f"📐 [偏移应用] 场景矩形: ({offset_rect.x():.1f}, {offset_rect.y():.1f}, {offset_rect.width():.1f}, {offset_rect.height():.1f})")
            
            # 验证实际效果
            actual_center = self.graphics_view.mapToScene(viewport_rect.center())
            print(f"📍 [偏移应用] 实际中心: ({actual_center.x():.1f}, {actual_center.y():.1f})")
        else:
            # 没有偏移，直接居中
            self.graphics_view.centerOn(visual_center)
        
        # 立即设置标志防止被覆盖
        self.graphics_view.disable_auto_center = True
        self.graphics_view.disable_auto_fit = True'''
    
    # 替换现有的偏移逻辑
    pattern = r'# 应用偏移效果 - 使用正确的方法.*?self\.graphics_view\.disable_auto_fit = True'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_offset_logic, content, flags=re.DOTALL)
        print("✅ 更新了偏移机制")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def add_force_offset_method():
    """添加强制偏移方法"""
    print("\n🔧 添加强制偏移方法...")
    
    force_method = '''
    def _force_apply_offset(self):
        """强制应用偏移效果"""
        if not hasattr(self, '_sector_view_settings'):
            return
            
        settings = self._sector_view_settings
        if 'offset_pixels' in settings and settings['offset_pixels'] > 0:
            # 获取当前视口中心
            viewport_rect = self.graphics_view.viewport().rect()
            current_center = self.graphics_view.mapToScene(viewport_rect.center())
            
            # 计算目标中心（考虑偏移）
            target_center = settings['visual_center']
            offset_scene = settings['offset_pixels'] / settings['scale']
            adjusted_center = QPointF(target_center.x() - offset_scene, target_center.y())
            
            # 如果当前中心与目标相差太大，强制调整
            diff = abs(current_center.x() - adjusted_center.x())
            if diff > 5:
                print(f"🔨 [强制偏移] 检测到偏移未生效，强制调整 {diff:.1f}px")
                
                # 使用平移而不是 centerOn
                dx = adjusted_center.x() - current_center.x()
                dy = adjusted_center.y() - current_center.y()
                
                # 获取当前变换并添加平移
                transform = self.graphics_view.transform()
                transform.translate(dx, dy)
                self.graphics_view.setTransform(transform)
'''
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在 _enforce_sector_settings 方法后添加
    pattern = r'(def _enforce_sector_settings.*?self\.graphics_view\.fitInView.*?\n)'
    
    if re.search(pattern, content, re.DOTALL):
        # 找到 DynamicSectorDisplayWidget 类的结尾位置
        class_pattern = r'(class DynamicSectorDisplayWidget.*?)((?=\nclass )|$)'
        match = re.search(class_pattern, content, re.DOTALL)
        
        if match:
            class_content = match.group(1)
            # 在类的末尾添加新方法
            class_content = class_content.rstrip() + force_method + '\n'
            content = content[:match.start()] + class_content + content[match.end():]
            print("✅ 添加了强制偏移方法")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    print("=" * 80)
    print("诊断和修复偏移视觉效果问题")
    print("=" * 80)
    
    print("\n问题分析：")
    print("- 偏移计算正确")
    print("- centerOn 命令执行但未生效")
    print("- 实际视图中心始终不变")
    
    add_debug_logging()
    fix_offset_mechanism()
    add_force_offset_method()
    
    print("\n" + "=" * 80)
    print("✅ 修复完成！")
    print("\n修复内容：")
    print("1. 添加了 centerOn 后的验证")
    print("2. 改用 setSceneRect + fitInView 方法")
    print("3. 添加了强制偏移的备用方法")
    print("\n请重启程序测试效果！")
    print("=" * 80)

if __name__ == "__main__":
    main()