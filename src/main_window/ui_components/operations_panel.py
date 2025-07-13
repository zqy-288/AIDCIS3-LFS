"""右侧操作面板组件"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QPushButton,
    QTextEdit, QProgressBar, QLabel
)
from PySide6.QtCore import Signal, Qt

from aidcis2.models.hole_data import HoleData


class OperationsPanel(QWidget):
    """
    右侧操作面板
    包含检测控制、孔位操作和日志显示
    """
    
    # 信号定义
    start_detection_clicked = Signal()
    pause_detection_clicked = Signal()
    stop_detection_clicked = Signal()
    simulate_clicked = Signal()
    goto_realtime_clicked = Signal()
    goto_history_clicked = Signal()
    mark_defective_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 设置固定宽度
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
        
        # 检测控制组
        self.detection_control_group = self._create_detection_control_group()
        layout.addWidget(self.detection_control_group)
        
        # 孔位操作组
        self.hole_operations_group = self._create_hole_operations_group()
        layout.addWidget(self.hole_operations_group)
        
        # 进度显示
        self.progress_group = self._create_progress_group()
        layout.addWidget(self.progress_group)
        
        # 日志显示
        self.log_group = self._create_log_group()
        layout.addWidget(self.log_group, 1)  # 占用剩余空间
        
    def _create_detection_control_group(self) -> QGroupBox:
        """创建检测控制组"""
        group = QGroupBox("检测控制")
        layout = QVBoxLayout(group)
        
        # 开始检测按钮
        self.start_detection_btn = QPushButton("开始检测")
        self.start_detection_btn.setEnabled(False)
        self.start_detection_btn.clicked.connect(self.start_detection_clicked.emit)
        layout.addWidget(self.start_detection_btn)
        
        # 暂停/恢复按钮
        self.pause_detection_btn = QPushButton("暂停检测")
        self.pause_detection_btn.setEnabled(False)
        self.pause_detection_btn.clicked.connect(self.pause_detection_clicked.emit)
        layout.addWidget(self.pause_detection_btn)
        
        # 停止检测按钮
        self.stop_detection_btn = QPushButton("停止检测")
        self.stop_detection_btn.setEnabled(False)
        self.stop_detection_btn.clicked.connect(self.stop_detection_clicked.emit)
        layout.addWidget(self.stop_detection_btn)
        
        # 模拟按钮
        self.simulate_btn = QPushButton("使用模拟进度")
        self.simulate_btn.setEnabled(False)
        self.simulate_btn.clicked.connect(self.simulate_clicked.emit)
        layout.addWidget(self.simulate_btn)
        
        return group
        
    def _create_hole_operations_group(self) -> QGroupBox:
        """创建孔位操作组"""
        group = QGroupBox("孔位操作")
        layout = QVBoxLayout(group)
        
        # 转到实时监控
        self.goto_realtime_btn = QPushButton("转到实时监控")
        self.goto_realtime_btn.setEnabled(False)
        self.goto_realtime_btn.clicked.connect(self.goto_realtime_clicked.emit)
        layout.addWidget(self.goto_realtime_btn)
        
        # 转到历史数据
        self.goto_history_btn = QPushButton("转到历史数据")
        self.goto_history_btn.setEnabled(False)
        self.goto_history_btn.clicked.connect(self.goto_history_clicked.emit)
        layout.addWidget(self.goto_history_btn)
        
        # 标记为异常
        self.mark_defective_btn = QPushButton("标记为异常")
        self.mark_defective_btn.setEnabled(False)
        self.mark_defective_btn.clicked.connect(self.mark_defective_clicked.emit)
        layout.addWidget(self.mark_defective_btn)
        
        return group
        
    def _create_progress_group(self) -> QGroupBox:
        """创建进度显示组"""
        group = QGroupBox("检测进度")
        layout = QVBoxLayout(group)
        
        # 总体进度
        layout.addWidget(QLabel("总体进度:"))
        self.overall_progress = QProgressBar()
        self.overall_progress.setTextVisible(True)
        layout.addWidget(self.overall_progress)
        
        # 当前扇形进度
        layout.addWidget(QLabel("当前扇形:"))
        self.sector_progress = QProgressBar()
        self.sector_progress.setTextVisible(True)
        layout.addWidget(self.sector_progress)
        
        return group
        
    def _create_log_group(self) -> QGroupBox:
        """创建日志显示组"""
        group = QGroupBox("操作日志")
        layout = QVBoxLayout(group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        return group
        
    def enable_detection_controls(self, enabled: bool):
        """启用/禁用检测控制按钮"""
        self.start_detection_btn.setEnabled(enabled)
        self.simulate_btn.setEnabled(enabled)
        
    def update_for_selected_hole(self, hole: HoleData):
        """根据选中的孔位更新按钮状态"""
        if hole:
            # 检查是否有数据
            has_data = hole.hole_id in ["H00001", "H00002"]
            
            self.goto_realtime_btn.setEnabled(has_data)
            self.goto_history_btn.setEnabled(has_data)
            self.mark_defective_btn.setEnabled(True)
            
            # 更新提示文本
            if has_data:
                self.goto_realtime_btn.setToolTip(f"查看 {hole.hole_id} 的实时监控数据")
                self.goto_history_btn.setToolTip(f"查看 {hole.hole_id} 的历史数据")
            else:
                self.goto_realtime_btn.setToolTip(f"{hole.hole_id} 无实时监控数据")
                self.goto_history_btn.setToolTip(f"{hole.hole_id} 无历史数据")
                
            self.mark_defective_btn.setToolTip(f"将 {hole.hole_id} 标记为异常")
        else:
            self.goto_realtime_btn.setEnabled(False)
            self.goto_history_btn.setEnabled(False)
            self.mark_defective_btn.setEnabled(False)
            
    def add_log_message(self, message: str):
        """添加日志消息"""
        self.log_text.append(message)
        # 滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def update_overall_progress(self, value: int, total: int):
        """更新总体进度"""
        if total > 0:
            percentage = int(value * 100 / total)
            self.overall_progress.setValue(percentage)
            self.overall_progress.setFormat(f"{value}/{total} ({percentage}%)")
        else:
            self.overall_progress.setValue(0)
            self.overall_progress.setFormat("0/0 (0%)")
            
    def update_sector_progress(self, value: int, total: int):
        """更新扇形进度"""
        if total > 0:
            percentage = int(value * 100 / total)
            self.sector_progress.setValue(percentage)
            self.sector_progress.setFormat(f"{value}/{total} ({percentage}%)")
        else:
            self.sector_progress.setValue(0)
            self.sector_progress.setFormat("0/0 (0%)")