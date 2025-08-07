#!/usr/bin/env python3
"""
调试扇形分组问题
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
from src.core_business.models.hole_data import HoleData, HoleCollection


def debug_grouping():
    """调试扇形分组"""
    test_holes = []
    
    # 注意：这里使用重复的hole_id但不同的坐标
    # sector_1 (右上) - 包含R164和R001
    test_holes.extend([
        HoleData(hole_id="BC098R164_S1", center_x=1176.0, center_y=1922.4, radius=5.0),  # 右上角的R164
        HoleData(hole_id="BC102R164_S1", center_x=1224.0, center_y=1922.4, radius=5.0),
        HoleData(hole_id="BC098R001_S1", center_x=1176.0, center_y=10.0, radius=5.0),
        HoleData(hole_id="BC102R001_S1", center_x=1224.0, center_y=10.0, radius=5.0),
    ])
    
    # sector_4 (右下) - 也有BC098R164但坐标不同
    test_holes.extend([
        HoleData(hole_id="BC098R164_S4", center_x=-0.000, center_y=-2111.200, radius=5.0),  # 实际坐标
        HoleData(hole_id="BC102R164_S4", center_x=48.0, center_y=-2111.200, radius=5.0),
    ])
    
    # 创建集合
    holes_dict = {hole.hole_id: hole for hole in test_holes}
    hole_collection = HoleCollection(holes=holes_dict)
    
    print(f"创建了 {len(hole_collection.holes)} 个测试孔位\n")
    
    # 创建渲染器
    renderer = SnakePathRenderer()
    renderer.set_hole_collection(hole_collection)
    
    # 获取分组
    holes = list(hole_collection.holes.values())
    sector_groups = renderer._group_holes_by_sector_v2(holes)
    
    print("扇形分组结果：")
    for sector_name in ['sector_1', 'sector_2', 'sector_3', 'sector_4']:
        sector_holes = sector_groups.get(sector_name, [])
        print(f"\n{sector_name}：{len(sector_holes)} 个孔位")
        for hole in sector_holes:
            print(f"  - {hole.hole_id}: ({hole.center_x:.3f}, {hole.center_y:.1f})")
    
    # 现在测试路径生成
    print("\n" + "=" * 60)
    print("生成检测路径...")
    
    # 直接调用内部方法
    detection_units = renderer._generate_interval_four_path()
    
    print(f"\n生成了 {len(detection_units)} 个检测单元：")
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
        
        if "R164_S1" in first_id:
            print("✅ 检测从右上角的R164开始!")
        else:
            print("❌ 检测起始位置不正确")


if __name__ == "__main__":
    debug_grouping()