#!/usr/bin/env python3
"""
简单检查扇形分配
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core_business.models.hole_data import HoleData, HoleCollection


def check_sector_logic():
    """检查扇形分配逻辑"""
    # 创建测试数据
    test_cases = [
        # hole_id, x, y, 期望扇形
        ("BC098R164_1", 1176.0, 1922.4, "sector_1"),    # 右上，Y > 0
        ("BC098R164_2", -0.000, -2111.2, "sector_4"),   # 右下，x≈0, Y < 0
        ("BC098R001", 1176.0, 10.0, "sector_1"),        # 右上，Y > 0
        ("AC098R001", -1176.0, 10.0, "sector_2"),       # 左上，Y > 0
        ("AC098R164", -1176.0, -1922.4, "sector_3"),    # 左下，Y < 0
        ("BC102R164", 1224.0, -1922.4, "sector_4"),     # 右下，Y < 0
    ]
    
    print("测试扇形分配逻辑")
    print("=" * 80)
    
    # 假设中心在 (0, 0) 附近
    center_x = 0
    center_y = 0
    
    for hole_id, x, y, expected in test_cases:
        dx = x - center_x
        dy = y - center_y
        
        # 现有逻辑
        if dx >= 0 and dy >= 0:
            actual = "sector_1"
        elif dx < 0 and dy >= 0:
            actual = "sector_2"
        elif dx < 0 and dy < 0:
            actual = "sector_3"
        else:  # dx >= 0 and dy < 0
            actual = "sector_4"
        
        status = "✅" if actual == expected else "❌"
        print(f"{status} {hole_id}: ({x:7.1f}, {y:7.1f}) -> {actual} (期望: {expected})")
    
    # 特殊情况：x接近0
    print("\n特殊情况处理 (x ≈ 0):")
    print("-" * 80)
    
    x = -0.000
    y = -2111.2
    hole_id = "BC098R164"
    
    # 不使用特殊处理
    dx = x - center_x
    dy = y - center_y
    if dx >= 0 and dy >= 0:
        result1 = "sector_1"
    elif dx < 0 and dy >= 0:
        result1 = "sector_2"
    elif dx < 0 and dy < 0:
        result1 = "sector_3"
    else:
        result1 = "sector_4"
    
    # 使用特殊处理
    tolerance = 1.0
    if abs(x) < tolerance and hole_id.startswith('B'):
        x_sign = 1  # B侧为正
    else:
        x_sign = 1 if x >= 0 else -1
    
    if x_sign >= 0 and dy >= 0:
        result2 = "sector_1"
    elif x_sign < 0 and dy >= 0:
        result2 = "sector_2"
    elif x_sign < 0 and dy < 0:
        result2 = "sector_3"
    else:
        result2 = "sector_4"
    
    print(f"坐标: ({x}, {y})")
    print(f"  不使用特殊处理: {result1}")
    print(f"  使用特殊处理: {result2} {'✅' if result2 == 'sector_4' else '❌'}")


if __name__ == "__main__":
    check_sector_logic()