#!/usr/bin/env python3
"""
修正扇形偏移方向
"""

import os
import re

def fix_offset_direction():
    """修正偏移方向为负值（向左偏移）"""
    print("🔧 修正偏移方向...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改场景矩形计算，使用负偏移
    old_rect = """offset_rect = QRectF(
                visual_center.x() - view_width_scene / 2 + offset_scene,
                visual_center.y() - view_height_scene / 2,
                view_width_scene,
                view_height_scene
            )"""
    
    new_rect = """offset_rect = QRectF(
                visual_center.x() - view_width_scene / 2 - offset_scene,  # 改为减法，向左偏移
                visual_center.y() - view_height_scene / 2,
                view_width_scene,
                view_height_scene
            )"""
    
    content = content.replace(old_rect, new_rect)
    
    # 同时修改日志说明
    old_log = "# 计算需要的偏移量（向左移动内容，相当于向右移动视图）"
    new_log = "# 计算需要的偏移量（向右移动内容，相当于向左移动视图）"
    
    content = content.replace(old_log, new_log)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 偏移方向已修正为负值")

def add_main_view_offset():
    """为主预览视图添加偏移逻辑"""
    print("\n🔧 为主预览视图添加偏移...")
    
    # 需要确认主预览视图的文件位置
    print("ℹ️  主预览视图可能在以下位置之一：")
    print("   - src/modules/main_detection_view.py")
    print("   - src/aidcis2/graphics/graphics_view.py")
    print("   - 或其他位置")
    
    # 检查可能的文件
    possible_files = [
        "src/modules/main_detection_view.py",
        "src/aidcis2/graphics/graphics_view.py"
    ]
    
    for filepath in possible_files:
        if os.path.exists(filepath):
            print(f"   ✓ 找到文件: {filepath}")
            with open(filepath, 'r') as f:
                content = f.read()
                if "OptimizedGraphicsView" in content or "主检测视图" in content:
                    print(f"     → 可能是主预览视图")

def create_offset_sync():
    """创建偏移同步机制"""
    sync_code = '''
def sync_offset_to_main_view(offset_ratio: float, enabled: bool):
    """同步偏移设置到主预览视图"""
    # TODO: 需要确定主预览视图的具体位置和访问方式
    # 可能的实现：
    # 1. 通过信号传递偏移设置
    # 2. 直接访问主视图实例并应用偏移
    # 3. 使用共享的配置管理器
    
    print(f"TODO: 同步偏移到主视图 - 比例: {offset_ratio:.1%}, 启用: {enabled}")
'''
    
    print("\n📝 偏移同步代码模板已创建")
    print(sync_code)

def main():
    print("=" * 80)
    print("修正偏移方向和主视图同步")
    print("=" * 80)
    
    fix_offset_direction()
    add_main_view_offset()
    create_offset_sync()
    
    print("\n" + "=" * 80)
    print("✅ 偏移方向已修正！")
    print("\n关于主预览视图：")
    print("主预览视图的偏移需要：")
    print("1. 确定主视图的具体实现位置")
    print("2. 了解主视图与扇形视图的关系")
    print("3. 实现偏移同步机制")
    print("\n如果您能提供主预览视图的更多信息，我可以帮您实现偏移同步。")
    print("=" * 80)

if __name__ == "__main__":
    main()