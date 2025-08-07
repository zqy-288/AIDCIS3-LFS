"""
状态面板组件 - 高内聚低耦合设计
职责：专门负责左侧状态和控制面板的显示和交互
基于重构前代码完全恢复左侧面板功能
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from typing import List, Dict, Optional
import logging


class StatusPanelWidget(QWidget):
    """
    状态面板组件 - 高内聚设计
    职责：
    1. 显示光谱共振历史数据查看控制
    2. 管理工件ID和孔位ID选择
    3. 提供查询、导出、人工复查按钮
    4. 显示当前状态信息
    """
    
    # 信号定义
    query_requested = Signal(str)        # 查询请求信号 (hole_id)
    export_requested = Signal()          # 导出请求信号
    review_requested = Signal()          # 人工复查请求信号
    workpiece_changed = Signal(str)      # 工件ID变更信号 (workpiece_id)
    hole_selected = Signal(str)          # 孔位选择信号 (hole_id)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 当前状态
        self.available_holes = []
        self.qualified_holes = []
        self.unqualified_holes = []
        
        # 设置界面
        self.setup_ui()
        
        self.logger.info("状态面板组件初始化完成")
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 创建主分组框 - 基于重构前的样式
        main_group = QGroupBox("光谱共振历史数据查看")
        main_group.setStyleSheet("""
            QGroupBox {
                font-size: 12px;
                font-weight: bold;
                color: #D3D8E0;
                border: 1px solid #505869;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #313642;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        main_layout = QVBoxLayout(main_group)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 20, 15, 15)
        
        # 创建各个子组件
        self.create_data_filter_section(main_layout)
        self.create_operation_buttons(main_layout)
        self.create_current_status_section(main_layout)
        
        layout.addWidget(main_group)
        layout.addStretch()  # 添加弹性空间
    
    def create_data_filter_section(self, parent_layout):
        """创建数据筛选区域"""
        filter_group = QGroupBox("数据筛选")
        filter_group.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                color: #D3D8E0;
                border: 1px solid #505869;
                border-radius: 3px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: #2a2d35;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px 0 3px;
            }
        """)
        
        filter_layout = QFormLayout(filter_group)
        filter_layout.setSpacing(10)
        filter_layout.setContentsMargins(10, 15, 10, 10)
        
        # 工件ID输入 - 基于重构前的显示框设计
        self.workpiece_input = QLineEdit()
        self.workpiece_input.setText("CAP1000")  # 默认值
        self.workpiece_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2d35;
                border: 1px solid #505869;
                padding: 5px;
                color: #D3D8E0;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #4A90E2;
            }
        """)
        self.workpiece_input.textChanged.connect(self.on_workpiece_changed)
        filter_layout.addRow("工件ID:", self.workpiece_input)
        
        # 合格孔ID选择
        self.qualified_combo = QComboBox()
        self.qualified_combo.setStyleSheet("""
            QComboBox {
                background-color: #2a2d35;
                border: 1px solid #505869;
                padding: 5px;
                color: #D3D8E0;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #3a3d45;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #2a2d35;
                border: 1px solid #505869;
                color: #D3D8E0;
                selection-background-color: #4A90E2;
            }
        """)
        self.qualified_combo.currentTextChanged.connect(self.on_qualified_hole_changed)
        filter_layout.addRow("合格孔ID:", self.qualified_combo)
        
        # 不合格孔ID选择
        self.unqualified_combo = QComboBox()
        self.unqualified_combo.setStyleSheet(self.qualified_combo.styleSheet())
        self.unqualified_combo.currentTextChanged.connect(self.on_unqualified_hole_changed)
        filter_layout.addRow("不合格孔ID:", self.unqualified_combo)
        
        parent_layout.addWidget(filter_group)
    
    def create_operation_buttons(self, parent_layout):
        """创建操作按钮区域"""
        button_group = QGroupBox("操作命令")
        button_group.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                color: #D3D8E0;
                border: 1px solid #505869;
                border-radius: 3px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: #2a2d35;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px 0 3px;
            }
        """)
        
        button_layout = QVBoxLayout(button_group)
        button_layout.setSpacing(8)
        button_layout.setContentsMargins(10, 15, 10, 10)
        
        # 按钮样式 - 基于重构前的蓝色按钮样式和10px字体大小
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
        
        # 查询数据按钮
        self.query_button = QPushButton("查询数据")
        self.query_button.setStyleSheet(button_style)
        self.query_button.clicked.connect(self.on_query_clicked)
        button_layout.addWidget(self.query_button)
        
        # 导出数据按钮
        self.export_button = QPushButton("导出数据")
        self.export_button.setStyleSheet(button_style)
        self.export_button.setEnabled(False)  # 初始禁用
        self.export_button.clicked.connect(self.on_export_clicked)
        button_layout.addWidget(self.export_button)
        
        # 人工复查按钮
        self.review_button = QPushButton("人工复查")
        self.review_button.setStyleSheet(button_style)
        self.review_button.setEnabled(False)  # 初始禁用
        self.review_button.clicked.connect(self.on_review_clicked)
        button_layout.addWidget(self.review_button)
        
        parent_layout.addWidget(button_group)
    
    def create_current_status_section(self, parent_layout):
        """创建当前状态区域"""
        status_group = QGroupBox("当前状态")
        status_group.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                color: #D3D8E0;
                border: 1px solid #505869;
                border-radius: 3px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: #2a2d35;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px 0 3px;
            }
        """)
        
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(8)
        status_layout.setContentsMargins(10, 15, 10, 10)
        
        # 状态显示标签 - 基于重构前的样式
        self.status_label = QLabel("请选择孔位加载数据")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #1a1d23;
                border: 1px solid #505869;
                padding: 10px;
                color: #D3D8E0;
                border-radius: 3px;
                font-size: 10px;
                min-height: 60px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(status_group)
    
    def update_available_holes(self, holes: List[str]):
        """更新可用孔位列表"""
        self.available_holes = holes
        
        # 简化分类逻辑 - 基于重构前的处理方式
        self.qualified_holes = holes.copy()  # 假设所有孔位都是合格的
        self.unqualified_holes = []          # 不合格孔位为空（实际应根据数据判断）
        
        self.update_combo_boxes()
        self.logger.info(f"更新可用孔位: 共 {len(holes)} 个孔位")
    
    def update_combo_boxes(self):
        """更新下拉框选项"""
        # 更新合格孔位下拉框
        self.qualified_combo.clear()
        self.qualified_combo.addItem("请选择合格孔ID")
        for hole in self.qualified_holes:
            self.qualified_combo.addItem(hole)
        
        # 更新不合格孔位下拉框
        self.unqualified_combo.clear()
        self.unqualified_combo.addItem("请选择不合格孔ID")
        for hole in self.unqualified_holes:
            self.unqualified_combo.addItem(hole)
    
    def on_workpiece_changed(self, workpiece_id: str):
        """处理工件ID变更"""
        self.workpiece_changed.emit(workpiece_id.strip())
    
    def on_qualified_hole_changed(self, hole_id: str):
        """处理合格孔位选择变更"""
        if hole_id and hole_id != "请选择合格孔ID":
            # 清空不合格孔位选择
            self.unqualified_combo.blockSignals(True)
            self.unqualified_combo.setCurrentText("请选择不合格孔ID")
            self.unqualified_combo.blockSignals(False)
            
            self.hole_selected.emit(hole_id)
    
    def on_unqualified_hole_changed(self, hole_id: str):
        """处理不合格孔位选择变更"""
        if hole_id and hole_id != "请选择不合格孔ID":
            # 清空合格孔位选择
            self.qualified_combo.blockSignals(True)
            self.qualified_combo.setCurrentText("请选择合格孔ID")
            self.qualified_combo.blockSignals(False)
            
            self.hole_selected.emit(hole_id)
    
    def on_query_clicked(self):
        """处理查询按钮点击"""
        # 获取选择的孔位ID
        qualified_hole = self.qualified_combo.currentText()
        unqualified_hole = self.unqualified_combo.currentText()
        
        selected_hole = ""
        if qualified_hole and qualified_hole != "请选择合格孔ID":
            selected_hole = qualified_hole
        elif unqualified_hole and unqualified_hole != "请选择不合格孔ID":
            selected_hole = unqualified_hole
        
        if not selected_hole:
            QMessageBox.warning(self, "警告", "请选择合格孔ID或不合格孔ID")
            return
        
        self.query_requested.emit(selected_hole)
    
    def on_export_clicked(self):
        """处理导出按钮点击"""
        self.export_requested.emit()
    
    def on_review_clicked(self):
        """处理人工复查按钮点击"""
        self.review_requested.emit()
    
    def update_status(self, status_text: str):
        """更新状态显示"""
        self.status_label.setText(status_text)
        self.logger.debug(f"状态更新: {status_text}")
    
    def set_buttons_enabled(self, query_enabled: bool, export_enabled: bool, review_enabled: bool):
        """设置按钮启用状态"""
        self.query_button.setEnabled(query_enabled)
        self.export_button.setEnabled(export_enabled)
        self.review_button.setEnabled(review_enabled)
    
    def enable_data_operations(self, enabled: bool):
        """启用/禁用数据操作按钮（导出和复查）"""
        self.export_button.setEnabled(enabled)
        self.review_button.setEnabled(enabled)
    
    def get_current_workpiece_id(self) -> str:
        """获取当前工件ID"""
        return self.workpiece_input.text().strip()
    
    def get_selected_hole_id(self) -> str:
        """获取当前选择的孔位ID"""
        qualified_hole = self.qualified_combo.currentText()
        unqualified_hole = self.unqualified_combo.currentText()
        
        if qualified_hole and qualified_hole != "请选择合格孔ID":
            return qualified_hole
        elif unqualified_hole and unqualified_hole != "请选择不合格孔ID":
            return unqualified_hole
        
        return ""
    
    def clear_selections(self):
        """清除所有选择"""
        self.qualified_combo.setCurrentText("请选择合格孔ID")
        self.unqualified_combo.setCurrentText("请选择不合格孔ID")
        self.update_status("请选择孔位加载数据")
        self.enable_data_operations(False)
    
    def set_workpiece_id(self, workpiece_id: str):
        """设置工件ID"""
        self.workpiece_input.setText(workpiece_id)
    
    def classify_holes_by_quality(self, holes_with_quality: Dict[str, bool]):
        """
        根据质量状态分类孔位
        holes_with_quality: {hole_id: is_qualified}
        """
        self.qualified_holes = [hole_id for hole_id, qualified in holes_with_quality.items() if qualified]
        self.unqualified_holes = [hole_id for hole_id, qualified in holes_with_quality.items() if not qualified]
        
        self.update_combo_boxes()
        self.logger.info(f"孔位分类完成: 合格 {len(self.qualified_holes)} 个, 不合格 {len(self.unqualified_holes)} 个")