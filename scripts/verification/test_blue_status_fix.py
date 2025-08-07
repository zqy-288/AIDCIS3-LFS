#!/usr/bin/env python3
"""
测试蓝色状态更新修复
验证孔位从蓝色检测状态正确更新为最终颜色
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor

# 导入必要的模块
from src.core_business.models.hole_data import HoleData, HoleStatus, HoleCollection
from src.core_business.graphics.hole_item import HoleGraphicsItem
from src.core_business.graphics.graphics_view import OptimizedGraphicsView


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("蓝色状态更新测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 创建图形视图
        self.graphics_view = OptimizedGraphicsView()
        layout.addWidget(self.graphics_view)
        
        # 创建控制按钮
        self.test_button = QPushButton("开始测试蓝色->最终颜色转换")
        self.test_button.clicked.connect(self.start_test)
        layout.addWidget(self.test_button)
        
        # 状态标签
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)
        
        # 创建测试数据
        self.create_test_data()
        
    def create_test_data(self):
        """创建测试孔位数据"""
        # 创建一些测试孔位
        holes = {}
        for i in range(5):
            for j in range(5):
                hole_id = f"TEST_{i}_{j}"
                hole = HoleData(
                    hole_id=hole_id,
                    center_x=100 + i * 50,
                    center_y=100 + j * 50,
                    radius=15,
                    status=HoleStatus.PENDING
                )
                holes[hole_id] = hole
        
        # 创建孔位集合
        self.hole_collection = HoleCollection(holes)
        
        # 加载到视图
        self.graphics_view.load_holes(self.hole_collection)
        
    def start_test(self):
        """开始测试蓝色状态更新"""
        self.status_label.setText("步骤1: 设置蓝色检测状态...")
        
        # 选择一些孔位进行测试
        test_holes = ["TEST_2_2", "TEST_2_3", "TEST_3_2", "TEST_3_3"]
        
        # 设置为蓝色检测状态
        for hole_id in test_holes:
            self.graphics_view.update_hole_status(
                hole_id, 
                HoleStatus.PENDING,
                color_override=QColor(33, 150, 243)  # 蓝色
            )
        
        self.status_label.setText("步骤2: 蓝色状态已设置，等待3秒...")
        
        # 3秒后更新为最终状态
        QTimer.singleShot(3000, lambda: self.update_to_final_status(test_holes))
        
    def update_to_final_status(self, test_holes):
        """更新为最终状态"""
        self.status_label.setText("步骤3: 清除蓝色，设置最终状态...")
        
        # 模拟检测结果
        for i, hole_id in enumerate(test_holes):
            # 交替设置合格和不合格
            final_status = HoleStatus.QUALIFIED if i % 2 == 0 else HoleStatus.DEFECTIVE
            
            # 清除颜色覆盖并设置最终状态
            self.graphics_view.update_hole_status(
                hole_id,
                final_status,
                color_override=None  # 清除蓝色覆盖
            )
            
            print(f"更新 {hole_id}: {final_status.value}")
        
        self.status_label.setText("步骤4: 测试完成！检查孔位是否正确显示为绿色/红色")
        
        # 验证颜色
        QTimer.singleShot(1000, self.verify_colors)
        
    def verify_colors(self):
        """验证最终颜色"""
        if hasattr(self.graphics_view, 'hole_items'):
            for hole_id, item in self.graphics_view.hole_items.items():
                if "TEST_2_2" in hole_id or "TEST_2_3" in hole_id or "TEST_3_2" in hole_id or "TEST_3_3" in hole_id:
                    color = item.brush().color()
                    status = item.hole_data.status
                    print(f"{hole_id}: 状态={status.value}, 颜色=RGB({color.red()}, {color.green()}, {color.blue()})")


def main():
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()