"""
P4报告生成页面
管孔检测系统的报告输出界面
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

from .report_output_interface import ReportOutputInterface


class ReportGenerationPage(QWidget):
    """P4报告生成页面"""

    # 信号定义
    status_updated = Signal(str)  # 状态更新信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建报告输出界面
        self.report_interface = ReportOutputInterface(self)

        # 连接信号
        self.report_interface.status_updated.connect(self.status_updated)

        # 添加到布局
        layout.addWidget(self.report_interface)

    def get_current_status(self) -> str:
        """获取当前状态"""
        return "P4报告生成界面已就绪"