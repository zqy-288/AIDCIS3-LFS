"""
报告输出控制器
负责管理报告生成和输出界面以及相关业务逻辑
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QComboBox, QLineEdit, QCheckBox, QProgressBar,
    QSplitter, QTreeWidget, QTreeWidgetItem, QFrame, QSpinBox,
    QFileDialog, QMessageBox, QTabWidget
)
from PySide6.QtCore import QObject, Signal, QTimer, Qt, QThread, QMutex
from PySide6.QtGui import QFont, QIcon, QPixmap, QTextDocument

from src.modules.report_output_interface import ReportOutputInterface


class ReportGenerationWorker(QThread):
    """报告生成工作线程"""
    
    progress_updated = Signal(int)  # 进度更新信号
    report_generated = Signal(str, dict)  # 报告生成完成信号
    error_occurred = Signal(str)  # 错误信号
    
    def __init__(self, report_config: Dict[str, Any]):
        super().__init__()
        self.report_config = report_config
        self.mutex = QMutex()
        self._is_cancelled = False
    
    def run(self):
        """执行报告生成"""
        try:
            # 模拟报告生成过程
            steps = [
                "初始化报告模板",
                "收集数据",
                "生成图表",
                "格式化内容",
                "生成文档",
                "保存文件"
            ]
            
            for i, step in enumerate(steps):
                if self._is_cancelled:
                    return
                
                # 模拟处理时间
                self.msleep(500)
                
                progress = int((i + 1) / len(steps) * 100)
                self.progress_updated.emit(progress)
            
            # 模拟生成的报告路径
            report_path = f"/tmp/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            report_info = {
                'path': report_path,
                'size': 1024 * 50,  # 50KB
                'pages': 10,
                'created_time': datetime.now()
            }
            
            self.report_generated.emit(report_path, report_info)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def cancel(self):
        """取消生成"""
        self.mutex.lock()
        self._is_cancelled = True
        self.mutex.unlock()


class ReportController(QObject):
    """报告输出控制器类"""
    
    # 信号定义
    report_generated = Signal(str, dict)  # 报告生成完成信号
    template_changed = Signal(str)  # 模板改变信号
    export_completed = Signal(str)  # 导出完成信号
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        
        # 核心组件
        self._widget: Optional[QWidget] = None
        self._report_interface: Optional[ReportOutputInterface] = None
        self._generation_worker: Optional[ReportGenerationWorker] = None
        
        # 报告管理
        self._report_templates: Dict[str, Dict] = {}
        self._current_template: Optional[str] = None
        self._report_config: Dict[str, Any] = {}
        self._generated_reports: List[Dict[str, Any]] = []
        
        # 状态管理
        self._is_generating = False
        self._generation_progress = 0
        
        # UI组件引用
        self._ui_components = {}
        
        # 初始化报告模板
        self._initialize_templates()
        
        self.logger.info("报告输出控制器初始化完成")
    
    def create_widget(self) -> QWidget:
        """创建报告输出界面"""
        if self._widget is not None:
            return self._widget
        
        self._widget = QWidget()
        self._setup_ui()
        self._connect_signals()
        
        self.logger.info("报告输出界面创建完成")
        return self._widget
    
    def _setup_ui(self):
        """设置用户界面"""
        if not self._widget:
            return
        
        # 主布局
        main_layout = QVBoxLayout(self._widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        
        # 报告生成选项卡
        generation_tab = self._create_generation_tab()
        tab_widget.addTab(generation_tab, "报告生成")
        
        # 报告管理选项卡
        management_tab = self._create_management_tab()
        tab_widget.addTab(management_tab, "报告管理")
        
        # 模板编辑选项卡
        template_tab = self._create_template_tab()
        tab_widget.addTab(template_tab, "模板编辑")
        
        main_layout.addWidget(tab_widget)
        
        self.logger.info("报告输出UI设置完成")
    
    def _create_generation_tab(self) -> QWidget:
        """创建报告生成选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 报告配置面板
        config_panel = self._create_config_panel()
        layout.addWidget(config_panel)
        
        # 内容选择面板
        content_panel = self._create_content_panel()
        layout.addWidget(content_panel)
        
        # 生成控制面板
        control_panel = self._create_generation_control_panel()
        layout.addWidget(control_panel)
        
        return widget
    
    def _create_config_panel(self) -> QWidget:
        """创建报告配置面板"""
        panel = QGroupBox("报告配置")
        panel.setMaximumHeight(150)
        
        layout = QVBoxLayout(panel)
        
        # 第一行：基本配置
        basic_layout = QHBoxLayout()
        
        # 报告模板
        basic_layout.addWidget(QLabel("报告模板:"))
        self._ui_components['template_combo'] = QComboBox()
        self._ui_components['template_combo'].addItems(list(self._report_templates.keys()))
        self._ui_components['template_combo'].currentTextChanged.connect(self._on_template_changed)
        basic_layout.addWidget(self._ui_components['template_combo'])
        
        # 报告标题
        basic_layout.addWidget(QLabel("报告标题:"))
        self._ui_components['report_title'] = QLineEdit()
        self._ui_components['report_title'].setText(f"检测报告_{datetime.now().strftime('%Y%m%d')}")
        basic_layout.addWidget(self._ui_components['report_title'])
        
        # 输出格式
        basic_layout.addWidget(QLabel("输出格式:"))
        self._ui_components['output_format'] = QComboBox()
        self._ui_components['output_format'].addItems(["PDF", "Word", "Excel", "HTML"])
        basic_layout.addWidget(self._ui_components['output_format'])
        
        basic_layout.addStretch()
        layout.addLayout(basic_layout)
        
        # 第二行：高级配置
        advanced_layout = QHBoxLayout()
        
        # 页面设置
        advanced_layout.addWidget(QLabel("页面大小:"))
        self._ui_components['page_size'] = QComboBox()
        self._ui_components['page_size'].addItems(["A4", "A3", "Letter", "Legal"])
        advanced_layout.addWidget(self._ui_components['page_size'])
        
        # 页面方向
        advanced_layout.addWidget(QLabel("页面方向:"))
        self._ui_components['page_orientation'] = QComboBox()
        self._ui_components['page_orientation'].addItems(["纵向", "横向"])
        advanced_layout.addWidget(self._ui_components['page_orientation'])
        
        # 输出路径
        advanced_layout.addWidget(QLabel("输出路径:"))
        self._ui_components['output_path'] = QLineEdit()
        self._ui_components['output_path'].setText(str(Path.home() / "Desktop"))
        advanced_layout.addWidget(self._ui_components['output_path'])
        
        self._ui_components['browse_btn'] = QPushButton("浏览...")
        self._ui_components['browse_btn'].clicked.connect(self._browse_output_path)
        advanced_layout.addWidget(self._ui_components['browse_btn'])
        
        layout.addLayout(advanced_layout)
        
        return panel
    
    def _create_content_panel(self) -> QWidget:
        """创建内容选择面板"""
        panel = QGroupBox("报告内容")
        layout = QHBoxLayout(panel)
        
        # 左侧：内容选择
        left_widget = QGroupBox("选择内容")
        left_layout = QVBoxLayout(left_widget)
        
        # 内容选项
        content_options = [
            ("封面页", True),
            ("目录", True),
            ("摘要", True),
            ("检测数据", True),
            ("统计分析", True),
            ("图表", True),
            ("结论", True),
            ("附录", False)
        ]
        
        self._ui_components['content_options'] = {}
        for option, default_checked in content_options:
            checkbox = QCheckBox(option)
            checkbox.setChecked(default_checked)
            self._ui_components['content_options'][option] = checkbox
            left_layout.addWidget(checkbox)
        
        layout.addWidget(left_widget)
        
        # 右侧：内容预览
        right_widget = QGroupBox("内容预览")
        right_layout = QVBoxLayout(right_widget)
        
        self._ui_components['content_preview'] = QTextEdit()
        self._ui_components['content_preview'].setReadOnly(True)
        self._ui_components['content_preview'].setMaximumHeight(200)
        right_layout.addWidget(self._ui_components['content_preview'])
        
        # 预览按钮
        preview_btn = QPushButton("预览内容")
        preview_btn.clicked.connect(self._preview_content)
        right_layout.addWidget(preview_btn)
        
        layout.addWidget(right_widget)
        
        return panel
    
    def _create_generation_control_panel(self) -> QWidget:
        """创建生成控制面板"""
        panel = QGroupBox("生成控制")
        panel.setMaximumHeight(120)
        
        layout = QVBoxLayout(panel)
        
        # 生成按钮行
        button_layout = QHBoxLayout()
        
        self._ui_components['generate_btn'] = QPushButton("生成报告")
        self._ui_components['generate_btn'].clicked.connect(self.generate_report)
        button_layout.addWidget(self._ui_components['generate_btn'])
        
        self._ui_components['cancel_btn'] = QPushButton("取消生成")
        self._ui_components['cancel_btn'].clicked.connect(self.cancel_generation)
        self._ui_components['cancel_btn'].setEnabled(False)
        button_layout.addWidget(self._ui_components['cancel_btn'])
        
        self._ui_components['preview_btn'] = QPushButton("预览报告")
        self._ui_components['preview_btn'].clicked.connect(self.preview_report)
        button_layout.addWidget(self._ui_components['preview_btn'])
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("生成进度:"))
        
        self._ui_components['progress_bar'] = QProgressBar()
        self._ui_components['progress_bar'].setVisible(False)
        progress_layout.addWidget(self._ui_components['progress_bar'])
        
        self._ui_components['progress_label'] = QLabel("")
        progress_layout.addWidget(self._ui_components['progress_label'])
        
        layout.addLayout(progress_layout)
        
        return panel
    
    def _create_management_tab(self) -> QWidget:
        """创建报告管理选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.clicked.connect(self._refresh_report_list)
        toolbar_layout.addWidget(refresh_btn)
        
        open_btn = QPushButton("打开报告")
        open_btn.clicked.connect(self._open_selected_report)
        toolbar_layout.addWidget(open_btn)
        
        delete_btn = QPushButton("删除报告")
        delete_btn.clicked.connect(self._delete_selected_report)
        toolbar_layout.addWidget(delete_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # 报告列表
        self._ui_components['report_table'] = QTableWidget()
        self._ui_components['report_table'].setColumnCount(6)
        self._ui_components['report_table'].setHorizontalHeaderLabels([
            "报告名称", "格式", "大小", "生成时间", "状态", "路径"
        ])
        
        # 设置表格属性
        table = self._ui_components['report_table']
        table.horizontalHeader().setStretchLastSection(True)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(table)
        
        return widget
    
    def _create_template_tab(self) -> QWidget:
        """创建模板编辑选项卡"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # 左侧：模板列表
        left_widget = QGroupBox("模板列表")
        left_layout = QVBoxLayout(left_widget)
        
        # 模板管理按钮
        template_toolbar = QHBoxLayout()
        
        new_template_btn = QPushButton("新建模板")
        new_template_btn.clicked.connect(self._new_template)
        template_toolbar.addWidget(new_template_btn)
        
        import_template_btn = QPushButton("导入模板")
        import_template_btn.clicked.connect(self._import_template)
        template_toolbar.addWidget(import_template_btn)
        
        export_template_btn = QPushButton("导出模板")
        export_template_btn.clicked.connect(self._export_template)
        template_toolbar.addWidget(export_template_btn)
        
        left_layout.addLayout(template_toolbar)
        
        # 模板列表
        self._ui_components['template_list'] = QTreeWidget()
        self._ui_components['template_list'].setHeaderLabel("模板")
        left_layout.addWidget(self._ui_components['template_list'])
        
        layout.addWidget(left_widget)
        
        # 右侧：模板编辑器
        right_widget = QGroupBox("模板编辑器")
        right_layout = QVBoxLayout(right_widget)
        
        # 编辑工具栏
        edit_toolbar = QHBoxLayout()
        
        save_template_btn = QPushButton("保存模板")
        save_template_btn.clicked.connect(self._save_template)
        edit_toolbar.addWidget(save_template_btn)
        
        reset_template_btn = QPushButton("重置")
        reset_template_btn.clicked.connect(self._reset_template)
        edit_toolbar.addWidget(reset_template_btn)
        
        edit_toolbar.addStretch()
        right_layout.addLayout(edit_toolbar)
        
        # 模板内容编辑器
        self._ui_components['template_editor'] = QTextEdit()
        self._ui_components['template_editor'].setFont(QFont("Consolas", 10))
        right_layout.addWidget(self._ui_components['template_editor'])
        
        layout.addWidget(right_widget)
        
        return widget
    
    def _connect_signals(self):
        """连接信号"""
        # 连接内部信号
        self.report_generated.connect(self._on_report_generated)
        self.template_changed.connect(self._on_template_changed)
        
        # 连接报告接口信号
        if self._report_interface:
            self._report_interface.generation_completed.connect(self._on_generation_completed)
    
    def _initialize_templates(self):
        """初始化报告模板"""
        self._report_templates = {
            "标准检测报告": {
                "description": "标准的检测报告模板",
                "sections": ["封面", "目录", "摘要", "检测数据", "结论"],
                "template": "standard_template.html"
            },
            "详细分析报告": {
                "description": "包含详细分析的报告模板",
                "sections": ["封面", "目录", "摘要", "检测数据", "统计分析", "图表", "结论", "附录"],
                "template": "detailed_template.html"
            },
            "简化报告": {
                "description": "简化版本的报告模板",
                "sections": ["摘要", "检测数据", "结论"],
                "template": "simple_template.html"
            }
        }
    
    def generate_report(self):
        """生成报告"""
        if self._is_generating:
            return
        
        try:
            # 收集报告配置
            self._collect_report_config()
            
            # 验证配置
            if not self._validate_config():
                return
            
            # 启动生成工作线程
            self._start_generation()
            
            self.logger.info("开始生成报告")
            
        except Exception as e:
            self.logger.error(f"生成报告失败: {e}")
            QMessageBox.critical(self._widget, "错误", f"生成报告失败: {e}")
    
    def cancel_generation(self):
        """取消报告生成"""
        if self._generation_worker:
            self._generation_worker.cancel()
            self._generation_worker.wait()
            self._generation_worker = None
        
        self._is_generating = False
        self._update_generation_ui(False)
        
        self.logger.info("报告生成已取消")
    
    def preview_report(self):
        """预览报告"""
        try:
            # 这里应该实现报告预览逻辑
            self.logger.info("预览报告")
            QMessageBox.information(self._widget, "信息", "报告预览功能正在开发中...")
            
        except Exception as e:
            self.logger.error(f"预览报告失败: {e}")
    
    def _collect_report_config(self):
        """收集报告配置"""
        self._report_config = {
            'template': self._ui_components['template_combo'].currentText(),
            'title': self._ui_components['report_title'].text(),
            'format': self._ui_components['output_format'].currentText(),
            'page_size': self._ui_components['page_size'].currentText(),
            'orientation': self._ui_components['page_orientation'].currentText(),
            'output_path': self._ui_components['output_path'].text(),
            'content_options': {}
        }
        
        # 收集内容选项
        for option, checkbox in self._ui_components['content_options'].items():
            self._report_config['content_options'][option] = checkbox.isChecked()
    
    def _validate_config(self) -> bool:
        """验证报告配置"""
        if not self._report_config.get('title'):
            QMessageBox.warning(self._widget, "警告", "请输入报告标题")
            return False
        
        output_path = Path(self._report_config.get('output_path', ''))
        if not output_path.exists():
            QMessageBox.warning(self._widget, "警告", "输出路径不存在")
            return False
        
        return True
    
    def _start_generation(self):
        """启动报告生成"""
        self._is_generating = True
        self._update_generation_ui(True)
        
        # 创建生成工作线程
        self._generation_worker = ReportGenerationWorker(self._report_config)
        self._generation_worker.progress_updated.connect(self._on_progress_updated)
        self._generation_worker.report_generated.connect(self._on_report_completed)
        self._generation_worker.error_occurred.connect(self._on_generation_error)
        
        self._generation_worker.start()
    
    def _update_generation_ui(self, generating: bool):
        """更新生成界面状态"""
        self._ui_components['generate_btn'].setEnabled(not generating)
        self._ui_components['cancel_btn'].setEnabled(generating)
        self._ui_components['progress_bar'].setVisible(generating)
        
        if not generating:
            self._ui_components['progress_bar'].setValue(0)
            self._ui_components['progress_label'].setText("")
    
    def _browse_output_path(self):
        """浏览输出路径"""
        current_path = self._ui_components['output_path'].text()
        path = QFileDialog.getExistingDirectory(
            self._widget, 
            "选择输出路径", 
            current_path
        )
        
        if path:
            self._ui_components['output_path'].setText(path)
    
    def _preview_content(self):
        """预览报告内容"""
        # 收集选中的内容选项
        selected_content = []
        for option, checkbox in self._ui_components['content_options'].items():
            if checkbox.isChecked():
                selected_content.append(option)
        
        # 生成预览文本
        preview_text = f"""
报告内容预览:
━━━━━━━━━━━━━━━━
模板: {self._ui_components['template_combo'].currentText()}
标题: {self._ui_components['report_title'].text()}
格式: {self._ui_components['output_format'].currentText()}

包含内容:
{chr(10).join(f"• {content}" for content in selected_content)}

页面设置:
• 大小: {self._ui_components['page_size'].currentText()}
• 方向: {self._ui_components['page_orientation'].currentText()}
        """
        
        self._ui_components['content_preview'].setText(preview_text.strip())
    
    def _refresh_report_list(self):
        """刷新报告列表"""
        # 这里应该从数据库或文件系统加载报告列表
        # 暂时使用模拟数据
        table = self._ui_components['report_table']
        table.setRowCount(len(self._generated_reports))
        
        for row, report in enumerate(self._generated_reports):
            table.setItem(row, 0, QTableWidgetItem(report.get('name', '')))
            table.setItem(row, 1, QTableWidgetItem(report.get('format', '')))
            table.setItem(row, 2, QTableWidgetItem(str(report.get('size', 0))))
            table.setItem(row, 3, QTableWidgetItem(str(report.get('created_time', ''))))
            table.setItem(row, 4, QTableWidgetItem(report.get('status', '')))
            table.setItem(row, 5, QTableWidgetItem(report.get('path', '')))
    
    def _open_selected_report(self):
        """打开选中的报告"""
        table = self._ui_components['report_table']
        current_row = table.currentRow()
        
        if current_row >= 0 and current_row < len(self._generated_reports):
            report = self._generated_reports[current_row]
            report_path = report.get('path', '')
            
            if Path(report_path).exists():
                # 这里应该使用系统默认程序打开文件
                self.logger.info(f"打开报告: {report_path}")
            else:
                QMessageBox.warning(self._widget, "警告", "报告文件不存在")
    
    def _delete_selected_report(self):
        """删除选中的报告"""
        table = self._ui_components['report_table']
        current_row = table.currentRow()
        
        if current_row >= 0 and current_row < len(self._generated_reports):
            reply = QMessageBox.question(
                self._widget, 
                "确认", 
                "确定要删除选中的报告吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                del self._generated_reports[current_row]
                self._refresh_report_list()
                self.logger.info("报告已删除")
    
    def _new_template(self):
        """新建模板"""
        # 这里应该打开新建模板对话框
        self.logger.info("新建模板")
    
    def _import_template(self):
        """导入模板"""
        # 这里应该实现模板导入功能
        self.logger.info("导入模板")
    
    def _export_template(self):
        """导出模板"""
        # 这里应该实现模板导出功能
        self.logger.info("导出模板")
    
    def _save_template(self):
        """保存模板"""
        # 这里应该实现模板保存功能
        self.logger.info("保存模板")
    
    def _reset_template(self):
        """重置模板"""
        # 这里应该实现模板重置功能
        self.logger.info("重置模板")
    
    def _on_template_changed(self, template_name: str):
        """处理模板改变"""
        self._current_template = template_name
        self.template_changed.emit(template_name)
        
        # 更新内容预览
        self._preview_content()
    
    def _on_progress_updated(self, progress: int):
        """处理进度更新"""
        self._generation_progress = progress
        self._ui_components['progress_bar'].setValue(progress)
        self._ui_components['progress_label'].setText(f"生成中... {progress}%")
    
    def _on_report_completed(self, report_path: str, report_info: Dict[str, Any]):
        """处理报告生成完成"""
        self._is_generating = False
        self._update_generation_ui(False)
        
        # 添加到报告列表
        report_data = {
            'name': Path(report_path).name,
            'format': self._report_config.get('format', 'PDF'),
            'size': report_info.get('size', 0),
            'created_time': report_info.get('created_time', datetime.now()),
            'status': '已完成',
            'path': report_path
        }
        
        self._generated_reports.append(report_data)
        self._refresh_report_list()
        
        self.report_generated.emit(report_path, report_info)
        
        # 显示完成消息
        QMessageBox.information(
            self._widget, 
            "完成", 
            f"报告生成完成！\n保存路径: {report_path}"
        )
        
        self.logger.info(f"报告生成完成: {report_path}")
    
    def _on_generation_error(self, error_message: str):
        """处理生成错误"""
        self._is_generating = False
        self._update_generation_ui(False)
        
        QMessageBox.critical(self._widget, "错误", f"报告生成失败: {error_message}")
        self.logger.error(f"报告生成失败: {error_message}")
    
    def _on_report_generated(self, report_path: str, report_info: Dict[str, Any]):
        """处理报告生成信号"""
        self.logger.info(f"报告生成信号: {report_path}")
    
    def _on_generation_completed(self, result: Dict[str, Any]):
        """处理生成完成信号"""
        self.logger.info(f"生成完成: {result}")
    
    def get_report_config(self) -> Dict[str, Any]:
        """获取报告配置"""
        return self._report_config.copy()
    
    def get_generated_reports(self) -> List[Dict[str, Any]]:
        """获取已生成的报告列表"""
        return self._generated_reports.copy()
    
    def is_generating(self) -> bool:
        """检查是否正在生成"""
        return self._is_generating
    
    def cleanup(self):
        """清理资源"""
        if self._generation_worker:
            self._generation_worker.cancel()
            self._generation_worker.wait()
            self._generation_worker = None
        
        if self._report_interface:
            self._report_interface.deleteLater()
        
        if self._widget:
            self._widget.deleteLater()
        
        self.logger.info("报告输出控制器清理完成")