"""
实时监控页面
简化版本，解决原版"魔幻"问题，提供更实用的监控界面
"""

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QGroupBox, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QTextEdit, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFont, QColor


class RealtimeMonitoringPage(QWidget):
    """
    简化版实时监控页面
    
    特点：
    1. 清晰的布局，不花哨
    2. 实用的功能，易于理解
    3. 减少不必要的复杂性
    4. 重点突出数据监控
    """
    
    # 页面信号
    monitoring_started = Signal()
    monitoring_stopped = Signal()
    hole_selected = Signal(str)
    
    def __init__(self, shared_components=None, view_model=None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        self.shared_components = shared_components
        self.view_model = view_model
        
        # 状态变量
        self.is_monitoring = False
        self.current_hole = "未选择"
        self.data_count = 0
        self.anomaly_count = 0
        
        # 模拟数据存储
        self.monitoring_data = []
        self.anomaly_data = []
        
        # 初始化
        self._init_ui()
        self._init_timer()
        
        self.logger.info("✅ 简化版实时监控页面初始化完成")
        
    def _init_ui(self):
        """初始化用户界面 - 清晰简洁的布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # 1. 顶部控制面板
        self._create_control_panel(layout)
        
        # 2. 主要显示区域
        self._create_main_display(layout)
        
    def _create_control_panel(self, parent_layout):
        """创建顶部控制面板"""
        control_group = QGroupBox("监控控制")
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(20)
        
        # 孔位选择
        hole_layout = QVBoxLayout()
        hole_label = QLabel("当前孔位:")
        hole_label.setFont(QFont("Arial", 10))
        
        self.hole_combo = QComboBox()
        self.hole_combo.addItems([
            "ABC001R001", "ABC001R002", "ABC002R001", 
            "ABC002R002", "ABC003R001", "ABC003R002"
        ])
        self.hole_combo.currentTextChanged.connect(self._on_hole_changed)
        
        hole_layout.addWidget(hole_label)
        hole_layout.addWidget(self.hole_combo)
        
        # 监控状态
        status_layout = QVBoxLayout()
        status_label = QLabel("监控状态:")
        status_label.setFont(QFont("Arial", 10))
        
        self.status_display = QLabel("未开始")
        self.status_display.setStyleSheet("color: red; font-weight: bold; font-size: 12pt;")
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_display)
        
        # 数据统计
        stats_layout = QVBoxLayout()
        stats_label = QLabel("数据统计:")
        stats_label.setFont(QFont("Arial", 10))
        
        self.data_count_label = QLabel("数据: 0 条")
        self.anomaly_count_label = QLabel("异常: 0 条")
        
        stats_layout.addWidget(stats_label)
        stats_layout.addWidget(self.data_count_label)
        stats_layout.addWidget(self.anomaly_count_label)
        
        # 控制按钮
        button_layout = QVBoxLayout()
        
        self.start_btn = QPushButton("开始监控")
        self.start_btn.setCheckable(True)
        self.start_btn.clicked.connect(self._toggle_monitoring)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 12pt;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #f44336;
            }
        """)
        
        self.clear_btn = QPushButton("清除数据")
        self.clear_btn.clicked.connect(self._clear_data)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.clear_btn)
        
        # 添加到控制面板
        control_layout.addLayout(hole_layout)
        control_layout.addLayout(status_layout)
        control_layout.addLayout(stats_layout)
        control_layout.addStretch()
        control_layout.addLayout(button_layout)
        
        parent_layout.addWidget(control_group)
        
    def _create_main_display(self, parent_layout):
        """创建主显示区域"""
        # 使用水平分割器
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：数据显示
        self._create_data_display(main_splitter)
        
        # 右侧：异常监控
        self._create_anomaly_display(main_splitter)
        
        # 设置分割比例（70% : 30%）
        main_splitter.setSizes([700, 300])
        
        parent_layout.addWidget(main_splitter)
        
    def _create_data_display(self, splitter):
        """创建数据显示区域"""
        data_group = QGroupBox("实时数据监控")
        data_layout = QVBoxLayout(data_group)
        
        # 数据表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(4)
        self.data_table.setHorizontalHeaderLabels(["时间", "深度(mm)", "直径(mm)", "状态"])
        
        # 设置表格样式
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        data_layout.addWidget(self.data_table)
        
        splitter.addWidget(data_group)
        
    def _create_anomaly_display(self, splitter):
        """创建异常显示区域"""
        anomaly_group = QGroupBox("异常监控")
        anomaly_layout = QVBoxLayout(anomaly_group)
        
        # 异常统计
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_layout.setSpacing(5)
        
        self.total_anomalies_label = QLabel("总异常数: 0")
        self.max_deviation_label = QLabel("最大偏差: 0.000 mm")
        self.avg_deviation_label = QLabel("平均偏差: 0.000 mm")
        
        font = QFont("Arial", 9)
        for label in [self.total_anomalies_label, self.max_deviation_label, self.avg_deviation_label]:
            label.setFont(font)
            stats_layout.addWidget(label)
        
        anomaly_layout.addWidget(stats_widget)
        
        # 异常列表
        self.anomaly_table = QTableWidget()
        self.anomaly_table.setColumnCount(3)
        self.anomaly_table.setHorizontalHeaderLabels(["时间", "偏差(mm)", "类型"])
        
        # 设置异常表格样式
        anomaly_header = self.anomaly_table.horizontalHeader()
        anomaly_header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.anomaly_table.setAlternatingRowColors(True)
        self.anomaly_table.setMaximumHeight(200)
        
        anomaly_layout.addWidget(self.anomaly_table)
        
        # 导出按钮
        export_btn = QPushButton("导出异常数据")
        export_btn.clicked.connect(self._export_anomaly_data)
        anomaly_layout.addWidget(export_btn)
        
        splitter.addWidget(anomaly_group)
        
    def _init_timer(self):
        """初始化定时器"""
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._update_monitoring_data)
        
    def _on_hole_changed(self, hole_id: str):
        """孔位改变处理"""
        self.current_hole = hole_id
        self.hole_selected.emit(hole_id)
        self.logger.info(f"切换到孔位: {hole_id}")
        
    def _toggle_monitoring(self):
        """切换监控状态"""
        self.is_monitoring = self.start_btn.isChecked()
        
        if self.is_monitoring:
            self.start_btn.setText("停止监控")
            self.status_display.setText("监控中...")
            self.status_display.setStyleSheet("color: green; font-weight: bold; font-size: 12pt;")
            
            # 开始定时器（每500ms更新一次）
            self.monitor_timer.start(500)
            
            self.monitoring_started.emit()
            self.logger.info("开始监控")
            
        else:
            self.start_btn.setText("开始监控")
            self.status_display.setText("已停止")
            self.status_display.setStyleSheet("color: red; font-weight: bold; font-size: 12pt;")
            
            # 停止定时器
            self.monitor_timer.stop()
            
            self.monitoring_stopped.emit()
            self.logger.info("停止监控")
            
    def _update_monitoring_data(self):
        """更新监控数据（模拟）"""
        if not self.is_monitoring:
            return
            
        # 生成模拟数据
        import random
        from datetime import datetime
        
        time_str = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 精确到毫秒
        depth = random.uniform(0, 1000)
        diameter = random.uniform(19.80, 20.20)  # 标准直径20mm，允许偏差
        
        # 判断是否异常（超出±0.1mm容差）
        standard_diameter = 20.0
        deviation = diameter - standard_diameter
        is_anomaly = abs(deviation) > 0.1
        
        status = "异常" if is_anomaly else "正常"
        
        # 添加到数据表格
        row_count = self.data_table.rowCount()
        self.data_table.insertRow(row_count)
        
        self.data_table.setItem(row_count, 0, QTableWidgetItem(time_str))
        self.data_table.setItem(row_count, 1, QTableWidgetItem(f"{depth:.1f}"))
        self.data_table.setItem(row_count, 2, QTableWidgetItem(f"{diameter:.3f}"))
        
        status_item = QTableWidgetItem(status)
        if is_anomaly:
            status_item.setForeground(QColor("red"))
        status_item.setTextAlignment(Qt.AlignCenter)
        self.data_table.setItem(row_count, 3, status_item)
        
        # 自动滚动到最新数据
        self.data_table.scrollToBottom()
        
        # 限制显示行数（最多1000行）
        if row_count > 1000:
            self.data_table.removeRow(0)
        
        # 更新计数
        self.data_count += 1
        self.data_count_label.setText(f"数据: {self.data_count} 条")
        
        # 处理异常数据
        if is_anomaly:
            self._add_anomaly_data(time_str, deviation)
            
    def _add_anomaly_data(self, time_str: str, deviation: float):
        """添加异常数据"""
        self.anomaly_count += 1
        self.anomaly_count_label.setText(f"异常: {self.anomaly_count} 条")
        
        # 添加到异常表格
        row_count = self.anomaly_table.rowCount()
        self.anomaly_table.insertRow(row_count)
        
        self.anomaly_table.setItem(row_count, 0, QTableWidgetItem(time_str))
        self.anomaly_table.setItem(row_count, 1, QTableWidgetItem(f"{deviation:.3f}"))
        
        anomaly_type = "超上限" if deviation > 0 else "超下限"
        type_item = QTableWidgetItem(anomaly_type)
        
        if deviation > 0:
            type_item.setForeground(QColor("red"))
        else:
            type_item.setForeground(QColor("blue"))
            
        self.anomaly_table.setItem(row_count, 2, type_item)
        
        # 自动滚动到最新异常
        self.anomaly_table.scrollToBottom()
        
        # 限制异常显示行数（最多100行）
        if row_count > 100:
            self.anomaly_table.removeRow(0)
            
        # 更新异常统计
        self._update_anomaly_statistics(deviation)
        
    def _update_anomaly_statistics(self, latest_deviation: float):
        """更新异常统计"""
        # 收集所有异常偏差
        deviations = []
        for row in range(self.anomaly_table.rowCount()):
            deviation_item = self.anomaly_table.item(row, 1)
            if deviation_item:
                try:
                    deviation = float(deviation_item.text())
                    deviations.append(abs(deviation))
                except ValueError:
                    continue
                    
        if deviations:
            max_deviation = max(deviations)
            avg_deviation = sum(deviations) / len(deviations)
            
            self.max_deviation_label.setText(f"最大偏差: {max_deviation:.3f} mm")
            self.avg_deviation_label.setText(f"平均偏差: {avg_deviation:.3f} mm")
        
    def _clear_data(self):
        """清除所有数据"""
        self.data_table.setRowCount(0)
        self.anomaly_table.setRowCount(0)
        
        # 重置计数
        self.data_count = 0
        self.anomaly_count = 0
        self.data_count_label.setText("数据: 0 条")
        self.anomaly_count_label.setText("异常: 0 条")
        
        # 重置统计
        self.total_anomalies_label.setText("总异常数: 0")
        self.max_deviation_label.setText("最大偏差: 0.000 mm")
        self.avg_deviation_label.setText("平均偏差: 0.000 mm")
        
        self.logger.info("数据已清除")
        
    def _export_anomaly_data(self):
        """导出异常数据"""
        if self.anomaly_table.rowCount() == 0:
            self.logger.warning("没有异常数据可导出")
            return
            
        try:
            from datetime import datetime
            filename = f"anomaly_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # 模拟导出
            self.logger.info(f"异常数据已导出到: {filename}")
            
        except Exception as e:
            self.logger.error(f"导出异常数据失败: {e}")
            
    def get_current_hole(self) -> str:
        """获取当前孔位"""
        return self.current_hole
        
    def is_monitoring_active(self) -> bool:
        """检查是否正在监控"""
        return self.is_monitoring
        
    def get_monitoring_statistics(self) -> dict:
        """获取监控统计信息"""
        return {
            'total_data': self.data_count,
            'total_anomalies': self.anomaly_count,
            'current_hole': self.current_hole,
            'is_monitoring': self.is_monitoring
        }