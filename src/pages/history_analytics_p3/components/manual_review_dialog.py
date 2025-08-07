"""
人工复查对话框 - 直接从重构前代码迁移
来源: /mnt/d/上位机历史版本/AIDCIS3-LFS-beifen/src/modules/evaluation/history_viewer.py
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QPushButton, QLineEdit, QComboBox,
                               QGroupBox, QTableWidget, QTableWidgetItem,
                               QSplitter, QTextEdit, QMessageBox, QFileDialog,
                               QDialog, QFormLayout, QDoubleSpinBox, QDialogButtonBox,
                               QScrollArea, QFrame, QTabWidget, QToolButton, QMenu)
from PySide6.QtCore import Qt
from datetime import datetime


def create_styled_message_box(parent, title, text, icon=QMessageBox.Information):
    """创建带有统一按钮样式的消息框"""
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(text)
    msg_box.setIcon(icon)
    
    # 添加标准按钮确保按钮存在
    msg_box.setStandardButtons(QMessageBox.Ok)
    
    # 应用白字蓝底样式
    button_style = """
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: normal;
            min-height: 20px;
            min-width: 60px;
        }
        QPushButton:hover {
            background-color: #1976D2;
        }
        QPushButton:pressed {
            background-color: #1565C0;
        }
    """
    
    # 为所有按钮应用样式
    for button in msg_box.buttons():
        button.setStyleSheet(button_style)
    
    return msg_box


class ManualReviewDialog(QDialog):
    """人工复查对话框"""

    def __init__(self, unqualified_measurements, parent=None):
        super().__init__(parent)
        self.unqualified_measurements = unqualified_measurements
        self.review_inputs = {}
        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("人工复查")
        self.setModal(True)
        self.resize(550, 500)  # 增加宽度以确保右侧信息完整显示

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 标题和说明
        title_label = QLabel("人工复查")
        layout.addWidget(title_label)

        info_label = QLabel("以下是检测为不合格的测量点，请输入人工复检的直径值：")
        layout.addWidget(info_label)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(350)  # 增加最大高度以显示更多数据

        # 创建滚动内容容器
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)

        # 为每个不合格测量点创建一行
        for i, (index, measurement) in enumerate(self.unqualified_measurements):
            # 创建一行的容器
            row_frame = QFrame()
            row_frame.setFrameStyle(QFrame.Box)

            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(8, 6, 8, 6)
            row_layout.setSpacing(8)

            # 位置信息（删除序号显示）
            position = measurement.get('position', measurement.get('depth', 0))
            position_label = QLabel(f"位置: {position:.1f}mm")
            row_layout.addWidget(position_label)

            # 原直径（显示原始数据，不四舍五入）
            original_diameter = measurement['diameter']
            original_label = QLabel(f"原直径: {original_diameter:.4f}mm")  # 使用4位小数显示原始数据
            row_layout.addWidget(original_label)

            # 复查直径输入
            review_label = QLabel("复查直径:")
            row_layout.addWidget(review_label)

            spin_box = QDoubleSpinBox()
            spin_box.setRange(10.0, 25.0)
            spin_box.setDecimals(4)  # 增加到4位小数以显示原始数据精度
            spin_box.setSingleStep(0.0001)  # 调整步长为0.0001
            spin_box.setValue(original_diameter)  # 使用原始直径数据
            spin_box.setSuffix(" mm")
            spin_box.setFixedWidth(110)  # 增加输入框宽度以显示完整数值
            row_layout.addWidget(spin_box)

            # 添加弹性空间，确保布局紧凑
            row_layout.addStretch()

            self.review_inputs[index] = spin_box
            scroll_layout.addWidget(row_frame)

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # 复查员输入区域
        reviewer_frame = QFrame()
        reviewer_layout = QHBoxLayout(reviewer_frame)

        reviewer_label = QLabel("复查员:")
        reviewer_layout.addWidget(reviewer_label)

        self.reviewer_input = QLineEdit()
        self.reviewer_input.setPlaceholderText("请输入复查员姓名")
        reviewer_layout.addWidget(self.reviewer_input)

        layout.addWidget(reviewer_frame)

        # 按钮区域
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("确定")
        button_box.button(QDialogButtonBox.Cancel).setText("取消")
        
        # 应用白字蓝底样式 - 与查询数据按钮保持一致
        button_style = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: normal;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """
        
        button_box.button(QDialogButtonBox.Ok).setStyleSheet(button_style)
        button_box.button(QDialogButtonBox.Cancel).setStyleSheet(button_style)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_review_results(self):
        """获取复查结果 - 只返回实际修改过的数据"""
        results = {}
        reviewer = self.reviewer_input.text().strip()

        if not reviewer:
            reviewer = "未知"

        review_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 只收集实际修改过的数据
        for index, spin_box in self.review_inputs.items():
            # 获取原始直径值
            original_diameter = None
            for i, (idx, measurement) in enumerate(self.unqualified_measurements):
                if idx == index:
                    original_diameter = measurement['diameter']
                    break

            current_value = spin_box.value()

            # 只有当值实际发生变化时才添加到结果中
            if original_diameter is not None and abs(current_value - original_diameter) > 0.0001:
                results[index] = {
                    'diameter': current_value,
                    'reviewer': reviewer,
                    'review_time': review_time
                }

        return results

    def accept(self):
        """重写accept方法，检查是否有实际修改"""
        review_results = self.get_review_results()

        if not review_results:
            # 没有任何修改
            msg_box = create_styled_message_box(self, "提示", "没有检测到任何修改，无需保存。", QMessageBox.Information)
            msg_box.exec()
            return

        # 检查复查员姓名
        reviewer = self.reviewer_input.text().strip()
        if not reviewer:
            msg_box = create_styled_message_box(self, "警告", "请输入复查员姓名！", QMessageBox.Warning)
            msg_box.exec()
            return

        # 有修改，继续正常流程
        super().accept()