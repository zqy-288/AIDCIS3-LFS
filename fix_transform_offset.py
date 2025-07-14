#!/usr/bin/env python3
"""
修复中间列偏移变换问题
问题：使用 QTransform 时，视图中心与期望中心有 43.44 像素偏差
"""

import os
import re
from datetime import datetime

def fix_transform_application():
    """修复变换应用逻辑"""
    print("🔧 修复变换应用逻辑...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return
    
    # 备份文件
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ 已备份到: {backup_path}")
    
    # 修复方案1：改用更精确的视图定位方法
    old_transform = """# 应用偏移效果而不使用fitInView（避免强制居中）
        # 设置变换以显示偏移后的视图区域
        transform = QTransform()
        transform.scale(scale, scale)
        transform.translate(-visual_center_x, -visual_center_y)
        self.graphics_view.setTransform(transform)"""
    
    new_transform = """# 应用偏移效果而不使用fitInView（避免强制居中）
        # 使用更精确的方法设置视图位置
        self.graphics_view.resetTransform()
        self.graphics_view.scale(scale, scale)
        
        # 计算视口中心在场景坐标中的位置
        viewport_center = self.graphics_view.viewport().rect().center()
        
        # 将视觉中心映射到视口中心
        # 这样可以确保扇形内容的视觉中心位于视图的中心
        self.graphics_view.centerOn(visual_center)
        
        # 立即禁用自动居中，防止后续操作覆盖
        self.graphics_view.disable_auto_center = True"""
    
    if old_transform in content:
        content = content.replace(old_transform, new_transform)
        print("✅ 修复了变换应用方法")
    else:
        print("⚠️ 未找到原始变换代码，尝试其他模式...")
        
        # 备用修复：查找并替换translate行
        pattern = r'transform\.translate\(-visual_center_x, -visual_center_y\)'
        replacement = '''# 直接使用centerOn方法，然后禁用自动居中
        self.graphics_view.resetTransform()
        self.graphics_view.scale(scale, scale)
        self.graphics_view.centerOn(visual_center)
        self.graphics_view.disable_auto_center = True'''
        
        if re.search(pattern, content):
            content = re.sub(pattern + r'\s*\n\s*self\.graphics_view\.setTransform\(transform\)', 
                           replacement, content)
            print("✅ 使用备用方法修复了变换")
    
    # 修复验证逻辑
    old_verify = """def _verify_transform_applied(self, expected_center_x: float, expected_center_y: float):
        \"\"\"验证变换是否成功应用\"\"\"
        try:
            # 获取当前视图中心
            view_center = self.graphics_view.mapToScene(self.graphics_view.viewport().rect().center())
            print(f"🔍 [变换验证] 期望中心: ({expected_center_x}, {expected_center_y})")
            print(f"🔍 [变换验证] 实际中心: ({view_center.x()}, {view_center.y()})")
            
            # 计算偏差
            diff_x = abs(view_center.x() - expected_center_x)
            diff_y = abs(view_center.y() - expected_center_y)"""
    
    new_verify = """def _verify_transform_applied(self, expected_center_x: float, expected_center_y: float):
        \"\"\"验证变换是否成功应用\"\"\"
        try:
            # 获取当前视图中心在场景坐标系中的位置
            viewport_rect = self.graphics_view.viewport().rect()
            view_center = self.graphics_view.mapToScene(viewport_rect.center())
            
            print(f"🔍 [变换验证] 期望中心: ({expected_center_x:.1f}, {expected_center_y:.1f})")
            print(f"🔍 [变换验证] 实际中心: ({view_center.x():.1f}, {view_center.y():.1f})")
            
            # 获取当前缩放
            current_scale = self.graphics_view.transform().m11()
            print(f"🔍 [变换验证] 当前缩放: {current_scale:.3f}")
            
            # 计算偏差（考虑浮点精度）
            diff_x = abs(view_center.x() - expected_center_x)
            diff_y = abs(view_center.y() - expected_center_y)"""
    
    content = content.replace(old_verify, new_verify)
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 变换修复完成")

def add_offset_debugging():
    """添加偏移调试工具"""
    print("\n🔧 添加偏移调试工具...")
    
    debug_code = '''
def debug_view_state(self):
    """调试视图状态"""
    if not hasattr(self, 'graphics_view'):
        return
        
    view = self.graphics_view
    viewport_rect = view.viewport().rect()
    scene_rect = view.sceneRect()
    
    # 视口中心在场景中的位置
    viewport_center_scene = view.mapToScene(viewport_rect.center())
    
    # 当前变换
    transform = view.transform()
    scale = transform.m11()
    
    print("=" * 60)
    print("📊 视图状态调试信息:")
    print(f"  视口尺寸: {viewport_rect.width()}x{viewport_rect.height()}")
    print(f"  场景矩形: ({scene_rect.x():.1f}, {scene_rect.y():.1f}, {scene_rect.width():.1f}, {scene_rect.height():.1f})")
    print(f"  视口中心(场景坐标): ({viewport_center_scene.x():.1f}, {viewport_center_scene.y():.1f})")
    print(f"  当前缩放: {scale:.3f}")
    print(f"  disable_auto_center: {getattr(view, 'disable_auto_center', False)}")
    print(f"  disable_auto_fit: {getattr(view, 'disable_auto_fit', False)}")
    
    # 检查是否有预期的扇形设置
    if hasattr(self, '_sector_view_settings'):
        settings = self._sector_view_settings
        expected_center = settings.get('visual_center')
        if expected_center:
            diff_x = viewport_center_scene.x() - expected_center.x()
            diff_y = viewport_center_scene.y() - expected_center.y()
            print(f"  期望中心: ({expected_center.x():.1f}, {expected_center.y():.1f})")
            print(f"  实际偏差: ({diff_x:.1f}, {diff_y:.1f})")
    print("=" * 60)
'''
    
    # 将调试函数添加到文件末尾
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已存在
    if "def debug_view_state" not in content:
        # 找到类的结尾位置
        class_pattern = r'class DynamicSectorDisplayWidget.*?(?=\nclass|\Z)'
        match = re.search(class_pattern, content, re.DOTALL)
        if match:
            # 在类结尾前插入调试函数
            insert_pos = match.end() - 1
            content = content[:insert_pos] + debug_code + content[insert_pos:]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print("✅ 添加了调试函数")
    
    print("✅ 调试工具添加完成")

def main():
    print("=" * 80)
    print("修复中间列偏移变换问题")
    print("=" * 80)
    
    fix_transform_application()
    add_offset_debugging()
    
    print("\n" + "=" * 80)
    print("✅ 修复完成！")
    print("\n测试方法:")
    print("1. 启动程序并加载数据")
    print("2. 观察中间列是否有向右偏移")
    print("3. 查看日志中的 '[变换验证]' 信息")
    print("4. 如果偏差仍然存在，可以在代码中调用 debug_view_state() 获取详细信息")
    print("=" * 80)

if __name__ == "__main__":
    main()