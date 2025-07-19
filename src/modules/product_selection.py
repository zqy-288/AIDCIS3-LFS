"""
产品型号选择界面
替代原有的DXF文件加载功能，提供产品型号选择功能
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QTextEdit, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox,
                             QGroupBox, QGridLayout, QFrame, QSpacerItem,
                             QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))
from product_model import get_product_manager

class ProductSelectionDialog(QDialog):
    """产品型号选择对话框"""
    
    product_selected = Signal(object)  # 产品选择信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.product_manager = get_product_manager()
        self.selected_product = None
        self.setup_ui()
        self.load_products()
        
    def setup_ui(self):
        """初始化界面"""
        self.setWindowTitle("产品型号选择")
        self.setModal(True)
        self.resize(800, 600)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("选择产品型号")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 产品选择区域
        selection_group = QGroupBox("产品型号列表")
        selection_layout = QVBoxLayout(selection_group)
        
        # 产品列表表格
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)
        self.product_table.setHorizontalHeaderLabels([
            "型号名称", "标准直径(mm)", "公差范围", "描述", "状态"
        ])
        
        # 设置表格列宽
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.product_table.setColumnWidth(0, 120)
        self.product_table.setColumnWidth(1, 100)
        self.product_table.setColumnWidth(2, 120)
        self.product_table.setColumnWidth(4, 60)
        
        # 设置选择模式
        self.product_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.product_table.setSelectionMode(QTableWidget.SingleSelection)
        self.product_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        selection_layout.addWidget(self.product_table)
        main_layout.addWidget(selection_group)
        
        # 产品详情区域
        details_group = QGroupBox("产品详情")
        details_layout = QGridLayout(details_group)
        
        # 详情标签
        self.detail_labels = {
            'model_name': QLabel("型号名称:"),
            'model_code': QLabel("型号代码:"),
            'standard_diameter': QLabel("标准直径:"),
            'tolerance_range': QLabel("公差范围:"),
            'diameter_range': QLabel("直径范围:"),
            'description': QLabel("产品描述:")
        }
        
        self.detail_values = {
            'model_name': QLabel("-"),
            'model_code': QLabel("-"),
            'standard_diameter': QLabel("-"),
            'tolerance_range': QLabel("-"),
            'diameter_range': QLabel("-"),
            'description': QTextEdit()
        }
        
        # 设置描述文本框为只读
        self.detail_values['description'].setReadOnly(True)
        self.detail_values['description'].setMaximumHeight(60)
        
        # 布局详情控件
        row = 0
        for key in ['model_name', 'model_code', 'standard_diameter', 'tolerance_range', 'diameter_range']:
            details_layout.addWidget(self.detail_labels[key], row, 0)
            details_layout.addWidget(self.detail_values[key], row, 1)
            row += 1
        
        details_layout.addWidget(self.detail_labels['description'], row, 0)
        details_layout.addWidget(self.detail_values['description'], row, 1)
        
        main_layout.addWidget(details_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 管理按钮
        self.manage_btn = QPushButton("产品信息维护")
        self.manage_btn.clicked.connect(self.open_product_management)
        
        # 刷新按钮
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self.load_products)
        
        # 确定和取消按钮
        self.select_btn = QPushButton("选择该产品")
        self.select_btn.setEnabled(False)
        self.select_btn.clicked.connect(self.select_product)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        # 设置按钮样式
        for btn in [self.select_btn, self.cancel_btn]:
            btn.setMinimumHeight(35)
            btn.setMinimumWidth(100)
        
        self.select_btn.setStyleSheet("QPushButton { background-color: #2ECC71; color: white; font-weight: bold; }")
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #313642; color: white; }")
        
        # 添加按钮到布局
        button_layout.addWidget(self.manage_btn)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.select_btn)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        
    def load_products(self):
        """加载产品列表"""
        try:
            products = self.product_manager.get_all_products(active_only=True)
            self.product_table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                # 型号名称
                name_item = QTableWidgetItem(product.model_name)
                name_item.setData(Qt.UserRole, product)
                self.product_table.setItem(row, 0, name_item)
                
                # 标准直径
                diameter_item = QTableWidgetItem(f"{product.standard_diameter:.2f}")
                self.product_table.setItem(row, 1, diameter_item)
                
                # 公差范围
                tolerance_item = QTableWidgetItem(product.tolerance_range)
                self.product_table.setItem(row, 2, tolerance_item)
                
                # 描述
                description_item = QTableWidgetItem(product.description or "")
                self.product_table.setItem(row, 3, description_item)
                
                # 状态
                status_item = QTableWidgetItem("启用" if product.is_active else "停用")
                status_item.setTextAlignment(Qt.AlignCenter)
                self.product_table.setItem(row, 4, status_item)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载产品列表失败: {str(e)}")
    
    def on_selection_changed(self):
        """处理选择变化"""
        current_row = self.product_table.currentRow()
        if current_row >= 0:
            name_item = self.product_table.item(current_row, 0)
            if name_item:
                product = name_item.data(Qt.UserRole)
                self.selected_product = product
                self.update_product_details(product)
                self.select_btn.setEnabled(True)
        else:
            self.selected_product = None
            self.clear_product_details()
            self.select_btn.setEnabled(False)
    
    def update_product_details(self, product):
        """更新产品详情显示"""
        self.detail_values['model_name'].setText(product.model_name)
        self.detail_values['model_code'].setText(product.model_code or "-")
        self.detail_values['standard_diameter'].setText(f"{product.standard_diameter:.3f} mm")
        self.detail_values['tolerance_range'].setText(product.tolerance_range)
        
        min_dia, max_dia = product.diameter_range
        self.detail_values['diameter_range'].setText(f"{min_dia:.3f} - {max_dia:.3f} mm")
        self.detail_values['description'].setText(product.description or "")
    
    def clear_product_details(self):
        """清空产品详情显示"""
        for key, widget in self.detail_values.items():
            if key == 'description':
                widget.setText("")
            else:
                widget.setText("-")
    
    def select_product(self):
        """选择产品"""
        if not self.selected_product:
            QMessageBox.warning(self, "警告", "请先选择一个产品型号")
            return
        
        # 重新验证产品是否存在
        try:
            existing_product = self.product_manager.get_product_by_id(self.selected_product.id)
            if not existing_product:
                QMessageBox.warning(self, "警告", f"产品 '{self.selected_product.model_name}' 不存在，可能已被删除")
                self.load_products()  # 刷新列表
                return
                
            # 检查产品是否仍然启用
            if not existing_product.is_active:
                QMessageBox.warning(self, "警告", f"产品 '{existing_product.model_name}' 已被停用，无法选择")
                self.load_products()  # 刷新列表
                return
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"验证产品失败: {str(e)}")
            return
        
        # 使用最新的产品数据
        self.selected_product = existing_product
        self.product_selected.emit(existing_product)
        self.accept()
    
    def get_selected_product(self):
        """获取选中的产品"""
        return self.selected_product
    
    def open_product_management(self):
        """打开产品信息维护界面"""
        from modules.product_management import ProductManagementDialog
        dialog = ProductManagementDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # 刷新产品列表
            self.load_products()


class ProductQuickSelector:
    """产品快速选择器"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.product_manager = get_product_manager()
    
    def show_selection_dialog(self):
        """显示产品选择对话框"""
        dialog = ProductSelectionDialog(self.parent)
        return dialog
    
    def get_active_products(self):
        """获取启用的产品列表"""
        return self.product_manager.get_all_products(active_only=True)
    
    def get_product_by_name(self, model_name):
        """根据名称获取产品"""
        return self.product_manager.get_product_by_name(model_name)