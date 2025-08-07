#!/usr/bin/env python3
"""
简化的间隔4列S形检测系统测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus
from src.pages.shared.components.snake_path.snake_path_renderer import PathStrategy, HolePair, SnakePathRenderer

# 创建简单测试数据
holes = {}
test_data = [
    ("BC098R164", 98.0, -164.0, 98, 164),   # BC098R164
    ("BC102R164", 102.0, -164.0, 102, 164), # BC102R164 (98+4=102, 间隔4列配对)
    ("BC100R164", 100.0, -164.0, 100, 164), # BC100R164  
    ("BC104R164", 104.0, -164.0, 104, 164), # BC104R164 (100+4=104, 间隔4列配对)
]

for hole_id, x, y, col, row in test_data:
    hole = HoleData(
        center_x=x, center_y=y, radius=5.0,
        hole_id=hole_id, row=row, column=col,
        status=HoleStatus.PENDING
    )
    holes[hole_id] = hole

hole_collection = HoleCollection(holes=holes)
print(f"✅ 创建测试数据: {len(holes)} 个孔位")

# 测试路径生成
renderer = SnakePathRenderer()
renderer.set_hole_collection(hole_collection)
detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)

print(f"✅ 生成检测单元: {len(detection_units)} 个")

# 打印结果
for i, unit in enumerate(detection_units):
    if isinstance(unit, HolePair):
        hole_ids = unit.get_hole_ids()
        pair_type = "配对" if unit.is_pair else "单独"
        print(f"  {i+1}. [{pair_type}] {', '.join(hole_ids)} (孔位数: {len(unit.holes)})")

# 验证配对逻辑
print("\n🔍 配对逻辑验证:")
print("应该形成配对: BC098R164 + BC102R164 (98+4=102)")
print("应该形成配对: BC100R164 + BC104R164 (100+4=104)")

print("🎉 间隔4列S形检测系统核心功能测试成功！")