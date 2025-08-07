#!/usr/bin/env python3
"""
调试间隔4列S形检测系统集成问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus
from src.core_business.graphics.snake_path_renderer import SnakePathRenderer, PathStrategy


def debug_hole_positions():
    """调试孔位位置和象限分配"""
    print("🔍 调试孔位位置和象限分配...")
    
    # 创建测试数据 - 确保都在第一象限
    holes = {}
    test_data = [
        ("BC098R164", 98.0, -164.0, 98, 164),   # 第一象限：右上
        ("BC102R164", 102.0, -164.0, 102, 164), # 第一象限：右上
        ("BC100R164", 100.0, -164.0, 100, 164), # 第一象限：右上
        ("BC104R164", 104.0, -164.0, 104, 164), # 第一象限：右上
        ("BC106R164", 106.0, -164.0, 106, 164), # 第一象限：右上
        ("BC110R164", 110.0, -164.0, 110, 164), # 第一象限：右上
    ]
    
    for hole_id, x, y, col, row in test_data:
        hole = HoleData(
            center_x=x, center_y=y, radius=5.0,
            hole_id=hole_id, row=row, column=col,
            status=HoleStatus.PENDING
        )
        holes[hole_id] = hole
    
    hole_collection = HoleCollection(holes=holes)
    
    # 计算中心点
    holes_list = list(hole_collection.holes.values())
    min_x = min(h.center_x for h in holes_list)
    max_x = max(h.center_x for h in holes_list)
    min_y = min(h.center_y for h in holes_list)
    max_y = max(h.center_y for h in holes_list)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    print(f"数据边界: X[{min_x}, {max_x}], Y[{min_y}, {max_y}]")
    print(f"计算中心: ({center_x}, {center_y})")
    print()
    
    # 分析每个孔位的象限
    print("🔍 孔位象限分析:")
    sector_1_count = 0
    for hole in holes_list:
        dx = hole.center_x - center_x
        dy = hole.center_y - center_y
        
        # 判断象限
        if dx >= 0 and dy <= 0:
            quadrant = "第一象限 (右上)"
            sector_1_count += 1
        elif dx < 0 and dy <= 0:
            quadrant = "第二象限 (左上)"
        elif dx < 0 and dy > 0:
            quadrant = "第三象限 (左下)"
        else:
            quadrant = "第四象限 (右下)"
            
        print(f"  {hole.hole_id}: ({hole.center_x}, {hole.center_y}) -> dx={dx:+.1f}, dy={dy:+.1f} -> {quadrant}")
    
    print(f"\n第一象限孔位总数: {sector_1_count}")
    
    # 测试路径生成
    print("\n🧪 测试路径生成:")
    renderer = SnakePathRenderer()
    renderer.set_hole_collection(hole_collection)
    path = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
    
    print(f"生成路径: {path}")
    print(f"路径长度: {len(path)}")
    
    return hole_collection


if __name__ == "__main__":
    debug_hole_positions()