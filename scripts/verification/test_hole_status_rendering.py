#!/usr/bin/env python3
"""
测试孔位状态渲染
验证修复后的状态更新是否正常工作
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor

from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.core_business.graphics.graphics_view import OptimizedGraphicsView


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("孔位状态渲染测试")
        self.setGeometry(100, 100, 800, 600)
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建图形视图
        self.graphics_view = OptimizedGraphicsView()
        layout.addWidget(self.graphics_view)
        
        # 创建控制按钮布局
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # 创建状态测试按钮
        self.test_pending_btn = QPushButton("测试 PENDING (灰色)")
        self.test_pending_btn.clicked.connect(lambda: self.test_status(HoleStatus.PENDING))
        button_layout.addWidget(self.test_pending_btn)
        
        self.test_qualified_btn = QPushButton("测试 QUALIFIED (绿色)")
        self.test_qualified_btn.clicked.connect(lambda: self.test_status(HoleStatus.QUALIFIED))
        button_layout.addWidget(self.test_qualified_btn)
        
        self.test_defective_btn = QPushButton("测试 DEFECTIVE (红色)")
        self.test_defective_btn.clicked.connect(lambda: self.test_status(HoleStatus.DEFECTIVE))
        button_layout.addWidget(self.test_defective_btn)
        
        self.test_blue_btn = QPushButton("测试蓝色覆盖")
        self.test_blue_btn.clicked.connect(self.test_blue_override)
        button_layout.addWidget(self.test_blue_btn)
        
        self.test_sequence_btn = QPushButton("测试检测序列")
        self.test_sequence_btn.clicked.connect(self.test_detection_sequence)
        button_layout.addWidget(self.test_sequence_btn)
        
        # 创建测试孔位
        self.create_test_holes()
        
    def create_test_holes(self):
        """创建测试孔位数据"""
        self.hole_collection = HoleCollection({})
        
        # 创建一排测试孔位
        for i in range(5):
            hole = HoleData(
                hole_id=f"TEST_{i+1}",
                center_x=100 + i * 100,
                center_y=300,
                radius=30,
                status=HoleStatus.PENDING
            )
            self.hole_collection.add_hole(hole)
        
        # 加载到视图
        self.graphics_view.load_holes(self.hole_collection)
        self.logger.info(f"创建了 {len(self.hole_collection)} 个测试孔位")
        
    def test_status(self, status: HoleStatus):
        """测试特定状态"""
        self.logger.info(f"\n测试状态: {status.value}")
        
        # 更新所有孔位到指定状态
        for hole_id in self.hole_collection.holes:
            self.graphics_view.update_hole_status(hole_id, status)
            
        # 验证状态
        QTimer.singleShot(100, lambda: self.verify_status(status))
        
    def test_blue_override(self):
        """测试蓝色覆盖（检测中状态）"""
        self.logger.info("\n测试蓝色覆盖")
        
        blue_color = QColor(33, 150, 243)
        
        # 设置所有孔位为PENDING但显示蓝色
        for hole_id in self.hole_collection.holes:
            self.graphics_view.update_hole_status(hole_id, HoleStatus.PENDING, color_override=blue_color)
            
        self.logger.info("所有孔位应该显示为蓝色（检测中）")
        
    def test_detection_sequence(self):
        """测试检测序列：灰色 -> 蓝色 -> 绿色/红色"""
        self.logger.info("\n测试检测序列")
        
        # 步骤1：初始状态（灰色）
        self.logger.info("步骤1: 设置为PENDING（灰色）")
        for hole_id in self.hole_collection.holes:
            self.graphics_view.update_hole_status(hole_id, HoleStatus.PENDING)
            
        # 步骤2：2秒后变为检测中（蓝色）
        QTimer.singleShot(2000, self.set_detecting)
        
        # 步骤3：5秒后变为最终状态
        QTimer.singleShot(5000, self.set_final_status)
        
    def set_detecting(self):
        """设置为检测中状态（蓝色）"""
        self.logger.info("步骤2: 设置为检测中（蓝色）")
        blue_color = QColor(33, 150, 243)
        
        for hole_id in self.hole_collection.holes:
            self.graphics_view.update_hole_status(hole_id, HoleStatus.PENDING, color_override=blue_color)
            
    def set_final_status(self):
        """设置最终状态"""
        self.logger.info("步骤3: 设置最终状态")
        
        # 模拟不同的检测结果
        import random
        for i, hole_id in enumerate(self.hole_collection.holes):
            if random.random() < 0.7:  # 70%合格
                self.graphics_view.update_hole_status(hole_id, HoleStatus.QUALIFIED)
                self.logger.info(f"{hole_id}: QUALIFIED（绿色）")
            else:
                self.graphics_view.update_hole_status(hole_id, HoleStatus.DEFECTIVE)
                self.logger.info(f"{hole_id}: DEFECTIVE（红色）")
                
    def verify_status(self, expected_status: HoleStatus):
        """验证状态是否正确"""
        for hole_id, hole in self.hole_collection.holes.items():
            if hole.status != expected_status:
                self.logger.error(f"❌ {hole_id} 状态不匹配: 期望 {expected_status.value}, 实际 {hole.status.value}")
            else:
                self.logger.info(f"✅ {hole_id} 状态正确: {hole.status.value}")
                
            # 检查图形项
            if hole_id in self.graphics_view.hole_items:
                item = self.graphics_view.hole_items[hole_id]
                color = item.brush().color()
                self.logger.info(f"   颜色: RGB({color.red()}, {color.green()}, {color.blue()})")


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()