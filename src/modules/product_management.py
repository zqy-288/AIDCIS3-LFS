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
        self.resize(900, 600)  # 减小窗口大小
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # 设置紧凑的边距
        
        # 标题
        title_label = QLabel("产品信息维护")
        title_font = QFont()
        title_font.setPointSize(18)  # 增大标题字体
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("padding: 5px; color: #D3D8E0;")  # 减小padding
        main_layout.addWidget(title_label)
        main_layout.setSpacing(5)  # 减小组件间距
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：产品列表
        left_container = QWidget()
        left_container.setObjectName("leftContainer")
        left_container.setStyleSheet("""
            #leftContainer {
                border: 1px solid #404552;
                border-radius: 5px;
                background-color: #313642;
                padding: 5px;
            }
        """)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # 产品列表标题和操作按钮
        list_header_layout = QHBoxLayout()
        list_title = QLabel("产品列表")
        list_title.setFont(QFont("", 14, QFont.Bold))  # 增大标题字体
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
        right_container = QWidget()
        right_container.setObjectName("rightContainer")
        right_container.setStyleSheet("""
            #rightContainer {
                border: 1px solid #404552;
                border-radius: 5px;
                background-color: #313642;
                padding: 5px;
            }
        """)
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        # 详情标题
        detail_title = QLabel("产品详情")
        detail_title.setFont(QFont("", 14, QFont.Bold))  # 增大标题字体
        right_layout.addWidget(detail_title)
        
        # 创建表单
        form_group = QGroupBox("产品信息")
        form_layout = QFormLayout(form_group)
        form_layout.setContentsMargins(10, 10, 10, 10)  # 减小表单边距
        form_layout.setSpacing(8)  # 减小行间距
        
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
        self.description_edit.setMaximumHeight(60)  # 减小描述框高度
        self.description_edit.setPlaceholderText("请输入产品描述")
        form_layout.addRow("产品描述:", self.description_edit)
        
        # DXF文件路径
        dxf_layout = QHBoxLayout()
        self.dxf_path_edit = QLineEdit()
        self.dxf_path_edit.setPlaceholderText("可选择关联的DXF文件")
        self.dxf_browse_btn = QPushButton("浏览")
        self.dxf_browse_btn.clicked.connect(self.browse_dxf_file)
        self.dxf_import_btn = QPushButton("从DXF导入")
        self.dxf_import_btn.clicked.connect(self.import_from_dxf)
        self.dxf_render_btn = QPushButton("渲染编号")
        self.dxf_render_btn.clicked.connect(self.render_dxf_file)
        self.dxf_render_btn.setEnabled(False)
        dxf_layout.addWidget(self.dxf_path_edit)
        dxf_layout.addWidget(self.dxf_browse_btn)
        dxf_layout.addWidget(self.dxf_import_btn)
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
        self.save_btn.setStyleSheet("QPushButton { background-color: #2ECC71; color: white; font-weight: bold; }")
        self.delete_btn.setStyleSheet("QPushButton { background-color: #313642; color: white; }")
        
        for btn in [self.save_btn, self.edit_btn, self.delete_btn, self.cancel_btn]:
            btn.setMinimumHeight(35)
            btn.setMinimumWidth(80)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        
        right_layout.addLayout(button_layout)
        # 移除addStretch()以减少底部空白
        
        # 添加到分割器
        splitter.addWidget(left_container)
        splitter.addWidget(right_container)
        splitter.setSizes([500, 400])  # 调整比例，减少右侧空白
        
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
        """删除产品（包含相关文件的选择性删除）"""
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
        
        # 收集相关文件信息
        related_files = self._collect_related_files(existing_product)
        
        # 显示删除确认对话框（带文件清单）
        delete_choice = self._show_delete_confirmation_dialog(existing_product, related_files)
        
        if delete_choice in ['database_only', 'database_and_files']:
            try:
                # 删除数据库记录
                self.product_manager.delete_product(self.current_product.id)
                
                # 根据用户选择删除相关文件
                if delete_choice == 'database_and_files':
                    deleted_files = self._delete_related_files(related_files)
                    if deleted_files:
                        QMessageBox.information(
                            self, "删除成功", 
                            f"产品删除成功!\n同时删除了 {len(deleted_files)} 个相关文件。"
                        )
                    else:
                        QMessageBox.information(self, "删除成功", "产品删除成功!")
                else:
                    QMessageBox.information(
                        self, "删除成功", 
                        "产品数据库记录删除成功!\n相关文件已保留。"
                    )
                
                self.load_products()
                self.cancel_edit()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
                # 刷新列表以防数据不同步
                self.load_products()
                self.cancel_edit()
    
    def _collect_related_files(self, product):
        """收集产品相关的文件"""
        related_files = []
        
        # DXF文件
        if product.dxf_file_path and os.path.exists(product.dxf_file_path):
            related_files.append({
                'type': 'DXF文件',
                'path': product.dxf_file_path,
                'size': os.path.getsize(product.dxf_file_path)
            })
        
        # 查找可能的产品数据目录
        # 基于产品名称和ID搜索Data目录下的相关文件夹
        data_dirs = self._find_product_data_directories(product)
        for data_dir in data_dirs:
            dir_size = self._calculate_directory_size(data_dir)
            related_files.append({
                'type': '检测数据目录',
                'path': data_dir,
                'size': dir_size
            })
        
        return related_files
    
    def _find_product_data_directories(self, product):
        """查找产品相关的数据目录"""
        data_dirs = []
        data_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'Data')
        
        if os.path.exists(data_root):
            # 搜索可能的目录名模式
            possible_patterns = [
                product.model_name,
                product.model_code,
                f"product_{product.id}",
                # 可以根据需要添加更多匹配模式
            ]
            
            for item in os.listdir(data_root):
                item_path = os.path.join(data_root, item)
                if os.path.isdir(item_path):
                    # 检查是否匹配任何模式
                    for pattern in possible_patterns:
                        if pattern and (pattern in item or item in pattern):
                            data_dirs.append(item_path)
                            break
        
        return data_dirs
    
    def _calculate_directory_size(self, directory):
        """计算目录总大小"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        return total_size
    
    def _show_delete_confirmation_dialog(self, product, related_files):
        """显示删除确认对话框"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QRadioButton, QDialogButtonBox, QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle("确认删除产品")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 基本信息
        info_label = QLabel(f"确定要删除产品型号 '{product.model_name}' 吗？")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(info_label)
        
        # 相关文件列表
        if related_files:
            files_label = QLabel("发现以下相关文件:")
            layout.addWidget(files_label)
            
            files_text = QTextEdit()
            files_text.setMaximumHeight(150)
            files_text.setReadOnly(True)
            
            files_content = []
            total_size = 0
            for file_info in related_files:
                size_mb = file_info['size'] / (1024 * 1024)
                files_content.append(f"• {file_info['type']}: {file_info['path']} ({size_mb:.2f} MB)")
                total_size += file_info['size']
            
            files_content.append(f"\n总大小: {total_size / (1024 * 1024):.2f} MB")
            files_text.setText('\n'.join(files_content))
            layout.addWidget(files_text)
        
        # 删除选项
        options_label = QLabel("请选择删除方式:")
        layout.addWidget(options_label)
        
        option1 = QRadioButton("仅删除数据库记录（保留相关文件）")
        option1.setChecked(True)
        layout.addWidget(option1)
        
        option2 = QRadioButton("删除数据库记录和所有相关文件")
        if related_files:
            option2.setText(f"删除数据库记录和所有相关文件 ({len(related_files)} 个文件/目录)")
        else:
            option2.setText("删除数据库记录（无相关文件）")
            option2.setEnabled(False)
        layout.addWidget(option2)
        
        # 警告
        warning_label = QLabel("⚠️ 注意：此操作不可撤销！")
        warning_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(warning_label)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # 执行对话框
        result = dialog.exec()
        if result == QDialog.Accepted:
            if option1.isChecked():
                return 'database_only'
            elif option2.isChecked():
                return 'database_and_files'
        
        return 'cancel'
    
    def _delete_related_files(self, related_files):
        """删除相关文件"""
        deleted_files = []
        
        for file_info in related_files:
            try:
                file_path = file_info['path']
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_files.append(file_path)
                elif os.path.isdir(file_path):
                    import shutil
                    shutil.rmtree(file_path)
                    deleted_files.append(file_path)
            except Exception as e:
                # 记录错误但继续删除其他文件
                print(f"删除文件失败: {file_path}, 错误: {str(e)}")
        
        return deleted_files
    
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
        # 暂时禁用渲染功能以防止崩溃
        QMessageBox.information(
            self, 
            "功能暂时禁用", 
            "渲染编号功能暂时禁用。\n由于存在稳定性问题，此功能正在修复中。\n您可以继续使用其他功能。"
        )
        return
        
        # 以下是原始代码（暂时注释）
        """
        dxf_path = self.dxf_path_edit.text().strip()
        
        if not dxf_path:
            QMessageBox.warning(self, "警告", "请先选择DXF文件")
            return
        
        if not os.path.exists(dxf_path):
            QMessageBox.warning(self, "警告", f"DXF文件不存在: {dxf_path}")
            return
        
        try:
            # 添加调试日志
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"开始渲染DXF文件: {dxf_path}")
            logger.info(f"文件大小: {os.path.getsize(dxf_path) / 1024:.2f} KB")
            
            from dxf_render_dialog import DXFRenderDialog
            
            # 创建对话框前记录
            logger.info("创建DXFRenderDialog对话框...")
            dialog = DXFRenderDialog(dxf_path, self)
            
            logger.info("显示对话框...")
            dialog.exec()
            logger.info("对话框关闭")
            
        except ImportError as e:
            if "matplotlib" in str(e):
                QMessageBox.critical(
                    self, "缺少依赖", 
                    "DXF渲染功能需要matplotlib库。\n请运行命令: pip install matplotlib"
                )
            else:
                QMessageBox.critical(self, "导入错误", f"模块导入失败: {str(e)}")
        except Exception as e:
            import traceback
            logger.error(f"渲染DXF失败: {str(e)}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "错误", f"打开DXF渲染对话框失败: {str(e)}")
        """
    
    def import_from_dxf(self):
        """从DXF文件导入产品信息"""
        # 检查当前是否在编辑状态
        is_editing = self.save_btn.isEnabled()
        
        if is_editing:
            # 如果正在编辑，提供选择：填充当前表单 或 创建新产品
            reply = QMessageBox.question(
                self, "DXF导入模式", 
                "检测到您正在编辑产品信息。\n\n请选择导入方式：\n"
                "• 是(Y)：用DXF数据填充当前表单\n"
                "• 否(N)：创建新产品\n"
                "• 取消：取消导入",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                self._import_and_fill_form()
                return
            # 如果选择No，继续执行原有的创建新产品逻辑
        
        # 原有的创建新产品逻辑
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
    
    def _import_and_fill_form(self):
        """导入DXF并填充当前表单"""
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
            
            # 获取DXF分析结果
            analysis_result = self.dxf_importer.import_from_dxf(file_path)
            if not analysis_result:
                QMessageBox.critical(self, "错误", "DXF文件分析失败")
                return
            
            # 自动填充表单字段
            # 如果型号名称为空，使用建议的名称
            if not self.model_name_edit.text().strip():
                self.model_name_edit.setText(analysis_result.suggested_model_name)
            
            # 设置标准直径
            self.standard_diameter_spin.setValue(analysis_result.standard_diameter)
            
            # 设置公差
            tolerance = analysis_result.tolerance_estimate
            self.tolerance_upper_spin.setValue(tolerance)
            self.tolerance_lower_spin.setValue(-tolerance)
            
            # 设置DXF文件路径
            self.dxf_path_edit.setText(file_path)
            
            # 更新描述（如果为空）
            if not self.description_edit.toPlainText().strip():
                file_name = os.path.basename(file_path)
                description = f"从DXF文件'{file_name}'导入，检测到{analysis_result.total_holes}个孔"
                self.description_edit.setText(description)
            
            # 更新DXF渲染按钮状态
            self.update_dxf_render_button()
            
            QMessageBox.information(
                self, "导入成功", 
                f"DXF数据已填充到表单！\n"
                f"• 标准直径: {analysis_result.standard_diameter:.2f}mm\n"
                f"• 检测孔数: {analysis_result.total_holes}个\n"
                f"• 建议公差: ±{tolerance:.3f}mm"
            )
            
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
        self.import_btn.setStyleSheet("QPushButton { background-color: #2ECC71; color: white; font-weight: bold; }")
        self.cancel_btn.setStyleSheet("QPushButton { background-color: #313642; color: white; }")
        
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