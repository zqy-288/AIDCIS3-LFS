#!/usr/bin/env python3
"""
测试包含右上角R164行的情况
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
from src.core_business.models.hole_data import HoleData, HoleCollection


def test_with_r164():
    """测试包含右上角R164的情况"""
    test_holes = []
    
    # sector_1 (右上) - 包含R164和R001
    test_holes.extend([
        HoleData(hole_id="BC098R164", center_x=1176.0, center_y=1922.4, radius=5.0),  # 右上角的R164
        HoleData(hole_id="BC102R164", center_x=1224.0, center_y=1922.4, radius=5.0),
        HoleData(hole_id="BC098R001", center_x=1176.0, center_y=10.0, radius=5.0),
        HoleData(hole_id="BC102R001", center_x=1224.0, center_y=10.0, radius=5.0),
    ])
    
    # sector_2 (左上)
    test_holes.extend([
        HoleData(hole_id="AC098R164", center_x=-1176.0, center_y=1922.4, radius=5.0),
        HoleData(hole_id="AC102R164", center_x=-1224.0, center_y=1922.4, radius=5.0),
        HoleData(hole_id="AC098R001", center_x=-1176.0, center_y=10.0, radius=5.0),
        HoleData(hole_id="AC102R001", center_x=-1224.0, center_y=10.0, radius=5.0),
    ])
    
    # sector_3 (左下)
    test_holes.extend([
        HoleData(hole_id="AC098R164", center_x=-1176.0, center_y=-1922.4, radius=5.0),
        HoleData(hole_id="AC102R164", center_x=-1224.0, center_y=-1922.4, radius=5.0),
    ])
    
    # sector_4 (右下) - 注意这里BC098R164的x坐标设为接近0
    test_holes.extend([
        HoleData(hole_id="BC098R164", center_x=-0.000, center_y=-2111.200, radius=5.0),  # 实际坐标
        HoleData(hole_id="BC102R164", center_x=48.0, center_y=-2111.200, radius=5.0),
    ])
    
    # 创建集合
    holes_dict = {hole.hole_id: hole for hole in test_holes}
    hole_collection = HoleCollection(holes=holes_dict)
    
    print(f"创建了 {len(hole_collection.holes)} 个测试孔位\n")
    
    # 显示孔位分布
    print("孔位分布：")
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
        print(f"  {hole.hole_id}: ({x:.3f}, {y:.1f}) -> {sector}")
    
    # 创建渲染器并生成路径
    print("\n" + "=" * 60)
    renderer = SnakePathRenderer()
    renderer.set_hole_collection(hole_collection)
    detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
    
    print(f"\n生成了 {len(detection_units)} 个检测单元:")
    print("-" * 60)
    
    # 显示前15个
    for i, unit in enumerate(detection_units[:15]):
        if unit.is_pair and len(unit.holes) == 2:
            hole_ids = f"{unit.holes[0].hole_id} + {unit.holes[1].hole_id}"
        else:
            hole_ids = unit.holes[0].hole_id
            
        # 判断扇形
        hole = unit.holes[0]
        x, y = hole.center_x, hole.center_y
        
        # 对于x接近0的特殊处理
        if abs(x) < 1.0 and hole.hole_id.startswith('B'):
            sector = "sector_4(右下)"
        elif x > 0 and y > 0:
            sector = "sector_1(右上)"
        elif x < 0 and y > 0:
            sector = "sector_2(左上)"
        elif x < 0 and y < 0:
            sector = "sector_3(左下)"
        else:
            sector = "sector_4(右下)"
            
        print(f"{i+1:2d}. {hole_ids:30s} [{sector}]")
    
    # 验证
    print("\n" + "=" * 60)
    if detection_units:
        first = detection_units[0]
        first_id = first.holes[0].hole_id
        print(f"第一个检测单元: {first_id}")
        
        # 检查是否从右上角的R164开始
        if first_id in ["BC098R164", "BC102R164"] and first.holes[0].center_y > 0:
            print("✅ 检测从右上角的R164开始!")
        else:
            print("❌ 检测起始位置不正确")
            print(f"   期望: 右上角的BC098R164或BC102R164")
            print(f"   实际: {first_id} at ({first.holes[0].center_x}, {first.holes[0].center_y})")


if __name__ == "__main__":
    test_with_r164()