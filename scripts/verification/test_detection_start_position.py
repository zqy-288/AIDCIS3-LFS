#!/usr/bin/env python3
"""
测试检测起始位置是否从BC098R164+BC102R164开始
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
from src.core_business.models.hole_data import HoleData, HoleCollection


def create_test_holes():
    """创建测试孔位数据"""
    holes = []
    
    # 创建一些测试孔位，包括起始位置附近的
    test_positions = [
        # 右下角区域 (sector_4) - 包含起始位置
        ("BC098R164", 1176.0, -1922.4),  # 起始位置1
        ("BC102R164", 1224.0, -1922.4),  # 起始位置2
        ("BC098R163", 1176.0, -1910.4),
        ("BC102R163", 1224.0, -1910.4),
        
        # 右上角区域 (sector_1)
        ("BC098R001", 1176.0, 10.0),
        ("BC102R001", 1224.0, 10.0),
        
        # 左上角区域 (sector_2)
        ("AC098R001", -1176.0, 10.0),
        ("AC102R001", -1224.0, 10.0),
        
        # 左下角区域 (sector_3)
        ("AC098R164", -1176.0, -1922.4),
        ("AC102R164", -1224.0, -1922.4),
    ]
    
    for hole_id, x, y in test_positions:
        hole = HoleData(
            hole_id=hole_id,
            center_x=x,
            center_y=y,
            radius=5.0  # 半径而不是直径
        )
        holes.append(hole)
    
    # 创建孔位字典
    holes_dict = {hole.hole_id: hole for hole in holes}
    return HoleCollection(holes=holes_dict)


def test_detection_order():
    """测试检测顺序"""
    print("=" * 80)
    print("测试检测起始位置")
    print("=" * 80)
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 创建测试数据
    hole_collection = create_test_holes()
    print(f"\n创建了 {len(hole_collection.holes)} 个测试孔位")
    
    # 创建渲染器并生成路径
    renderer = SnakePathRenderer()
    renderer.set_hole_collection(hole_collection)
    detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
    
    print(f"\n生成了 {len(detection_units)} 个检测单元")
    
    # 显示前10个检测单元
    print("\n前10个检测单元:")
    print("-" * 60)
    
    for i, unit in enumerate(detection_units[:10]):
        if unit.is_pair and len(unit.holes) == 2:
            print(f"{i+1:3d}. {unit.holes[0].hole_id} + {unit.holes[1].hole_id}")
        else:
            print(f"{i+1:3d}. {unit.holes[0].hole_id}")
    
    # 验证起始位置
    print("\n" + "=" * 60)
    print("验证结果:")
    print("-" * 60)
    
    if len(detection_units) > 0:
        first_unit = detection_units[0]
        if first_unit.is_pair and len(first_unit.holes) == 2:
            first_holes = f"{first_unit.holes[0].hole_id} + {first_unit.holes[1].hole_id}"
            expected = "BC098R164 + BC102R164"
            
            if first_holes == expected:
                print(f"✅ 检测起始位置正确: {first_holes}")
            else:
                print(f"❌ 检测起始位置错误:")
                print(f"   期望: {expected}")
                print(f"   实际: {first_holes}")
        else:
            print(f"❌ 第一个检测单元不是配对: {first_unit.holes[0].hole_id}")
    else:
        print("❌ 没有生成检测单元")
    
    # 分析扇形顺序
    print("\n扇形处理顺序分析:")
    print("-" * 60)
    
    current_sector = None
    sector_changes = []
    
    for i, unit in enumerate(detection_units):
        # 使用第一个孔位判断扇形
        hole = unit.holes[0]
        x, y = hole.center_x, hole.center_y
        
        # 判断扇形
        if x > 0 and y > 0:
            sector = "sector_1 (右上)"
        elif x < 0 and y > 0:
            sector = "sector_2 (左上)"
        elif x < 0 and y < 0:
            sector = "sector_3 (左下)"
        else:  # x > 0 and y < 0
            sector = "sector_4 (右下)"
        
        if sector != current_sector:
            current_sector = sector
            sector_changes.append((i, sector))
    
    for idx, (unit_idx, sector) in enumerate(sector_changes):
        print(f"{idx+1}. 从单元 {unit_idx+1} 开始: {sector}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_detection_order()