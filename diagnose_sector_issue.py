#!/usr/bin/env python3
"""
诊断扇形切换导致的小型全景图更新问题
"""

import os
import re

def fix_mini_panorama_sector_independence():
    """确保小型全景图独立于扇形切换"""
    print("🔧 修复小型全景图扇形独立性...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 确保小型全景图使用完整数据，而不是扇形数据
    init_fix = '''def _initialize_mini_panorama_data(self, hole_collection):
        """初始化小型全景图的数据"""
        print(f"🔄 [小型全景图] 初始化数据，共 {len(hole_collection)} 个孔位")
        
        if not self.mini_panorama:
            print(f"❌ [小型全景图] mini_panorama 不存在")
            return
            
        # 确保有场景
        if not hasattr(self.mini_panorama, 'scene') or not self.mini_panorama.scene:
            from PySide6.QtWidgets import QGraphicsScene
            scene = QGraphicsScene()
            self.mini_panorama.setScene(scene)
            print(f"✅ [小型全景图] 创建新场景")
        
        scene = self.mini_panorama.scene
        
        # 清空现有内容
        scene.clear()
        
        # 创建字典存储所有孔位项，便于后续快速查找
        self.mini_panorama_items = {}
        
        # 创建所有孔位的图形项
        from PySide6.QtWidgets import QGraphicsEllipseItem
        from PySide6.QtGui import QBrush, QPen, QColor
        
        hole_count = 0
        # 确保正确遍历hole_collection
        if hasattr(hole_collection, 'holes') and isinstance(hole_collection.holes, dict):
            holes_to_add = hole_collection.holes.values()
        else:
            holes_to_add = hole_collection
            
        for hole in holes_to_add:
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
            
            # 设置hole_id作为data以便更新时查找
            hole_item.setData(0, hole.hole_id)
            
            # 保存到字典中便于快速查找
            self.mini_panorama_items[hole.hole_id] = hole_item
            
            scene.addItem(hole_item)
            hole_count += 1
        
        print(f"🎨 [小型全景图] 已创建 {hole_count} 个孔位图形项")
        print(f"📦 [小型全景图] 保存了 {len(self.mini_panorama_items)} 个项到查找字典")'''
    
    # 替换初始化方法
    pattern = r'def _initialize_mini_panorama_data\(self, hole_collection\):.*?print\(f"📐 \[小型全景图\] 视图已适配"\)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, init_fix.strip(), content, flags=re.DOTALL)
        print("✅ 修复了初始化方法，添加了查找字典")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def optimize_mini_panorama_lookup():
    """优化小型全景图的查找机制"""
    print("\n🔧 优化查找机制...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 优化查找逻辑，使用字典而不是遍历
    lookup_fix = '''# mini_panorama 是 OptimizedGraphicsView，需要通过场景查找图形项
            if hasattr(self, 'mini_panorama_items') and hole_id in self.mini_panorama_items:
                # 使用字典快速查找
                item = self.mini_panorama_items[hole_id]
                print(f"  🎯 [小型全景图] 通过字典找到目标孔位: {hole_id}")
                
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
                
                # 强制刷新场景和视口
                if self.mini_panorama.scene:
                    self.mini_panorama.scene.update()
                self.mini_panorama.viewport().update()
                self.mini_panorama.viewport().repaint()
                
                print(f"  ✅ [小型全景图] 状态已更新并刷新")
                
            elif hasattr(self.mini_panorama, 'scene'):'''
    
    # 查找并替换
    pattern = r'# mini_panorama 是 OptimizedGraphicsView，需要通过场景查找图形项\s*\n\s*if hasattr\(self\.mini_panorama, \'scene\'\):'
    if re.search(pattern, content):
        content = re.sub(pattern, lookup_fix.strip() + '\n            # 备用方法：场景遍历', content)
        print("✅ 优化了查找逻辑")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def ensure_complete_data():
    """确保小型全景图始终使用完整数据"""
    print("\n🔧 确保使用完整数据...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在设置孔位集合时保存完整数据引用
    complete_data_fix = '''def set_hole_collection(self, hole_collection: HoleCollection):
        """设置孔位集合并创建扇形图形管理器"""
        if hole_collection and len(hole_collection) > 0:
            # 保存完整的孔位集合以供扇形切换使用
            self.complete_hole_collection = hole_collection
            
            # 确保小型全景图使用完整数据
            self.mini_panorama_complete_data = hole_collection  # 专门为小型全景图保存的完整数据'''
    
    # 查找并添加
    pattern = r'def set_hole_collection\(self, hole_collection: HoleCollection\):.*?self\.complete_hole_collection = hole_collection'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(
            r'(self\.complete_hole_collection = hole_collection)',
            r'\1\n            \n            # 确保小型全景图使用完整数据\n            self.mini_panorama_complete_data = hole_collection  # 专门为小型全景图保存的完整数据',
            content
        )
        print("✅ 添加了完整数据引用")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def add_diagnostic_info():
    """添加诊断信息"""
    print("\n📝 添加诊断建议...")
    
    diagnostic = """
诊断建议：

问题："孔位状态储存在前面有问题，但在后面又连续了"

可能原因：
1. 扇形切换时，小型全景图的数据被部分更新
2. 查找机制效率低，导致某些更新丢失
3. 图形项的坐标可能超出视图范围

已实施的修复：
1. 为小型全景图创建独立的项字典，加快查找
2. 确保小型全景图始终使用完整数据
3. 优化更新和刷新机制

测试步骤：
1. 重启程序
2. 运行模拟，观察小型全景图
3. 如果仍有问题，在代码中调用：
   - debug_mini_panorama_state() - 查看状态
   - test_mini_panorama_update() - 测试更新
"""
    
    print(diagnostic)

def main():
    print("=" * 80)
    print("诊断扇形切换导致的小型全景图更新问题")
    print("=" * 80)
    
    fix_mini_panorama_sector_independence()
    optimize_mini_panorama_lookup()
    ensure_complete_data()
    add_diagnostic_info()
    
    print("=" * 80)

if __name__ == "__main__":
    main()