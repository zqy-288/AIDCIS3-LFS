"""
报告预览面板组件
提供数据预览和报告内容预览功能
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QTableWidget, QTableWidgetItem, QTabWidget
)
from PySide6.QtCore import Qt, Signal

# 从assets/old目录导入报告数据模型
from assets.old.report_models import ReportData


class ReportPreviewPanel(QWidget):
    """报告预览面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 标签页
        tab_widget = QTabWidget()
        
        # 数据预览标签页  
        self._create_data_preview_tab(tab_widget)
        
        layout.addWidget(tab_widget)
    
    def _create_data_preview_tab(self, tab_widget):
        """创建数据预览标签页"""
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        
        # 数据状态指示器
        self.data_status_label = QLabel("📊 数据状态: 未加载")
        self.data_status_label.setObjectName("DataStatusLabel")
        preview_layout.addWidget(self.data_status_label)
        
        # 数据汇总显示
        summary_group = QGroupBox("数据汇总")
        summary_layout = QVBoxLayout(summary_group)
        
        # 关键指标显示
        self.total_holes_label = QLabel("总孔位数: --")
        self.qualified_holes_label = QLabel("合格孔位: --")
        self.unqualified_holes_label = QLabel("不合格孔位: --")
        self.qualification_rate_label = QLabel("合格率: --%")
        
        summary_layout.addWidget(self.total_holes_label)
        summary_layout.addWidget(self.qualified_holes_label)
        summary_layout.addWidget(self.unqualified_holes_label)
        summary_layout.addWidget(self.qualification_rate_label)
        
        preview_layout.addWidget(summary_group)
        
        # 孔位数据表格
        table_group = QGroupBox("孔位数据")
        table_layout = QVBoxLayout(table_group)
        
        self.hole_data_table = QTableWidget()
        self.hole_data_table.setColumnCount(6)
        self.hole_data_table.setHorizontalHeaderLabels([
            "孔位ID", "位置(X,Y)", "合格率", "测量次数", "状态", "最后测量时间"
        ])
        
        table_layout.addWidget(self.hole_data_table)
        preview_layout.addWidget(table_group)
        
        tab_widget.addTab(preview_tab, "数据预览")
    
    def update_data_status(self, status_text: str):
        """更新数据状态显示"""
        self.data_status_label.setText(status_text)
    
    def update_summary_display(self, report_data: ReportData):
        """更新汇总显示"""
        summary = report_data.quality_summary
        
        self.total_holes_label.setText(f"总孔位数: {summary.total_holes}")
        self.qualified_holes_label.setText(f"合格孔位: {summary.qualified_holes}")
        self.unqualified_holes_label.setText(f"不合格孔位: {summary.unqualified_holes}")
        self.qualification_rate_label.setText(f"合格率: {summary.qualification_rate:.1f}%")
    
    def update_hole_data_table(self, report_data: ReportData):
        """更新孔位数据表格"""
        all_holes = report_data.qualified_holes + report_data.unqualified_holes
        
        self.hole_data_table.setRowCount(len(all_holes))
        
        for row, hole in enumerate(all_holes):
            self.hole_data_table.setItem(row, 0, QTableWidgetItem(hole.hole_id))
            
            position_text = f"({hole.position_x:.1f}, {hole.position_y:.1f})"
            self.hole_data_table.setItem(row, 1, QTableWidgetItem(position_text))
            
            rate_text = f"{hole.qualification_rate:.1f}%"
            self.hole_data_table.setItem(row, 2, QTableWidgetItem(rate_text))
            
            count_text = f"{hole.qualified_count}/{hole.total_count}"
            self.hole_data_table.setItem(row, 3, QTableWidgetItem(count_text))
            
            status_text = "合格" if hole.is_qualified else "不合格"
            self.hole_data_table.setItem(row, 4, QTableWidgetItem(status_text))
            
            time_text = hole.measurement_timestamp.strftime("%Y-%m-%d %H:%M") if hole.measurement_timestamp else "未知"
            self.hole_data_table.setItem(row, 5, QTableWidgetItem(time_text))
    
    def clear_data(self):
        """清空数据显示"""
        self.data_status_label.setText("📊 数据状态: 未加载")
        self.total_holes_label.setText("总孔位数: --")
        self.qualified_holes_label.setText("合格孔位: --")
        self.unqualified_holes_label.setText("不合格孔位: --")
        self.qualification_rate_label.setText("合格率: --%")
        self.hole_data_table.setRowCount(0)