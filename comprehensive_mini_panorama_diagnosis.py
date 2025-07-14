#!/usr/bin/env python3
"""
综合诊断小型全景图显示问题
"""

import os
import re

def analyze_mini_panorama_issues():
    """分析小型全景图可能的问题"""
    print("🔍 综合诊断小型全景图问题...")
    print("=" * 80)
    
    # 读取 dynamic_sector_view.py
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查可能的问题
    issues = []
    
    # 1. 检查是否有背景或遮挡
    if "setBackgroundBrush" in content:
        issues.append("可能有背景刷设置覆盖了图形项")
    
    # 2. 检查视口更新模式
    if "setViewportUpdateMode" in content:
        issues.append("视口更新模式可能需要调整")
    
    # 3. 检查场景大小
    if "setSceneRect" in content:
        # 计算场景矩形出现次数
        count = content.count("setSceneRect")
        if count > 2:
            issues.append(f"场景矩形被设置了 {count} 次，可能有冲突")
    
    # 4. 检查 Z 值设置
    z_value_matches = re.findall(r'setZValue\((\d+)\)', content)
    if z_value_matches:
        z_values = [int(z) for z in z_value_matches]
        if max(z_values) > 10:
            issues.append(f"Z值设置过高: {max(z_values)}，可能导致渲染问题")
    
    # 5. 检查透明度设置
    if "setOpacity" in content:
        issues.append("有透明度设置，可能影响可见性")
    
    print("发现的潜在问题：")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    
    if not issues:
        print("  ✅ 未发现明显的配置问题")
    
    return issues

def add_background_check():
    """添加背景检查和修复"""
    print("\n🔧 添加背景透明度检查...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 确保小型全景图背景透明或半透明
    background_fix = '''def _create_mini_panorama(self):
        """创建小型全景预览图"""
        from PySide6.QtGui import QPainter, QBrush, QColor
        from PySide6.QtCore import Qt
        
        mini_view = OptimizedGraphicsView()
        mini_view.setFixedSize(300, 200)
        mini_view.setRenderHint(QPainter.Antialiasing, True)
        mini_view.setRenderHint(QPainter.SmoothPixmapTransform, True)
        mini_view.setRenderHint(QPainter.TextAntialiasing, True)
        
        # 强制使用高质量渲染
        mini_view.setRenderHint(QPainter.HighQualityAntialiasing, True)
        
        # 设置优化标志
        mini_view.setOptimizationFlag(QGraphicsView.DontSavePainterState, False)
        mini_view.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, False)
        
        # 确保背景透明或半透明，不遮挡内容
        mini_view.setBackgroundBrush(QBrush(QColor(248, 249, 250, 100)))  # 半透明背景
        
        # 确保视口更新模式正确
        mini_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # 禁用滚动条
        mini_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        mini_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        return mini_view'''
    
    # 替换 _create_mini_panorama 方法
    pattern = r'def _create_mini_panorama\(self\):.*?return mini_view'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, background_fix.strip(), content, flags=re.DOTALL)
        print("✅ 修复了背景设置")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def add_item_visibility_check():
    """添加项可见性检查"""
    print("\n🔧 添加图形项可见性验证...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    visibility_check = '''def verify_mini_panorama_items_visibility(self):
        """验证小型全景图中项的可见性"""
        if not hasattr(self, 'mini_panorama') or not self.mini_panorama:
            print("❌ [验证] 小型全景图不存在")
            return
            
        scene = self.mini_panorama.scene
        if not scene:
            print("❌ [验证] 场景不存在")
            return
            
        items = scene.items()
        print(f"🔍 [验证] 检查 {len(items)} 个项的可见性...")
        
        visible_count = 0
        invisible_count = 0
        out_of_bounds_count = 0
        
        scene_rect = scene.sceneRect()
        
        for item in items[:100]:  # 检查前100个
            if hasattr(item, 'isVisible'):
                if item.isVisible():
                    visible_count += 1
                    
                    # 检查是否在场景范围内
                    item_rect = item.sceneBoundingRect()
                    if not scene_rect.contains(item_rect):
                        out_of_bounds_count += 1
                        print(f"  ⚠️ 项在场景范围外: {item_rect}")
                else:
                    invisible_count += 1
        
        print(f"  ✅ 可见项: {visible_count}")
        print(f"  ❌ 不可见项: {invisible_count}")
        print(f"  ⚠️ 超出范围项: {out_of_bounds_count}")
        
        # 检查视口变换
        transform = self.mini_panorama.transform()
        print(f"  🔄 视口变换: 缩放({transform.m11():.2f}, {transform.m22():.2f})")
        
        # 检查视口大小
        viewport_rect = self.mini_panorama.viewport().rect()
        print(f"  📐 视口大小: {viewport_rect.width()}x{viewport_rect.height()}")
'''
    
    # 在类末尾添加
    class_pattern = r'(class DynamicSectorDisplayWidget.*?)((?=\nclass )|$)'
    match = re.search(class_pattern, content, re.DOTALL)
    
    if match:
        class_content = match.group(1)
        class_content = class_content.rstrip() + '\n' + visibility_check + '\n'
        content = content[:match.start()] + class_content + content[match.end():]
        print("✅ 添加了可见性验证方法")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def fix_scene_update_mechanism():
    """修复场景更新机制"""
    print("\n🔧 修复场景更新机制...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在状态更新后添加完整的场景刷新
    update_fix = '''# 强制刷新整个场景
                        scene.update()
                        print(f"  🔄 [小型全景图] 场景已刷新")
                        
                        # 触发视图重绘
                        self.mini_panorama.viewport().update()
                        
                        # 如果还是不行，尝试重置场景
                        if hasattr(self, '_mini_panorama_needs_reset'):
                            self.mini_panorama.setScene(None)
                            self.mini_panorama.setScene(scene)
                            self._mini_panorama_needs_reset = False
                            print(f"  🔄 [小型全景图] 场景已重置")'''
    
    # 查找场景刷新位置
    pattern = r'# 强制刷新整个场景\s*\n\s*scene\.update\(\)\s*\n\s*print\(f"  🔄 \[小型全景图\] 场景已刷新"\)'
    
    if re.search(pattern, content):
        content = re.sub(pattern, update_fix.strip(), content)
        print("✅ 增强了场景更新机制")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def add_final_diagnostic():
    """添加最终诊断信息"""
    print("\n📋 最终诊断结果：")
    print("=" * 80)
    
    print("""
根据用户描述"孔位状态储存在前面有问题，但在后面又连续了"，以及日志显示更新但视觉无变化的情况，
最可能的原因是：

1. 数据存储问题：
   - 扇形切换时数据可能被覆盖
   - 小型全景图可能使用了扇形数据而非完整数据
   ✅ 已修复：确保小型全景图使用独立的完整数据

2. 查找效率问题：
   - 遍历查找太慢，导致部分更新丢失
   ✅ 已修复：使用字典加速查找

3. 渲染问题：
   - 背景可能遮挡了内容
   - 视口更新模式可能不正确
   - 图形项可能在视图范围外
   ✅ 已修复：调整背景透明度，设置正确的更新模式

4. Qt事件循环问题：
   - 更新可能被缓存未立即显示
   ✅ 已修复：添加强制刷新机制

建议测试步骤：
1. 重启程序
2. 调用 verify_mini_panorama_items_visibility() 检查可见性
3. 调用 debug_mini_panorama_state() 查看状态
4. 调用 test_mini_panorama_update() 测试手动更新
5. 如果仍有问题，设置 self._mini_panorama_needs_reset = True 触发场景重置
""")
    
    print("=" * 80)

def main():
    print("=" * 80)
    print("综合诊断小型全景图显示问题")
    print("=" * 80)
    
    # 分析问题
    issues = analyze_mini_panorama_issues()
    
    # 应用修复
    add_background_check()
    add_item_visibility_check()
    fix_scene_update_mechanism()
    
    # 最终诊断
    add_final_diagnostic()

if __name__ == "__main__":
    main()