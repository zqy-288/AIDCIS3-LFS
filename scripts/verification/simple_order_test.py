#!/usr/bin/env python3
"""
简单测试检测顺序
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
from src.core_business.models.hole_data import HoleData, HoleCollection


def test_order():
    """测试检测顺序"""
    # 创建一些测试孔位 - 每个扇形只创建几个关键孔位
    test_holes = []
    
    # sector_4 (右下) - BC098R164和BC102R164
    test_holes.extend([
        HoleData(hole_id="BC098R164", center_x=1176.0, center_y=-1922.4, radius=5.0),
        HoleData(hole_id="BC102R164", center_x=1224.0, center_y=-1922.4, radius=5.0),
        HoleData(hole_id="BC098R163", center_x=1176.0, center_y=-1910.4, radius=5.0),
        HoleData(hole_id="BC102R163", center_x=1224.0, center_y=-1910.4, radius=5.0),
    ])
    
    # sector_1 (右上)
    test_holes.extend([
        HoleData(hole_id="BC098R001", center_x=1176.0, center_y=10.0, radius=5.0),
        HoleData(hole_id="BC102R001", center_x=1224.0, center_y=10.0, radius=5.0),
    ])
    
    # sector_2 (左上)
    test_holes.extend([
        HoleData(hole_id="AC098R001", center_x=-1176.0, center_y=10.0, radius=5.0),
        HoleData(hole_id="AC102R001", center_x=-1224.0, center_y=10.0, radius=5.0),
    ])
    
    # sector_3 (左下)
    test_holes.extend([
        HoleData(hole_id="AC098R164", center_x=-1176.0, center_y=-1922.4, radius=5.0),
        HoleData(hole_id="AC102R164", center_x=-1224.0, center_y=-1922.4, radius=5.0),
    ])
    
    # 创建集合
    holes_dict = {hole.hole_id: hole for hole in test_holes}
    hole_collection = HoleCollection(holes=holes_dict)
    
    print(f"创建了 {len(hole_collection.holes)} 个测试孔位")
    
    # 创建渲染器并生成路径
    renderer = SnakePathRenderer()
    renderer.set_hole_collection(hole_collection)
    detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
    
    print(f"\n生成了 {len(detection_units)} 个检测单元:")
    print("-" * 60)
    
    for i, unit in enumerate(detection_units):
        if unit.is_pair and len(unit.holes) == 2:
            hole_ids = f"{unit.holes[0].hole_id} + {unit.holes[1].hole_id}"
        else:
            hole_ids = unit.holes[0].hole_id
            
        # 判断扇形
        hole = unit.holes[0]
        x, y = hole.center_x, hole.center_y
        if x > 0 and y > 0:
            sector = "sector_1(右上)"
        elif x < 0 and y > 0:
            sector = "sector_2(左上)"
        elif x < 0 and y < 0:
            sector = "sector_3(左下)"
        else:
            sector = "sector_4(右下)"
            
        print(f"{i+1:2d}. {hole_ids:30s} [{sector}]")
    
    # 验证第一个单元
    print("\n" + "=" * 60)
    if detection_units:
        first = detection_units[0]
        if first.is_pair and len(first.holes) == 2:
            print(f"第一个检测单元: {first.holes[0].hole_id} + {first.holes[1].hole_id}")
        else:
            print(f"第一个检测单元: {first.holes[0].hole_id}")
        
        # 检查是否包含期望的孔位
        first_ids = [h.hole_id for h in first.holes]
        if "BC098R164" in first_ids or "BC102R164" in first_ids:
            print("✅ 检测从期望的位置开始!")
        else:
            print("❌ 检测起始位置不正确")


if __name__ == "__main__":
    test_order()