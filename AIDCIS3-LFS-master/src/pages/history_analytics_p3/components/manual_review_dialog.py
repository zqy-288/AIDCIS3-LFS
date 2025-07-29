"""
人工复查对话框
基于重构前的ManualReviewDialog完整实现
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QDoubleSpinBox, QLineEdit, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt
from datetime import datetime


class ManualReviewDialog(QDialog):
    """人工复查对话框 - 完全按照重构前的实现"""
    
    def __init__(self, unqualified_measurements, parent=None):
        super().__init__(parent)
        self.unqualified_measurements = unqualified_measurements
        self.review_inputs = {}
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面 - 完全按照重构前的布局"""
        self.setWindowTitle("人工复查")
        self.setModal(True)
        self.resize(550, 500)  # 按照重构前的尺寸
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题和说明 - 按照重构前的设计
        title_label = QLabel("人工复查")
        title_label.setObjectName("DialogTitle")
        layout.addWidget(title_label)
        
        info_label = QLabel("以下是检测为不合格的测量点，请输入人工复检的直径值：")
        info_label.setObjectName("DialogInfo")
        layout.addWidget(info_label)
        
        # 创建滚动区域 - 按照重构前的设计
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(350)  # 按照重构前的高度
        
        # 创建滚动内容容器
        scroll_widget = QFrame()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(8)
        
        # 为每个不合格测量点创建一行 - 按照重构前的实现
        for i, (index, measurement) in enumerate(self.unqualified_measurements):
            # 创建一行的容器
            row_frame = QFrame()
            row_frame.setFrameStyle(QFrame.Box)
            row_frame.setObjectName("ReviewRow")
            
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(8, 6, 8, 6)
            row_layout.setSpacing(8)
            
            # 位置信息 - 按照重构前的格式
            position = measurement.get('position', measurement.get('depth', 0))
            position_label = QLabel(f"位置: {position:.1f}mm")
            position_label.setObjectName("PositionLabel")
            row_layout.addWidget(position_label)
            
            # 原直径 - 按照重构前的精度
            original_diameter = measurement['diameter']
            original_label = QLabel(f"原直径: {original_diameter:.4f}mm")
            original_label.setObjectName("OriginalDiameterLabel")
            row_layout.addWidget(original_label)
            
            # 复查直径输入 - 按照重构前的配置
            review_label = QLabel("复查直径:")
            review_label.setObjectName("ReviewLabel")
            row_layout.addWidget(review_label)
            
            spin_box = QDoubleSpinBox()
            spin_box.setRange(10.0, 25.0)  # 按照重构前的范围
            spin_box.setDecimals(4)  # 按照重构前的精度
            spin_box.setSingleStep(0.0001)  # 按照重构前的步长
            spin_box.setValue(original_diameter)  # 使用原始直径数据
            spin_box.setSuffix(" mm")
            spin_box.setFixedWidth(110)  # 按照重构前的宽度
            spin_box.setObjectName("ReviewSpinBox")
            row_layout.addWidget(spin_box)
            
            # 添加弹性空间
            row_layout.addStretch()
            
            self.review_inputs[index] = spin_box
            scroll_layout.addWidget(row_frame)
            
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # 复查员输入区域 - 按照重构前的设计
        reviewer_frame = QFrame()
        reviewer_frame.setObjectName("ReviewerFrame")
        reviewer_layout = QHBoxLayout(reviewer_frame)
        
        reviewer_label = QLabel("复查员:")
        reviewer_label.setObjectName("ReviewerLabel")
        reviewer_layout.addWidget(reviewer_label)
        
        self.reviewer_input = QLineEdit()
        self.reviewer_input.setPlaceholderText("请输入复查员姓名")
        self.reviewer_input.setObjectName("ReviewerInput")
        reviewer_layout.addWidget(self.reviewer_input)
        
        layout.addWidget(reviewer_frame)
        
        # 按钮区域 - 按照重构前的设计
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("确定")
        button_box.button(QDialogButtonBox.Cancel).setText("取消")
        button_box.setObjectName("DialogButtonBox")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_review_results(self):
        """获取复查结果 - 完全按照重构前的实现"""
        results = {}
        reviewer = self.reviewer_input.text().strip()
        
        if not reviewer:
            reviewer = "未知"
            
        review_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 只收集实际修改过的数据 - 按照重构前的逻辑
        for index, spin_box in self.review_inputs.items():
            # 获取原始直径值
            original_diameter = None
            for i, (idx, measurement) in enumerate(self.unqualified_measurements):
                if idx == index:
                    original_diameter = measurement['diameter']
                    break
                    
            current_value = spin_box.value()
            
            # 只有当值实际发生变化时才添加到结果中 - 按照重构前的阈值
            if original_diameter is not None and abs(current_value - original_diameter) > 0.0001:
                results[index] = {
                    'diameter': current_value,
                    'reviewer': reviewer,
                    'review_time': review_time
                }
                
        return results
        
    def accept(self):
        """重写accept方法，检查是否有实际修改 - 按照重构前的验证逻辑"""
        review_results = self.get_review_results()
        
        if not review_results:
            # 没有任何修改
            QMessageBox.information(self, "提示", "没有检测到任何修改，无需保存。")
            return
            
        # 检查复查员姓名
        reviewer = self.reviewer_input.text().strip()
        if not reviewer:
            QMessageBox.warning(self, "警告", "请输入复查员姓名！")
            return
            
        # 有修改，继续正常流程
        super().accept()
