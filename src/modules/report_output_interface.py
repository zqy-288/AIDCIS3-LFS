"""
报告输出界面
第四级界面 - 报告生成与管理
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QGroupBox, QTextEdit,
    QTableWidget, QTableWidgetItem, QProgressBar, QSplitter,
    QCheckBox, QSpinBox, QLineEdit, QFileDialog, QMessageBox,
    QTabWidget, QScrollArea, QFrame, QHeaderView, QDialog, QMenu
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QPixmap, QPalette, QAction

from .report_models import (
    ReportType, ReportFormat, ReportConfiguration,
    ReportInstance, ReportData
)
from .report_generator import ReportGenerator
from .report_history_manager import ReportHistoryManager
from .report_templates import ReportTemplateManager

try:
    from .pdf_report_generator import PDFReportGenerator
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class ReportGenerationWorker(QThread):
    """报告生成工作线程"""

    progress_updated = Signal(int)
    status_updated = Signal(str)
    report_completed = Signal(str)  # 报告文件路径
    error_occurred = Signal(str)
    
    def __init__(self, workpiece_id: str, config: ReportConfiguration):
        super().__init__()
        self.workpiece_id = workpiece_id
        self.config = config
        self.generator = ReportGenerator()
    
    def run(self):
        """执行报告生成"""
        try:
            self.status_updated.emit("正在收集数据...")
            self.progress_updated.emit(10)
            
            # 收集报告数据
            report_data = self.generator.collect_workpiece_data(self.workpiece_id)
            self.progress_updated.emit(50)
            
            self.status_updated.emit("正在生成报告...")
            
            # 生成报告实例
            instance = self.generator.generate_report_instance(self.workpiece_id, self.config)
            self.progress_updated.emit(80)

            # 根据配置选择报告生成器
            if self.config.report_format == ReportFormat.PDF and PDF_AVAILABLE:
                self._generate_pdf_report(report_data, instance.output_path)
            else:
                # 回退到简单文本报告
                self._generate_simple_report(report_data, instance.output_path)
            
            self.progress_updated.emit(100)
            self.status_updated.emit("报告生成完成")
            self.report_completed.emit(instance.output_path)
            
        except Exception as e:
            self.error_occurred.emit(f"报告生成失败: {str(e)}")
    
    def _generate_simple_report(self, report_data: ReportData, output_path: str):
        """生成简单的文本报告"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("管孔检测系统 - 质量检测报告\n")
            f.write("=" * 60 + "\n\n")
            
            # 工件信息
            f.write("1. 工件信息\n")
            f.write("-" * 30 + "\n")
            f.write(f"工件ID: {report_data.workpiece_info.workpiece_id}\n")
            f.write(f"工件名称: {report_data.workpiece_info.name}\n")
            f.write(f"工件类型: {report_data.workpiece_info.type}\n")
            f.write(f"材料: {report_data.workpiece_info.material}\n")
            f.write(f"总孔位数: {report_data.workpiece_info.total_holes}\n\n")
            
            # 质量汇总
            f.write("2. 质量汇总\n")
            f.write("-" * 30 + "\n")
            summary = report_data.quality_summary
            f.write(f"总孔位数: {summary.total_holes}\n")
            f.write(f"合格孔位: {summary.qualified_holes}\n")
            f.write(f"不合格孔位: {summary.unqualified_holes}\n")
            f.write(f"合格率: {summary.qualification_rate:.2f}%\n")
            f.write(f"有缺陷孔位: {summary.holes_with_defects}\n")
            f.write(f"人工复检数: {summary.manual_review_count}\n\n")
            
            # 不合格孔位详情
            if report_data.unqualified_holes:
                f.write("3. 不合格孔位详情\n")
                f.write("-" * 30 + "\n")
                for hole in report_data.unqualified_holes:
                    f.write(f"孔位ID: {hole.hole_id}\n")
                    f.write(f"  位置: ({hole.position_x:.1f}, {hole.position_y:.1f})\n")
                    f.write(f"  合格率: {hole.qualification_rate:.2f}%\n")
                    f.write(f"  测量次数: {hole.total_count}\n")
                    f.write(f"  合格次数: {hole.qualified_count}\n\n")
            
            # 人工复检记录
            if report_data.manual_reviews:
                f.write("4. 人工复检记录\n")
                f.write("-" * 30 + "\n")
                for review in report_data.manual_reviews:
                    f.write(f"孔位ID: {review.hole_id}\n")
                    f.write(f"  复检员: {review.reviewer}\n")
                    f.write(f"  原始直径: {review.original_diameter:.4f}mm\n")
                    f.write(f"  复检直径: {review.reviewed_diameter:.4f}mm\n")
                    f.write(f"  最终判定: {review.final_judgment}\n")
                    f.write(f"  复检时间: {review.review_timestamp}\n\n")
            
            f.write(f"报告生成时间: {report_data.generated_at}\n")
            f.write(f"生成者: {report_data.generated_by}\n")

    def _generate_pdf_report(self, report_data: ReportData, output_path: str):
        """生成PDF报告"""
        try:
            pdf_generator = PDFReportGenerator()
            result_path = pdf_generator.generate_report(report_data, self.config, output_path)
            print(f"✅ PDF报告生成成功: {result_path}")
        except Exception as e:
            # 如果PDF生成失败，回退到文本报告
            print(f"❌ PDF生成失败，回退到文本报告: {e}")
            txt_path = output_path.replace('.pdf', '.txt')
            self._generate_simple_report(report_data, txt_path)
            # 抛出异常以便上层处理
            raise Exception(f"PDF生成失败，已生成文本报告: {txt_path}")


class ReportOutputInterface(QWidget):
    """报告输出界面"""

    # --- 新增代码：定义一个信号，用于向外发送状态消息 ---
    # 这个信号可以传递一个字符串参数
    status_updated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_workpiece_id = None
        self.report_generator = ReportGenerator()
        self.history_manager = ReportHistoryManager()
        self.template_manager = ReportTemplateManager()
        self.generation_worker = None
        
        self.setup_ui()
        self.setup_connections()
        self.load_workpiece_list()
    
    def setup_ui(self):
        """设置用户界面"""
        # 使用主题管理器的样式，不需要内联样式

        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("报告输出 - 质量检测报告生成与管理")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("MainTitle")  # 设置对象名用于QSS样式
        layout.addWidget(title_label)
        
        # 主内容区域
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：配置面板
        self.create_config_panel(splitter)
        
        # 右侧：预览和管理面板
        self.create_preview_panel(splitter)
        
        # 设置分割器比例
        splitter.setSizes([400, 600])
        layout.addWidget(splitter)
    
    def create_config_panel(self, parent):
        """创建配置面板"""
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        
        # 步骤1：工件选择
        step1_header = self.create_step_header("1", "工件选择")
        config_layout.addWidget(step1_header)

        workpiece_group = QGroupBox()  # 移除标题，使用自定义标题
        workpiece_layout = QVBoxLayout(workpiece_group)

        self.workpiece_combo = QComboBox()
        self.workpiece_combo.currentTextChanged.connect(self.on_workpiece_changed)
        self.workpiece_combo.setToolTip("选择要生成报告的工件\n系统会自动扫描Data目录下的可用工件")
        workpiece_layout.addWidget(QLabel("选择工件:"))
        workpiece_layout.addWidget(self.workpiece_combo)

        config_layout.addWidget(workpiece_group)

        # 步骤2：模板选择
        step2_header = self.create_step_header("2", "报告模板")
        config_layout.addWidget(step2_header)

        template_group = QGroupBox()  # 移除标题，使用自定义标题
        template_layout = QVBoxLayout(template_group)

        self.template_combo = QComboBox()
        self.template_combo.addItem("自定义配置")

        # 添加预定义模板
        display_names = self.template_manager.get_template_display_names()
        for template_id, display_name in display_names.items():
            self.template_combo.addItem(display_name)

        self.template_combo.currentTextChanged.connect(self.on_template_text_changed)
        self.template_combo.setToolTip("选择预定义的报告模板或使用自定义配置")
        template_layout.addWidget(self.template_combo)

        config_layout.addWidget(template_group)

        # 步骤3：报告类型配置
        step3_header = self.create_step_header("3", "报告类型")
        config_layout.addWidget(step3_header)

        type_group = QGroupBox()  # 移除标题，使用自定义标题
        type_layout = QVBoxLayout(type_group)

        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "综合报告", "工件汇总报告", "质量分析报告", "缺陷分析报告"
        ])
        self.report_type_combo.setToolTip(
            "选择报告类型:\n"
            "• 综合报告: 包含所有检测信息的完整报告\n"
            "• 工件汇总报告: 重点关注工件基本信息和整体质量状况\n"
            "• 质量分析报告: 专注于质量数据分析和统计\n"
            "• 缺陷分析报告: 重点分析缺陷数据和异常情况"
        )
        type_layout.addWidget(self.report_type_combo)

        config_layout.addWidget(type_group)
        
        # 步骤4：报告格式配置
        step4_header = self.create_step_header("4", "输出格式")
        config_layout.addWidget(step4_header)

        format_group = QGroupBox()  # 移除标题，使用自定义标题
        format_layout = QVBoxLayout(format_group)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF", "HTML", "Excel", "Word"])
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        self.format_combo.setToolTip(
            "选择输出格式:\n"
            "• PDF: 专业的报告格式，适合打印和存档\n"
            "• HTML: 网页格式，便于在线查看和分享\n"
            "• Excel: 表格格式，便于数据分析\n"
            "• Word: 文档格式，便于编辑和修改"
        )
        format_layout.addWidget(self.format_combo)

        # PDF依赖状态提示
        self.pdf_status_label = QLabel()
        self.pdf_status_label.setWordWrap(True)
        self.pdf_status_label.setObjectName("StatusLabel")  # 设置对象名用于QSS样式
        format_layout.addWidget(self.pdf_status_label)

        # 安装PDF依赖按钮
        self.install_pdf_btn = QPushButton("安装PDF支持")
        self.install_pdf_btn.setVisible(False)
        self.install_pdf_btn.clicked.connect(self.show_pdf_install_guide)
        format_layout.addWidget(self.install_pdf_btn)

        config_layout.addWidget(format_group)
        
        # 步骤5：内容选项
        step5_header = self.create_step_header("5", "报告内容")
        config_layout.addWidget(step5_header)

        content_group = QGroupBox()  # 移除标题，使用自定义标题
        content_layout = QGridLayout(content_group)  # 使用栅格布局替换垂直布局
        content_layout.setSpacing(10)

        # 将复选框放入两列的栅格中
        checkboxes = [
            QCheckBox("包含工件信息"), QCheckBox("包含质量汇总"),
            QCheckBox("包含合格孔位"), QCheckBox("包含不合格孔位"),
            QCheckBox("包含缺陷分析"), QCheckBox("包含人工复检记录"),
            QCheckBox("包含图表"), QCheckBox("包含内窥镜图像")
        ]

        # 为了方便，我们将这些复选框的引用保存到self
        self.include_workpiece_info, self.include_quality_summary, \
        self.include_qualified_holes, self.include_unqualified_holes, \
        self.include_defect_analysis, self.include_manual_reviews, \
        self.include_charts, self.include_endoscope_images = checkboxes

        for i, checkbox in enumerate(checkboxes):
            checkbox.setChecked(True)
            row = i // 2  # 计算行号
            col = i % 2   # 计算列号 (0 或 1)
            content_layout.addWidget(checkbox, row, col)
        
        config_layout.addWidget(content_group)
        
        # 生成按钮
        button_layout = QGridLayout()  # 确保使用的是 QGridLayout
        button_layout.setSpacing(15)

        self.preview_btn = QPushButton("预览报告")
        self.preview_btn.setProperty("class", "PrimaryAction")  
        self.preview_btn.clicked.connect(self.preview_report)
        self.preview_btn.setToolTip("预览报告内容结构，无需生成实际文件")

        self.generate_btn = QPushButton("生成报告")
        self.generate_btn.setProperty("class", "PrimaryAction")  
        self.generate_btn.clicked.connect(self.generate_report)
        self.generate_btn.setToolTip("根据当前配置生成完整的报告文件")

        # 将按钮添加到网格的不同列中
        button_layout.addWidget(self.preview_btn, 0, 0)  # 第0行，第0列
        button_layout.addWidget(self.generate_btn, 0, 1)  # 第0行，第1列

        # (核心步骤) 设置两列的拉伸因子相同，强制它们等宽
        button_layout.setColumnStretch(0, 1)
        button_layout.setColumnStretch(1, 1)

        config_layout.addLayout(button_layout)
        config_layout.addStretch()
        
        parent.addWidget(config_widget)

    def create_step_header(self, number_text, title_text):
        """创建带序号的步骤标题"""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        num_label = QLabel(number_text)
        num_label.setObjectName("StepNumberLabel")

        title_label = QLabel(title_text)
        title_label.setObjectName("StepTitleLabel")

        header_layout.addWidget(num_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        return header_widget

    def create_preview_panel(self, parent):
        """创建预览面板"""
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        
        # 标签页
        tab_widget = QTabWidget()
        
        # 数据预览标签页
        self.create_data_preview_tab(tab_widget)
        
        # 报告管理标签页
        self.create_report_management_tab(tab_widget)
        
        preview_layout.addWidget(tab_widget)
        parent.addWidget(preview_widget)
    
    def create_data_preview_tab(self, tab_widget):
        """创建数据预览标签页"""
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        
        # 数据状态指示器
        status_layout = QHBoxLayout()
        self.data_status_label = QLabel("📊 数据状态: 未加载")
        self.data_status_label.setObjectName("DataStatusLabel")  # 设置对象名用于QSS样式
        status_layout.addWidget(self.data_status_label)
        status_layout.addStretch()
        preview_layout.addLayout(status_layout)

        # 数据汇总显示 - 升级为可视化仪表盘
        summary_group = QGroupBox("数据汇总")
        summary_layout = QVBoxLayout(summary_group)

        # 创建一个专门的仪表盘Widget
        dashboard_widget = QWidget()
        dashboard_layout = QGridLayout(dashboard_widget)  # 使用栅格布局，灵活对齐
        dashboard_layout.setSpacing(15)

        # 1. 工件信息（保持简洁）
        self.db_workpiece_id_label = QLabel("工件ID: --")
        self.db_workpiece_type_label = QLabel("类型: --")
        dashboard_layout.addWidget(self.db_workpiece_id_label, 0, 0, 1, 2)  # 跨2列
        dashboard_layout.addWidget(self.db_workpiece_type_label, 1, 0, 1, 2)

        # 2. 关键指标 (大号数字)
        self.db_total_holes_label = QLabel("0")
        self.db_qualified_holes_label = QLabel("0")
        self.db_unqualified_holes_label = QLabel("0")
        self.db_total_holes_label.setObjectName("DashboardNumber")
        self.db_qualified_holes_label.setObjectName("DashboardNumber")
        self.db_unqualified_holes_label.setObjectName("DashboardNumber")
        # 使用主题管理器的颜色而不是硬编码颜色
        try:
            from .theme_manager import theme_manager
            colors = theme_manager.COLORS
            self.db_qualified_holes_label.setStyleSheet(f"color: {colors['success']};")  # 合格用绿色
            self.db_unqualified_holes_label.setStyleSheet(f"color: {colors['error']};")  # 不合格用红色
        except ImportError:
            # 备用颜色
            self.db_qualified_holes_label.setStyleSheet("color: #2ECC71;")  # 合格用绿色
            self.db_unqualified_holes_label.setStyleSheet("color: #E74C3C;")  # 不合格用红色

        dashboard_layout.addWidget(QLabel("总检测孔数"), 2, 0)
        dashboard_layout.addWidget(self.db_total_holes_label, 3, 0)
        dashboard_layout.addWidget(QLabel("合格孔数"), 2, 1)
        dashboard_layout.addWidget(self.db_qualified_holes_label, 3, 1)
        dashboard_layout.addWidget(QLabel("不合格孔数"), 2, 2)
        dashboard_layout.addWidget(self.db_unqualified_holes_label, 3, 2)

        # 3. 合格率 (使用进度条可视化)
        dashboard_layout.addWidget(QLabel("合格率"), 4, 0)
        self.db_qualification_rate_bar = QProgressBar()
        self.db_qualification_rate_bar.setObjectName("DashboardRateBar")
        self.db_qualification_rate_bar.setFormat("%.1f %%" % 0)  # 设置显示格式
        dashboard_layout.addWidget(self.db_qualification_rate_bar, 5, 0, 1, 3)  # 跨3列

        summary_layout.addWidget(dashboard_widget)
        preview_layout.addWidget(summary_group)
        
        # 孔位数据表格
        table_group = QGroupBox("孔位数据")
        table_layout = QVBoxLayout(table_group)

        self.hole_data_table = QTableWidget()
        # 隐藏默认的垂直表头，解决左上角空白问题
        self.hole_data_table.verticalHeader().setVisible(False)
        self.hole_data_table.setColumnCount(7)  # 增加序号列，从6列改为7列
        self.hole_data_table.setHorizontalHeaderLabels([
            "序号", "孔位ID", "位置(X,Y)", "合格率", "测量次数", "状态", "最后测量时间"
        ])
        
        # 设置表格属性
        header = self.hole_data_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.hole_data_table.setAlternatingRowColors(True)
        self.hole_data_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        table_layout.addWidget(self.hole_data_table)
        preview_layout.addWidget(table_group)
        
        tab_widget.addTab(preview_tab, "数据预览")
    
    def create_report_management_tab(self, tab_widget):
        """创建报告管理标签页"""
        management_tab = QWidget()
        management_layout = QVBoxLayout(management_tab)

        # 工具栏
        toolbar_layout = QHBoxLayout()

        self.refresh_history_btn = QPushButton("刷新")
        self.refresh_history_btn.clicked.connect(self.refresh_history)
        toolbar_layout.addWidget(self.refresh_history_btn)

        self.cleanup_history_btn = QPushButton("清理失效记录")
        self.cleanup_history_btn.clicked.connect(self.cleanup_history)
        toolbar_layout.addWidget(self.cleanup_history_btn)

        self.export_history_btn = QPushButton("导出历史记录")
        self.export_history_btn.clicked.connect(self.export_history)
        toolbar_layout.addWidget(self.export_history_btn)

        toolbar_layout.addStretch()
        management_layout.addLayout(toolbar_layout)

        # 报告历史表格
        history_group = QGroupBox("报告历史")
        history_layout = QVBoxLayout(history_group)

        self.report_history_table = QTableWidget()
        # 隐藏默认的垂直表头，解决左上角空白问题
        self.report_history_table.verticalHeader().setVisible(False)

        # --- 修改列数和列标题，移除"操作"列 ---
        self.report_history_table.setColumnCount(6)  # 修改后：减少一列
        self.report_history_table.setHorizontalHeaderLabels([
            "序号", "生成时间", "工件ID", "状态", "文件大小", "格式"
        ])

        # --- 新增代码：启用自定义上下文菜单 ---
        self.report_history_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.report_history_table.customContextMenuRequested.connect(self.show_history_context_menu)
        # ------------------------------------

        header = self.report_history_table.horizontalHeader()
        # 重新设置列的拉伸模式
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 让工件ID列占据更多空间
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        # 第6列（操作列）已被删除，无需设置

        self.report_history_table.setAlternatingRowColors(True)
        self.report_history_table.setSelectionBehavior(QTableWidget.SelectRows)

        history_layout.addWidget(self.report_history_table)
        management_layout.addWidget(history_group)

        tab_widget.addTab(management_tab, "报告管理")
    

    
    def setup_connections(self):
        """设置信号连接"""
        # 检查PDF依赖状态
        self.check_pdf_dependencies()

        # 设置默认格式状态
        self.on_format_changed(self.format_combo.currentText())

        # 加载可用工件
        self.load_available_workpieces()

        # 加载历史记录
        self.refresh_history()
    
    def load_workpiece_list(self):
        """加载工件列表"""
        # 添加标准工件ID，该工件包含20000个孔
        # AI员工4号修改开始
        # 目前数据目录中有C001R001~C003R001三个孔的数据
        # AI员工4号修改结束
        self.workpiece_combo.addItem("WP-2025-001")

        # 设置默认选择
        if self.workpiece_combo.count() > 0:
            self.workpiece_combo.setCurrentIndex(0)
            self.on_workpiece_changed("WP-2025-001")
    
    def on_workpiece_changed(self, workpiece_id: str):
        """工件选择改变"""
        if workpiece_id:
            self.current_workpiece_id = workpiece_id
            self.load_workpiece_data(workpiece_id)
    
    def load_workpiece_data(self, workpiece_id: str):
        """加载工件数据预览"""
        try:
            # 更新状态
            self.data_status_label.setText("📊 数据状态: 正在加载...")
            self.data_status_label.setProperty("status", "loading")  # 使用属性来控制样式
            self.data_status_label.style().unpolish(self.data_status_label)
            self.data_status_label.style().polish(self.data_status_label)

            # 收集工件数据
            report_data = self.report_generator.collect_workpiece_data(workpiece_id)

            # 更新汇总信息
            self.update_summary_display(report_data)

            # 更新孔位数据表格
            self.update_hole_data_table(report_data)

            # 更新状态
            total_holes = report_data.quality_summary.total_holes
            if total_holes > 0:
                self.data_status_label.setText(f"✅ 数据状态: 已加载 ({total_holes} 个孔位)")
                self.data_status_label.setProperty("status", "success")  # 使用属性来控制样式
            else:
                self.data_status_label.setText("⚠️ 数据状态: 无有效数据")
                self.data_status_label.setProperty("status", "warning")  # 使用属性来控制样式

            # 刷新样式
            self.data_status_label.style().unpolish(self.data_status_label)
            self.data_status_label.style().polish(self.data_status_label)

        except Exception as e:
            self.data_status_label.setText("❌ 数据状态: 加载失败")
            self.data_status_label.setProperty("status", "error")  # 使用属性来控制样式
            self.data_status_label.style().unpolish(self.data_status_label)
            self.data_status_label.style().polish(self.data_status_label)
            QMessageBox.warning(self, "错误", f"加载工件数据失败: {str(e)}")
    
    def update_summary_display(self, report_data: ReportData):
        """更新汇总显示"""
        summary = report_data.quality_summary
        workpiece = report_data.workpiece_info
        
        # 填充仪表盘数据
        self.db_workpiece_id_label.setText(f"<b>工件ID:</b> {workpiece.workpiece_id}")
        self.db_workpiece_type_label.setText(f"<b>类型:</b> {workpiece.type}")

        self.db_total_holes_label.setText(str(summary.total_holes))
        self.db_qualified_holes_label.setText(str(summary.qualified_holes))
        self.db_unqualified_holes_label.setText(str(summary.unqualified_holes))

        self.db_qualification_rate_bar.setValue(int(summary.qualification_rate))
        self.db_qualification_rate_bar.setFormat(f"{summary.qualification_rate:.1f} %")
    
    def update_hole_data_table(self, report_data: ReportData):
        """更新孔位数据表格"""
        all_holes = report_data.qualified_holes + report_data.unqualified_holes
        
        self.hole_data_table.setRowCount(len(all_holes))
        
        for row, hole in enumerate(all_holes):
            # 序号列（新增）
            seq_item = QTableWidgetItem(str(row + 1))
            seq_item.setTextAlignment(Qt.AlignCenter)
            self.hole_data_table.setItem(row, 0, seq_item)

            # 孔位ID（原第0列，现在是第1列）
            self.hole_data_table.setItem(row, 1, QTableWidgetItem(hole.hole_id))

            # 位置（原第1列，现在是第2列）
            position_text = f"({hole.position_x:.1f}, {hole.position_y:.1f})"
            self.hole_data_table.setItem(row, 2, QTableWidgetItem(position_text))

            # 合格率（原第2列，现在是第3列）
            rate_text = f"{hole.qualification_rate:.1f}%"
            self.hole_data_table.setItem(row, 3, QTableWidgetItem(rate_text))

            # 测量次数（原第3列，现在是第4列）
            count_text = f"{hole.qualified_count}/{hole.total_count}"
            self.hole_data_table.setItem(row, 4, QTableWidgetItem(count_text))

            # 状态（原第4列，现在是第5列）
            status_text = "合格" if hole.is_qualified else "不合格"
            status_item = QTableWidgetItem(status_text)
            if hole.is_qualified:
                status_item.setBackground(QPalette().color(QPalette.ColorRole.Base))
            else:
                status_item.setBackground(QPalette().color(QPalette.ColorRole.AlternateBase))
            self.hole_data_table.setItem(row, 5, status_item)

            # 最后测量时间（原第5列，现在是第6列）
            time_text = hole.measurement_timestamp.strftime("%Y-%m-%d %H:%M") if hole.measurement_timestamp else "未知"
            self.hole_data_table.setItem(row, 6, QTableWidgetItem(time_text))
    
    def preview_report(self):
        """预览报告"""
        if not self.current_workpiece_id:
            QMessageBox.warning(self, "警告", "请先选择工件")
            return

        try:
            # 收集报告数据
            report_data = self.report_generator.collect_workpiece_data(self.current_workpiece_id)

            # 创建预览对话框
            preview_dialog = ReportPreviewDialog(report_data, self.create_report_configuration(), self)
            preview_dialog.exec()

        except Exception as e:
            QMessageBox.warning(self, "错误", f"生成预览失败: {str(e)}")
    
    def generate_report(self):
        """生成报告"""
        if not self.current_workpiece_id:
            QMessageBox.warning(self, "警告", "请先选择工件")
            return
        
        # 创建报告配置
        config = self.create_report_configuration()

        # 创建报告实例并保存
        self.current_report_instance = self.report_generator.generate_report_instance(
            self.current_workpiece_id, config
        )

        # 启动报告生成工作线程
        self.generation_worker = ReportGenerationWorker(self.current_workpiece_id, config)
        # 将子线程的信号直接转发出去
        self.generation_worker.status_updated.connect(self.status_updated.emit)
        self.generation_worker.report_completed.connect(self.on_report_completed)
        self.generation_worker.error_occurred.connect(self.on_generation_error)

        # 发射状态信号
        self.status_updated.emit("正在生成报告...")
        self.generate_btn.setEnabled(False)

        self.generation_worker.start()
    
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
    
    def on_report_completed(self, output_path: str):
        """报告生成完成"""
        self.generate_btn.setEnabled(True)

        # 发射状态信号
        file_name = os.path.basename(output_path)
        self.status_updated.emit(f"报告生成成功: {file_name}")

        # 添加到历史记录
        if hasattr(self, 'current_report_instance'):
            print(f"DEBUG: 添加报告记录到历史 - {output_path}")
            self.current_report_instance.output_path = output_path
            self.history_manager.add_report_record(self.current_report_instance)
            print(f"DEBUG: 历史记录数量: {len(self.history_manager.get_history_records())}")
            self.refresh_history()
            print(f"DEBUG: 刷新历史记录完成")
        else:
            print("DEBUG: current_report_instance 不存在")

        reply = QMessageBox.question(
            self,
            "成功",
            f"报告生成完成!\n\n文件路径: {output_path}\n\n是否打开文件所在目录?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            import platform
            import subprocess

            directory = os.path.dirname(output_path)
            try:
                if platform.system() == 'Windows':
                    os.startfile(directory)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', directory])
                else:  # Linux
                    subprocess.run(['xdg-open', directory])
            except Exception as e:
                QMessageBox.warning(self, "错误", f"无法打开目录: {str(e)}")
    
    def on_generation_error(self, error_message: str):
        """报告生成错误"""
        self.generate_btn.setEnabled(True)

        # 发射状态信号
        self.status_updated.emit(f"错误: {error_message}")

        QMessageBox.critical(self, "错误", error_message)
    
    def load_data_for_hole(self, hole_id: str):
        """为指定孔位加载数据（兼容导航接口）"""
        # 从孔位ID推断工件ID
        # 这里需要根据实际的数据结构来实现
        pass

    def load_data_for_workpiece(self, workpiece_id: str):
        """为指定工件加载数据"""
        # 在工件下拉框中选择对应的工件
        index = self.workpiece_combo.findText(workpiece_id)
        if index >= 0:
            self.workpiece_combo.setCurrentIndex(index)
        else:
            # 如果工件不在列表中，重新加载工件列表
            self.load_workpiece_list()
            index = self.workpiece_combo.findText(workpiece_id)
            if index >= 0:
                self.workpiece_combo.setCurrentIndex(index)

    def check_pdf_dependencies(self):
        """检查PDF依赖"""
        if PDF_AVAILABLE:
            self.pdf_status_label.setText("✅ PDF支持已启用")
            self.pdf_status_label.setProperty("status", "success")  # 使用属性来控制样式
            self.install_pdf_btn.setVisible(False)
        else:
            self.pdf_status_label.setText("⚠️ PDF支持未安装，将使用文本格式")
            self.pdf_status_label.setProperty("status", "warning")  # 使用属性来控制样式
            self.install_pdf_btn.setVisible(True)

        # 刷新样式
        self.pdf_status_label.style().unpolish(self.pdf_status_label)
        self.pdf_status_label.style().polish(self.pdf_status_label)

    def on_format_changed(self, format_text: str):
        """格式选择改变"""
        if format_text == "PDF" and not PDF_AVAILABLE:
            self.pdf_status_label.setText("⚠️ 选择PDF格式但未安装支持库，将回退到文本格式")
            self.pdf_status_label.setProperty("status", "error")  # 使用属性来控制样式
        elif format_text == "PDF" and PDF_AVAILABLE:
            self.pdf_status_label.setText("✅ PDF格式已就绪")
            self.pdf_status_label.setProperty("status", "success")  # 使用属性来控制样式
        else:
            self.pdf_status_label.setText(f"📄 将生成{format_text}格式报告")
            self.pdf_status_label.setProperty("status", "info")  # 使用属性来控制样式

        # 刷新样式
        self.pdf_status_label.style().unpolish(self.pdf_status_label)
        self.pdf_status_label.style().polish(self.pdf_status_label)

    def show_pdf_install_guide(self):
        """显示PDF安装指南"""
        guide_text = """
PDF报告生成需要安装reportlab库。

安装方法：
1. 打开命令提示符或终端
2. 运行以下命令：
   pip install reportlab

或者：
   conda install reportlab

安装完成后重启程序即可使用PDF功能。

当前可用的替代格式：
• 文本格式 (.txt) - 简单易读
• HTML格式 (.html) - 网页格式
• Excel格式 (.xlsx) - 表格格式
        """

        QMessageBox.information(
            self,
            "PDF支持安装指南",
            guide_text.strip(),
            QMessageBox.Ok
        )

    def refresh_history(self):
        """刷新历史记录"""
        try:
            # 重新加载历史记录
            self.history_manager.history_records = self.history_manager.load_history()

            # 更新表格
            records = self.history_manager.get_history_records()
            self.report_history_table.setRowCount(len(records))

            for row, record in enumerate(records):
                # 序号列（新增）
                seq_item = QTableWidgetItem(str(row + 1))
                seq_item.setTextAlignment(Qt.AlignCenter)
                self.report_history_table.setItem(row, 0, seq_item)

                # 生成时间（原第0列，现在是第1列）
                created_at = record.get('created_at', '')
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        time_str = dt.strftime('%m-%d %H:%M')
                    except:
                        time_str = created_at[:16]
                else:
                    time_str = '未知'
                self.report_history_table.setItem(row, 1, QTableWidgetItem(time_str))

                # 工件ID（原第1列，现在是第2列）
                workpiece_id = record.get('workpiece_id', '未知')
                self.report_history_table.setItem(row, 2, QTableWidgetItem(workpiece_id))

                # 状态（原第2列，现在是第3列）
                status = record.get('status', '未知')
                status_item = QTableWidgetItem(status)
                if status == 'completed':
                    status_item.setBackground(QPalette().color(QPalette.ColorRole.Base))
                elif status == 'failed':
                    status_item.setBackground(QPalette().color(QPalette.ColorRole.AlternateBase))
                self.report_history_table.setItem(row, 3, status_item)

                # 文件大小（原第3列，现在是第4列）
                file_size = record.get('file_size', 0)
                if file_size:
                    size_str = self.history_manager.format_file_size(file_size)
                else:
                    size_str = '-'
                self.report_history_table.setItem(row, 4, QTableWidgetItem(size_str))

                # 格式（原第4列，现在是第5列）
                file_ext = record.get('file_extension', '').upper()
                if file_ext.startswith('.'):
                    file_ext = file_ext[1:]
                self.report_history_table.setItem(row, 5, QTableWidgetItem(file_ext))

        except Exception as e:
            QMessageBox.warning(self, "错误", f"刷新历史记录失败: {str(e)}")

    def show_history_context_menu(self, position):
        """显示报告历史表格的右键上下文菜单"""
        # 获取右键点击位置的行索引
        item = self.report_history_table.itemAt(position)
        if not item:
            return  # 如果没有点在任何条目上，则不显示菜单

        row = item.row()

        # 从历史记录中获取该行的数据
        try:
            record = self.history_manager.get_history_records()[row]
            instance_id = record.get('instance_id')
            file_exists = record.get('file_exists', False)
        except IndexError:
            return  # 如果索引超出范围，则不显示

        # 创建菜单
        menu = QMenu()

        # --- 为了最佳视觉效果，建议使用图标库 ---
        # import qtawesome as qta
        # icon_color = "#D3D8E0"
        # open_icon = qta.icon('fa5s.folder-open', color=icon_color)
        # dir_icon = qta.icon('fa5.folder', color=icon_color)
        # delete_icon = qta.icon('fa5s.trash-alt', color='#E74C3C')

        # 创建操作 (Action)
        open_action = QAction("打开文件", self)
        # open_action.setIcon(open_icon)  # 设置图标
        open_action.setEnabled(file_exists)
        open_action.triggered.connect(lambda: self.open_report_file(instance_id))

        dir_action = QAction("打开所在目录", self)
        # dir_action.setIcon(dir_icon)  # 设置图标
        dir_action.setEnabled(file_exists)
        dir_action.triggered.connect(lambda: self.open_report_directory(instance_id))

        delete_action = QAction("删除记录", self)
        # delete_action.setIcon(delete_icon)  # 设置图标
        delete_action.triggered.connect(lambda: self.delete_report_file(instance_id))

        # 将操作添加到菜单
        menu.addAction(open_action)
        menu.addAction(dir_action)
        menu.addSeparator()  # 添加一条分割线
        menu.addAction(delete_action)

        # 在鼠标光标位置显示菜单
        # viewport()是表格的可视区域
        menu.exec(self.report_history_table.viewport().mapToGlobal(position))

    def open_report_file(self, instance_id: str):
        """打开报告文件"""
        if self.history_manager.open_report(instance_id):
            self.status_updated.emit("报告文件已打开")
        else:
            QMessageBox.warning(self, "错误", "无法打开报告文件")

    def open_report_directory(self, instance_id: str):
        """打开报告目录"""
        if self.history_manager.open_report_directory(instance_id):
            self.status_updated.emit("报告目录已打开")
        else:
            QMessageBox.warning(self, "错误", "无法打开报告目录")

    def delete_report_file(self, instance_id: str):
        """删除报告文件"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个报告文件吗？\n\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.history_manager.delete_report(instance_id):
                self.refresh_history()
                self.status_updated.emit("报告已删除")
            else:
                QMessageBox.warning(self, "错误", "删除报告失败")

    def cleanup_history(self):
        """清理失效的历史记录"""
        removed_count = self.history_manager.cleanup_missing_files()
        if removed_count > 0:
            self.refresh_history()
            QMessageBox.information(self, "清理完成", f"已清理 {removed_count} 条失效记录")
        else:
            QMessageBox.information(self, "清理完成", "没有发现失效记录")

    def export_history(self):
        """导出历史记录"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出历史记录",
            f"report_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "文本文件 (*.txt);;所有文件 (*)"
        )

        if file_path:
            if self.history_manager.export_history_report(file_path):
                QMessageBox.information(self, "导出成功", f"历史记录已导出到:\n{file_path}")
            else:
                QMessageBox.warning(self, "导出失败", "导出历史记录失败")

    def on_template_text_changed(self, template_text: str):
        """模板选择改变（通过文本）"""
        # 根据显示文本找到对应的模板ID
        template_id = None

        if template_text == "自定义配置":
            template_id = "custom"
        else:
            # 查找匹配的模板ID
            display_names = self.template_manager.get_template_display_names()
            for tid, display_name in display_names.items():
                if display_name == template_text:
                    template_id = tid
                    break

        if not template_id or template_id == "custom":
            # 自定义配置，不做任何改变
            return

        # 应用模板到UI组件
        ui_components = {
            "report_type_combo": self.report_type_combo,
            "format_combo": self.format_combo,
            "include_workpiece_info": self.include_workpiece_info,
            "include_quality_summary": self.include_quality_summary,
            "include_qualified_holes": self.include_qualified_holes,
            "include_unqualified_holes": self.include_unqualified_holes,
            "include_defect_analysis": self.include_defect_analysis,
            "include_manual_reviews": self.include_manual_reviews,
            "include_charts": self.include_charts,
            "include_endoscope_images": self.include_endoscope_images
        }

        self.template_manager.apply_template_to_ui(template_id, ui_components)

        # 显示模板描述
        description = self.template_manager.get_template_description(template_id)
        self.status_updated.emit(f"已应用模板: {description}")

    def load_data_for_workpiece(self, workpiece_id: str):
        """为指定工件加载数据（从其他界面导航时调用）"""
        try:
            # 设置工件选择
            index = self.workpiece_combo.findText(workpiece_id)
            if index >= 0:
                self.workpiece_combo.setCurrentIndex(index)
            else:
                # 如果下拉框中没有该工件，尝试刷新工件列表
                self.load_available_workpieces()
                index = self.workpiece_combo.findText(workpiece_id)
                if index >= 0:
                    self.workpiece_combo.setCurrentIndex(index)
                else:
                    # 如果仍然找不到，显示警告但继续
                    self.status_updated.emit(f"⚠️ 工件 {workpiece_id} 不在可用列表中")

            # 加载数据
            if self.current_workpiece_id:
                self.load_workpiece_data(self.current_workpiece_id)

        except Exception as e:
            self.status_updated.emit(f"❌ 加载工件数据失败: {str(e)}")

    def load_available_workpieces(self):
        """加载可用的工件列表"""
        try:
            # 清空现有项目
            self.workpiece_combo.clear()

            # 添加统一的工件ID，与第二级和第三级界面保持一致
            # 根据项目需求，这里使用统一的工件ID：WP-2025-001
            # AI员工4号修改开始
            # 该工件包含20000个孔，目前有C001R001~C003R001的数据，后续会增加
            # AI员工4号修改结束
            self.workpiece_combo.addItem("WP-2025-001")

            # 设置工具提示说明
            self.workpiece_combo.setToolTip(
                "工件 WP-2025-001:\n"
                "• 总孔位数: 20000个\n"
                "• 当前有数据的孔位: C001R001, C002R001, C003R001\n"
                "• 后续会增加更多孔位数据\n"
                "• 报告将包含所有已检测孔位的数据"
            )

        except Exception as e:
            self.workpiece_combo.addItem("加载失败")
            print(f"加载工件列表失败: {e}")


class ReportPreviewDialog(QDialog):
    """报告预览对话框"""

    def __init__(self, report_data: ReportData, config: ReportConfiguration, parent=None):
        super().__init__(parent)
        self.report_data = report_data
        self.config = config

        self.setWindowTitle("报告预览")
        self.setModal(True)
        self.resize(800, 600)

        self.setup_ui()
        self.generate_preview()

    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("报告内容预览")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setObjectName("DialogTitle")  # 设置对象名用于QSS样式
        layout.addWidget(title_label)

        # 预览内容
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.preview_text)

        # 按钮
        button_layout = QHBoxLayout()

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def generate_preview(self):
        """生成预览内容"""
        try:
            preview_content = self._generate_text_preview()
            self.preview_text.setPlainText(preview_content)
        except Exception as e:
            self.preview_text.setPlainText(f"预览生成失败: {str(e)}")

    def _generate_text_preview(self) -> str:
        """生成文本预览"""
        lines = []

        # 标题
        lines.append("=" * 60)
        lines.append("管孔检测系统 - 质量检测报告")
        lines.append("=" * 60)
        lines.append("")

        # 工件信息
        if self.config.include_workpiece_info:
            lines.append("1. 工件信息")
            lines.append("-" * 30)
            workpiece = self.report_data.workpiece_info
            lines.append(f"工件ID: {workpiece.workpiece_id}")
            lines.append(f"工件名称: {workpiece.name}")
            lines.append(f"工件类型: {workpiece.type}")
            lines.append(f"材料: {workpiece.material}")
            lines.append(f"总孔位数: {workpiece.total_holes}")
            if workpiece.description:
                lines.append(f"描述: {workpiece.description}")
            lines.append("")

        # 质量汇总
        if self.config.include_quality_summary:
            lines.append("2. 质量汇总")
            lines.append("-" * 30)
            summary = self.report_data.quality_summary
            lines.append(f"总孔位数: {summary.total_holes}")
            lines.append(f"合格孔位: {summary.qualified_holes}")
            lines.append(f"不合格孔位: {summary.unqualified_holes}")
            lines.append(f"合格率: {summary.qualification_rate:.2f}%")
            lines.append(f"有缺陷孔位: {summary.holes_with_defects}")
            lines.append(f"人工复检数: {summary.manual_review_count}")
            lines.append(f"完成率: {summary.completion_rate:.2f}%")
            lines.append("")

            # 直径统计
            if summary.diameter_statistics:
                lines.append("2.1 直径测量统计")
                stats = summary.diameter_statistics
                lines.append(f"  最小直径: {stats.get('min', 0):.4f}mm")
                lines.append(f"  最大直径: {stats.get('max', 0):.4f}mm")
                lines.append(f"  平均直径: {stats.get('avg', 0):.4f}mm")
                lines.append(f"  标准偏差: {stats.get('std', 0):.4f}mm")
                lines.append(f"  测量点数: {stats.get('count', 0)}")
                lines.append("")

        # 合格孔位
        if self.config.include_qualified_holes and self.report_data.qualified_holes:
            lines.append("3. 合格孔位汇总")
            lines.append("-" * 30)
            lines.append(f"共有 {len(self.report_data.qualified_holes)} 个孔位检测合格。")

            if len(self.report_data.qualified_holes) <= 10:
                lines.append("")
                lines.append("孔位详情:")
                for hole in self.report_data.qualified_holes:
                    lines.append(f"  {hole.hole_id}: 位置({hole.position_x:.1f}, {hole.position_y:.1f}), "
                               f"合格率{hole.qualification_rate:.1f}%, "
                               f"测量{hole.qualified_count}/{hole.total_count}")
            else:
                hole_ids = [hole.hole_id for hole in self.report_data.qualified_holes[:10]]
                lines.append(f"合格孔位: {', '.join(hole_ids)} ... (共{len(self.report_data.qualified_holes)}个)")
            lines.append("")

        # 不合格孔位
        if self.config.include_unqualified_holes and self.report_data.unqualified_holes:
            lines.append("4. 不合格孔位详情")
            lines.append("-" * 30)
            lines.append(f"共有 {len(self.report_data.unqualified_holes)} 个孔位检测不合格，详情如下：")
            lines.append("")

            for i, hole in enumerate(self.report_data.unqualified_holes, 1):
                lines.append(f"4.{i} 孔位 {hole.hole_id}")
                lines.append(f"  位置坐标: ({hole.position_x:.1f}, {hole.position_y:.1f})")
                lines.append(f"  目标直径: {hole.target_diameter:.2f}mm")
                lines.append(f"  公差范围: +{hole.tolerance_upper:.3f}/-{hole.tolerance_lower:.3f}mm")
                lines.append(f"  合格率: {hole.qualification_rate:.1f}%")
                lines.append(f"  测量次数: {hole.total_count}")
                lines.append(f"  合格次数: {hole.qualified_count}")
                lines.append(f"  平均偏差: {hole.deviation_stats.get('avg', 0):.4f}mm")
                lines.append("")

        # 人工复检记录
        if self.config.include_manual_reviews and self.report_data.manual_reviews:
            lines.append("5. 人工复检记录")
            lines.append("-" * 30)
            for review in self.report_data.manual_reviews:
                lines.append(f"孔位 {review.hole_id}:")
                lines.append(f"  复检员: {review.reviewer}")
                lines.append(f"  原始直径: {review.original_diameter:.4f}mm")
                lines.append(f"  复检直径: {review.reviewed_diameter:.4f}mm")
                lines.append(f"  最终判定: {review.final_judgment}")
                lines.append(f"  复检时间: {review.review_timestamp}")
                if review.notes:
                    lines.append(f"  备注: {review.notes}")
                lines.append("")

        # 缺陷分析
        if self.config.include_defect_analysis and self.report_data.defect_data:
            lines.append("6. 缺陷分析")
            lines.append("-" * 30)

            # 缺陷统计
            defect_types = {}
            for defect in self.report_data.defect_data:
                defect_types[defect.defect_type] = defect_types.get(defect.defect_type, 0) + defect.defect_count

            lines.append("缺陷类型统计:")
            for defect_type, count in defect_types.items():
                lines.append(f"  {defect_type}: {count} 个")
            lines.append("")

        # 附录
        lines.append("附录")
        lines.append("-" * 30)
        lines.append("A. 检测标准: 管孔直径标准 17.6mm ±0.05/-0.07mm")
        lines.append("B. 检测设备: 光谱共焦测量系统")
        lines.append("C. 合格判定标准: 单孔合格率 ≥ 95%")
        lines.append(f"D. 报告生成时间: {self.report_data.generated_at.strftime('%Y年%m月%d日 %H:%M:%S')}")
        lines.append(f"E. 数据版本: {self.report_data.report_version}")

        return "\n".join(lines)
