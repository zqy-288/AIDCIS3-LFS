#!/usr/bin/env python3
"""
修复双重旋转问题 - 只保留坐标层旋转
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core_business.graphics.rotation_utils import *


def fix_double_rotation():
    """修复双重旋转问题"""
    print("🔧 修复双重旋转问题")
    print("=" * 40)
    
    print("📋 当前状态:")
    print_rotation_status()
    
    print(f"\n🎯 应用修复方案：只保留坐标层旋转")
    print("   - 保持坐标系旋转：✅ 启用")
    print("   - 禁用显示层旋转：❌ 禁用")
    
    # 保持坐标层旋转
    toggle_component_rotation("coordinate", True)
    
    # 禁用显示层旋转  
    toggle_component_rotation("scale_manager", False)
    toggle_component_rotation("dynamic_sector", False)
    toggle_component_rotation("view_transform", False)
    
    print(f"\n✅ 修复完成！新配置:")
    print_rotation_status()
    
    # 验证总旋转角度
    manager = get_rotation_manager()
    total_rotation = 0.0
    if manager.is_rotation_enabled("coordinate"):
        total_rotation += manager.get_rotation_angle("coordinate")
    if manager.is_rotation_enabled("scale_manager"):
        total_rotation += manager.get_rotation_angle("scale_manager")
    
    print(f"\n🔄 修复后总旋转角度: {total_rotation}°")
    
    if abs(total_rotation) == 90:
        print("✅ 修复成功：单层90度旋转")
    else:
        print("⚠️ 修复可能不完整")
    
    return total_rotation


if __name__ == "__main__":
    fix_double_rotation()
    
    print(f"\n📝 修复说明:")
    print("   1. 孔位坐标在数据层统一旋转90度顺时针")  
    print("   2. 扇形分配基于旋转后的坐标计算")
    print("   3. 显示时不再额外旋转，避免双重旋转")
    print("   4. 最终效果：整体顺时针旋转90度")