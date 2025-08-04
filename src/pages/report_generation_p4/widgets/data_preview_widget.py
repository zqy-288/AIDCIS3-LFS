"""
数据预览小部件
提供报告数据的可视化预览功能
"""

from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QProgressBar, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

# 从assets/old目录导入报告数据模型
from assets.old.report_models import ReportData


class DataPreviewWidget(QWidget):
    """数据预览小部件 - 仪表盘风格"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 创建仪表盘样式的数据显示
        dashboard_widget = QWidget()
        dashboard_layout = QGridLayout(dashboard_widget)
        dashboard_layout.setSpacing(15)
        
        # 工件信息（保持简洁）
        self.workpiece_id_label = QLabel("工件ID: --")
        self.workpiece_type_label = QLabel("类型: --")
        dashboard_layout.addWidget(self.workpiece_id_label, 0, 0, 1, 2)
        dashboard_layout.addWidget(self.workpiece_type_label, 1, 0, 1, 2)
        
        # 关键指标 (大号数字)
        self.total_holes_label = QLabel("0")
        self.qualified_holes_label = QLabel("0")
        self.unqualified_holes_label = QLabel("0")
        
        # 设置样式
        self.total_holes_label.setObjectName("DashboardNumber")
        self.qualified_holes_label.setObjectName("DashboardNumber")
        self.unqualified_holes_label.setObjectName("DashboardNumber")
        
        # 设置颜色
        self.qualified_holes_label.setStyleSheet("color: #2ECC71;")  # 合格用绿色
        self.unqualified_holes_label.setStyleSheet("color: #E74C3C;")  # 不合格用红色
        
        dashboard_layout.addWidget(QLabel("总检测孔数"), 2, 0)
        dashboard_layout.addWidget(self.total_holes_label, 3, 0)
        dashboard_layout.addWidget(QLabel("合格孔数"), 2, 1)
        dashboard_layout.addWidget(self.qualified_holes_label, 3, 1)
        dashboard_layout.addWidget(QLabel("不合格孔数"), 2, 2)
        dashboard_layout.addWidget(self.unqualified_holes_label, 3, 2)
        
        # 合格率 (使用进度条可视化)
        dashboard_layout.addWidget(QLabel("合格率"), 4, 0)
        self.qualification_rate_bar = QProgressBar()
        self.qualification_rate_bar.setObjectName("DashboardRateBar")
        self.qualification_rate_bar.setFormat("%.1f %%" % 0)
        dashboard_layout.addWidget(self.qualification_rate_bar, 5, 0, 1, 3)  # 跨3列
        
        layout.addWidget(dashboard_widget)
    
    def update_data(self, report_data: ReportData):
        """更新数据显示"""
        if not report_data:
            self.clear_data()
            return
        
        # 更新工件信息
        workpiece = report_data.workpiece_info
        self.workpiece_id_label.setText(f"<b>工件ID:</b> {workpiece.workpiece_id}")
        self.workpiece_type_label.setText(f"<b>类型:</b> {workpiece.type}")
        
        # 更新关键指标
        summary = report_data.quality_summary
        self.total_holes_label.setText(str(summary.total_holes))
        self.qualified_holes_label.setText(str(summary.qualified_holes))
        self.unqualified_holes_label.setText(str(summary.unqualified_holes))
        
        # 更新合格率进度条
        self.qualification_rate_bar.setValue(int(summary.qualification_rate))
        self.qualification_rate_bar.setFormat(f"{summary.qualification_rate:.1f} %")
    
    def clear_data(self):
        """清空数据显示"""
        self.workpiece_id_label.setText("工件ID: --")
        self.workpiece_type_label.setText("类型: --")
        self.total_holes_label.setText("0")
        self.qualified_holes_label.setText("0")
        self.unqualified_holes_label.setText("0")
        self.qualification_rate_bar.setValue(0)
        self.qualification_rate_bar.setFormat("0.0 %")
    
    def set_loading_state(self, is_loading: bool):
        """设置加载状态"""
        if is_loading:
            self.workpiece_id_label.setText("工件ID: 加载中...")
            self.workpiece_type_label.setText("类型: 加载中...")
        else:
            # 如果不是加载中，显示空状态
            if self.workpiece_id_label.text() == "工件ID: 加载中...":
                self.clear_data()