"""
异常监控面板组件
负责显示超出公差的测量点和异常统计信息
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QScrollArea, QPushButton
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from typing import List, Tuple, Optional
from collections import deque


class AnomalyPanel(QWidget):
    """
    异常监控面板
    显示大号数字异常计数 + 异常率百分比 + 异常数据滚动区域
    """
    
    # 信号定义
    next_sample_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 异常数据存储
        self.anomaly_data = deque(maxlen=100)
        self.total_points = 0
        self.anomaly_count = 0
        
        # 公差参数
        self.standard_diameter = 17.73
        self.upper_tolerance = 0.07
        self.lower_tolerance = 0.05
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面 - 完全按照重构前的精确布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 异常监控窗口 - 按照重构前的精确尺寸和样式
        anomaly_widget = QGroupBox("异常直径监控")
        anomaly_widget.setObjectName("anomaly_widget")
        anomaly_widget.setMinimumWidth(310)  # 按照重构前的精确尺寸
        anomaly_widget.setMaximumWidth(390)  # 按照重构前的精确尺寸
        anomaly_layout = QVBoxLayout(anomaly_widget)
        anomaly_layout.setContentsMargins(8, 8, 8, 8)  # 按照重构前的边距
        anomaly_layout.setSpacing(5)  # 按照重构前的间距

        # 标题 - 按照重构前的样式
        title_label = QLabel("超出公差的测量点")
        title_label.setObjectName("AnomalyTitle")
        title_label.setFixedHeight(25)  # 按照重构前的高度
        anomaly_layout.addWidget(title_label)

        # 滚动区域用于显示异常数据 - 按照重构前的设计
        from PySide6.QtWidgets import QScrollArea
        self.anomaly_scroll = QScrollArea()
        self.anomaly_scroll.setWidgetResizable(True)
        self.anomaly_scroll.setObjectName("anomaly_scroll")

        self.anomaly_content = QWidget()
        self.anomaly_content.setObjectName("anomaly_content")
        self.anomaly_content_layout = QVBoxLayout(self.anomaly_content)
        self.anomaly_content_layout.setContentsMargins(5, 5, 5, 5)
        self.anomaly_scroll.setWidget(self.anomaly_content)

        # 滚动区域占据可用空间，但为统计信息预留足够空间
        anomaly_layout.addWidget(self.anomaly_scroll, 1)

        # 统计信息 - 使用栅格布局精确控制异常计数显示，按照重构前的设计
        stats_widget = QWidget()
        stats_widget.setFixedHeight(60)  # 按照重构前的高度
        stats_widget.setObjectName("AnomalyStatsWidget")

        # 使用QGridLayout实现精确的控件对齐 - 按照重构前的布局
        from PySide6.QtWidgets import QGridLayout
        stats_layout = QGridLayout(stats_widget)
        stats_layout.setContentsMargins(10, 5, 10, 5)
        stats_layout.setSpacing(5)

        # 大号数字显示异常计数 - 按照重构前的样式
        self.anomaly_count_number = QLabel("0")
        self.anomaly_count_number.setObjectName("AnomalyCountLabel")

        # 异常计数说明文字 - 按照重构前的设计
        count_text_label = QLabel("个异常点")
        count_text_label.setObjectName("AnomalyUnitLabel")

        # 异常率显示 - 按照重构前的样式
        self.anomaly_rate_label = QLabel("异常率: 0.0%")
        self.anomaly_rate_label.setObjectName("AnomalyRateLabel")

        # 将控件放入网格布局 - 按照重构前的精确对齐方式
        # 第0行，第0列：大号数字，右对齐
        stats_layout.addWidget(self.anomaly_count_number, 0, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 第0行，第1列：单位文字，左对齐并垂直居中
        stats_layout.addWidget(count_text_label, 0, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # 第0行，第2列：异常率，右对齐并垂直居中
        stats_layout.addWidget(self.anomaly_rate_label, 0, 2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # 设置列的伸缩比例，让中间有适当的空间 - 按照重构前的设计
        stats_layout.setColumnStretch(0, 0)  # 大号数字列不伸缩
        stats_layout.setColumnStretch(1, 1)  # 单位文字列可以伸缩，提供间距
        stats_layout.setColumnStretch(2, 0)  # 异常率列不伸缩

        # 添加统计区域，不使用stretch factor，保持固定位置
        anomaly_layout.addWidget(stats_widget, 0)

        layout.addWidget(anomaly_widget)

        # 添加固定间距，确保按钮不会紧贴异常面板 - 按照重构前的设计
        layout.addSpacing(15)

        # 添加【查看下一个样品】按钮 - 按照重构前的样式
        self.next_sample_button = QPushButton("查看下一个样品")
        self.next_sample_button.clicked.connect(self.next_sample_clicked.emit)
        self.next_sample_button.setObjectName("next_sample_button")
        from PySide6.QtWidgets import QSizePolicy
        self.next_sample_button.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        layout.addWidget(self.next_sample_button)

        # 添加底部间距，确保按钮不会贴底 - 按照重构前的设计
        layout.addSpacing(10)
        
    def set_tolerance_parameters(self, standard_diameter: float, upper_tol: float, lower_tol: float):
        """设置公差参数"""
        self.standard_diameter = standard_diameter
        self.upper_tolerance = upper_tol
        self.lower_tolerance = lower_tol
        
    def add_measurement_point(self, depth: float, diameter: float):
        """添加测量点并检查是否异常"""
        self.total_points += 1
        
        # 检查是否超出公差
        max_diameter = self.standard_diameter + self.upper_tolerance
        min_diameter = self.standard_diameter - self.lower_tolerance
        
        is_anomaly = diameter > max_diameter or diameter < min_diameter
        
        if is_anomaly:
            self.anomaly_count += 1
            self.anomaly_data.append((depth, diameter))
            self.add_anomaly_item(depth, diameter, max_diameter, min_diameter)
            
        self.update_statistics()
        
    def add_anomaly_item(self, depth: float, diameter: float, max_allowed: float, min_allowed: float):
        """添加异常项到显示列表"""
        # 创建异常项显示
        anomaly_item = QLabel()
        anomaly_item.setObjectName("anomaly_item")
        
        # 确定异常类型
        if diameter > max_allowed:
            anomaly_type = "超上限"
            excess = diameter - max_allowed
            anomaly_item.setStyleSheet("color: #E74C3C; background-color: rgba(231, 76, 60, 0.1); padding: 3px; border-radius: 3px;")
        else:
            anomaly_type = "超下限"
            excess = min_allowed - diameter
            anomaly_item.setStyleSheet("color: #E67E22; background-color: rgba(230, 126, 34, 0.1); padding: 3px; border-radius: 3px;")
            
        anomaly_text = f"深度 {depth:.1f}mm: {diameter:.3f}mm ({anomaly_type} {excess:.3f}mm)"
        anomaly_item.setText(anomaly_text)
        anomaly_item.setWordWrap(True)
        
        # 添加到布局顶部（最新的在上面）
        self.anomaly_content_layout.insertWidget(0, anomaly_item)
        
        # 限制显示的异常项数量
        if self.anomaly_content_layout.count() > 50:
            # 移除最旧的项
            old_item = self.anomaly_content_layout.takeAt(self.anomaly_content_layout.count() - 1)
            if old_item and old_item.widget():
                old_item.widget().deleteLater()
                
        # 滚动到顶部显示最新异常
        self.anomaly_scroll.verticalScrollBar().setValue(0)
        
    def update_statistics(self):
        """更新异常统计显示 - 按照重构前的样式"""
        # 更新异常计数 - 使用重构前的组件名称
        self.anomaly_count_number.setText(str(self.anomaly_count))

        # 计算异常率
        if self.total_points > 0:
            anomaly_rate = (self.anomaly_count / self.total_points) * 100
            self.anomaly_rate_label.setText(f"异常率: {anomaly_rate:.1f}%")
        else:
            self.anomaly_rate_label.setText("异常率: 0.0%")
            
    def clear_anomalies(self):
        """清除所有异常数据"""
        self.anomaly_data.clear()
        self.total_points = 0
        self.anomaly_count = 0
        
        # 清除显示的异常项
        while self.anomaly_content_layout.count():
            child = self.anomaly_content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        self.update_statistics()
        
    def get_anomaly_statistics(self) -> Tuple[int, int, float]:
        """获取异常统计信息"""
        anomaly_rate = (self.anomaly_count / self.total_points * 100) if self.total_points > 0 else 0.0
        return self.anomaly_count, self.total_points, anomaly_rate
        
    def export_anomaly_data(self) -> List[Tuple[float, float]]:
        """导出异常数据"""
        return list(self.anomaly_data)
