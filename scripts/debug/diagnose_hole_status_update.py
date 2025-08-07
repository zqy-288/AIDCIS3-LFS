#!/usr/bin/env python3
"""
诊断孔位状态更新问题
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor

from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.core_business.graphics.graphics_view import OptimizedGraphicsView
from src.pages.main_detection_p1.components.simulation_controller import SimulationController

class DiagnosticWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("孔位状态更新诊断")
        self.setGeometry(100, 100, 1400, 800)
        
        # 配置日志
        logging.basicConfig(
            level=logging.DEBUG,
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
        
        # 创建控制按钮
        self.start_button = QPushButton("开始诊断测试")
        self.start_button.clicked.connect(self.start_diagnostic)
        layout.addWidget(self.start_button)
        
        # 创建日志显示
        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(200)
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        
        # 创建模拟控制器
        self.simulation_controller = SimulationController()
        
        # 连接信号以监控状态更新
        self.simulation_controller.hole_status_updated.connect(self.on_hole_status_updated)
        
        # 创建测试孔位
        self.create_test_holes()
        
    def log(self, message):
        """添加日志到显示"""
        self.log_display.append(message)
        self.logger.info(message)
        
    def create_test_holes(self):
        """创建测试孔位数据"""
        self.hole_collection = HoleCollection({})
        
        # 创建一个2x2的测试孔位网格
        hole_id = 0
        for row in range(2):
            for col in range(2):
                hole_id += 1
                hole = HoleData(
                    hole_id=f"H{hole_id}",
                    center_x=100 + col * 50,
                    center_y=100 + row * 50,
                    radius=15,
                    status=HoleStatus.PENDING,
                    row=row,
                    column=col
                )
                self.hole_collection.add_hole(hole)
        
        # 加载到视图
        self.graphics_view.load_holes(self.hole_collection)
        self.simulation_controller.load_hole_collection(self.hole_collection)
        self.simulation_controller.set_graphics_view(self.graphics_view)
        
        self.log(f"创建了 {len(self.hole_collection)} 个测试孔位")
        
    def start_diagnostic(self):
        """开始诊断测试"""
        self.log("\n=== 开始诊断测试 ===")
        
        # 测试1: 直接更新状态
        self.log("\n测试1: 直接更新孔位状态")
        self.test_direct_status_update()
        
        # 测试2: 通过simulation_controller更新
        QTimer.singleShot(2000, self.test_simulation_update)
        
        # 测试3: 测试颜色覆盖
        QTimer.singleShot(4000, self.test_color_override)
        
        # 测试4: 监控模拟过程
        QTimer.singleShot(6000, self.test_simulation_process)
        
    def test_direct_status_update(self):
        """测试直接更新状态"""
        hole_id = "H1"
        
        # 检查初始状态
        hole = self.hole_collection.get_hole(hole_id)
        self.log(f"孔位 {hole_id} 初始状态: {hole.status.value}")
        
        # 直接通过graphics_view更新
        self.graphics_view.update_hole_status(hole_id, HoleStatus.QUALIFIED)
        
        # 检查更新后状态
        QTimer.singleShot(100, lambda: self.check_hole_visual_state(hole_id, "QUALIFIED(绿色)"))
        
    def test_simulation_update(self):
        """测试通过simulation_controller更新"""
        self.log("\n测试2: 通过simulation_controller更新状态")
        
        hole_id = "H2"
        
        # 通过simulation_controller更新
        self.simulation_controller._update_hole_status(hole_id, HoleStatus.DEFECTIVE)
        
        # 检查视觉状态
        QTimer.singleShot(100, lambda: self.check_hole_visual_state(hole_id, "DEFECTIVE(红色)"))
        
    def test_color_override(self):
        """测试颜色覆盖功能"""
        self.log("\n测试3: 测试颜色覆盖（蓝色检测中）")
        
        hole_id = "H3"
        blue_color = QColor(33, 150, 243)
        
        # 设置为PENDING状态但使用蓝色覆盖
        self.simulation_controller._update_hole_status(hole_id, HoleStatus.PENDING, color_override=blue_color)
        
        # 检查视觉状态
        QTimer.singleShot(100, lambda: self.check_hole_visual_state(hole_id, "PENDING但显示蓝色"))
        
        # 2秒后清除颜色覆盖，变为合格
        QTimer.singleShot(2000, lambda: self.clear_color_and_set_qualified(hole_id))
        
    def clear_color_and_set_qualified(self, hole_id):
        """清除颜色覆盖并设置为合格"""
        self.log(f"\n清除 {hole_id} 的颜色覆盖，设置为QUALIFIED")
        self.simulation_controller._update_hole_status(hole_id, HoleStatus.QUALIFIED)
        QTimer.singleShot(100, lambda: self.check_hole_visual_state(hole_id, "QUALIFIED(绿色)"))
        
    def test_simulation_process(self):
        """测试模拟过程"""
        self.log("\n测试4: 启动模拟过程，监控状态变化")
        
        # 设置较快的模拟速度用于测试
        self.simulation_controller.pair_detection_time = 3000  # 3秒
        self.simulation_controller.status_change_time = 2500   # 2.5秒
        self.simulation_controller.simulation_timer.setInterval(3000)
        
        # 启动模拟
        self.simulation_controller.start_simulation()
        
    def check_hole_visual_state(self, hole_id, expected_state):
        """检查孔位的视觉状态"""
        if hole_id in self.graphics_view.hole_items:
            hole_item = self.graphics_view.hole_items[hole_id]
            
            # 获取当前颜色
            current_color = hole_item.brush().color()
            color_name = self.get_color_name(current_color)
            
            # 获取数据状态
            data_status = hole_item.hole_data.status.value
            
            # 检查是否有颜色覆盖
            has_override = hole_item._color_override is not None
            
            self.log(f"孔位 {hole_id} 视觉检查:")
            self.log(f"  - 期望状态: {expected_state}")
            self.log(f"  - 数据状态: {data_status}")
            self.log(f"  - 当前颜色: {color_name} (RGB: {current_color.red()}, {current_color.green()}, {current_color.blue()})")
            self.log(f"  - 颜色覆盖: {'是' if has_override else '否'}")
            
            # 验证视图是否更新
            scene = self.graphics_view.scene
            self.log(f"  - 场景项数: {len(scene.items())}")
            
    def get_color_name(self, color):
        """根据颜色获取名称"""
        r, g, b = color.red(), color.green(), color.blue()
        
        # 定义颜色阈值
        if g > 150 and r < 100 and b < 100:
            return "绿色(合格)"
        elif r > 200 and g < 100 and b < 100:
            return "红色(异常)"
        elif b > 150 and r < 100 and g < 200:
            return "蓝色(检测中)"
        elif r > 180 and g > 180 and b > 180:
            return "灰色(待检)"
        else:
            return f"未知颜色({r},{g},{b})"
            
    def on_hole_status_updated(self, hole_id, status):
        """监控状态更新信号"""
        self.log(f"信号: 孔位 {hole_id} 状态更新为 {status.value}")


def main():
    app = QApplication(sys.argv)
    window = DiagnosticWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()