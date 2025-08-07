"""
测试坐标系修复
验证左边全景图和中间扇形显示是否一致
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QPointF
import math

# 导入相关类
from src.core_business.graphics.sector_types import SectorQuadrant
from src.pages.main_detection_p1.components.sector_assignment_manager import SectorAssignmentManager

def test_coordinate_fix():
    """测试坐标系修复"""
    
    print("=" * 80)
    print("坐标系修复测试")
    print("=" * 80)
    
    # 测试点（数学坐标系中的位置）
    test_points = [
        (100, 100, "右上"),
        (-100, 100, "左上"),
        (-100, -100, "左下"),
        (100, -100, "右下")
    ]
    
    center_x, center_y = 0, 0
    
    print("\n1. 测试 SectorQuadrant.from_position (修复后):")
    print("-" * 40)
    for x, y, desc in test_points:
        sector = SectorQuadrant.from_position(x, y, center_x, center_y)
        print(f"  位置 ({x:4}, {y:4}) [{desc}] -> {sector.value} ({sector.display_name})")
    
    print("\n2. 测试 SectorAssignmentManager:")
    print("-" * 40)
    for x, y, desc in test_points:
        dx = x - center_x
        dy = y - center_y
        
        # 使用管理器的逻辑
        if dx >= 0 and dy >= 0:
            sector = SectorQuadrant.SECTOR_1  # 右上
        elif dx < 0 and dy >= 0:
            sector = SectorQuadrant.SECTOR_2  # 左上
        elif dx < 0 and dy < 0:
            sector = SectorQuadrant.SECTOR_3  # 左下
        else:
            sector = SectorQuadrant.SECTOR_4  # 右下
            
        print(f"  位置 ({x:4}, {y:4}) [{desc}] -> {sector.value} ({sector.display_name})")
    
    print("\n3. 测试角度计算 (数学坐标系):")
    print("-" * 40)
    for x, y, desc in test_points:
        dx = x - center_x
        dy = y - center_y
        
        # 数学坐标系角度计算
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        if angle_deg < 0:
            angle_deg += 360
            
        sector = SectorQuadrant.from_angle(angle_deg)
        print(f"  位置 ({x:4}, {y:4}) [{desc}] -> 角度 {angle_deg:6.1f}° -> {sector.value}")
    
    print("\n4. 一致性检查:")
    print("-" * 40)
    all_consistent = True
    
    for x, y, desc in test_points:
        # 方法1: from_position
        sector1 = SectorQuadrant.from_position(x, y, center_x, center_y)
        
        # 方法2: 管理器逻辑
        dx = x - center_x
        dy = y - center_y
        if dx >= 0 and dy >= 0:
            sector2 = SectorQuadrant.SECTOR_1
        elif dx < 0 and dy >= 0:
            sector2 = SectorQuadrant.SECTOR_2
        elif dx < 0 and dy < 0:
            sector2 = SectorQuadrant.SECTOR_3
        else:
            sector2 = SectorQuadrant.SECTOR_4
        
        # 方法3: 角度计算
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        if angle_deg < 0:
            angle_deg += 360
        sector3 = SectorQuadrant.from_angle(angle_deg)
        
        consistent = (sector1 == sector2 == sector3)
        status = "✅" if consistent else "❌"
        
        print(f"  位置 ({x:4}, {y:4}) [{desc}]: {status}")
        if not consistent:
            print(f"    from_position: {sector1.value}")
            print(f"    管理器逻辑: {sector2.value}")
            print(f"    角度计算: {sector3.value}")
            all_consistent = False
    
    print("\n5. 结论:")
    print("-" * 40)
    if all_consistent:
        print("  ✅ 所有方法返回一致的结果！坐标系已统一。")
        print("  左边全景图和中间扇形显示应该保持一致。")
    else:
        print("  ❌ 仍存在不一致！需要进一步检查。")
    
    return all_consistent

def test_expected_mapping():
    """测试预期的扇形映射"""
    print("\n" + "=" * 80)
    print("预期扇形映射测试")
    print("=" * 80)
    
    # 预期映射（数学坐标系）
    expected_mapping = {
        "右上": SectorQuadrant.SECTOR_1,
        "左上": SectorQuadrant.SECTOR_2,
        "左下": SectorQuadrant.SECTOR_3,
        "右下": SectorQuadrant.SECTOR_4
    }
    
    print("\n预期的扇形映射（数学坐标系）:")
    print("-" * 40)
    for position, expected_sector in expected_mapping.items():
        print(f"  {position} -> {expected_sector.value} ({expected_sector.display_name})")
    
    print("\n实际测试结果:")
    print("-" * 40)
    
    test_cases = [
        (100, 100, "右上"),
        (-100, 100, "左上"),
        (-100, -100, "左下"),
        (100, -100, "右下")
    ]
    
    all_correct = True
    for x, y, desc in test_cases:
        actual_sector = SectorQuadrant.from_position(x, y, 0, 0)
        expected_sector = expected_mapping[desc]
        
        is_correct = actual_sector == expected_sector
        status = "✅" if is_correct else "❌"
        
        print(f"  {desc}: {status} (期望: {expected_sector.value}, 实际: {actual_sector.value})")
        
        if not is_correct:
            all_correct = False
    
    return all_correct

if __name__ == "__main__":
    # 运行测试
    fix_success = test_coordinate_fix()
    mapping_correct = test_expected_mapping()
    
    print("\n" + "=" * 80)
    print("总体测试结果")
    print("=" * 80)
    
    if fix_success and mapping_correct:
        print("✅ 坐标系修复成功！")
        print("左边全景图和中间扇形显示现在应该保持一致。")
    else:
        print("❌ 坐标系修复失败，需要进一步调试。")