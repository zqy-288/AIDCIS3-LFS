#!/usr/bin/env python3
"""
测试蓝色清除功能
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor

from src.core_business.models.hole_data import HoleData, HoleStatus
from src.core_business.graphics.hole_item import HoleGraphicsItem


def test_color_override():
    """测试颜色覆盖功能"""
    app = QApplication(sys.argv)
    
    # 手动创建测试孔位
    hole = HoleData(
        center_x=0.0,
        center_y=0.0,
        radius=10.0,
        hole_id="TEST001",
        layer="管孔"
    )
    hole.status = HoleStatus.PENDING
    
    # 创建图形项
    item = HoleGraphicsItem(hole)
    
    print("1. 初始状态:")
    print(f"   颜色覆盖: {item._color_override}")
    print(f"   画刷颜色: {item.brush().color().name()}")
    print(f"   孔位状态: {hole.status.value}")
    
    # 设置蓝色覆盖
    blue = QColor(33, 150, 243)
    item.set_color_override(blue)
    
    print("\n2. 设置蓝色后:")
    print(f"   颜色覆盖: {item._color_override.name() if item._color_override else None}")
    print(f"   画刷颜色: {item.brush().color().name()}")
    
    # 验证颜色是否为蓝色
    brush_color = item.brush().color()
    if brush_color.red() == 33 and brush_color.green() == 150 and brush_color.blue() == 243:
        print("   ✅ 颜色正确设置为蓝色")
    else:
        print("   ❌ 颜色设置失败")
    
    # 清除覆盖
    item.clear_color_override()
    
    print("\n3. 清除覆盖后:")
    print(f"   颜色覆盖: {item._color_override}")
    print(f"   画刷颜色: {item.brush().color().name()}")
    
    # 验证颜色是否恢复
    brush_color = item.brush().color()
    if brush_color.red() == 33 and brush_color.green() == 150 and brush_color.blue() == 243:
        print("   ❌ 颜色仍然是蓝色！问题确认")
    else:
        print("   ✅ 颜色已恢复为状态默认色")
    
    # 更新状态为合格
    item.update_status(HoleStatus.QUALIFIED)
    
    print("\n4. 更新为合格状态后:")
    print(f"   颜色覆盖: {item._color_override}")
    print(f"   画刷颜色: {item.brush().color().name()}")
    print(f"   孔位状态: {hole.status.value}")
    
    # 验证是否为绿色（合格色）
    brush_color = item.brush().color()
    expected_green = QColor(50, 200, 50)  # HoleStatus.QUALIFIED 的颜色
    if abs(brush_color.green() - expected_green.green()) < 10:
        print("   ✅ 颜色正确显示为合格状态色（绿色）")
    else:
        print(f"   ❌ 颜色不正确: RGB({brush_color.red()}, {brush_color.green()}, {brush_color.blue()})")
    
    # 测试另一种情况：在有颜色覆盖时更新状态
    print("\n5. 测试：在蓝色覆盖时更新状态")
    item.set_color_override(blue)
    print(f"   设置蓝色覆盖后: {item.brush().color().name()}")
    
    item.update_status(HoleStatus.DEFECTIVE)
    print(f"   更新为异常状态后: {item.brush().color().name()}")
    print(f"   颜色覆盖仍存在: {item._color_override is not None}")
    
    # 应该仍然是蓝色，因为覆盖优先级更高
    brush_color = item.brush().color()
    if brush_color.red() == 33 and brush_color.green() == 150 and brush_color.blue() == 243:
        print("   ✅ 正确：颜色覆盖优先级高于状态颜色")
    else:
        print("   ❌ 错误：状态更新影响了颜色覆盖")
    
    return 0


if __name__ == "__main__":
    test_color_override()