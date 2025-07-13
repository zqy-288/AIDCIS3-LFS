"""异常显示面板组件"""
from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QScrollArea,
    QWidget, QLabel, QPushButton
)
from PySide6.QtCore import Signal, Qt


class AnomalyPanel(QGroupBox):
    """
    异常数据显示面板
    显示检测到的异常数据点
    """
    
    # 信号定义
    anomaly_clicked = Signal(dict)  # 点击异常项时发出
    clear_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__("异常数据", parent)
        self.setup_ui()
        self.apply_styles()
        
        # 异常数据列表
        self.anomaly_widgets = []
        
    def setup_ui(self):
        """设置UI布局"""
        layout = QVBoxLayout(self)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        self.count_label = QLabel("异常数量: 0")
        control_layout.addWidget(self.count_label)
        
        control_layout.addStretch()
        
        self.clear_btn = QPushButton("清除")
        self.clear_btn.clicked.connect(self.clear_requested.emit)
        control_layout.addWidget(self.clear_btn)
        
        layout.addLayout(control_layout)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # 内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setSpacing(2)
        
        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)
        
    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #ff5722;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ff5722;
            }
            QPushButton {
                background-color: #ff5722;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e64a19;
            }
        """)
        
    def add_anomaly(self, anomaly_info: dict):
        """添加异常数据"""
        anomaly_widget = self._create_anomaly_widget(anomaly_info)
        self.content_layout.addWidget(anomaly_widget)
        self.anomaly_widgets.append(anomaly_widget)
        
        # 更新计数
        self.count_label.setText(f"异常数量: {len(self.anomaly_widgets)}")
        
        # 限制显示数量
        if len(self.anomaly_widgets) > 10:
            # 移除最早的异常
            oldest = self.anomaly_widgets.pop(0)
            oldest.setParent(None)
            
    def _create_anomaly_widget(self, anomaly_info: dict) -> QWidget:
        """创建异常数据显示组件"""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #ffebee;
                border: 1px solid #ff5722;
                border-radius: 4px;
                padding: 4px;
            }
            QLabel {
                color: #d32f2f;
                font-size: 11px;
            }
        """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # 深度和直径信息
        info_label = QLabel(
            f"深度: {anomaly_info['depth']:.1f}mm\n"
            f"直径: {anomaly_info['diameter']:.3f}mm"
        )
        layout.addWidget(info_label)
        
        # 偏差信息
        deviation_label = QLabel(
            f"偏差: {anomaly_info['deviation']:.3f}mm\n"
            f"样品: {anomaly_info.get('sample_id', 'Unknown')}"
        )
        layout.addWidget(deviation_label)
        
        # 点击处理
        widget.mousePressEvent = lambda event: self.anomaly_clicked.emit(anomaly_info)
        
        return widget
        
    def update_anomalies(self, anomaly_list: list):
        """批量更新异常数据"""
        self.clear_anomalies()
        
        # 显示最近的异常（最多10个）
        recent_anomalies = anomaly_list[-10:] if len(anomaly_list) > 10 else anomaly_list
        
        for anomaly in recent_anomalies:
            self.add_anomaly(anomaly)
            
    def clear_anomalies(self):
        """清除所有异常显示"""
        for widget in self.anomaly_widgets:
            widget.setParent(None)
        self.anomaly_widgets.clear()
        self.count_label.setText("异常数量: 0")
        
    def get_anomaly_count(self) -> int:
        """获取异常数量"""
        return len(self.anomaly_widgets)