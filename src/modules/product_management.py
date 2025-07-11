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
import os
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))
from product_model import get_product_manager
from modules.dxf_import import get_dxf_importer

class ProductManagementDialog(QDialog):
    """产品信息维护对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.product_manager = get_product_manager()
        self.dxf_importer = get_dxf_importer()
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
        
        # DXF导入按钮
        self.import_dxf_btn = QPushButton("从DXF导入")
        self.import_dxf_btn.clicked.connect(self.import_from_dxf)
        list_header_layout.addWidget(self.import_dxf_btn)
        
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
        self.dxf_render_btn = QPushButton("渲染编号")
        self.dxf_render_btn.clicked.connect(self.render_dxf_file)
        self.dxf_render_btn.setEnabled(False)
        dxf_layout.addWidget(self.dxf_path_edit)
        dxf_layout.addWidget(self.dxf_browse_btn)
        dxf_layout.addWidget(self.dxf_render_btn)
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
        
        # 更新DXF渲染按钮状态
        self.update_dxf_render_button()
    
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
        
        # 更新DXF渲染按钮状态
        self.update_dxf_render_button()
    
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
        
        # DXF渲染按钮始终可用（如果有DXF文件）
        self.update_dxf_render_button()
    
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
            QMessageBox.warning(self, "警告", "请先选择要删除的产品")
            return
        
        # 重新验证产品是否存在
        try:
            existing_product = self.product_manager.get_product_by_id(self.current_product.id)
            if not existing_product:
                QMessageBox.warning(self, "警告", f"产品 ID {self.current_product.id} 不存在，可能已被删除")
                self.load_products()  # 刷新列表
                self.cancel_edit()
                return
        except Exception as e:
            QMessageBox.critical(self, "错误", f"验证产品失败: {str(e)}")
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
                # 刷新列表以防数据不同步
                self.load_products()
                self.cancel_edit()
    
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
            self.update_dxf_render_button()
    
    def update_dxf_render_button(self):
        """更新DXF渲染按钮状态"""
        dxf_path = self.dxf_path_edit.text().strip()
        has_dxf = bool(dxf_path and os.path.exists(dxf_path))
        self.dxf_render_btn.setEnabled(has_dxf)
    
    def render_dxf_file(self):
        """渲染DXF文件"""
        dxf_path = self.dxf_path_edit.text().strip()
        
        if not dxf_path:
            QMessageBox.warning(self, "警告", "请先选择DXF文件")
            return
        
        if not os.path.exists(dxf_path):
            QMessageBox.warning(self, "警告", f"DXF文件不存在: {dxf_path}")
            return
        
        try:
            from dxf_render_dialog import DXFRenderDialog
            
            dialog = DXFRenderDialog(dxf_path, self)
            dialog.exec()
            
        except ImportError as e:
            if "matplotlib" in str(e):
                QMessageBox.critical(
                    self, "缺少依赖", 
                    "DXF渲染功能需要matplotlib库。\n请运行命令: pip install matplotlib"
                )
            else:
                QMessageBox.critical(self, "导入错误", f"模块导入失败: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开DXF渲染对话框失败: {str(e)}")
    
    def import_from_dxf(self):
        """从DXF文件导入产品信息"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要导入的DXF文件", "", "DXF文件 (*.dxf);;所有文件 (*)"
        )
        
        if not file_path:
            return
        
        try:
            # 检查DXF导入器是否可用
            if not self.dxf_importer.check_ezdxf_availability():
                QMessageBox.critical(
                    self, "错误", 
                    "DXF导入功能需要安装ezdxf库。\n请运行命令: pip install ezdxf"
                )
                return
            
            # 显示DXF导入预览对话框
            dialog = DXFImportDialog(file_path, self)
            if dialog.exec() == QDialog.Accepted:
                # 刷新产品列表
                self.load_products()
                QMessageBox.information(self, "成功", "DXF文件导入成功!")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"DXF导入失败: {str(e)}")


class DXFImportDialog(QDialog):
    """DXF导入预览对话框"""
    
    def __init__(self, dxf_file_path, parent=None):
        super().__init__(parent)
        self.dxf_file_path = dxf_file_path
        self.dxf_importer = get_dxf_importer()
        self.analysis_result = None
        self.setup_ui()
        self.load_dxf_preview()
        
    def setup_ui(self):
        """初始化界面"""
        self.setWindowTitle("DXF文件导入预览")
        self.setModal(True)
        self.resize(600, 500)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("DXF文件导入预览")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 文件信息
        file_info_group = QGroupBox("文件信息")
        file_info_layout = QGridLayout(file_info_group)
        
        file_info_layout.addWidget(QLabel("文件路径:"), 0, 0)
        self.file_path_label = QLabel(self.dxf_file_path)
        self.file_path_label.setWordWrap(True)
        file_info_layout.addWidget(self.file_path_label, 0, 1)
        
        main_layout.addWidget(file_info_group)
        
        # 分析结果
        analysis_group = QGroupBox("分析结果")
        analysis_layout = QGridLayout(analysis_group)
        
        # 分析结果标签
        self.analysis_labels = {
            'total_holes': QLabel("检测到的孔数量:"),
            'standard_diameter': QLabel("标准直径:"),
            'tolerance_estimate': QLabel("建议公差:"),
            'suggested_name': QLabel("建议产品型号:")
        }
        
        self.analysis_values = {
            'total_holes': QLabel("-"),
            'standard_diameter': QLabel("-"),
            'tolerance_estimate': QLabel("-"),
            'suggested_name': QLabel("-")
        }
        
        row = 0
        for key in ['total_holes', 'standard_diameter', 'tolerance_estimate', 'suggested_name']:
            analysis_layout.addWidget(self.analysis_labels[key], row, 0)
            analysis_layout.addWidget(self.analysis_values[key], row, 1)
            row += 1
        
        main_layout.addWidget(analysis_group)
        
        # 产品信息设置
        product_group = QGroupBox("产品信息设置")
        product_layout = QGridLayout(product_group)
        
        # 产品型号名称
        product_layout.addWidget(QLabel("型号名称*:"), 0, 0)
        self.model_name_edit = QLineEdit()
        product_layout.addWidget(self.model_name_edit, 0, 1)
        
        # 型号代码
        product_layout.addWidget(QLabel("型号代码:"), 1, 0)
        self.model_code_edit = QLineEdit()
        product_layout.addWidget(self.model_code_edit, 1, 1)
        
        # 标准直径
        product_layout.addWidget(QLabel("标准直径(mm)*:"), 2, 0)
        self.standard_diameter_spin = QDoubleSpinBox()
        self.standard_diameter_spin.setRange(0.001, 999.999)
        self.standard_diameter_spin.setDecimals(3)
        product_layout.addWidget(self.standard_diameter_spin, 2, 1)
        
        # 公差上限
        product_layout.addWidget(QLabel("公差上限(mm)*:"), 3, 0)
        self.tolerance_upper_spin = QDoubleSpinBox()
        self.tolerance_upper_spin.setRange(0.001, 99.999)
        self.tolerance_upper_spin.setDecimals(3)
        product_layout.addWidget(self.tolerance_upper_spin, 3, 1)
        
        # 公差下限
        product_layout.addWidget(QLabel("公差下限(mm)*:"), 4, 0)
        self.tolerance_lower_spin = QDoubleSpinBox()
        self.tolerance_lower_spin.setRange(-99.999, -0.001)
        self.tolerance_lower_spin.setDecimals(3)
        product_layout.addWidget(self.tolerance_lower_spin, 4, 1)
        
        # 产品描述
        product_layout.addWidget(QLabel("产品描述:"), 5, 0)
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        product_layout.addWidget(self.description_edit, 5, 1)
        
        main_layout.addWidget(product_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("导入产品")
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self.import_product)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        # 设置按钮样式
        self.import_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        
        for btn in [self.import_btn, self.cancel_btn]:
            btn.setMinimumHeight(35)
            btn.setMinimumWidth(100)
        
        button_layout.addStretch()
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        
    def load_dxf_preview(self):
        """加载DXF预览信息"""
        try:
            # 获取DXF导入预览
            preview_info = self.dxf_importer.get_import_preview(self.dxf_file_path)
            
            if 'error' in preview_info:
                QMessageBox.critical(self, "错误", f"DXF分析失败: {preview_info['error']}")
                return
            
            # 加载分析结果
            self.analysis_result = self.dxf_importer.import_from_dxf(self.dxf_file_path)
            
            # 更新分析结果显示
            self.analysis_values['total_holes'].setText(str(preview_info['total_holes']))
            self.analysis_values['standard_diameter'].setText(f"{preview_info['standard_diameter']:.2f} mm")
            self.analysis_values['tolerance_estimate'].setText(f"±{preview_info['tolerance_estimate']:.3f} mm")
            self.analysis_values['suggested_name'].setText(preview_info['suggested_model_name'])
            
            # 填充默认值到编辑框
            self.model_name_edit.setText(preview_info['suggested_model_name'])
            self.standard_diameter_spin.setValue(preview_info['standard_diameter'])
            self.tolerance_upper_spin.setValue(preview_info['tolerance_estimate'])
            self.tolerance_lower_spin.setValue(-preview_info['tolerance_estimate'])
            
            # 设置默认描述
            file_name = os.path.basename(self.dxf_file_path)
            default_description = f"从DXF文件'{file_name}'导入，检测到{preview_info['total_holes']}个孔"
            self.description_edit.setText(default_description)
            
            self.import_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"DXF预览加载失败: {str(e)}")
    
    def import_product(self):
        """导入产品"""
        try:
            # 验证表单
            if not self.validate_form():
                return
            
            # 获取表单数据
            model_name = self.model_name_edit.text().strip()
            model_code = self.model_code_edit.text().strip() or None
            standard_diameter = self.standard_diameter_spin.value()
            tolerance_upper = self.tolerance_upper_spin.value()
            tolerance_lower = self.tolerance_lower_spin.value()
            description = self.description_edit.toPlainText().strip() or None
            
            # 创建产品
            self.dxf_importer.create_product_from_dxf(
                self.analysis_result,
                self.dxf_file_path,
                model_name=model_name,
                model_code=model_code,
                tolerance_upper=tolerance_upper,
                tolerance_lower=tolerance_lower,
                description=description
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"产品导入失败: {str(e)}")
    
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