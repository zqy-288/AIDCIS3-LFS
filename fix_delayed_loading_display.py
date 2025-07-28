#!/usr/bin/env python3
"""
修复延迟加载显示问题
确保组件在数据延迟加载后能正确显示
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import QTimer

from src.core.shared_data_manager import SharedDataManager
from src.core_business.dxf_parser import DXFParser
from src.core_business.hole_numbering_service import HoleNumberingService
from src.core_business.graphics.dynamic_sector_display_refactored import DynamicSectorDisplayRefactored
from src.core_business.graphics.dynamic_sector_view import SectorQuadrant


class DelayedLoadingFixWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("修复延迟加载显示问题")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化SharedDataManager
        self.shared_data_manager = SharedDataManager()
        
        # 设置UI
        self._setup_ui()
        
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 状态标签
        self.status_label = QLabel("准备测试...")
        layout.addWidget(self.status_label)
        
        # 按钮
        btn_layout = QVBoxLayout()
        
        # 修复后的测试
        btn1 = QPushButton("测试修复: 延迟加载并自动切换扇形")
        btn1.clicked.connect(self.test_fixed_delayed_loading)
        btn_layout.addWidget(btn1)
        
        # 原始测试（展示问题）
        btn2 = QPushButton("原始测试: 延迟加载但不切换扇形")
        btn2.clicked.connect(self.test_original_delayed_loading)
        btn_layout.addWidget(btn2)
        
        layout.addLayout(btn_layout)
        
        # 组件容器
        self.component_container = QWidget()
        self.component_container.setMinimumHeight(600)
        layout.addWidget(self.component_container)
        
        self.sector_display = None
        
    def test_fixed_delayed_loading(self):
        """测试修复后的延迟加载"""
        self.status_label.setText("测试修复: 延迟加载并自动切换扇形...")
        
        # 清理
        self._cleanup()
        
        # 创建组件（无数据）
        layout = QVBoxLayout(self.component_container)
        self.sector_display = DynamicSectorDisplayRefactored(self.shared_data_manager)
        layout.addWidget(self.sector_display)
        
        # 延迟加载数据并触发显示
        QTimer.singleShot(1000, self._delayed_load_and_show)
        
    def test_original_delayed_loading(self):
        """测试原始的延迟加载（展示问题）"""
        self.status_label.setText("原始测试: 延迟加载但不切换扇形...")
        
        # 清理
        self._cleanup()
        
        # 创建组件（无数据）
        layout = QVBoxLayout(self.component_container)
        self.sector_display = DynamicSectorDisplayRefactored(self.shared_data_manager)
        layout.addWidget(self.sector_display)
        
        # 仅加载数据，不主动切换扇形
        QTimer.singleShot(1000, self._delayed_load_only)
        
    def _delayed_load_and_show(self):
        """延迟加载数据并确保显示"""
        self.status_label.setText("加载数据...")
        
        # 加载数据
        hole_collection = self._load_test_data()
        self.sector_display.set_hole_collection(hole_collection)
        
        # 检查初始化状态并手动触发扇形切换
        def ensure_display():
            if self.sector_display.is_initialized:
                # 如果当前没有选中扇形，手动切换到扇形1
                if not self.sector_display.current_sector:
                    self.sector_display.switch_to_sector(SectorQuadrant.SECTOR_1)
                    self.status_label.setText("✅ 数据加载完成，已切换到扇形1")
                else:
                    self.status_label.setText(f"✅ 数据加载完成，当前扇形: {self.sector_display.current_sector.value}")
            else:
                self.status_label.setText("❌ 组件未正确初始化")
                
        # 给一点时间让数据处理完成
        QTimer.singleShot(500, ensure_display)
        
    def _delayed_load_only(self):
        """仅延迟加载数据"""
        self.status_label.setText("加载数据（不切换扇形）...")
        
        # 加载数据
        hole_collection = self._load_test_data()
        self.sector_display.set_hole_collection(hole_collection)
        
        # 检查状态
        def check_status():
            if self.sector_display.is_initialized:
                if self.sector_display.current_sector:
                    self.status_label.setText(f"数据已加载，当前扇形: {self.sector_display.current_sector.value}")
                else:
                    self.status_label.setText("⚠️ 数据已加载，但未选择扇形（这就是问题所在）")
            else:
                self.status_label.setText("❌ 组件未正确初始化")
                
        QTimer.singleShot(500, check_status)
        
    def _load_test_data(self):
        """加载测试数据"""
        dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/测试管板.dxf"
        
        parser = DXFParser()
        hole_collection = parser.parse_file(dxf_path)
        
        # 应用编号
        numbering_service = HoleNumberingService()
        numbering_service.apply_numbering(hole_collection)
        
        return hole_collection
        
    def _cleanup(self):
        """清理组件"""
        if self.sector_display:
            self.sector_display.deleteLater()
            self.sector_display = None
            
        # 清理布局
        if self.component_container.layout():
            layout = self.component_container.layout()
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                    
        # 清理数据
        self.shared_data_manager.clear_cache()


def main():
    app = QApplication(sys.argv)
    window = DelayedLoadingFixWindow()
    window.show()
    
    print("延迟加载显示问题修复测试")
    print("======================")
    print("测试修复: 数据延迟加载后会自动切换到扇形1")
    print("原始测试: 数据延迟加载后不切换扇形，展示问题")
    print("")
    print("问题原因: 数据加载后所有孔位都被隐藏，需要切换扇形才能显示")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()