#!/usr/bin/env python3
"""
测试蓝色状态未更新问题
验证停止模拟时是否有孔位保持蓝色
"""

import sys
import os
import logging
import time
from typing import List, Dict

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QHBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt, QObject, Signal
from PySide6.QtGui import QColor

from src.pages.main_detection_p1.services.dxf_loader_service import DXFLoaderService
from src.core_business.models.hole_collection import HoleCollection
from src.core_business.models.hole_data import HoleStatus
from src.pages.main_detection_p1.components.simulation_controller import SimulationController
from src.core_business.graphics.graphics_view import EnhancedGraphicsView
from src.core_business.graphics.snake_path_coordinator import SnakePathCoordinator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.hole_collection = None
        self.simulation_controller = None
        self.graphics_view = None
        self.blue_holes = set()  # 跟踪蓝色状态的孔位
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("蓝色状态更新测试")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 图形视图
        self.graphics_view = EnhancedGraphicsView()
        layout.addWidget(self.graphics_view, 3)
        
        # 控制面板
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        self.btn_load = QPushButton("加载DXF")
        self.btn_load.clicked.connect(self.load_dxf)
        control_layout.addWidget(self.btn_load)
        
        self.btn_start = QPushButton("开始模拟")
        self.btn_start.clicked.connect(self.start_simulation)
        self.btn_start.setEnabled(False)
        control_layout.addWidget(self.btn_start)
        
        self.btn_stop_5s = QPushButton("5秒后停止")
        self.btn_stop_5s.clicked.connect(self.stop_after_5s)
        self.btn_stop_5s.setEnabled(False)
        control_layout.addWidget(self.btn_stop_5s)
        
        self.btn_stop_15s = QPushButton("15秒后停止")
        self.btn_stop_15s.clicked.connect(self.stop_after_15s)
        self.btn_stop_15s.setEnabled(False)
        control_layout.addWidget(self.btn_stop_15s)
        
        self.btn_check = QPushButton("检查蓝色孔位")
        self.btn_check.clicked.connect(self.check_blue_holes)
        self.btn_check.setEnabled(False)
        control_layout.addWidget(self.btn_check)
        
        self.status_label = QLabel("准备就绪")
        control_layout.addWidget(self.status_label)
        
        layout.addWidget(control_panel)
        
        # 日志区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(200)
        layout.addWidget(self.log_area, 1)
        
    def log(self, message):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        logger.info(message)
        
    def load_dxf(self):
        """加载DXF文件"""
        self.log("开始加载DXF文件...")
        
        # 加载DXF
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/Data/Products/CAP1000/dxf/CAP1000.dxf"
        loader_service = DXFLoaderService()
        
        try:
            self.hole_collection = loader_service.load_dxf(dxf_path, "CAP1000")
            self.log(f"成功加载 {len(self.hole_collection.holes)} 个孔位")
            
            # 显示在图形视图中
            self.graphics_view.load_holes(self.hole_collection, "CAP1000")
            
            # 创建模拟控制器
            self.simulation_controller = SimulationController()
            self.simulation_controller.hole_collection = self.hole_collection
            self.simulation_controller.set_graphics_view(self.graphics_view)
            
            # 连接信号来跟踪蓝色孔位
            self.simulation_controller.hole_status_updated.connect(self.on_hole_status_updated)
            
            # 创建蛇形路径
            coordinator = SnakePathCoordinator()
            detection_units = coordinator.create_detection_units(self.hole_collection)
            self.simulation_controller.detection_units = detection_units
            self.log(f"创建了 {len(detection_units)} 个检测单元")
            
            self.btn_start.setEnabled(True)
            self.status_label.setText("DXF已加载")
            
        except Exception as e:
            self.log(f"加载失败: {str(e)}")
            
    def on_hole_status_updated(self, hole_id: str, status: HoleStatus):
        """孔位状态更新时的处理"""
        # 跟踪哪些孔位被设置为蓝色
        if hasattr(self.graphics_view, 'hole_items') and hole_id in self.graphics_view.hole_items:
            item = self.graphics_view.hole_items[hole_id]
            if hasattr(item, '_color_override') and item._color_override:
                # 有颜色覆盖，说明是蓝色
                self.blue_holes.add(hole_id)
                self.log(f"孔位 {hole_id} 设置为蓝色")
            else:
                # 没有颜色覆盖，说明蓝色被清除
                if hole_id in self.blue_holes:
                    self.blue_holes.remove(hole_id)
                    self.log(f"孔位 {hole_id} 蓝色已清除，状态: {status.value}")
                    
    def start_simulation(self):
        """开始模拟"""
        self.log("开始模拟检测...")
        self.blue_holes.clear()
        self.simulation_controller.start_simulation_detection()
        self.btn_start.setEnabled(False)
        self.btn_stop_5s.setEnabled(True)
        self.btn_stop_15s.setEnabled(True)
        self.btn_check.setEnabled(True)
        self.status_label.setText("模拟进行中...")
        
    def stop_after_5s(self):
        """5秒后停止（测试状态变化定时器被中断的情况）"""
        self.log("将在5秒后停止模拟...")
        QTimer.singleShot(5000, self.stop_simulation)
        
    def stop_after_15s(self):
        """15秒后停止（测试多个孔位处于不同状态的情况）"""
        self.log("将在15秒后停止模拟...")
        QTimer.singleShot(15000, self.stop_simulation)
        
    def stop_simulation(self):
        """停止模拟"""
        self.log(f"停止模拟前，有 {len(self.blue_holes)} 个蓝色孔位")
        
        # 检查当前正在检测的孔位
        if self.simulation_controller.current_detecting_pair:
            current_holes = [hole.hole_id for hole in self.simulation_controller.current_detecting_pair.holes]
            self.log(f"当前正在检测的孔位: {current_holes}")
        
        self.simulation_controller.stop_simulation()
        self.status_label.setText("模拟已停止")
        
        # 延迟检查，给UI时间更新
        QTimer.singleShot(100, self.check_blue_holes)
        
    def check_blue_holes(self):
        """检查仍然是蓝色的孔位"""
        self.log("\n=== 检查蓝色孔位 ===")
        
        still_blue = []
        color_override_count = 0
        
        # 检查所有孔位的颜色状态
        if hasattr(self.graphics_view, 'hole_items'):
            for hole_id, item in self.graphics_view.hole_items.items():
                if hasattr(item, '_color_override') and item._color_override:
                    color_override_count += 1
                    color = item._color_override
                    # 检查是否是蓝色 (33, 150, 243)
                    if color.red() == 33 and color.green() == 150 and color.blue() == 243:
                        still_blue.append(hole_id)
                        
        self.log(f"总共有 {color_override_count} 个孔位有颜色覆盖")
        self.log(f"其中 {len(still_blue)} 个孔位仍然是蓝色")
        
        if still_blue:
            self.log("蓝色孔位列表:")
            for i, hole_id in enumerate(still_blue[:10]):  # 只显示前10个
                self.log(f"  {i+1}. {hole_id}")
            if len(still_blue) > 10:
                self.log(f"  ... 还有 {len(still_blue) - 10} 个")
                
        # 检查这些孔位的实际状态
        if still_blue and self.hole_collection:
            self.log("\n检查蓝色孔位的数据状态:")
            for hole_id in still_blue[:5]:  # 检查前5个
                if hole_id in self.hole_collection.holes:
                    hole = self.hole_collection.holes[hole_id]
                    self.log(f"  {hole_id}: 状态={hole.status.value}")
                    
        self.log("=== 检查完成 ===\n")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()