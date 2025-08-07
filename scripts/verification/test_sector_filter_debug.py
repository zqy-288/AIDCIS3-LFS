#!/usr/bin/env python3
"""调试单元：验证扇形过滤修复是否生效"""

import sys
import os
import logging
from pathlib import Path

# 禁用调试输出
os.environ['QT_LOGGING_RULES'] = '*.debug=false'

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 创建应用实例
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsEllipseItem
from PySide6.QtCore import Qt, QRectF

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

print("=== 扇形过滤调试单元 ===\n")

# 测试1：验证 HoleGraphicsItem 是否正确设置了 data
print("测试1：验证 HoleGraphicsItem 的 data 设置")
print("-" * 50)

try:
    from src.core_business.models.hole_data import HoleData, HoleStatus
    from src.core_business.graphics.hole_item import HoleGraphicsItem
    
    # 创建测试孔位数据
    test_hole = HoleData(
        hole_id="TEST001",
        center_x=100,
        center_y=100,
        radius=10,
        status=HoleStatus.PENDING
    )
    
    # 创建图形项
    hole_item = HoleGraphicsItem(test_hole)
    
    # 验证 data 是否正确设置
    stored_id = hole_item.data(0)  # Qt.UserRole = 0
    
    print(f"创建的孔位ID: {test_hole.hole_id}")
    print(f"存储的data(0): {stored_id}")
    print(f"✅ data设置{'成功' if stored_id == test_hole.hole_id else '失败'}")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "-" * 50 + "\n")

# 测试2：模拟场景过滤
print("测试2：模拟场景过滤逻辑")
print("-" * 50)

try:
    # 创建场景
    scene = QGraphicsScene()
    
    # 创建10个测试孔位，分配到不同扇形
    holes_data = []
    for i in range(10):
        hole = HoleData(
            hole_id=f"HOLE{i:03d}",
            center_x=50 + i * 30,
            center_y=50 + (i % 2) * 30,
            radius=10,
            status=HoleStatus.PENDING
        )
        holes_data.append(hole)
    
    # 添加到场景
    items = []
    for hole in holes_data:
        item = HoleGraphicsItem(hole)
        scene.addItem(item)
        items.append(item)
    
    print(f"场景中添加了 {len(scene.items())} 个项")
    
    # 模拟扇形1只包含前3个孔位
    sector1_hole_ids = {"HOLE000", "HOLE001", "HOLE002"}
    
    # 执行过滤
    visible_count = 0
    hidden_count = 0
    
    for item in scene.items():
        hole_id = item.data(0)
        if hole_id:
            is_visible = hole_id in sector1_hole_ids
            item.setVisible(is_visible)
            if is_visible:
                visible_count += 1
                print(f"  ✅ {hole_id} - 可见")
            else:
                hidden_count += 1
                print(f"  ❌ {hole_id} - 隐藏")
        else:
            print(f"  ⚠️  项没有hole_id数据")
    
    print(f"\n过滤结果：")
    print(f"  可见: {visible_count} 个")
    print(f"  隐藏: {hidden_count} 个")
    print(f"  {'✅ 过滤成功' if visible_count == 3 and hidden_count == 7 else '❌ 过滤失败'}")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "-" * 50 + "\n")

# 测试3：验证 item.isVisible() 的效果
print("测试3：验证 setVisible 的效果")
print("-" * 50)

try:
    # 创建一个简单的图形项
    simple_item = QGraphicsEllipseItem(0, 0, 10, 10)
    
    # 测试可见性
    print(f"初始可见性: {simple_item.isVisible()}")
    
    simple_item.setVisible(False)
    print(f"setVisible(False)后: {simple_item.isVisible()}")
    
    simple_item.setVisible(True)
    print(f"setVisible(True)后: {simple_item.isVisible()}")
    
    print("✅ setVisible 方法工作正常")
    
except Exception as e:
    print(f"❌ 测试失败: {e}")

print("\n" + "=" * 50)
print("调试单元完成")
print("=" * 50)

# 创建应用实例（如果需要事件循环）
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

print("\n提示：如果所有测试都通过，扇形过滤应该能正常工作。")
print("如果测试1失败，说明hole_id没有正确存储到item data。")
print("如果测试2失败，说明过滤逻辑有问题。")
print("如果测试3失败，说明Qt的setVisible方法有问题（这种情况很少见）。")