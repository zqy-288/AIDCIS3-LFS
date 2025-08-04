#!/usr/bin/env python3
"""
修复微观视图默认显示问题
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def fix_micro_view_display():
    """修复微观视图显示"""
    print("=" * 80)
    print("修复微观视图显示问题")
    print("=" * 80)
    
    # 读取native_main_detection_view_p1.py文件
    file_path = "src/pages/main_detection_p1/native_main_detection_view_p1.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键修复点
    fixes_needed = []
    
    # 1. 检查数据加载后是否触发微观视图
    if "_load_default_sector1()" not in content:
        fixes_needed.append("数据加载后未触发默认扇形加载")
    
    # 2. 检查微观视图按钮默认状态
    if 'self.micro_view_btn.setChecked(True)' not in content:
        fixes_needed.append("微观视图按钮未默认选中")
    
    # 3. 检查视图模式初始化
    if 'self.current_view_mode = "micro"' not in content:
        fixes_needed.append("视图模式未初始化为micro")
    
    print("\n检查结果：")
    if fixes_needed:
        for fix in fixes_needed:
            print(f"   ❌ {fix}")
    else:
        print("   ✅ 所有关键代码都存在")
    
    # 提出修复建议
    print("\n修复建议：")
    print("1. 确保在load_hole_collection方法中，微观视图模式下调用_load_default_sector1")
    print("2. 确保_load_default_sector1方法正确触发_show_sector_in_view")
    print("3. 确保graphics_view在微观模式下不显示所有孔位")
    
    # 检查具体的问题
    print("\n详细分析：")
    
    # 查找load_hole_collection方法中的关键代码
    if "if self.center_panel and hasattr(self.center_panel, 'micro_view_btn') and self.center_panel.micro_view_btn.isChecked():" in content:
        print("   ✅ load_hole_collection中有微观视图检查")
    else:
        print("   ❌ load_hole_collection中缺少微观视图检查")
    
    # 查找_show_sector_in_view的场景过滤逻辑
    if "item.setVisible(is_visible)" in content:
        print("   ✅ _show_sector_in_view中有场景项过滤逻辑")
    else:
        print("   ❌ _show_sector_in_view中缺少场景项过滤逻辑")
    
    # 添加关键修复：确保graphics_view在加载数据时不会显示所有孔位
    print("\n关键修复点：")
    print("在load_hole_collection中，当微观视图模式时：")
    print("1. 不要调用graphics_view.load_holes()")
    print("2. 先加载所有数据到场景，但设置为不可见")
    print("3. 然后调用_load_default_sector1来只显示sector1的孔位")


if __name__ == "__main__":
    fix_micro_view_display()