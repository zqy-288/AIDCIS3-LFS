#!/usr/bin/env python3
"""
修复偏移设置保存问题
"""

import os
import re

def fix_settings_storage():
    """修复设置存储以包含偏移信息"""
    print("🔧 修复偏移设置存储...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到保存设置的位置
    old_settings = '''self._sector_view_settings = {
            'scale': scale,
            'scene_rect': view_rect,
            'visual_center': visual_center
        }'''
    
    new_settings = '''self._sector_view_settings = {
            'scale': scale,
            'scene_rect': view_rect,
            'visual_center': visual_center,
            'offset_enabled': self.sector_offset_enabled,
            'offset_ratio': self.sector_offset_ratio,
            'offset_pixels': offset_pixels if self.sector_offset_enabled else 0
        }'''
    
    content = content.replace(old_settings, new_settings)
    
    # 同时需要在偏移逻辑之前定义 offset_pixels
    pattern = r'(if self\.sector_offset_enabled and self\.sector_offset_ratio > 0:)'
    replacement = r'offset_pixels = 0  # 初始化\n        \1'
    content = re.sub(pattern, replacement, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 修复了设置存储")

def add_manual_offset_test():
    """添加手动偏移测试方法"""
    print("\n🔧 添加手动偏移测试方法...")
    
    test_method = '''
    def test_offset_effect(self):
        """测试偏移效果（开发调试用）"""
        if not hasattr(self, 'graphics_view'):
            return
            
        print("=" * 60)
        print("🧪 偏移效果测试")
        
        # 获取当前状态
        viewport_rect = self.graphics_view.viewport().rect()
        scene_rect = self.graphics_view.sceneRect()
        current_center = self.graphics_view.mapToScene(viewport_rect.center())
        
        print(f"视口: {viewport_rect.width()}x{viewport_rect.height()}")
        print(f"场景矩形: ({scene_rect.x():.1f}, {scene_rect.y():.1f}, {scene_rect.width():.1f}, {scene_rect.height():.1f})")
        print(f"当前中心: ({current_center.x():.1f}, {current_center.y():.1f})")
        
        # 手动应用偏移
        if self.sector_offset_enabled:
            offset_pixels = viewport_rect.width() * self.sector_offset_ratio
            print(f"\\n应用 {self.sector_offset_ratio:.1%} 偏移 = {offset_pixels:.1f}px")
            
            # 方法1：使用滚动条
            h_bar = self.graphics_view.horizontalScrollBar()
            if h_bar:
                current_value = h_bar.value()
                new_value = current_value + int(offset_pixels)
                h_bar.setValue(new_value)
                print(f"滚动条: {current_value} -> {new_value}")
            
            # 验证效果
            new_center = self.graphics_view.mapToScene(viewport_rect.center())
            actual_offset = new_center.x() - current_center.x()
            print(f"实际偏移: {actual_offset:.1f}px")
            
        print("=" * 60)
'''
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在类的末尾添加测试方法
    class_pattern = r'(class DynamicSectorDisplayWidget.*?)((?=\nclass )|$)'
    match = re.search(class_pattern, content, re.DOTALL)
    
    if match:
        class_content = match.group(1)
        class_content = class_content.rstrip() + test_method + '\n'
        content = content[:match.start()] + class_content + content[match.end():]
        print("✅ 添加了测试方法")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def add_scrollbar_offset():
    """添加基于滚动条的偏移方法"""
    print("\n🔧 添加滚动条偏移方法...")
    
    scrollbar_method = '''
    def _apply_offset_via_scrollbar(self, offset_pixels: float):
        """通过滚动条应用偏移"""
        try:
            h_bar = self.graphics_view.horizontalScrollBar()
            if h_bar and h_bar.isVisible():
                # 计算滚动条位置
                current = h_bar.value()
                # 正值向右滚动（内容向左移）
                target = current + int(offset_pixels)
                
                # 确保在有效范围内
                target = max(h_bar.minimum(), min(h_bar.maximum(), target))
                
                h_bar.setValue(target)
                print(f"🎚️ [滚动条偏移] {current} -> {target} (偏移 {offset_pixels:.1f}px)")
                return True
            return False
        except Exception as e:
            print(f"❌ [滚动条偏移] 失败: {e}")
            return False
'''
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在合适的位置添加
    class_pattern = r'(class DynamicSectorDisplayWidget.*?)((?=\nclass )|$)'
    match = re.search(class_pattern, content, re.DOTALL)
    
    if match:
        class_content = match.group(1)
        class_content = class_content.rstrip() + scrollbar_method + '\n'
        content = content[:match.start()] + class_content + content[match.end():]
        print("✅ 添加了滚动条方法")
    
    # 在偏移逻辑中调用滚动条方法
    call_pattern = r'(print\(f"📍 \[偏移应用\] 实际中心:.*?\n)'
    call_code = r'''\1
            
            # 尝试使用滚动条方法作为备用
            if not self._apply_offset_via_scrollbar(offset_pixels):
                print("⚠️ [偏移应用] 滚动条方法不可用")
'''
    
    content = re.sub(call_pattern, call_code, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    print("=" * 80)
    print("修复偏移设置问题")
    print("=" * 80)
    
    fix_settings_storage()
    add_manual_offset_test()
    add_scrollbar_offset()
    
    print("\n" + "=" * 80)
    print("✅ 所有修复完成！")
    print("\n新增功能：")
    print("1. 偏移信息保存到设置中")
    print("2. 添加了手动测试方法")
    print("3. 添加了滚动条偏移作为备用方案")
    print("\n如果偏移仍然不生效，可以在代码中调用 test_offset_effect() 进行调试")
    print("=" * 80)

if __name__ == "__main__":
    main()