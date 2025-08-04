"""
紧凑型异常监控面板组件
专为右侧面板设计，优化空间利用
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton,
    QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QBrush, QFont
import logging
from datetime import datetime


class CompactAnomalyPanel(QWidget):
    """
    紧凑型异常监控面板
    
    功能：
    1. 显示异常数据列表
    2. 统计异常信息
    3. 支持异常数据导出
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
        """初始化UI布局 - 紧凑设计"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # 1. 统计信息区域（紧凑型）
        self._create_compact_stats(layout)
        
        # 2. 异常列表区域
        self._create_compact_list(layout)
        
        # 3. 操作按钮区域
        self._create_compact_buttons(layout)
        
    def _create_compact_stats(self, parent_layout):
        """创建紧凑型统计区域"""
        stats_group = QGroupBox("异常统计")
        stats_group.setMaximumHeight(120)
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(2)
        
        # 使用小字体
        font = QFont("Arial", 8)
        
        # 第一行：总数和分类
        row1_layout = QHBoxLayout()
        self.total_label = QLabel("总数: 0")
        self.total_label.setFont(font)
        self.above_label = QLabel("超上限: 0")
        self.above_label.setFont(font)
        self.below_label = QLabel("超下限: 0")
        self.below_label.setFont(font)
        
        row1_layout.addWidget(self.total_label)
        row1_layout.addWidget(self.above_label)
        row1_layout.addWidget(self.below_label)
        
        # 第二行：偏差信息
        row2_layout = QHBoxLayout()
        self.max_dev_label = QLabel("最大偏差: 0.00 mm")
        self.max_dev_label.setFont(font)
        self.avg_dev_label = QLabel("平均偏差: 0.00 mm")
        self.avg_dev_label.setFont(font)
        
        row2_layout.addWidget(self.max_dev_label)
        row2_layout.addWidget(self.avg_dev_label)
        
        stats_layout.addLayout(row1_layout)
        stats_layout.addLayout(row2_layout)
        
        parent_layout.addWidget(stats_group)
        
    def _create_compact_list(self, parent_layout):
        """创建紧凑型异常列表"""
        list_group = QGroupBox("异常列表")
        list_layout = QVBoxLayout(list_group)
        list_layout.setContentsMargins(5, 5, 5, 5)
        
        # 使用列表控件替代表格，更紧凑
        self.anomaly_list_widget = QListWidget()
        self.anomaly_list_widget.setMaximumHeight(150)
        self.anomaly_list_widget.setFont(QFont("Arial", 8))
        self.anomaly_list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        
        # 设置占位符文本
        if len(self.anomaly_list) == 0:
            placeholder_item = QListWidgetItem("暂无异常数据...")
            placeholder_item.setTextAlignment(Qt.AlignCenter)
            placeholder_item.setForeground(QColor(128, 128, 128))
            self.anomaly_list_widget.addItem(placeholder_item)
        
        list_layout.addWidget(self.anomaly_list_widget)
        parent_layout.addWidget(list_group)
        
    def _create_compact_buttons(self, parent_layout):
        """创建紧凑型按钮区域"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        # 紧凑型按钮
        self.clear_btn = QPushButton("清除列表")
        self.clear_btn.setMaximumHeight(25)
        self.clear_btn.setFont(QFont("Arial", 8))
        self.clear_btn.clicked.connect(self.clear_anomalies)
        
        self.export_btn = QPushButton("导出数据")
        self.export_btn.setMaximumHeight(25)
        self.export_btn.setFont(QFont("Arial", 8))
        self.export_btn.clicked.connect(self._export_data)
        
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.export_btn)
        
        parent_layout.addLayout(button_layout)
        
    def add_anomaly(self, anomaly_data: dict):
        """添加异常数据"""
        # 移除占位符
        if self.anomaly_list_widget.count() == 1:
            item = self.anomaly_list_widget.item(0)
            if item and item.text() == "暂无异常数据...":
                self.anomaly_list_widget.clear()
        
        # 添加到数据列表
        self.anomaly_list.append(anomaly_data)
        
        # 创建显示文本
        time_str = anomaly_data.get('time', datetime.now().strftime('%H:%M:%S'))
        diameter = anomaly_data.get('diameter', 0)
        deviation = anomaly_data.get('deviation', 0)
        probe_depth = anomaly_data.get('probe_depth', 0)
        
        # 确定类型
        anomaly_type = "超上限" if deviation > 0 else "超下限"
        
        # 格式化显示文本
        item_text = f"{time_str} | 深度:{probe_depth:.1f}mm | 直径:{diameter:.3f}mm | 偏差:{deviation:.3f}mm"
        
        # 创建列表项
        list_item = QListWidgetItem(item_text)
        list_item.setFont(QFont("Arial", 8))
        
        # 根据类型设置颜色
        if anomaly_type == "超上限":
            list_item.setForeground(QColor(255, 100, 100))  # 红色
        else:
            list_item.setForeground(QColor(100, 150, 255))  # 蓝色
            
        self.anomaly_list_widget.addItem(list_item)
        
        # 滚动到最新项
        self.anomaly_list_widget.scrollToBottom()
        
        # 更新统计信息
        self._update_statistics()
        
        self.logger.info(f"检测到异常: {anomaly_data}")
        
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
            total = len(self.anomaly_list)
            above_count = sum(1 for item in self.anomaly_list if item.get('deviation', 0) > 0)
            below_count = total - above_count
            
            deviations = [abs(item.get('deviation', 0)) for item in self.anomaly_list]
            max_deviation = max(deviations) if deviations else 0
            avg_deviation = sum(deviations) / len(deviations) if deviations else 0
            
            self.anomaly_statistics = {
                'total': total,
                'above_tolerance': above_count,
                'below_tolerance': below_count,
                'max_deviation': max_deviation,
                'avg_deviation': avg_deviation
            }
        
        # 更新显示
        stats = self.anomaly_statistics
        self.total_label.setText(f"总数: {stats['total']}")
        self.above_label.setText(f"超上限: {stats['above_tolerance']}")
        self.below_label.setText(f"超下限: {stats['below_tolerance']}")
        self.max_dev_label.setText(f"最大偏差: {stats['max_deviation']:.3f} mm")
        self.avg_dev_label.setText(f"平均偏差: {stats['avg_deviation']:.3f} mm")
        
    def clear_anomalies(self):
        """清除所有异常数据"""
        self.anomaly_list.clear()
        self.anomaly_list_widget.clear()
        
        # 添加占位符
        placeholder_item = QListWidgetItem("暂无异常数据...")
        placeholder_item.setTextAlignment(Qt.AlignCenter)
        placeholder_item.setForeground(QColor(128, 128, 128))
        self.anomaly_list_widget.addItem(placeholder_item)
        
        self._update_statistics()
        self.logger.info("异常数据已清除")
        
    def _on_selection_changed(self):
        """选择改变处理"""
        current_item = self.anomaly_list_widget.currentItem()
        if current_item and current_item.text() != "暂无异常数据...":
            current_row = self.anomaly_list_widget.currentRow()
            if 0 <= current_row < len(self.anomaly_list):
                selected_anomaly = self.anomaly_list[current_row]
                self.anomaly_selected.emit(selected_anomaly)
                
    def _export_data(self):
        """导出数据"""
        if self.anomaly_list:
            self.export_requested.emit(self.anomaly_list.copy())
            self.logger.info(f"请求导出 {len(self.anomaly_list)} 条异常数据")
        else:
            self.logger.warning("没有异常数据可导出")
            
    def get_statistics(self) -> dict:
        """获取统计信息"""
        return self.anomaly_statistics.copy()