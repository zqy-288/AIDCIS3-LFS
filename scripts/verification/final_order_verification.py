#!/usr/bin/env python3
"""
最终验证检测顺序和扇形分配
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
from src.core_business.models.hole_data import HoleData, HoleCollection


def final_verification():
    """最终验证"""
    # 创建完整的测试数据，包含所有四个扇形
    test_holes = []
    
    # sector_1 (右上) - Y > 0, X > 0
    test_holes.extend([
        HoleData(hole_id="BC098R164_S1", center_x=1176.0, center_y=1922.4, radius=5.0),  # 最高行
        HoleData(hole_id="BC102R164_S1", center_x=1224.0, center_y=1922.4, radius=5.0),
        HoleData(hole_id="BC098R001_S1", center_x=1176.0, center_y=10.0, radius=5.0),
        HoleData(hole_id="BC102R001_S1", center_x=1224.0, center_y=10.0, radius=5.0),
    ])
    
    # sector_2 (左上) - Y > 0, X < 0
    test_holes.extend([
        HoleData(hole_id="AC098R164_S2", center_x=-1176.0, center_y=1922.4, radius=5.0),
        HoleData(hole_id="AC102R164_S2", center_x=-1224.0, center_y=1922.4, radius=5.0),
        HoleData(hole_id="AC098R001_S2", center_x=-1176.0, center_y=10.0, radius=5.0),
        HoleData(hole_id="AC102R001_S2", center_x=-1224.0, center_y=10.0, radius=5.0),
    ])
    
    # sector_3 (左下) - Y < 0, X < 0
    test_holes.extend([
        HoleData(hole_id="AC098R164_S3", center_x=-1176.0, center_y=-1922.4, radius=5.0),
        HoleData(hole_id="AC102R164_S3", center_x=-1224.0, center_y=-1922.4, radius=5.0),
        HoleData(hole_id="AC098R001_S3", center_x=-1176.0, center_y=-10.0, radius=5.0),
        HoleData(hole_id="AC102R001_S3", center_x=-1224.0, center_y=-10.0, radius=5.0),
    ])
    
    # sector_4 (右下) - Y < 0, X > 0 (包含x接近0的特殊情况)
    test_holes.extend([
        HoleData(hole_id="BC098R164_S4", center_x=-0.000, center_y=-1922.4, radius=5.0),  # x接近0
        HoleData(hole_id="BC102R164_S4", center_x=48.0, center_y=-1922.4, radius=5.0),
        HoleData(hole_id="BC098R001_S4", center_x=1176.0, center_y=-10.0, radius=5.0),
        HoleData(hole_id="BC102R001_S4", center_x=1224.0, center_y=-10.0, radius=5.0),
    ])
    
    # 创建集合
    holes_dict = {hole.hole_id: hole for hole in test_holes}
    hole_collection = HoleCollection(holes=holes_dict)
    
    print("=" * 80)
    print("最终验证：检测顺序和扇形分配")
    print("=" * 80)
    print(f"\n创建了 {len(hole_collection.holes)} 个测试孔位")
    
    # 创建渲染器并生成路径
    renderer = SnakePathRenderer()
    renderer.set_hole_collection(hole_collection)
    
    # 显示扇形分组
    print("\n扇形分组情况：")
    print("-" * 60)
    holes = list(hole_collection.holes.values())
    sector_groups = renderer._group_holes_by_sector_v2(holes)
    
    for sector_name in ['sector_1', 'sector_2', 'sector_3', 'sector_4']:
        sector_holes = sector_groups[sector_name]
        print(f"\n{sector_name}: {len(sector_holes)} 个孔位")
        for hole in sector_holes:
            print(f"  - {hole.hole_id}: ({hole.center_x:7.1f}, {hole.center_y:7.1f})")
    
    # 生成检测路径
    print("\n" + "=" * 60)
    print("生成检测路径...")
    detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
    
    print(f"\n生成了 {len(detection_units)} 个检测单元：")
    print("-" * 60)
    
    # 显示所有检测单元
    current_sector = None
    for i, unit in enumerate(detection_units):
        if unit.is_pair and len(unit.holes) == 2:
            hole_ids = f"{unit.holes[0].hole_id} + {unit.holes[1].hole_id}"
        else:
            hole_ids = unit.holes[0].hole_id
            
        # 判断扇形
        hole = unit.holes[0]
        x, y = hole.center_x, hole.center_y
        
        # 根据hole_id后缀判断扇形
        if "_S1" in hole.hole_id:
            sector = "sector_1(右上)"
        elif "_S2" in hole.hole_id:
            sector = "sector_2(左上)"
        elif "_S3" in hole.hole_id:
            sector = "sector_3(左下)"
        elif "_S4" in hole.hole_id:
            sector = "sector_4(右下)"
        else:
            sector = "unknown"
            
        # 标记扇形变化
        if sector != current_sector:
            if current_sector is not None:
                print()  # 空行分隔
            current_sector = sector
            print(f"[{sector}]")
            
        print(f"  {i+1:2d}. {hole_ids}")
    
    # 验证结果
    print("\n" + "=" * 60)
    print("验证结果：")
    print("-" * 60)
    
    if detection_units:
        first = detection_units[0]
        first_id = first.holes[0].hole_id
        
        # 检查第一个是否来自sector_1的R164
        if "_S1" in first_id and "R164" in first_id:
            print("✅ 检测从右上角(sector_1)的R164开始")
        else:
            print(f"❌ 检测起始位置: {first_id}")
        
        # 检查扇形顺序
        sector_order = []
        current = None
        for unit in detection_units:
            hole_id = unit.holes[0].hole_id
            if "_S1" in hole_id:
                s = "sector_1"
            elif "_S2" in hole_id:
                s = "sector_2"
            elif "_S3" in hole_id:
                s = "sector_3"
            elif "_S4" in hole_id:
                s = "sector_4"
            else:
                s = "unknown"
                
            if s != current:
                current = s
                sector_order.append(s)
        
        expected = ["sector_1", "sector_2", "sector_3", "sector_4"]
        if sector_order == expected:
            print("✅ 扇形顺序正确: " + " → ".join(sector_order))
        else:
            print("❌ 扇形顺序错误:")
            print("   期望: " + " → ".join(expected))
            print("   实际: " + " → ".join(sector_order))
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    final_verification()