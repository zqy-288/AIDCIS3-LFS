#!/usr/bin/env python3
"""测试扇形中心对齐的修复方案"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import QPointF, QTimer
from aidcis2.graphics.graphics_view import OptimizedGraphicsView
from aidcis2.models.hole_data import HoleData, HoleCollection

def main():
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("centerOn 测试")
    window.setGeometry(100, 100, 800, 600)
    
    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)
    
    # 创建图形视图
    view = OptimizedGraphicsView()
    layout.addWidget(view)
    
    # 创建测试数据
    holes = {}
    # 在 (1000, 1000) 附近创建一些孔位
    for i in range(10):
        for j in range(10):
            hole_id = f"H{i}_{j}"
            hole = HoleData(
                hole_id=hole_id,
                center_x=1000 + i * 20,
                center_y=1000 + j * 20,
                diameter=10
            )
            holes[hole_id] = hole
    
    collection = HoleCollection(holes=holes)
    view.load_holes(collection)
    
    # 测试按钮
    def test_center():
        target = QPointF(1100, 1100)
        print(f"\n测试 centerOn({target.x()}, {target.y()})")
        
        # 重置变换
        view.resetTransform()
        view.scale(0.5, 0.5)
        
        # 第一次 centerOn
        view.centerOn(target)
        
        # 检查结果
        view_center = view.viewport().rect().center()
        scene_center = view.mapToScene(view_center)
        print(f"第一次调用后: 视图中心 -> 场景({scene_center.x():.1f}, {scene_center.y():.1f})")
        
        # 强制刷新
        view.viewport().update()
        app.processEvents()
        
        # 第二次 centerOn
        view.centerOn(target)
        scene_center2 = view.mapToScene(view_center)
        print(f"第二次调用后: 视图中心 -> 场景({scene_center2.x():.1f}, {scene_center2.y():.1f})")
        
        # 手动设置滚动条
        if hasattr(view, 'horizontalScrollBar') and hasattr(view, 'verticalScrollBar'):
            # 计算需要的滚动位置
            transform = view.transform()
            scaled_target = transform.map(target)
            
            h_offset = int(scaled_target.x() - view.viewport().width() / 2)
            v_offset = int(scaled_target.y() - view.viewport().height() / 2)
            
            view.horizontalScrollBar().setValue(h_offset)
            view.verticalScrollBar().setValue(v_offset)
            
            scene_center3 = view.mapToScene(view_center)
            print(f"手动滚动后: 视图中心 -> 场景({scene_center3.x():.1f}, {scene_center3.y():.1f})")
    
    btn = QPushButton("测试 centerOn")
    btn.clicked.connect(test_center)
    layout.addWidget(btn)
    
    window.show()
    
    # 延迟测试
    QTimer.singleShot(500, test_center)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()