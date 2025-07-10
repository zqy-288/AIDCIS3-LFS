"""
产品信息维护后台管理界面
支持产品型号的新增、修改、删除等操作
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QDoubleSpinBox, QTextEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QGroupBox, QGridLayout, QFormLayout,
                             QCheckBox, QFileDialog, QComboBox, QSpacerItem,
                             QSizePolicy, QSplitter, QTabWidget, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
from models.product_model import get_product_manager

class ProductManagementDialog(QDialog):
    """产品信息维护对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.product_manager = get_product_manager()
        self.current_product = None
        self.setup_ui()
        self.load_products()
        
    def setup_ui(self):
        """初始化界面"""
        self.setWindowTitle("产品信息维护")
        self.setModal(True)
        self.resize(1000, 700)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("产品信息维护")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：产品列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 产品列表标题和操作按钮
        list_header_layout = QHBoxLayout()
        list_title = QLabel("产品列表")
        list_title.setFont(QFont("", 12, QFont.Bold))
        list_header_layout.addWidget(list_title)
        
        list_header_layout.addStretch()
        
        # 新增按钮
        self.add_btn = QPushButton("新增产品")
        self.add_btn.clicked.connect(self.add_product)
        list_header_layout.addWidget(self.add_btn)
        
        left_layout.addLayout(list_header_layout)
        
        # 产品列表表格
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(6)
        self.product_table.setHorizontalHeaderLabels([
            "型号名称", "标准直径", "公差范围", "状态", "创建时间", "操作"
        ])
        
        # 设置表格列宽
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        
        self.product_table.setColumnWidth(0, 120)
        self.product_table.setColumnWidth(1, 80)
        self.product_table.setColumnWidth(2, 100)
        self.product_table.setColumnWidth(3, 60)
        self.product_table.setColumnWidth(5, 80)
        
        # 设置选择模式
        self.product_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.product_table.setSelectionMode(QTableWidget.SingleSelection)
        self.product_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        left_layout.addWidget(self.product_table)
        
        # 右侧：产品详情编辑
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 详情标题
        detail_title = QLabel("产品详情")
        detail_title.setFont(QFont("", 12, QFont.Bold))
        right_layout.addWidget(detail_title)
        
        # 创建表单
        form_group = QGroupBox("产品信息")
        form_layout = QFormLayout(form_group)
        
        # 表单字段
        self.model_name_edit = QLineEdit()
        self.model_name_edit.setPlaceholderText("请输入产品型号名称")
        form_layout.addRow("型号名称*:", self.model_name_edit)
        
        self.model_code_edit = QLineEdit()
        self.model_code_edit.setPlaceholderText("请输入产品型号代码")
        form_layout.addRow("型号代码:", self.model_code_edit)
        
        self.standard_diameter_spin = QDoubleSpinBox()
        self.standard_diameter_spin.setRange(0.001, 999.999)
        self.standard_diameter_spin.setDecimals(3)
        self.standard_diameter_spin.setSuffix(" mm")
        form_layout.addRow("标准直径*:", self.standard_diameter_spin)
        
        self.tolerance_upper_spin = QDoubleSpinBox()
        self.tolerance_upper_spin.setRange(0.001, 99.999)
        self.tolerance_upper_spin.setDecimals(3)
        self.tolerance_upper_spin.setSuffix(" mm")
        form_layout.addRow("公差上限*:", self.tolerance_upper_spin)
        
        self.tolerance_lower_spin = QDoubleSpinBox()
        self.tolerance_lower_spin.setRange(-99.999, -0.001)
        self.tolerance_lower_spin.setDecimals(3)
        self.tolerance_lower_spin.setSuffix(" mm")
        form_layout.addRow("公差下限*:", self.tolerance_lower_spin)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("请输入产品描述")
        form_layout.addRow("产品描述:", self.description_edit)
        
        # DXF文件路径
        dxf_layout = QHBoxLayout()
        self.dxf_path_edit = QLineEdit()
        self.dxf_path_edit.setPlaceholderText("可选择关联的DXF文件")
        self.dxf_browse_btn = QPushButton("浏览")
        self.dxf_browse_btn.clicked.connect(self.browse_dxf_file)
        dxf_layout.addWidget(self.dxf_path_edit)
        dxf_layout.addWidget(self.dxf_browse_btn)
        form_layout.addRow("DXF文件:", dxf_layout)
        
        self.is_active_check = QCheckBox("启用该产品型号")
        self.is_active_check.setChecked(True)
        form_layout.addRow("状态:", self.is_active_check)
        
        right_layout.addWidget(form_group)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_product)
        self.save_btn.setEnabled(False)
        
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self.edit_product)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self.delete_product)
        self.delete_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_edit)
        self.cancel_btn.setEnabled(False)
        
        # 设置按钮样式
        self.save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        self.delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        
        for btn in [self.save_btn, self.edit_btn, self.delete_btn, self.cancel_btn]:
            btn.setMinimumHeight(35)
            btn.setMinimumWidth(80)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        right_layout.addLayout(button_layout)
        right_layout.addStretch()
        
        # 添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        
        # 底部按钮
        bottom_layout = QHBoxLayout()
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setMinimumHeight(35)
        self.close_btn.setMinimumWidth(100)
        
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(bottom_layout)
        
        # 设置初始状态
        self.set_form_enabled(False)
        
    def load_products(self):
        """加载产品列表"""
        try:
            products = self.product_manager.get_all_products(active_only=False)
            self.product_table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                # 型号名称
                name_item = QTableWidgetItem(product.model_name)
                name_item.setData(Qt.UserRole, product)
                self.product_table.setItem(row, 0, name_item)
                
                # 标准直径
                diameter_item = QTableWidgetItem(f"{product.standard_diameter:.3f}")
                self.product_table.setItem(row, 1, diameter_item)
                
                # 公差范围
                tolerance_item = QTableWidgetItem(product.tolerance_range)
                self.product_table.setItem(row, 2, tolerance_item)
                
                # 状态
                status_item = QTableWidgetItem("启用" if product.is_active else "停用")
                status_item.setTextAlignment(Qt.AlignCenter)
                if product.is_active:
                    status_item.setBackground(Qt.green)
                else:
                    status_item.setBackground(Qt.red)
                self.product_table.setItem(row, 3, status_item)
                
                # 创建时间
                created_item = QTableWidgetItem(product.created_at.strftime("%Y-%m-%d %H:%M") if product.created_at else "")
                self.product_table.setItem(row, 4, created_item)
                
                # 操作按钮
                action_item = QTableWidgetItem("详情")
                action_item.setTextAlignment(Qt.AlignCenter)
                self.product_table.setItem(row, 5, action_item)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载产品列表失败: {str(e)}")
    
    def on_selection_changed(self):
        """处理选择变化"""
        current_row = self.product_table.currentRow()
        if current_row >= 0:
            name_item = self.product_table.item(current_row, 0)
            if name_item:
                product = name_item.data(Qt.UserRole)
                self.current_product = product
                self.load_product_details(product)
                self.edit_btn.setEnabled(True)
                self.delete_btn.setEnabled(True)
        else:
            self.current_product = None
            self.clear_form()
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
    
    def load_product_details(self, product):
        """加载产品详情到表单"""
        self.model_name_edit.setText(product.model_name)
        self.model_code_edit.setText(product.model_code or "")
        self.standard_diameter_spin.setValue(product.standard_diameter)
        self.tolerance_upper_spin.setValue(product.tolerance_upper)
        self.tolerance_lower_spin.setValue(product.tolerance_lower)
        self.description_edit.setText(product.description or "")
        self.dxf_path_edit.setText(product.dxf_file_path or "")
        self.is_active_check.setChecked(product.is_active)
    
    def clear_form(self):
        """清空表单"""
        self.model_name_edit.clear()
        self.model_code_edit.clear()
        self.standard_diameter_spin.setValue(0.0)
        self.tolerance_upper_spin.setValue(0.0)
        self.tolerance_lower_spin.setValue(0.0)
        self.description_edit.clear()
        self.dxf_path_edit.clear()
        self.is_active_check.setChecked(True)
    
    def set_form_enabled(self, enabled):
        """设置表单是否可编辑"""
        self.model_name_edit.setEnabled(enabled)
        self.model_code_edit.setEnabled(enabled)
        self.standard_diameter_spin.setEnabled(enabled)
        self.tolerance_upper_spin.setEnabled(enabled)
        self.tolerance_lower_spin.setEnabled(enabled)
        self.description_edit.setEnabled(enabled)
        self.dxf_path_edit.setEnabled(enabled)
        self.dxf_browse_btn.setEnabled(enabled)
        self.is_active_check.setEnabled(enabled)
    
    def add_product(self):
        """新增产品"""
        self.current_product = None
        self.clear_form()
        self.set_form_enabled(True)
        self.save_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.add_btn.setEnabled(False)
    
    def edit_product(self):
        """编辑产品"""
        if self.current_product:
            self.set_form_enabled(True)
            self.save_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.add_btn.setEnabled(False)
    
    def save_product(self):
        """保存产品"""
        try:
            # 验证表单
            if not self.validate_form():
                return
            
            model_name = self.model_name_edit.text().strip()
            model_code = self.model_code_edit.text().strip() or None
            standard_diameter = self.standard_diameter_spin.value()
            tolerance_upper = self.tolerance_upper_spin.value()
            tolerance_lower = self.tolerance_lower_spin.value()
            description = self.description_edit.toPlainText().strip() or None
            dxf_file_path = self.dxf_path_edit.text().strip() or None
            is_active = self.is_active_check.isChecked()
            
            if self.current_product:
                # 更新现有产品
                self.product_manager.update_product(
                    self.current_product.id,
                    model_name=model_name,
                    model_code=model_code,
                    standard_diameter=standard_diameter,
                    tolerance_upper=tolerance_upper,
                    tolerance_lower=tolerance_lower,
                    description=description,
                    dxf_file_path=dxf_file_path,
                    is_active=is_active
                )
                QMessageBox.information(self, "成功", "产品信息更新成功!")
            else:
                # 创建新产品
                self.product_manager.create_product(
                    model_name=model_name,
                    standard_diameter=standard_diameter,
                    tolerance_upper=tolerance_upper,
                    tolerance_lower=tolerance_lower,
                    model_code=model_code,
                    description=description,
                    dxf_file_path=dxf_file_path
                )
                QMessageBox.information(self, "成功", "产品创建成功!")
            
            # 刷新列表
            self.load_products()
            self.cancel_edit()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def validate_form(self):
        """验证表单"""
        if not self.model_name_edit.text().strip():
            QMessageBox.warning(self, "警告", "请输入产品型号名称")
            self.model_name_edit.setFocus()
            return False
        
        if self.standard_diameter_spin.value() <= 0:
            QMessageBox.warning(self, "警告", "标准直径必须大于0")
            self.standard_diameter_spin.setFocus()
            return False
        
        if self.tolerance_upper_spin.value() <= 0:
            QMessageBox.warning(self, "警告", "公差上限必须大于0")
            self.tolerance_upper_spin.setFocus()
            return False
        
        if self.tolerance_lower_spin.value() >= 0:
            QMessageBox.warning(self, "警告", "公差下限必须小于0")
            self.tolerance_lower_spin.setFocus()
            return False
        
        return True
    
    def delete_product(self):
        """删除产品"""
        if not self.current_product:
            return
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除产品型号 '{self.current_product.model_name}' 吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.product_manager.delete_product(self.current_product.id)
                QMessageBox.information(self, "成功", "产品删除成功!")
                self.load_products()
                self.cancel_edit()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
    
    def cancel_edit(self):
        """取消编辑"""
        self.set_form_enabled(False)
        self.save_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.add_btn.setEnabled(True)
        
        if self.current_product:
            self.load_product_details(self.current_product)
            self.edit_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.clear_form()
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
    
    def browse_dxf_file(self):
        """浏览DXF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择DXF文件", "", "DXF文件 (*.dxf);;所有文件 (*)"
        )
        if file_path:
            self.dxf_path_edit.setText(file_path)