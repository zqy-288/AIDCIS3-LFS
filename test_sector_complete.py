#!/usr/bin/env python3
"""
扇形区域完整显示测试
验证扇形图显示问题是否已解决
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from aidcis2.graphics.sector_view import SectorOverviewWidget
from aidcis2.graphics.sector_manager import SectorManager, SectorQuadrant
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


class SectorCompleteTestWindow(QMainWindow):
    """扇形完整显示测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("扇形区域完整显示测试")
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.current_progress = 0
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """设置界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("扇形区域完整显示测试")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        main_layout.addWidget(title_label)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始进度模拟")
        self.start_btn.clicked.connect(self.start_simulation)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止模拟")
        self.stop_btn.clicked.connect(self.stop_simulation)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.resize_btn = QPushButton("测试窗口缩放")
        self.resize_btn.clicked.connect(self.test_resize)
        control_layout.addWidget(self.resize_btn)
        
        main_layout.addLayout(control_layout)
        
        # 扇形区域显示
        display_layout = QHBoxLayout()
        
        # 左侧：扇形概览 - 给予充足空间
        left_panel = QWidget()
        left_panel.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        
        panel_title = QLabel("扇形进度概览")
        panel_title.setAlignment(Qt.AlignCenter)
        panel_title.setFont(QFont("Arial", 12, QFont.Bold))
        left_layout.addWidget(panel_title)
        
        self.sector_overview = SectorOverviewWidget()
        self.sector_overview.setMinimumSize(350, 350)  # 确保有足够空间
        left_layout.addWidget(self.sector_overview)
        
        # 右侧：测试信息
        right_panel = QWidget()
        right_panel.setStyleSheet("""
            QWidget {
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        right_layout = QVBoxLayout(right_panel)
        
        info_title = QLabel("测试信息")
        info_title.setAlignment(Qt.AlignCenter)
        info_title.setFont(QFont("Arial", 12, QFont.Bold))
        right_layout.addWidget(info_title)
        
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignTop)
        right_layout.addWidget(self.info_label)
        right_layout.addStretch()
        
        display_layout.addWidget(left_panel, 1)
        display_layout.addWidget(right_panel, 1)
        
        main_layout.addLayout(display_layout)
        
        # 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("padding: 5px; background-color: #e3f2fd;")
        main_layout.addWidget(self.status_label)
        
        # 设置窗口大小
        self.resize(900, 600)
        self.center_window()
    
    def center_window(self):
        """居中窗口"""
        screen = QApplication.primaryScreen()
        if screen:
            screen_rect = screen.availableGeometry()
            window_rect = self.frameGeometry()
            window_rect.moveCenter(screen_rect.center())
            self.move(window_rect.topLeft())
    
    def load_data(self):
        """加载测试数据"""
        # 创建均匀分布的孔位
        holes = {}
        hole_id = 1
        
        # 生成圆形分布的孔位
        import math
        for r in range(5, 50, 5):  # 半径
            angle_step = 360 / (r * 2)  # 根据半径调整角度步长
            for angle in range(0, 360, int(angle_step)):
                x = r * math.cos(math.radians(angle))
                y = r * math.sin(math.radians(angle))
                holes[f"H{hole_id:05d}"] = HoleData(
                    hole_id=f"H{hole_id:05d}",
                    center_x=x,
                    center_y=y,
                    radius=1.0,
                    status=HoleStatus.PENDING
                )
                hole_id += 1
        
        hole_collection = HoleCollection(holes=holes)
        
        # 创建并设置扇形管理器
        self.sector_manager = SectorManager()
        self.sector_manager.load_hole_collection(hole_collection)
        
        # 设置到显示组件
        self.sector_overview.set_sector_manager(self.sector_manager)
        
        # 更新信息
        self.update_info()
    
    def update_info(self):
        """更新测试信息"""
        info_lines = [
            "测试目标：",
            "✓ 扇形图完整显示，不被截断",
            "✓ 文本标签清晰可见",
            "✓ 进度动态更新正常",
            "✓ 窗口缩放时自动适应",
            "",
            "扇形分布：",
        ]
        
        for sector in SectorQuadrant:
            holes = self.sector_manager.get_sector_holes(sector)
            info_lines.append(f"{sector.value}: {len(holes)} 个孔位")
        
        info_lines.append("")
        info_lines.append(f"当前进度: {self.current_progress}%")
        
        self.info_label.setText("\n".join(info_lines))
    
    def start_simulation(self):
        """开始进度模拟"""
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.current_progress = 0
        self.progress_timer.start(100)  # 每100ms更新一次
        self.status_label.setText("正在模拟进度更新...")
    
    def stop_simulation(self):
        """停止模拟"""
        self.progress_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("模拟已停止")
    
    def update_progress(self):
        """更新进度"""
        self.current_progress += 1
        if self.current_progress > 100:
            self.current_progress = 0
        
        # 为每个扇形更新不同的进度
        for i, sector in enumerate(SectorQuadrant):
            holes = self.sector_manager.get_sector_holes(sector)
            
            # 计算该扇形的进度
            sector_progress = (self.current_progress + i * 20) % 100
            completed_count = int(len(holes) * sector_progress / 100)
            
            # 更新孔位状态
            for j, hole in enumerate(holes):
                if j < completed_count:
                    if j < completed_count * 0.9:  # 90%合格
                        self.sector_manager.update_hole_status(hole.hole_id, HoleStatus.QUALIFIED)
                    else:
                        self.sector_manager.update_hole_status(hole.hole_id, HoleStatus.DEFECTIVE)
                else:
                    self.sector_manager.update_hole_status(hole.hole_id, HoleStatus.PENDING)
        
        self.update_info()
    
    def test_resize(self):
        """测试窗口缩放"""
        # 改变窗口大小
        current_size = self.size()
        if current_size.width() > 700:
            self.resize(700, 500)
        else:
            self.resize(1000, 700)
        
        self.status_label.setText(f"窗口大小已调整为: {self.size()}")
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self.status_label.setText(f"窗口大小: {event.size()}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = SectorCompleteTestWindow()
    window.show()
    
    print("\n=== 扇形区域完整显示测试 ===")
    print("功能测试：")
    print("1. 点击'开始进度模拟'查看动态更新")
    print("2. 点击'测试窗口缩放'验证自适应")
    print("3. 观察扇形是否完整显示")
    print("4. 检查文本标签是否清晰可见")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()