#!/usr/bin/env python3
"""
DXF导入适配器
将新的DXF产品转换器适配到现有的UI系统
"""

from typing import Optional, Dict, Any
import os

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QLabel, QLineEdit, QPushButton, QSpinBox,
                             QDoubleSpinBox, QTextEdit, QDialogButtonBox,
                             QGridLayout, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.utilities.product_import_service import ProductImportService
from src.shared.models.product_model import get_product_manager


class DXFImportPreviewDialog(QDialog):
    """DXF导入预览对话框（使用新的转换器）"""
    
    # 信号
    import_completed = Signal(dict)
    
    def __init__(self, dxf_file_path: str, parent=None):
        super().__init__(parent)
        self.dxf_file_path = dxf_file_path
        self.import_service = ProductImportService()
        self.preview_data = None
        
        self.setup_ui()
        self.load_preview()
    
    def setup_ui(self):
        """初始化界面"""
        self.setWindowTitle("DXF产品导入")
        self.setModal(True)
        self.resize(700, 600)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("从DXF文件导入产品")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 文件信息组
        file_group = QGroupBox("DXF文件信息")
        file_layout = QGridLayout(file_group)
        
        file_layout.addWidget(QLabel("文件路径:"), 0, 0)
        self.file_path_label = QLabel(self.dxf_file_path)
        self.file_path_label.setWordWrap(True)
        file_layout.addWidget(self.file_path_label, 0, 1, 1, 3)
        
        file_layout.addWidget(QLabel("文件大小:"), 1, 0)
        self.file_size_label = QLabel()
        file_layout.addWidget(self.file_size_label, 1, 1)
        
        main_layout.addWidget(file_group)
        
        # 产品信息组
        product_group = QGroupBox("产品信息")
        product_layout = QGridLayout(product_group)
        
        # 产品名称
        product_layout.addWidget(QLabel("产品名称:"), 0, 0)
        self.name_edit = QLineEdit()
        product_layout.addWidget(self.name_edit, 0, 1, 1, 3)
        
        # 产品编号
        product_layout.addWidget(QLabel("产品编号:"), 1, 0)
        self.code_edit = QLineEdit()
        product_layout.addWidget(self.code_edit, 1, 1, 1, 3)
        
        # 孔位信息
        product_layout.addWidget(QLabel("孔位数量:"), 2, 0)
        self.hole_count_label = QLabel()
        product_layout.addWidget(self.hole_count_label, 2, 1)
        
        product_layout.addWidget(QLabel("孔径 (mm):"), 2, 2)
        self.diameter_spin = QDoubleSpinBox()
        self.diameter_spin.setRange(0.1, 1000)
        self.diameter_spin.setSingleStep(0.1)
        self.diameter_spin.setDecimals(2)
        product_layout.addWidget(self.diameter_spin, 2, 3)
        
        # 公差设置
        product_layout.addWidget(QLabel("上公差 (mm):"), 3, 0)
        self.upper_tolerance_spin = QDoubleSpinBox()
        self.upper_tolerance_spin.setRange(0, 10)
        self.upper_tolerance_spin.setSingleStep(0.01)
        self.upper_tolerance_spin.setDecimals(3)
        self.upper_tolerance_spin.setValue(0.1)
        product_layout.addWidget(self.upper_tolerance_spin, 3, 1)
        
        product_layout.addWidget(QLabel("下公差 (mm):"), 3, 2)
        self.lower_tolerance_spin = QDoubleSpinBox()
        self.lower_tolerance_spin.setRange(-10, 0)
        self.lower_tolerance_spin.setSingleStep(0.01)
        self.lower_tolerance_spin.setDecimals(3)
        self.lower_tolerance_spin.setValue(-0.1)
        product_layout.addWidget(self.lower_tolerance_spin, 3, 3)
        
        # 形状和尺寸
        product_layout.addWidget(QLabel("产品形状:"), 4, 0)
        self.shape_label = QLabel()
        product_layout.addWidget(self.shape_label, 4, 1)
        
        product_layout.addWidget(QLabel("外形尺寸:"), 4, 2)
        self.size_label = QLabel()
        product_layout.addWidget(self.size_label, 4, 3)
        
        # 分区设置
        product_layout.addWidget(QLabel("分区数量:"), 5, 0)
        self.sector_spin = QSpinBox()
        self.sector_spin.setRange(2, 12)
        self.sector_spin.setSingleStep(2)
        self.sector_spin.setValue(4)
        product_layout.addWidget(self.sector_spin, 5, 1)
        
        main_layout.addWidget(product_group)
        
        # 数据完整性组
        completeness_group = QGroupBox("数据完整性")
        completeness_layout = QVBoxLayout(completeness_group)
        
        self.completeness_label = QLabel()
        completeness_layout.addWidget(self.completeness_label)
        
        self.missing_info_text = QTextEdit()
        self.missing_info_text.setMaximumHeight(80)
        self.missing_info_text.setReadOnly(True)
        completeness_layout.addWidget(self.missing_info_text)
        
        main_layout.addWidget(completeness_group)
        
        # 按钮
        button_box = QDialogButtonBox()
        self.import_button = QPushButton("导入产品")
        self.import_button.setDefault(True)
        self.import_button.clicked.connect(self.import_product)
        button_box.addButton(self.import_button, QDialogButtonBox.AcceptRole)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_box.addButton(cancel_button, QDialogButtonBox.RejectRole)
        
        main_layout.addWidget(button_box)
        
        # 连接信号
        self.import_service.import_completed.connect(self.on_import_completed)
        self.import_service.import_error.connect(self.on_import_error)
    
    def load_preview(self):
        """加载预览数据"""
        try:
            # 获取文件大小
            file_size = os.path.getsize(self.dxf_file_path) / (1024 * 1024)
            self.file_size_label.setText(f"{file_size:.2f} MB")
            
            # 预览导入
            self.preview_data = self.import_service.preview_dxf_import(self.dxf_file_path)
            
            if not self.preview_data or 'error' in self.preview_data:
                error_msg = self.preview_data.get('error', '未知错误') if self.preview_data else 'DXF文件解析失败'
                QMessageBox.critical(self, "错误", f"无法预览DXF文件: {error_msg}")
                self.reject()
                return
            
            # 填充界面
            product_info = self.preview_data['product_info']
            validation = self.preview_data['validation']
            
            # 基本信息
            self.name_edit.setText(product_info['product_name'])
            self.code_edit.setText(product_info['product_code'])
            self.hole_count_label.setText(str(product_info['hole_count']))
            self.diameter_spin.setValue(product_info['hole_diameter'])
            
            # 形状和尺寸
            shape_map = {
                'circular': '圆形',
                'elliptical': '椭圆形',
                'rectangular': '矩形',
                'unknown': '未知'
            }
            self.shape_label.setText(shape_map.get(product_info['shape'], product_info['shape']))
            self.size_label.setText(f"{product_info['outer_diameter']:.1f} x {product_info['inner_diameter']:.1f} mm")
            
            # 分区设置
            self.sector_spin.setValue(product_info.get('sector_count', 4))
            
            # 数据完整性
            self.completeness_label.setText(f"数据完整性评分: {validation['completeness_score']}%")
            
            # 缺失信息
            missing_info = []
            if validation['missing_required']:
                missing_info.append(f"必需字段缺失: {', '.join(validation['missing_required'])}")
            if validation['missing_important']:
                missing_info.append(f"重要字段缺失: {', '.join(validation['missing_important'])}")
            
            if missing_info:
                self.missing_info_text.setText('\n'.join(missing_info))
            else:
                self.missing_info_text.setText("所有必需信息完整")
            
            # 检查是否已存在
            if self.preview_data.get('existing_product'):
                self.import_button.setText("更新产品")
                QMessageBox.warning(
                    self, "提示", 
                    f"产品 '{product_info['product_name']}' 已存在，点击导入将更新现有产品。"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载预览失败: {str(e)}")
            self.reject()
    
    def import_product(self):
        """执行产品导入"""
        try:
            # 收集用户输入
            overrides = {
                'product_name': self.name_edit.text().strip(),
                'product_code': self.code_edit.text().strip(),
                'standard_diameter': self.diameter_spin.value(),
                'tolerance_upper': self.upper_tolerance_spin.value(),
                'tolerance_lower': self.lower_tolerance_spin.value(),
                'sector_count': self.sector_spin.value(),
                'force_update': self.preview_data.get('existing_product', False)
            }
            
            # 验证必填字段
            if not overrides['product_name']:
                QMessageBox.warning(self, "警告", "请输入产品名称")
                return
            
            # 执行导入
            self.import_button.setEnabled(False)
            self.import_button.setText("正在导入...")
            
            product = self.import_service.import_from_dxf(self.dxf_file_path, **overrides)
            
            if product:
                self.accept()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
            self.import_button.setEnabled(True)
            self.import_button.setText("导入产品")
    
    def on_import_completed(self, result):
        """导入完成处理"""
        self.import_completed.emit(result)
        QMessageBox.information(self, "成功", "产品导入成功！")
        self.accept()
    
    def on_import_error(self, error_msg):
        """导入错误处理"""
        QMessageBox.critical(self, "错误", error_msg)
        self.import_button.setEnabled(True)
        self.import_button.setText("导入产品")