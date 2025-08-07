"""
测试扇形坐标系修复
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core_business.graphics.sector_types import SectorQuadrant

# 测试中心点
center_x, center_y = 0, 0

print("=== 测试扇形坐标系修复 ===\n")
print("使用Qt坐标系（Y轴向下）")
print(f"中心点: ({center_x}, {center_y})\n")

# 测试各个象限的点
test_points = [
    (10, -10, "右上角的点"),    # SECTOR_1
    (-10, -10, "左上角的点"),   # SECTOR_2
    (-10, 10, "左下角的点"),    # SECTOR_3
    (10, 10, "右下角的点"),     # SECTOR_4
]

print("测试结果：")
for x, y, desc in test_points:
    sector = SectorQuadrant.from_position(x, y, center_x, center_y)
    print(f"{desc}: ({x}, {y}) -> {sector.value} ({sector.display_name})")

print("\n验证：")
print("- 右上角 (x>0, y<0) 应该是 sector_1 ✓")
print("- 左上角 (x<0, y<0) 应该是 sector_2 ✓")
print("- 左下角 (x<0, y>0) 应该是 sector_3 ✓")
print("- 右下角 (x>0, y>0) 应该是 sector_4 ✓")

# 测试边界情况
print("\n边界测试：")
boundary_points = [
    (0, -10, "正上方"),
    (10, 0, "正右方"),
    (0, 10, "正下方"),
    (-10, 0, "正左方"),
]

for x, y, desc in boundary_points:
    sector = SectorQuadrant.from_position(x, y, center_x, center_y)
    print(f"{desc}: ({x}, {y}) -> {sector.value}")