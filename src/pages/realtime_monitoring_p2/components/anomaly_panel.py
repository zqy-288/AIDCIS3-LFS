"""
异常监控面板组件
显示和管理检测到的异常数据
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QPushButton,
    QGroupBox, QHeaderView, QTextEdit
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QBrush
import logging
from datetime import datetime


class AnomalyPanel(QWidget):
    """
    异常监控面板
    
    功能：
    1. 显示异常数据列表
    2. 统计异常信息
    3. 支持异常数据导出
    4. 异常趋势分析
    """
    
    # 信号定义
    anomaly_selected = Signal(dict)  # 选择异常
    export_requested = Signal(list)  # 导出请求
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 异常数据存储
        self.anomaly_list = []
        self.anomaly_statistics = {
            'total': 0,
            'above_tolerance': 0,
            'below_tolerance': 0,
            'max_deviation': 0,
            'avg_deviation': 0
        }
        
        # 初始化UI
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 统计信息区域
        stats_group = QGroupBox("异常统计")
        stats_layout = QVBoxLayout(stats_group)
        
        # 统计标签
        self.total_label = QLabel("总异常数: 0")
        self.above_label = QLabel("超上限: 0")
        self.below_label = QLabel("超下限: 0")
        self.max_dev_label = QLabel("最大偏差: 0.00 mm")
        self.avg_dev_label = QLabel("平均偏差: 0.00 mm")
        
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.above_label)
        stats_layout.addWidget(self.below_label)
        stats_layout.addWidget(self.max_dev_label)
        stats_layout.addWidget(self.avg_dev_label)
        
        # 异常列表区域
        list_group = QGroupBox("异常列表")
        list_layout = QVBoxLayout(list_group)
        
        # 创建表格
        self.anomaly_table = QTableWidget()
        self.anomaly_table.setColumnCount(5)
        self.anomaly_table.setHorizontalHeaderLabels([
            "时间", "探头深度(mm)", "直径(mm)", "偏差(mm)", "类型"
        ])
        
        # 设置表格属性
        self.anomaly_table.setAlternatingRowColors(True)
        self.anomaly_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.anomaly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.anomaly_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("清除列表")
        self.clear_btn.clicked.connect(self.clear_anomalies)
        
        self.export_btn = QPushButton("导出数据")
        self.export_btn.clicked.connect(self._export_data)
        
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        
        list_layout.addWidget(self.anomaly_table)
        list_layout.addLayout(button_layout)
        
        # 详细信息区域
        detail_group = QGroupBox("异常详情")
        detail_layout = QVBoxLayout(detail_group)
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(100)
        
        detail_layout.addWidget(self.detail_text)
        
        # 添加到主布局
        layout.addWidget(stats_group)
        layout.addWidget(list_group, 1)  # 列表占主要空间
        layout.addWidget(detail_group)
        
    def add_anomaly(self, anomaly_data: dict):
        """添加新的异常数据"""
        # 添加时间戳
        anomaly_data['time'] = datetime.now().strftime("%H:%M:%S")
        
        # 确定异常类型
        if anomaly_data['deviation'] > 0:
            anomaly_data['type'] = "超上限"
            self.anomaly_statistics['above_tolerance'] += 1
        else:
            anomaly_data['type'] = "超下限"
            self.anomaly_statistics['below_tolerance'] += 1
            
        # 添加到列表
        self.anomaly_list.append(anomaly_data)
        
        # 更新统计
        self._update_statistics()
        
        # 添加到表格
        self._add_table_row(anomaly_data)
        
        self.logger.info(f"检测到异常: {anomaly_data}")
        
    def _add_table_row(self, anomaly_data: dict):
        """添加表格行"""
        row_position = self.anomaly_table.rowCount()
        self.anomaly_table.insertRow(row_position)
        
        # 时间
        time_item = QTableWidgetItem(anomaly_data['time'])
        self.anomaly_table.setItem(row_position, 0, time_item)
        
        # 探头深度
        depth_item = QTableWidgetItem(f"{anomaly_data.get('probe_depth', 0):.2f}")
        self.anomaly_table.setItem(row_position, 1, depth_item)
        
        # 直径
        diameter_item = QTableWidgetItem(f"{anomaly_data['diameter']:.3f}")
        self.anomaly_table.setItem(row_position, 2, diameter_item)
        
        # 偏差
        deviation_item = QTableWidgetItem(f"{anomaly_data['deviation']:.3f}")
        # 根据偏差正负设置颜色
        if anomaly_data['deviation'] > 0:
            deviation_item.setForeground(QBrush(QColor(255, 0, 0)))  # 红色
        else:
            deviation_item.setForeground(QBrush(QColor(0, 0, 255)))  # 蓝色
        self.anomaly_table.setItem(row_position, 3, deviation_item)
        
        # 类型
        type_item = QTableWidgetItem(anomaly_data['type'])
        self.anomaly_table.setItem(row_position, 4, type_item)
        
        # 自动滚动到最新行
        self.anomaly_table.scrollToBottom()
        
    def _update_statistics(self):
        """更新统计信息"""
        if not self.anomaly_list:
            self.anomaly_statistics = {
                'total': 0,
                'above_tolerance': 0,
                'below_tolerance': 0,
                'max_deviation': 0,
                'avg_deviation': 0
            }
        else:
            deviations = [abs(a['deviation']) for a in self.anomaly_list]
            self.anomaly_statistics['total'] = len(self.anomaly_list)
            self.anomaly_statistics['max_deviation'] = max(deviations)
            self.anomaly_statistics['avg_deviation'] = sum(deviations) / len(deviations)
        
        # 更新显示
        self.total_label.setText(f"总异常数: {self.anomaly_statistics['total']}")
        self.above_label.setText(f"超上限: {self.anomaly_statistics['above_tolerance']}")
        self.below_label.setText(f"超下限: {self.anomaly_statistics['below_tolerance']}")
        self.max_dev_label.setText(f"最大偏差: {self.anomaly_statistics['max_deviation']:.3f} mm")
        self.avg_dev_label.setText(f"平均偏差: {self.anomaly_statistics['avg_deviation']:.3f} mm")
        
    def _on_selection_changed(self):
        """选择改变处理"""
        selected_rows = self.anomaly_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            if row < len(self.anomaly_list):
                anomaly = self.anomaly_list[row]
                self._show_detail(anomaly)
                self.anomaly_selected.emit(anomaly)
                
    def _show_detail(self, anomaly: dict):
        """显示异常详情"""
        detail_text = f"""
时间: {anomaly['time']}
探头深度: {anomaly.get('probe_depth', 0):.2f} mm
实测直径: {anomaly['diameter']:.3f} mm
偏差值: {anomaly['deviation']:.3f} mm
异常类型: {anomaly['type']}
时间戳: {anomaly.get('timestamp', 'N/A')}
"""
        self.detail_text.setPlainText(detail_text.strip())
        
    def clear_anomalies(self):
        """清除所有异常数据"""
        self.anomaly_list.clear()
        self.anomaly_table.setRowCount(0)
        self.detail_text.clear()
        self.anomaly_statistics = {
            'total': 0,
            'above_tolerance': 0,
            'below_tolerance': 0,
            'max_deviation': 0,
            'avg_deviation': 0
        }
        self._update_statistics()
        self.logger.info("异常列表已清除")
        
    def _export_data(self):
        """导出异常数据"""
        if self.anomaly_list:
            self.export_requested.emit(self.anomaly_list)
            self.logger.info(f"导出 {len(self.anomaly_list)} 条异常数据")
        else:
            self.logger.warning("没有异常数据可导出")
            
    def get_anomaly_count(self) -> int:
        """获取异常数量"""
        return len(self.anomaly_list)
        
    def get_anomaly_list(self) -> list:
        """获取异常列表"""
        return self.anomaly_list.copy()
        
    def get_statistics(self) -> dict:
        """获取统计信息"""
        return self.anomaly_statistics.copy()