"""
报告配置面板组件
提供报告生成的各种配置选项
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QLabel, QPushButton, QComboBox, QCheckBox
)
from PySide6.QtCore import Signal

# 从assets/old目录导入报告配置相关模块，使用容错导入
try:
    from assets.old.report_models import ReportType, ReportFormat, ReportConfiguration
except ImportError:
    # 如果导入失败，从主页面导入模拟版本
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from report_generation_page import ReportType, ReportFormat, ReportConfiguration


class ReportConfigPanel(QWidget):
    """报告配置面板"""
    
    # 信号
    workpiece_changed = Signal(str)  # 工件ID变更
    preview_requested = Signal()     # 预览请求
    generate_requested = Signal()    # 生成请求
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._init_connections()
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 工件选择
        workpiece_group = QGroupBox("1. 工件选择")
        workpiece_layout = QVBoxLayout(workpiece_group)
        
        self.workpiece_combo = QComboBox()
        self.workpiece_combo.setToolTip("选择要生成报告的工件")
        workpiece_layout.addWidget(QLabel("选择工件:"))
        workpiece_layout.addWidget(self.workpiece_combo)
        
        layout.addWidget(workpiece_group)
        
        # 报告类型配置
        type_group = QGroupBox("2. 报告类型")
        type_layout = QVBoxLayout(type_group)
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "综合报告", "工件汇总报告", "质量分析报告", "缺陷分析报告"
        ])
        type_layout.addWidget(self.report_type_combo)
        
        layout.addWidget(type_group)
        
        # 报告格式配置
        format_group = QGroupBox("3. 输出格式")
        format_layout = QVBoxLayout(format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF", "HTML", "Excel", "Word"])
        format_layout.addWidget(self.format_combo)
        
        # PDF状态提示
        self.pdf_status_label = QLabel()
        self.pdf_status_label.setWordWrap(True)
        self.pdf_status_label.setObjectName("StatusLabel")
        format_layout.addWidget(self.pdf_status_label)
        
        layout.addWidget(format_group)
        
        # 内容选项
        content_group = QGroupBox("4. 报告内容")
        content_layout = QVBoxLayout(content_group)
        
        # 创建复选框
        self.include_workpiece_info = QCheckBox("包含工件信息")
        self.include_quality_summary = QCheckBox("包含质量汇总")
        self.include_qualified_holes = QCheckBox("包含合格孔位")
        self.include_unqualified_holes = QCheckBox("包含不合格孔位")
        self.include_defect_analysis = QCheckBox("包含缺陷分析")
        self.include_manual_reviews = QCheckBox("包含人工复检记录")
        self.include_charts = QCheckBox("包含图表")
        self.include_endoscope_images = QCheckBox("包含内窥镜图像")
        
        # 默认全部选中
        for checkbox in [self.include_workpiece_info, self.include_quality_summary,
                        self.include_qualified_holes, self.include_unqualified_holes,
                        self.include_defect_analysis, self.include_manual_reviews,
                        self.include_charts, self.include_endoscope_images]:
            checkbox.setChecked(True)
            content_layout.addWidget(checkbox)
        
        layout.addWidget(content_group)
        
        # 生成按钮
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("预览报告")
        self.generate_btn = QPushButton("生成报告")
        
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.generate_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
    
    def _init_connections(self):
        """初始化信号连接"""
        self.workpiece_combo.currentTextChanged.connect(self.workpiece_changed.emit)
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        self.preview_btn.clicked.connect(self.preview_requested.emit)
        self.generate_btn.clicked.connect(self.generate_requested.emit)
    
    def _on_format_changed(self, format_text: str):
        """格式选择改变"""
        # 这里可以添加PDF依赖检查等逻辑
        self.pdf_status_label.setText(f"📄 将生成{format_text}格式报告")
    
    def add_workpiece(self, workpiece_id: str):
        """添加工件到选择列表"""
        if workpiece_id not in [self.workpiece_combo.itemText(i) for i in range(self.workpiece_combo.count())]:
            self.workpiece_combo.addItem(workpiece_id)
    
    def set_current_workpiece(self, workpiece_id: str):
        """设置当前选中的工件"""
        index = self.workpiece_combo.findText(workpiece_id)
        if index >= 0:
            self.workpiece_combo.setCurrentIndex(index)
    
    def get_current_workpiece(self) -> Optional[str]:
        """获取当前选中的工件ID"""
        return self.workpiece_combo.currentText() if self.workpiece_combo.count() > 0 else None
    
    def create_report_configuration(self) -> ReportConfiguration:
        """创建报告配置"""
        # 映射报告类型
        type_mapping = {
            "综合报告": ReportType.COMPREHENSIVE,
            "工件汇总报告": ReportType.WORKPIECE_SUMMARY,
            "质量分析报告": ReportType.QUALITY_ANALYSIS,
            "缺陷分析报告": ReportType.DEFECT_ANALYSIS
        }
        
        # 映射报告格式
        format_mapping = {
            "PDF": ReportFormat.PDF,
            "HTML": ReportFormat.HTML,
            "Excel": ReportFormat.EXCEL,
            "Word": ReportFormat.WORD
        }
        
        return ReportConfiguration(
            report_type=type_mapping[self.report_type_combo.currentText()],
            report_format=format_mapping[self.format_combo.currentText()],
            include_workpiece_info=self.include_workpiece_info.isChecked(),
            include_quality_summary=self.include_quality_summary.isChecked(),
            include_qualified_holes=self.include_qualified_holes.isChecked(),
            include_unqualified_holes=self.include_unqualified_holes.isChecked(),
            include_defect_analysis=self.include_defect_analysis.isChecked(),
            include_manual_reviews=self.include_manual_reviews.isChecked(),
            include_charts=self.include_charts.isChecked(),
            include_endoscope_images=self.include_endoscope_images.isChecked()
        )
    
    def set_generate_enabled(self, enabled: bool):
        """设置生成按钮启用状态"""
        self.generate_btn.setEnabled(enabled)
    
    def update_pdf_status(self, pdf_available: bool, format_text: str):
        """更新PDF状态提示"""
        if format_text == "PDF" and not pdf_available:
            self.pdf_status_label.setText("⚠️ 选择PDF格式但未安装支持库，将回退到文本格式")
        elif format_text == "PDF" and pdf_available:
            self.pdf_status_label.setText("✅ PDF格式已就绪")
        else:
            self.pdf_status_label.setText(f"📄 将生成{format_text}格式报告")