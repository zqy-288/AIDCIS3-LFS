#!/usr/bin/env python3
"""
最终修复：确保小型全景图正确显示
"""

import os
import re

def ensure_mini_panorama_on_top():
    """确保小型全景图在最上层"""
    print("🔧 确保小型全景图在最上层...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在浮动面板显示时确保层级
    layer_fix = '''# 显示浮动面板
        self.floating_panorama.show()
        self.floating_panorama.raise_()  # 确保在最上层
        
        # 同时确保小型全景图本身可见
        if self.mini_panorama:
            self.mini_panorama.show()
            self.mini_panorama.setEnabled(True)
            # 确保小型全景图在浮动面板内部也是最上层
            self.mini_panorama.raise_()
            
            # 强制刷新一次
            if hasattr(self.mini_panorama, 'scene') and self.mini_panorama.scene:
                self.mini_panorama.scene.update()
            self.mini_panorama.update()
            print(f"✅ [小型全景图] 已确保在最上层并刷新")'''
    
    # 查找并替换
    pattern = r'# 显示浮动面板\s*\n\s*self\.floating_panorama\.show\(\)\s*\n\s*self\.floating_panorama\.raise_\(\).*?print\(f"✅ \[小型全景图\] 已确保在最上层并刷新"\)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, layer_fix.strip(), content, flags=re.DOTALL)
        print("✅ 更新了层级设置")
    else:
        # 如果没找到，尝试其他模式
        pattern2 = r'self\.floating_panorama\.show\(\)\s*\n\s*self\.floating_panorama\.raise_\(\)'
        if re.search(pattern2, content):
            content = re.sub(pattern2, 
                           'self.floating_panorama.show()\n        self.floating_panorama.raise_()\n        \n        # 确保小型全景图可见\n        if self.mini_panorama:\n            self.mini_panorama.show()\n            self.mini_panorama.raise_()',
                           content)
            print("✅ 添加了层级设置")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def add_explicit_paint_event():
    """添加显式的绘制事件触发"""
    print("\n🔧 添加显式绘制事件...")
    
    paint_trigger = '''
    def trigger_mini_panorama_paint(self):
        """触发小型全景图的绘制事件"""
        if not hasattr(self, 'mini_panorama') or not self.mini_panorama:
            return
            
        try:
            # 方法1：使用 QApplication 处理事件
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            
            # 方法2：触发 paintEvent
            self.mini_panorama.update()
            self.mini_panorama.repaint()
            
            # 方法3：如果有场景，更新场景
            if hasattr(self.mini_panorama, 'scene') and self.mini_panorama.scene:
                self.mini_panorama.scene.update()
                
                # 获取所有项并强制更新
                items = self.mini_panorama.scene.items()
                update_count = 0
                for item in items[:50]:  # 更新前50个作为测试
                    if hasattr(item, 'update'):
                        item.update()
                        update_count += 1
                
                print(f"🎨 [小型全景图] 触发了 {update_count} 个项的更新")
            
            print("🔄 [小型全景图] 已触发绘制事件")
            
        except Exception as e:
            print(f"❌ [小型全景图] 触发绘制事件失败: {e}")
'''
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在类末尾添加
    class_pattern = r'(class DynamicSectorDisplayWidget.*?)((?=\nclass )|$)'
    match = re.search(class_pattern, content, re.DOTALL)
    
    if match:
        class_content = match.group(1)
        class_content = class_content.rstrip() + paint_trigger + '\n'
        content = content[:match.start()] + class_content + content[match.end():]
        print("✅ 添加了绘制触发方法")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_item_creation_with_proper_size():
    """修复项创建时的大小问题"""
    print("\n🔧 修复图形项大小...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 确保创建的圆形有合适的大小
    size_fix = '''for hole in holes_to_add:
            # 创建简单的圆形表示
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
            hole_item.setZValue(1)
            
            # 确保大小合适（如果孔太小，放大显示）
            min_display_radius = 2.0  # 最小显示半径
            if hole.radius < min_display_radius:
                scale_factor = min_display_radius / hole.radius
                hole_item.setScale(scale_factor)
                print(f"  🔍 [小型全景图] 孔位 {hole.hole_id} 太小，放大 {scale_factor:.1f} 倍")'''
    
    # 查找并替换
    pattern = r'for hole in holes_to_add:.*?hole_item\.setZValue\(1\)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, size_fix.strip(), content, flags=re.DOTALL)
        print("✅ 修复了项大小设置")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def add_mini_panorama_style_fix():
    """修复小型全景图的样式"""
    print("\n🔧 修复小型全景图样式...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 确保样式不会遮挡内容
    style_fix = '''self.mini_panorama.setStyleSheet("""
            QGraphicsView {
                background-color: rgba(248, 249, 250, 180);
                border: 2px solid #2196F3;
                border-radius: 8px;
            }
        """)'''
    
    # 查找并替换样式设置
    pattern = r'self\.mini_panorama\.setStyleSheet\(""".*?"""\)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, style_fix.strip(), content, flags=re.DOTALL)
        print("✅ 修复了样式设置")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def add_diagnostic_summary():
    """添加诊断总结"""
    print("\n📋 修复总结：")
    print("=" * 80)
    
    print("""
已应用的修复：

1. 层级问题修复：
   - 确保浮动面板在最上层
   - 确保小型全景图在浮动面板内也是最上层
   - 添加了 raise_() 调用

2. 绘制触发修复：
   - 添加了显式的绘制事件触发方法
   - 处理 Qt 事件队列
   - 强制更新场景和项

3. 图形项大小修复：
   - 确保小孔位也能显示（最小半径 2.0）
   - 自动缩放太小的项

4. 样式修复：
   - 调整背景透明度避免遮挡
   - 保持边框可见

测试建议：
1. 重启程序
2. 开始模拟，观察小型全景图
3. 如果仍无显示，在代码中调用：
   - trigger_mini_panorama_paint() - 强制触发绘制
   - verify_mini_panorama_items_visibility() - 检查可见性
   - debug_mini_panorama_state() - 查看状态

可能的剩余问题：
- 如果孔位坐标超出了小型全景图的视图范围
- 如果有其他 UI 元素遮挡
- 如果 Qt 样式表冲突

调试提示：
可以临时设置不同的背景色来确认小型全景图是否真的显示：
self.mini_panorama.setStyleSheet("background-color: red;")
""")
    
    print("=" * 80)

def main():
    print("=" * 80)
    print("最终修复：确保小型全景图正确显示")
    print("=" * 80)
    
    ensure_mini_panorama_on_top()
    add_explicit_paint_event()
    fix_item_creation_with_proper_size()
    add_mini_panorama_style_fix()
    add_diagnostic_summary()

if __name__ == "__main__":
    main()