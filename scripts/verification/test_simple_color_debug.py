#!/usr/bin/env python3
"""
简单测试颜色调试日志
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PySide6.QtCore import QTimer, QPointF
from PySide6.QtGui import QColor
from src.core_business.models.hole_data import HoleData, HoleStatus
from src.core_business.graphics.hole_item import HoleGraphicsItem

def test_color_update():
    """测试颜色更新"""
    app = QApplication(sys.argv)
    
    # 创建场景和视图
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    
    # 创建测试孔位
    hole_data = HoleData(
        hole_id="TEST001",
        center_x=100,
        center_y=100,
        radius=20,
        status=HoleStatus.PENDING
    )
    
    # 创建图形项
    hole_item = HoleGraphicsItem(hole_data)
    scene.addItem(hole_item)
    
    print("\n=== 测试开始 ===")
    print("1. 初始状态：灰色（PENDING）")
    
    # 2秒后设置为蓝色（检测中）
    def set_blue():
        print("\n2. 设置蓝色覆盖（检测中）")
        hole_item.set_color_override(QColor(33, 150, 243))
        
    # 4秒后清除蓝色，显示最终状态
    def clear_blue():
        print("\n3. 清除蓝色覆盖，显示最终状态")
        hole_item.update_status(HoleStatus.QUALIFIED)
        hole_item.clear_color_override()
        
    # 设置定时器
    QTimer.singleShot(2000, set_blue)
    QTimer.singleShot(4000, clear_blue)
    QTimer.singleShot(6000, app.quit)
    
    view.show()
    app.exec()
    
    print("\n=== 测试结束 ===")

if __name__ == '__main__':
    test_color_update()