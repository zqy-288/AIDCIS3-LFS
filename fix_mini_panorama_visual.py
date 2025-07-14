#!/usr/bin/env python3
"""
修复小型全景图视觉更新问题
"""

import os
import re

def add_visual_update_debugging():
    """添加视觉更新调试代码"""
    print("🔧 添加小型全景图视觉更新调试...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在更新颜色后添加强制刷新和验证
    debug_code = '''print(f"  🎯 [小型全景图] 找到目标孔位: {hole_id}")
                            # 更新颜色
                            from PySide6.QtGui import QBrush, QPen
                            old_brush = item.brush()
                            old_color = old_brush.color()
                            
                            item.setBrush(QBrush(color))
                            item.setPen(QPen(color.darker(120), 0.5))
                            
                            # 验证颜色是否真正改变
                            new_brush = item.brush()
                            new_color = new_brush.color()
                            print(f"  🎨 [小型全景图] 颜色变化: ({old_color.red()}, {old_color.green()}, {old_color.blue()}) -> ({new_color.red()}, {new_color.green()}, {new_color.blue()})")
                            
                            # 强制更新该项
                            item.update()
                            
                            # 确保项是可见的
                            if not item.isVisible():
                                item.setVisible(True)
                                print(f"  ⚠️ [小型全景图] 项不可见，已设置为可见")
                            
                            # 获取项的位置用于调试
                            pos = item.pos()
                            rect = item.boundingRect()
                            print(f"  📍 [小型全景图] 项位置: ({pos.x():.1f}, {pos.y():.1f}), 大小: {rect.width():.1f}x{rect.height():.1f}")
                            
                            found = True'''
    
    # 替换原有的更新代码
    pattern = r'print\(f"  🎯 \[小型全景图\] 找到目标孔位: {hole_id}"\)\s*\n\s*# 更新颜色.*?found = True'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, debug_code, content, flags=re.DOTALL)
        print("✅ 添加了颜色验证调试")
    
    # 在更新完成后添加场景刷新
    scene_refresh = '''
                    if not found:
                        print(f"  ⚠️ [小型全景图] 未找到孔位 {hole_id}")
                    else:
                        # 强制刷新整个场景
                        scene.update()
                        print(f"  🔄 [小型全景图] 场景已刷新")'''
    
    # 在 for 循环结束后添加场景刷新
    pattern2 = r'(if not found:\s*\n\s*print\(f"  ⚠️ \[小型全景图\] 未找到孔位 {hole_id}"\))'
    replacement2 = scene_refresh
    
    if re.search(pattern2, content):
        content = re.sub(pattern2, replacement2, content)
        print("✅ 添加了场景刷新")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def add_mini_panorama_refresh():
    """添加小型全景图强制刷新机制"""
    print("\n🔧 添加小型全景图强制刷新...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在 _apply_mini_immediate_update 结尾添加视口刷新
    viewport_refresh = '''
            # 强制刷新小型全景图视图（与CompletePanoramaWidget保持一致）
            self.mini_panorama.update()
            if hasattr(self.mini_panorama, 'viewport'):
                self.mini_panorama.viewport().update()
                self.mini_panorama.viewport().repaint()  # 添加 repaint 强制立即重绘
                print(f"  🖼️ [小型全景图] 视口已强制重绘")'''
    
    # 找到原有的视口更新代码并增强
    pattern = r'# 强制刷新小型全景图视图（与CompletePanoramaWidget保持一致）\s*\n\s*self\.mini_panorama\.update\(\)\s*\n\s*if hasattr\(self\.mini_panorama, \'viewport\'\):\s*\n\s*self\.mini_panorama\.viewport\(\)\.update\(\)'
    
    if re.search(pattern, content):
        content = re.sub(pattern, viewport_refresh.strip(), content)
        print("✅ 增强了视口刷新机制")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def check_mini_panorama_type():
    """检查小型全景图的实际类型和属性"""
    print("\n🔧 添加小型全景图类型检查...")
    
    type_check = '''
    def debug_mini_panorama_state(self):
        """调试小型全景图状态"""
        if not hasattr(self, 'mini_panorama'):
            print("❌ [调试] 没有 mini_panorama 属性")
            return
            
        print("=" * 60)
        print("🔍 小型全景图状态调试:")
        print(f"  类型: {type(self.mini_panorama)}")
        print(f"  是否可见: {self.mini_panorama.isVisible()}")
        
        if hasattr(self.mini_panorama, 'scene'):
            scene = self.mini_panorama.scene
            if scene:
                items = scene.items()
                print(f"  场景项数量: {len(items)}")
                
                # 统计不同颜色的项
                color_stats = {}
                for item in items[:100]:  # 只检查前100个避免太慢
                    if hasattr(item, 'brush'):
                        brush = item.brush()
                        color = brush.color()
                        color_key = f"({color.red()}, {color.green()}, {color.blue()})"
                        color_stats[color_key] = color_stats.get(color_key, 0) + 1
                
                print(f"  颜色统计 (前100项):")
                for color, count in color_stats.items():
                    print(f"    {color}: {count} 个")
                    
                # 检查视口设置
                if hasattr(self.mini_panorama, 'viewport'):
                    viewport = self.mini_panorama.viewport()
                    print(f"  视口大小: {viewport.width()}x{viewport.height()}")
                    print(f"  视口更新模式: {self.mini_panorama.viewportUpdateMode()}")
                    
        print("=" * 60)
'''
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在类的末尾添加调试方法
    class_pattern = r'(class DynamicSectorDisplayWidget.*?)((?=\nclass )|$)'
    match = re.search(class_pattern, content, re.DOTALL)
    
    if match:
        class_content = match.group(1)
        class_content = class_content.rstrip() + type_check + '\n'
        content = content[:match.start()] + class_content + content[match.end():]
        print("✅ 添加了状态调试方法")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_graphicsitem_update():
    """修复图形项更新问题"""
    print("\n🔧 修复图形项更新机制...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 确保使用正确的 QGraphicsEllipseItem
    fix_import = '''from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsItem, QGraphicsPathItem, QGraphicsEllipseItem'''
    
    # 替换导入
    old_import = r'from PySide6\.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsItem, QGraphicsPathItem'
    if re.search(old_import, content):
        content = re.sub(old_import, fix_import, content)
        print("✅ 修复了导入")
    
    # 在创建孔位时确保正确设置
    create_fix = '''# 创建简单的圆形表示
            hole_item = QGraphicsEllipseItem(
                hole.center_x - hole.radius,
                hole.center_y - hole.radius,
                hole.radius * 2,
                hole.radius * 2
            )
            
            # 设置初始颜色（灰色）
            hole_item.setBrush(QBrush(QColor(200, 200, 200)))
            hole_item.setPen(QPen(QColor(150, 150, 150), 0.5))
            
            # 确保项是可见的
            hole_item.setVisible(True)
            
            # 设置 Z 值确保在上层
            hole_item.setZValue(1)'''
    
    # 查找并替换创建代码
    pattern = r'# 创建简单的圆形表示.*?hole_item\.setPen\(QPen\(QColor\(150, 150, 150\), 0\.5\)\)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, create_fix.strip(), content, flags=re.DOTALL)
        print("✅ 修复了项创建")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def add_force_refresh_method():
    """添加强制刷新方法"""
    print("\n🔧 添加强制刷新方法...")
    
    refresh_method = '''
    def force_mini_panorama_refresh(self):
        """强制刷新小型全景图"""
        if hasattr(self, 'mini_panorama') and self.mini_panorama:
            # 方法1：重置视口
            if hasattr(self.mini_panorama, 'viewport'):
                self.mini_panorama.viewport().update()
                
            # 方法2：触发重绘事件
            from PySide6.QtCore import QEvent
            from PySide6.QtGui import QPaintEvent
            event = QPaintEvent(self.mini_panorama.rect())
            self.mini_panorama.event(event)
            
            # 方法3：重置变换
            transform = self.mini_panorama.transform()
            self.mini_panorama.resetTransform()
            self.mini_panorama.setTransform(transform)
            
            print("🔄 [小型全景图] 已执行强制刷新")
'''
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在类末尾添加
    class_pattern = r'(class DynamicSectorDisplayWidget.*?)((?=\nclass )|$)'
    match = re.search(class_pattern, content, re.DOTALL)
    
    if match:
        class_content = match.group(1)
        class_content = class_content.rstrip() + refresh_method + '\n'
        content = content[:match.start()] + class_content + content[match.end():]
        print("✅ 添加了强制刷新方法")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    print("=" * 80)
    print("修复小型全景图视觉更新问题")
    print("=" * 80)
    
    add_visual_update_debugging()
    add_mini_panorama_refresh()
    check_mini_panorama_type()
    fix_graphicsitem_update()
    add_force_refresh_method()
    
    print("\n" + "=" * 80)
    print("✅ 修复完成！")
    print("\n新增功能：")
    print("1. 增强了颜色更新验证")
    print("2. 添加了强制视口刷新")
    print("3. 添加了状态调试方法 debug_mini_panorama_state()")
    print("4. 确保图形项正确创建和显示")
    print("5. 添加了强制刷新方法 force_mini_panorama_refresh()")
    print("\n如果问题仍然存在，可以在代码中调用调试方法查看状态")
    print("=" * 80)

if __name__ == "__main__":
    main()