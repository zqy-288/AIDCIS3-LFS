#!/usr/bin/env python3
"""
调试检测顺序问题
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
from src.core_business.models.hole_data import HoleData, HoleCollection


def debug_order():
    """调试检测顺序"""
    # 创建测试孔位 - 确保 sector_4 有 BC098R164 和 BC102R164
    test_holes = []
    
    # sector_4 (右下) - 这些应该最先被处理
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
    
    # 创建集合
    holes_dict = {hole.hole_id: hole for hole in test_holes}
    hole_collection = HoleCollection(holes=holes_dict)
    
    print(f"创建了 {len(hole_collection.holes)} 个测试孔位\n")
    
    # 先分组看看
    print("孔位分组情况：")
    for hole in test_holes:
        x, y = hole.center_x, hole.center_y
        if x > 0 and y > 0:
            sector = "sector_1(右上)"
        elif x < 0 and y > 0:
            sector = "sector_2(左上)"
        elif x < 0 and y < 0:
            sector = "sector_3(左下)"
        else:
            sector = "sector_4(右下)"
        print(f"  {hole.hole_id}: ({x:.1f}, {y:.1f}) -> {sector}")
    
    # 创建渲染器
    renderer = SnakePathRenderer()
    
    # 手动调用内部方法看看分组情况
    renderer.set_hole_collection(hole_collection)
    holes = list(hole_collection.holes.values())
    
    # 测试分组方法
    sector_groups = renderer._group_holes_by_sector_v2(holes)
    
    print("\n扇形分组结果：")
    for sector_name, sector_holes in sector_groups.items():
        print(f"  {sector_name}: {len(sector_holes)} 个孔位")
        for hole in sector_holes[:2]:  # 只显示前2个
            print(f"    - {hole.hole_id}")
    
    # 现在测试路径生成
    print("\n" + "=" * 60)
    print("生成检测路径...")
    
    # 直接调用内部方法以便调试
    detection_units = renderer._generate_interval_four_path()
    
    print(f"\n生成了 {len(detection_units)} 个检测单元：")
    print("-" * 60)
    
    for i, unit in enumerate(detection_units):
        if unit.is_pair and len(unit.holes) == 2:
            hole_ids = f"{unit.holes[0].hole_id} + {unit.holes[1].hole_id}"
        else:
            hole_ids = unit.holes[0].hole_id
        print(f"{i+1:2d}. {hole_ids}")
    
    # 验证
    print("\n" + "=" * 60)
    if detection_units:
        first = detection_units[0]
        first_id = first.holes[0].hole_id
        print(f"第一个检测单元: {first_id}")
        
        if "BC098R164" in first_id or "BC102R164" in first_id:
            print("✅ 检测从正确的位置开始!")
        else:
            print("❌ 检测起始位置不正确")
            print(f"   期望: BC098R164 或 BC102R164")
            print(f"   实际: {first_id}")


if __name__ == "__main__":
    debug_order()