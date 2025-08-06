"""
DXF渲染和编号对话框
提供DXF文件的可视化渲染、孔位编号和数据导出功能
"""

import os
from typing import Optional

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QGroupBox, QGridLayout,
                             QFileDialog, QTextEdit, QSplitter, QWidget,
                             QProgressBar, QCheckBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QPixmap

class DXFRenderWorker(QThread):
    """DXF渲染工作线程"""
    
    progress_updated = Signal(int, str)
    render_completed = Signal(object)  # DXFRenderResult
    error_occurred = Signal(str)
    
    def __init__(self, dxf_file_path: str, numbering_strategy: str, 
                 output_image_path: str, parent=None):
        super().__init__(parent)
        self.dxf_file_path = dxf_file_path
        self.numbering_strategy = numbering_strategy
        self.output_image_path = output_image_path
    
    def run(self):
        """执行渲染"""
        try:
            from dxf_renderer import get_dxf_renderer
            
            self.progress_updated.emit(10, "初始化渲染器...")
            renderer = get_dxf_renderer()
            
            # 检查依赖
            self.progress_updated.emit(20, "检查依赖库...")
            deps = renderer.check_dependencies()
            if not all(deps.values()):
                missing = [k for k, v in deps.items() if not v]
                raise ImportError(f"缺少依赖库: {', '.join(missing)}")
            
            self.progress_updated.emit(40, "解析DXF文件...")
            
            # 执行渲染
            self.progress_updated.emit(60, "渲染图形和编号...")
            render_result = renderer.render_dxf_with_numbering(
                self.dxf_file_path,
                self.numbering_strategy,
                self.output_image_path
            )
            
            self.progress_updated.emit(100, "渲染完成!")
            self.render_completed.emit(render_result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))

class DXFRenderDialog(QDialog):
    """DXF渲染和编号对话框"""
    
    def __init__(self, dxf_file_path: str, parent=None):
        super().__init__(parent)
        self.dxf_file_path = dxf_file_path
        self.render_result = None
        self.worker = None
        self.setup_ui()
        
    def setup_ui(self):
        """初始化界面"""
        self.setWindowTitle("DXF文件渲染和编号")
        self.setModal(True)
        self.resize(1000, 700)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("DXF文件渲染和编号")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 文件信息
        file_info_group = QGroupBox("文件信息")
        file_info_layout = QGridLayout(file_info_group)
        
        file_info_layout.addWidget(QLabel("DXF文件:"), 0, 0)
        self.file_path_label = QLabel(self.dxf_file_path)
        self.file_path_label.setWordWrap(True)
        file_info_layout.addWidget(self.file_path_label, 0, 1)
        
        main_layout.addWidget(file_info_group)
        
        # 渲染设置
        settings_group = QGroupBox("渲染设置")
        settings_layout = QGridLayout(settings_group)
        
        # 编号策略
        settings_layout.addWidget(QLabel("编号策略:"), 0, 0)
        self.numbering_combo = QComboBox()
        # 修复：添加默认编号选项
        self.numbering_combo.addItems([
            "默认编号",
            "从左到右",
            "从上到下",
            "螺旋编号",
            "距离中心"
        ])
        self.numbering_combo.setCurrentText("默认编号")
        settings_layout.addWidget(self.numbering_combo, 0, 1)
        
        # 输出选项
        settings_layout.addWidget(QLabel("输出选项:"), 1, 0)
        output_options_layout = QHBoxLayout()
        
        self.export_image_check = QCheckBox("导出图像")
        self.export_image_check.setChecked(True)
        output_options_layout.addWidget(self.export_image_check)
        
        self.export_csv_check = QCheckBox("导出CSV")
        self.export_csv_check.setChecked(True)
        output_options_layout.addWidget(self.export_csv_check)
        
        self.create_numbered_dxf_check = QCheckBox("创建带编号DXF")
        output_options_layout.addWidget(self.create_numbered_dxf_check)
        
        output_options_layout.addStretch()
        settings_layout.addLayout(output_options_layout, 1, 1)
        
        main_layout.addWidget(settings_group)
        
        # 操作按钮
        action_layout = QHBoxLayout()
        
        self.render_btn = QPushButton("开始渲染")
        self.render_btn.clicked.connect(self.start_render)
        action_layout.addWidget(self.render_btn)
        
        self.preview_btn = QPushButton("预览结果")
        self.preview_btn.setEnabled(False)
        self.preview_btn.clicked.connect(self.preview_result)
        action_layout.addWidget(self.preview_btn)
        
        action_layout.addStretch()
        
        main_layout.addLayout(action_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        main_layout.addWidget(self.progress_label)
        
        # 结果区域
        self.result_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：孔位表
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        table_header = QLabel("孔位信息表")
        table_header.setFont(QFont("", 12, QFont.Bold))
        table_layout.addWidget(table_header)
        
        self.hole_table = QTableWidget()
        table_layout.addWidget(self.hole_table)
        
        # 右侧：预览图像
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        preview_header = QLabel("渲染预览")
        preview_header.setFont(QFont("", 12, QFont.Bold))
        preview_layout.addWidget(preview_header)
        
        self.preview_label = QLabel("等待渲染...")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("border: 1px solid gray;")
        preview_layout.addWidget(self.preview_label)
        
        self.result_splitter.addWidget(table_widget)
        self.result_splitter.addWidget(preview_widget)
        self.result_splitter.setSizes([400, 600])
        
        main_layout.addWidget(self.result_splitter)
        
        # 底部按钮
        bottom_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("导出数据")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_data)
        bottom_layout.addWidget(self.export_btn)
        
        bottom_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(bottom_layout)
        
        # 设置按钮样式
        self.render_btn.setStyleSheet("QPushButton { background-color: #2ECC71; color: white; font-weight: bold; }")
        self.export_btn.setStyleSheet("QPushButton { background-color: #007ACC; color: white; }")
        
        for btn in [self.render_btn, self.preview_btn, self.export_btn, self.close_btn]:
            btn.setMinimumHeight(35)
            btn.setMinimumWidth(100)
    
    def get_numbering_strategy(self) -> str:
        """获取选中的编号策略"""
        strategy_map = {
            "默认编号": "left_to_right",  # 默认编号使用从左到右策略
            "从左到右": "left_to_right",
            "从上到下": "top_to_bottom", 
            "螺旋编号": "spiral",
            "距离中心": "distance_from_center"
        }
        return strategy_map.get(self.numbering_combo.currentText(), "left_to_right")
    
    def start_render(self):
        """开始渲染"""
        try:
            # 检查依赖
            from dxf_renderer import get_dxf_renderer
            renderer = get_dxf_renderer()
            deps = renderer.check_dependencies()
            
            missing_deps = []
            if not deps.get('ezdxf', False):
                missing_deps.append("ezdxf")
            if not deps.get('matplotlib', False):
                missing_deps.append("matplotlib")
            
            if missing_deps:
                QMessageBox.critical(
                    self, "缺少依赖", 
                    f"请安装缺少的依赖库:\n{chr(10).join([f'pip install {dep}' for dep in missing_deps])}"
                )
                return
            
            # 准备输出路径
            base_name = os.path.splitext(os.path.basename(self.dxf_file_path))[0]
            output_dir = os.path.dirname(self.dxf_file_path)
            output_image_path = os.path.join(output_dir, f"{base_name}_rendered.png")
            
            # 启动工作线程
            self.worker = DXFRenderWorker(
                self.dxf_file_path,
                self.get_numbering_strategy(),
                output_image_path,
                self
            )
            
            # 连接信号
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.render_completed.connect(self.on_render_completed)
            self.worker.error_occurred.connect(self.on_render_error)
            
            # 更新界面状态
            self.render_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_label.setVisible(True)
            
            # 开始渲染
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动渲染失败: {str(e)}")
    
    def update_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
    
    def on_render_completed(self, render_result):
        """渲染完成"""
        self.render_result = render_result
        
        # 更新界面
        self.render_btn.setEnabled(True)
        self.preview_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        # 更新孔位表
        self.update_hole_table()
        
        # 显示预览图
        if render_result.rendered_image_path and os.path.exists(render_result.rendered_image_path):
            self.load_preview_image(render_result.rendered_image_path)
        
        QMessageBox.information(self, "成功", "DXF渲染完成!")
    
    def on_render_error(self, error_message: str):
        """渲染错误"""
        self.render_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        QMessageBox.critical(self, "渲染失败", f"渲染过程中发生错误:\n{error_message}")
    
    def update_hole_table(self):
        """更新孔位表"""
        if not self.render_result or not self.render_result.hole_table_data:
            return
        
        data = self.render_result.hole_table_data
        self.hole_table.setRowCount(len(data))
        self.hole_table.setColumnCount(len(data[0]) if data else 0)
        
        if data:
            # 设置表头
            headers = list(data[0].keys())
            self.hole_table.setHorizontalHeaderLabels(headers)
            
            # 填充数据
            for row, item in enumerate(data):
                for col, (key, value) in enumerate(item.items()):
                    table_item = QTableWidgetItem(str(value))
                    self.hole_table.setItem(row, col, table_item)
            
            # 调整列宽
            self.hole_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    
    def load_preview_image(self, image_path: str):
        """加载预览图像"""
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # 缩放图像适应预览区域
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
        except Exception as e:
            self.preview_label.setText(f"预览加载失败: {str(e)}")
    
    def preview_result(self):
        """预览结果"""
        if not self.render_result or not self.render_result.rendered_image_path:
            QMessageBox.warning(self, "警告", "没有可预览的渲染结果")
            return
        
        # 打开图像文件
        try:
            import subprocess
            import sys
            
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", self.render_result.rendered_image_path])
            elif sys.platform == "win32":  # Windows
                os.startfile(self.render_result.rendered_image_path)
            else:  # Linux
                subprocess.run(["xdg-open", self.render_result.rendered_image_path])
        except Exception as e:
            QMessageBox.warning(self, "警告", f"无法打开预览: {str(e)}")
    
    def export_data(self):
        """导出数据"""
        if not self.render_result:
            QMessageBox.warning(self, "警告", "没有可导出的数据")
            return
        
        try:
            from dxf_renderer import get_dxf_renderer
            renderer = get_dxf_renderer()
            
            base_name = os.path.splitext(os.path.basename(self.dxf_file_path))[0]
            output_dir = os.path.dirname(self.dxf_file_path)
            
            exported_files = []
            
            # 导出CSV
            if self.export_csv_check.isChecked():
                csv_path = os.path.join(output_dir, f"{base_name}_holes.csv")
                renderer.export_hole_data(self.render_result, csv_path, 'csv')
                exported_files.append(f"CSV: {csv_path}")
            
            # 创建带编号的DXF
            if self.create_numbered_dxf_check.isChecked():
                numbered_dxf_path = os.path.join(output_dir, f"{base_name}_numbered.dxf")
                renderer.create_numbered_dxf(
                    self.dxf_file_path, 
                    numbered_dxf_path,
                    self.get_numbering_strategy()
                )
                exported_files.append(f"编号DXF: {numbered_dxf_path}")
            
            if exported_files:
                QMessageBox.information(
                    self, "导出成功", 
                    f"数据导出完成:\n{chr(10).join(exported_files)}"
                )
            else:
                QMessageBox.information(self, "提示", "没有选择导出选项")
                
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"数据导出失败: {str(e)}")