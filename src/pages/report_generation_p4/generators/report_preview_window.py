"""
报告预览窗口
提供更丰富的报告预览功能，包括模板信息展示
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QTextEdit, QLabel, QPushButton, QGroupBox, QScrollArea,
    QFrame, QSplitter, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont, QDesktopServices
from typing import Optional

# 尝试导入WebEngine用于显示HTML/PDF
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False


class ReportPreviewWindow(QDialog):
    """增强的报告预览窗口"""
    
    def __init__(self, report_data, template, config, output_format="PDF", parent=None):
        super().__init__(parent)
        self.report_data = report_data
        self.template = template
        self.config = config
        self.output_format = output_format
        self.preview_file_path = None
        
        self.setWindowTitle(f"报告预览 - {output_format}格式")
        self.setModal(True)
        self.resize(1000, 750)
        
        self._init_ui()
        self._load_preview_content()
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("📋 报告预览")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 主内容区域
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：模板信息面板
        self._create_template_info_panel(splitter)
        
        # 右侧：预览内容
        self._create_preview_panel(splitter)
        
        # 设置分割器比例
        splitter.setSizes([250, 650])
        layout.addWidget(splitter)
        
        # 底部按钮
        self._create_button_panel(layout)
    
    def _create_template_info_panel(self, parent):
        """创建模板信息面板"""
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        # 模板信息组
        template_group = QGroupBox("🎨 使用的模板")
        template_layout = QVBoxLayout(template_group)
        
        if self.template:
            # 模板名称
            name_label = QLabel(f"名称: {self.template.template_name}")
            name_label.setStyleSheet("font-weight: bold; color: #2E7D32;")
            template_layout.addWidget(name_label)
            
            # 模板类型
            type_label = QLabel(f"类型: {self.template.template_type.value}")
            template_layout.addWidget(type_label)
            
            # 权限级别
            permission_label = QLabel(f"权限: {self.template.permission_level.value}")
            template_layout.addWidget(permission_label)
            
            # 模板描述
            desc_title = QLabel("描述:")
            desc_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
            template_layout.addWidget(desc_title)
            
            desc_text = QLabel(self.template.description)
            desc_text.setWordWrap(True)
            desc_text.setStyleSheet("color: #555; margin-left: 10px;")
            template_layout.addWidget(desc_text)
            
            # 包含内容
            content_title = QLabel("包含内容:")
            content_title.setStyleSheet("font-weight: bold; margin-top: 15px;")
            template_layout.addWidget(content_title)
            
            content_items = []
            if self.template.include_workpiece_info:
                content_items.append("✓ 工件信息")
            if self.template.include_quality_summary:
                content_items.append("✓ 质量汇总")
            if self.template.include_qualified_holes:
                content_items.append("✓ 合格孔位")
            if self.template.include_unqualified_holes:
                content_items.append("✓ 不合格孔位")
            if self.template.include_defect_analysis:
                content_items.append("✓ 缺陷分析")
            if self.template.include_manual_reviews:
                content_items.append("✓ 人工复检")
            if self.template.include_charts:
                content_items.append("✓ 图表")
            if self.template.include_endoscope_images:
                content_items.append("✓ 内窥镜图像")
            
            for item in content_items:
                item_label = QLabel(item)
                item_label.setStyleSheet("color: #2E7D32; margin-left: 10px;")
                template_layout.addWidget(item_label)
        else:
            no_template_label = QLabel("未选择模板")
            no_template_label.setStyleSheet("color: #F44336;")
            template_layout.addWidget(no_template_label)
        
        info_layout.addWidget(template_group)
        info_layout.addStretch()
        
        parent.addWidget(info_widget)
    
    def _create_preview_panel(self, parent):
        """创建预览面板"""
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        # 标签页
        tab_widget = QTabWidget()
        
        # 报告内容预览
        self._create_content_preview_tab(tab_widget)
        
        # 数据概览
        self._create_data_overview_tab(tab_widget)
        
        preview_layout.addWidget(tab_widget)
        parent.addWidget(preview_widget)
    
    def _create_content_preview_tab(self, tab_widget):
        """创建内容预览标签页"""
        content_tab = QWidget()
        content_layout = QVBoxLayout(content_tab)
        
        # 根据格式和可用性选择预览方式
        if WEB_ENGINE_AVAILABLE and self.output_format in ["PDF", "HTML"]:
            # 使用Web引擎显示
            self.preview_widget = QWebEngineView()
            content_layout.addWidget(self.preview_widget)
        else:
            # 使用文本显示或外部查看器
            preview_container = QVBoxLayout()
            
            # 格式提示
            format_label = QLabel(f"📋 {self.output_format} 格式预览")
            format_label.setStyleSheet("font-weight: bold; color: #2E7D32; margin: 5px;")
            preview_container.addWidget(format_label)
            
            if self.output_format == "PDF":
                # PDF预览提示和打开按钮
                pdf_info = QLabel("PDF文件将在外部应用程序中打开以获得最佳预览效果")
                pdf_info.setStyleSheet("color: #666; margin: 5px;")
                preview_container.addWidget(pdf_info)
                
                self.open_external_btn = QPushButton("🔍 在外部应用中预览PDF")
                self.open_external_btn.clicked.connect(self._open_external_preview)
                preview_container.addWidget(self.open_external_btn)
            
            # 文本预览区域（作为备选）
            self.preview_text = QTextEdit()
            self.preview_text.setReadOnly(True)
            self.preview_text.setFont(QFont("Consolas", 10))
            preview_container.addWidget(self.preview_text, 1)  # 设置拉伸因子
            
            preview_widget = QWidget()
            preview_widget.setLayout(preview_container)
            content_layout.addWidget(preview_widget)
        
        tab_widget.addTab(content_tab, f"📄 {self.output_format} 预览")
    
    def _create_data_overview_tab(self, tab_widget):
        """创建数据概览标签页"""
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        
        if self.report_data and hasattr(self.report_data, 'quality_summary'):
            summary = self.report_data.quality_summary
            
            # 关键指标
            metrics_group = QGroupBox("📊 关键指标")
            metrics_layout = QVBoxLayout(metrics_group)
            
            total_label = QLabel(f"总孔位数: {getattr(summary, 'total_holes', '--')}")
            qualified_label = QLabel(f"合格孔位: {getattr(summary, 'qualified_holes', '--')}")
            unqualified_label = QLabel(f"不合格孔位: {getattr(summary, 'unqualified_holes', '--')}")
            rate_label = QLabel(f"合格率: {getattr(summary, 'qualification_rate', '--')}%")
            
            for label in [total_label, qualified_label, unqualified_label, rate_label]:
                label.setStyleSheet("font-size: 14px; margin: 5px;")
                metrics_layout.addWidget(label)
            
            overview_layout.addWidget(metrics_group)
        
        # 工件信息
        if self.report_data and hasattr(self.report_data, 'workpiece_info'):
            workpiece = self.report_data.workpiece_info
            
            workpiece_group = QGroupBox("🔧 工件信息")
            workpiece_layout = QVBoxLayout(workpiece_group)
            
            id_label = QLabel(f"工件ID: {getattr(workpiece, 'workpiece_id', '--')}")
            name_label = QLabel(f"名称: {getattr(workpiece, 'name', '--')}")
            type_label = QLabel(f"类型: {getattr(workpiece, 'type', '--')}")
            
            for label in [id_label, name_label, type_label]:
                label.setStyleSheet("font-size: 12px; margin: 3px;")
                workpiece_layout.addWidget(label)
            
            overview_layout.addWidget(workpiece_group)
        
        overview_layout.addStretch()
        tab_widget.addTab(overview_tab, "📈 数据概览")
    
    def _create_button_panel(self, parent_layout):
        """创建按钮面板"""
        button_layout = QHBoxLayout()
        
        # 左侧：信息标签
        info_label = QLabel("💡 这是基于选定模板的预览内容")
        info_label.setStyleSheet("color: #666; font-size: 11px;")
        button_layout.addWidget(info_label)
        
        button_layout.addStretch()
        
        # 右侧：操作按钮
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        
        self.generate_btn = QPushButton("生成报告")
        self.generate_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        self.generate_btn.clicked.connect(self._generate_report)
        
        button_layout.addWidget(self.close_btn)
        button_layout.addWidget(self.generate_btn)
        
        parent_layout.addLayout(button_layout)
    
    def _load_preview_content(self):
        """加载预览内容"""
        try:
            # 使用独立的预览生成器
            from src.modules.report_preview_generator import ReportPreviewGenerator
            
            generator = ReportPreviewGenerator()
            self.preview_file_path = generator.generate_preview_file(
                self.report_data, 
                self.template, 
                self.output_format
            )
            
            if self.preview_file_path:
                self._display_preview_file()
            else:
                self._display_fallback_preview()
                
        except Exception as e:
            print(f"❌ 加载预览内容失败: {e}")
            self._display_fallback_preview()
    
    def _display_preview_file(self):
        """显示预览文件"""
        if not self.preview_file_path:
            return
            
        try:
            if WEB_ENGINE_AVAILABLE and hasattr(self, 'preview_widget'):
                # 使用WebEngine显示
                file_url = QUrl.fromLocalFile(self.preview_file_path)
                self.preview_widget.load(file_url)
            elif hasattr(self, 'preview_text'):
                # 显示在文本框中（用于HTML格式）
                if self.preview_file_path.endswith('.html'):
                    with open(self.preview_file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    self.preview_text.setHtml(html_content)
                else:
                    with open(self.preview_file_path, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                    self.preview_text.setPlainText(text_content)
        except Exception as e:
            print(f"❌ 显示预览文件失败: {e}")
            self._display_fallback_preview()
    
    def _display_fallback_preview(self):
        """显示回退预览"""
        if hasattr(self, 'preview_text'):
            fallback_text = self._generate_preview_text()
            self.preview_text.setPlainText(fallback_text)
    
    def _open_external_preview(self):
        """在外部应用程序中打开预览"""
        if self.preview_file_path:
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.preview_file_path))
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法打开预览文件: {str(e)}")
    
    def _generate_preview_text(self) -> str:
        """生成预览文本"""
        lines = []
        lines.append("=" * 60)
        lines.append("质量检测报告预览")
        lines.append("=" * 60)
        lines.append("")
        
        if self.template:
            lines.append(f"报告模板: {self.template.template_name}")
            lines.append(f"模板类型: {self.template.template_type.value}")
            lines.append("")
        
        if self.report_data:
            # 工件信息
            if hasattr(self.report_data, 'workpiece_info') and self.template and self.template.include_workpiece_info:
                workpiece = self.report_data.workpiece_info
                lines.append("1. 工件信息")
                lines.append("-" * 20)
                lines.append(f"工件ID: {getattr(workpiece, 'workpiece_id', '--')}")
                lines.append(f"工件名称: {getattr(workpiece, 'name', '--')}")
                lines.append(f"工件类型: {getattr(workpiece, 'type', '--')}")
                if hasattr(workpiece, 'material'):
                    lines.append(f"材质: {workpiece.material}")
                lines.append("")
            
            # 质量汇总
            if hasattr(self.report_data, 'quality_summary') and self.template and self.template.include_quality_summary:
                summary = self.report_data.quality_summary
                lines.append("2. 质量汇总")
                lines.append("-" * 20)
                lines.append(f"总孔位数: {getattr(summary, 'total_holes', '--')}")
                lines.append(f"合格孔位: {getattr(summary, 'qualified_holes', '--')}")
                lines.append(f"不合格孔位: {getattr(summary, 'unqualified_holes', '--')}")
                lines.append(f"合格率: {getattr(summary, 'qualification_rate', '--')}%")
                if hasattr(summary, 'holes_with_defects'):
                    lines.append(f"有缺陷孔位: {summary.holes_with_defects}")
                if hasattr(summary, 'manual_review_count'):
                    lines.append(f"人工复检数: {summary.manual_review_count}")
                lines.append("")
            
            # 不合格孔位详情
            if (hasattr(self.report_data, 'unqualified_holes') and 
                self.template and self.template.include_unqualified_holes and
                self.report_data.unqualified_holes):
                lines.append("3. 不合格孔位详情")
                lines.append("-" * 20)
                for i, hole in enumerate(self.report_data.unqualified_holes[:5], 1):  # 限制显示前5个
                    hole_id = hole.get('hole_id', f'孔位{i}') if isinstance(hole, dict) else f'孔位{i}'
                    lines.append(f"- {hole_id}")
                
                if len(self.report_data.unqualified_holes) > 5:
                    lines.append(f"... 还有 {len(self.report_data.unqualified_holes) - 5} 个不合格孔位")
                lines.append("")
        
        # 报告生成信息
        if self.report_data and hasattr(self.report_data, 'generated_at'):
            lines.append("报告生成信息")
            lines.append("-" * 20)
            lines.append(f"生成时间: {self.report_data.generated_at}")
            if hasattr(self.report_data, 'generated_by'):
                lines.append(f"生成者: {self.report_data.generated_by}")
            if hasattr(self.report_data, 'report_version'):
                lines.append(f"版本: {self.report_data.report_version}")
        
        lines.append("")
        lines.append("=" * 60)
        lines.append("预览结束")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _generate_report(self):
        """触发报告生成"""
        # 这里可以发射信号或调用父窗口的生成方法
        self.accept()  # 关闭预览窗口，让主窗口处理报告生成