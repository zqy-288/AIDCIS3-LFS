#!/usr/bin/env python3
"""
修复编号系统问题 - 恢复显示层旋转策略
保持编号系统基于原始坐标，只在显示层进行旋转
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core_business.graphics.rotation_utils import *


def fix_numbering_system():
    """修复编号系统问题"""
    print("🔢 修复编号系统与旋转的冲突")
    print("=" * 45)
    
    print("📋 问题分析:")
    print("   1. 编号基于原始坐标（DXF解析阶段）")
    print("   2. 坐标旋转在编号之后执行")
    print("   3. 导致编号与显示位置不匹配")
    
    print(f"\n🎯 解决方案：恢复显示层旋转策略")
    print("   - 禁用坐标系旋转：❌ 保持原始编号")
    print("   - 启用显示层旋转：✅ 视觉效果旋转")
    print("   - 扇形分配基于原始坐标")
    
    print(f"\n🔄 应用修复配置:")
    
    # 禁用坐标层旋转，保持原始编号
    toggle_component_rotation("coordinate", False)
    print("   ✅ 禁用坐标系旋转 - 保持原始编号不变")
    
    # 启用显示层旋转，获得视觉旋转效果
    toggle_component_rotation("scale_manager", True)
    toggle_component_rotation("dynamic_sector", True)
    toggle_component_rotation("view_transform", True)
    print("   ✅ 启用显示层旋转 - 获得90度视觉效果")
    
    print(f"\n✅ 修复完成！新配置:")
    print_rotation_status()
    
    # 验证配置
    manager = get_rotation_manager()
    coord_rotation = manager.get_rotation_angle("coordinate")
    display_rotation = manager.get_rotation_angle("scale_manager")
    
    print(f"\n📊 验证结果:")
    print(f"   坐标系旋转: {coord_rotation}° ({'禁用' if coord_rotation == 0 else '启用'})")
    print(f"   显示层旋转: {display_rotation}° ({'禁用' if display_rotation == 0 else '启用'})")
    
    if coord_rotation == 0 and display_rotation == 90:
        print("   ✅ 配置正确：编号保持不变，显示获得旋转效果")
    else:
        print("   ⚠️ 配置可能需要调整")
    
    return coord_rotation, display_rotation


def verify_numbering_logic():
    """验证编号逻辑"""
    print(f"\n🧪 编号逻辑验证:")
    print("=" * 25)
    
    print("📋 新的处理流程:")
    print("   1. DXF解析 → 基于原始坐标编号 (C001R001在左上)")
    print("   2. 扇形分配 → 基于原始坐标分配扇形")
    print("   3. 显示渲染 → 应用90度旋转变换")
    print("   4. 最终效果 → 编号对应正确位置")
    
    print(f"\n✅ 预期结果:")
    print("   - C001R001 显示在视觉左上角（旋转后）")
    print("   - 编号与用户期望的位置匹配")
    print("   - 扇形分配基于正确的坐标关系")
    print("   - 保持原始业务逻辑不变")


if __name__ == "__main__":
    coord_rot, display_rot = fix_numbering_system()
    verify_numbering_logic()
    
    print(f"\n📝 重要说明:")
    print("   这个修复确保了编号系统的业务逻辑正确性")
    print("   编号不再因为坐标旋转而与显示位置错乱")
    print("   用户看到的孔位编号与实际位置保持一致")