"""
诊断坐标系使用情况
分析左边全景图和中间扇形显示不一致的原因
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QPointF
import math

# 导入相关类
from src.core_business.graphics.sector_types import SectorQuadrant
from src.pages.main_detection_p1.components.sector_assignment_manager import SectorAssignmentManager

def analyze_coordinate_systems():
    """分析坐标系使用情况"""
    
    print("=" * 80)
    print("坐标系分析报告")
    print("=" * 80)
    
    # 1. 分析扇形定义
    print("\n1. 扇形定义（SectorQuadrant）:")
    print("-" * 40)
    for sector in SectorQuadrant:
        print(f"  {sector.value}: {sector.display_name}")
        print(f"    角度范围: {sector.angle_range}")
    
    # 2. 分析扇形分配逻辑
    print("\n2. 扇形分配逻辑（SectorAssignmentManager）:")
    print("-" * 40)
    manager = SectorAssignmentManager()
    
    # 查看象限定义
    print("  数学坐标系下的象限定义（Y轴向上）:")
    for sector, definition in manager.quadrant_definitions.items():
        print(f"    {sector.value}: {definition}")
    
    # 3. 测试关键函数
    print("\n3. 测试坐标系转换:")
    print("-" * 40)
    
    # 测试from_angle函数
    test_angles = [45, 135, 225, 315]
    print("  from_angle函数测试:")
    for angle in test_angles:
        sector = SectorQuadrant.from_angle(angle)
        print(f"    角度 {angle}° -> {sector.value}")
    
    # 测试from_position函数
    print("\n  from_position函数测试（中心点在原点）:")
    test_positions = [
        (1, 1, "右上"),
        (-1, 1, "左上"),
        (-1, -1, "左下"),
        (1, -1, "右下")
    ]
    for x, y, desc in test_positions:
        sector = SectorQuadrant.from_position(x, y, 0, 0)
        print(f"    位置 ({x}, {y}) [{desc}] -> {sector.value}")
    
    # 4. 分析问题
    print("\n4. 问题分析:")
    print("-" * 40)
    print("  发现的问题:")
    print("    1. from_position函数使用Qt坐标系（Y轴向下）:")
    print("       - y < center_y 表示在上方（Qt坐标系）")
    print("       - 但数学坐标系中 y > center_y 才表示在上方")
    print("    2. SectorAssignmentManager使用数学坐标系（Y轴向上）:")
    print("       - dy >= 0 表示在上方（数学坐标系）")
    print("    3. 两者坐标系不一致导致扇形分配混乱")
    
    # 5. 验证问题
    print("\n5. 问题验证:")
    print("-" * 40)
    
    # 模拟一个右上角的点
    test_x, test_y = 100, 100
    center_x, center_y = 0, 0
    
    # 使用from_position（Qt坐标系）
    qt_sector = SectorQuadrant.from_position(test_x, test_y, center_x, center_y)
    
    # 使用数学坐标系逻辑
    dx = test_x - center_x
    dy = test_y - center_y
    if dx >= 0 and dy >= 0:
        math_sector = SectorQuadrant.SECTOR_1  # 右上
    elif dx < 0 and dy >= 0:
        math_sector = SectorQuadrant.SECTOR_2  # 左上
    elif dx < 0 and dy < 0:
        math_sector = SectorQuadrant.SECTOR_3  # 左下
    else:
        math_sector = SectorQuadrant.SECTOR_4  # 右下
    
    print(f"  对于点 ({test_x}, {test_y})，中心在 ({center_x}, {center_y}):")
    print(f"    Qt坐标系判断: {qt_sector.value} ({qt_sector.display_name})")
    print(f"    数学坐标系判断: {math_sector.value} ({math_sector.display_name})")
    
    if qt_sector != math_sector:
        print("    ❌ 坐标系不一致！")
    
    # 6. 解决方案
    print("\n6. 解决方案:")
    print("-" * 40)
    print("  需要统一坐标系使用:")
    print("    1. 修改 SectorQuadrant.from_position 使用数学坐标系")
    print("    2. 或者修改 SectorAssignmentManager 使用Qt坐标系")
    print("    3. 建议使用数学坐标系，因为DXF文件通常使用数学坐标系")
    
    # 7. 检查扇形高亮项
    print("\n7. 扇形高亮项分析:")
    print("-" * 40)
    print("  SectorHighlightItem使用的角度映射:")
    print("    SECTOR_1: (0, 90)    - 右上")
    print("    SECTOR_2: (90, 180)  - 左上")
    print("    SECTOR_3: (180, 270) - 左下")
    print("    SECTOR_4: (270, 360) - 右下")
    print("  这个映射符合数学坐标系（0°在右，逆时针增加）")
    
    # 8. 全景图点击检测
    print("\n8. 全景图点击检测分析:")
    print("-" * 40)
    print("  CompletePanoramaWidget._detect_sector_at_position:")
    print("    使用 math.atan2(-dy, dx) 计算角度")
    print("    注意：-dy 表示Y轴反向，这是为了适配Qt坐标系")
    print("    然后调用 SectorQuadrant.from_angle(angle_deg)")
    
    return True

def propose_fix():
    """提出修复方案"""
    print("\n" + "=" * 80)
    print("修复方案")
    print("=" * 80)
    
    print("\n方案：修改 SectorQuadrant.from_position 使用数学坐标系")
    print("-" * 40)
    print("""
修改 src/core_business/graphics/sector_types.py 中的 from_position 方法:

@classmethod
def from_position(cls, x: float, y: float, center_x: float, center_y: float) -> 'SectorQuadrant':
    \"\"\"根据位置相对于中心点确定扇形象限（数学坐标系）\"\"\"
    # 使用数学坐标系：Y轴向上
    if x >= center_x and y >= center_y:
        return cls.SECTOR_1  # 右上
    elif x < center_x and y >= center_y:
        return cls.SECTOR_2  # 左上
    elif x < center_x and y < center_y:
        return cls.SECTOR_3  # 左下
    else:  # x >= center_x and y < center_y
        return cls.SECTOR_4  # 右下
""")
    
    print("\n这样修改后:")
    print("  1. SectorQuadrant.from_position 和 SectorAssignmentManager 使用相同的坐标系")
    print("  2. 左边全景图和中间扇形显示将保持一致")
    print("  3. 扇形分配将正确对应到数学坐标系的四个象限")

if __name__ == "__main__":
    analyze_coordinate_systems()
    propose_fix()