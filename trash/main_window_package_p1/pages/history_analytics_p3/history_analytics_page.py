"""
历史统计页面主类
提供数据分析、趋势统计、质量报告等功能
"""

import logging
import traceback
from typing import Optional, Dict, List, Any
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QGroupBox, QLabel, QPushButton, QComboBox,
    QDateEdit, QTableWidget, QTabWidget, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtGui import QFont

# 导入组件模块
from .components import (
    StatisticsEngine,
    DataFilterManager,
    TrendAnalyzer,
    QualityMetricsCalculator,
    ExportManager
)

# 导入UI组件
from .widgets import (
    TrendChartWidget,
    QualityDashboardWidget,
    StatisticsTableWidget,
    FilterPanelWidget,
    TimeRangeWidget
)

# 导入数据模型
from .models import (
    HistoryDataModel,
    StatisticsDataModel,
    TrendDataModel
)


class HistoryAnalyticsPage(QWidget):
    """
    历史统计页面
    
    功能特性：
    1. 多维度数据统计分析
    2. 时间序列趋势分析
    3. 质量指标dashboard
    4. 可视化图表展示
    5. 数据导出功能
    6. 自定义筛选器
    """
    
    # 页面信号
    data_loaded = Signal(dict)
    analysis_completed = Signal(dict)
    export_requested = Signal(str, dict)
    
    def __init__(self, shared_components=None, view_model=None, parent=None):
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.shared_components = shared_components
        self.view_model = view_model
        
        # 核心组件
        self.statistics_engine = None
        self.data_filter_manager = None
        self.trend_analyzer = None
        self.quality_calculator = None
        self.export_manager = None
        
        # 数据模型
        self.history_data_model = None
        self.statistics_data_model = None
        self.trend_data_model = None
        
        # UI组件
        self.main_layout = None
        self.left_panel = None
        self.center_panel = None
        self.right_panel = None
        
        # 页面状态
        self.current_project = None
        self.selected_date_range = None
        self.active_filters = {}
        
        # 初始化
        self._init_components()
        self._init_ui()
        self._init_connections()
        self._load_initial_data()
        
    def _init_components(self):
        """初始化核心组件"""
        try:
            self.logger.info("🔧 初始化历史统计页面组件...")
            
            # 数据模型
            self.history_data_model = HistoryDataModel()
            self.statistics_data_model = StatisticsDataModel()
            self.trend_data_model = TrendDataModel()
            
            # 核心业务组件
            self.statistics_engine = StatisticsEngine(self.history_data_model)
            self.data_filter_manager = DataFilterManager()
            self.trend_analyzer = TrendAnalyzer(self.trend_data_model)
            self.quality_calculator = QualityMetricsCalculator()
            self.export_manager = ExportManager()
            
            self.logger.info("✅ 历史统计页面组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 组件初始化失败: {e}")
            self.logger.error(f"❌ 详细错误: {traceback.format_exc()}")
            
    def _init_ui(self):
        """初始化用户界面"""
        try:
            self.logger.info("🎨 构建历史统计页面UI...")
            
            # 主布局
            self.main_layout = QVBoxLayout(self)
            self.main_layout.setContentsMargins(10, 10, 10, 10)
            self.main_layout.setSpacing(10)
            
            # 页面标题
            self._create_header()
            
            # 主内容区域 (三栏布局)
            self._create_main_content()
            
            # 底部状态栏
            self._create_status_bar()
            
            self.logger.info("✅ 历史统计页面UI构建完成")
            
        except Exception as e:
            self.logger.error(f"❌ UI构建失败: {e}")
            self.logger.error(f"❌ 详细错误: {traceback.format_exc()}")
            
    def _create_header(self):
        """创建页面标题区域"""
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        
        # 标题
        title_label = QLabel("📊 历史数据统计分析")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # 快速操作按钮
        refresh_btn = QPushButton("🔄 刷新数据")
        export_btn = QPushButton("📤 导出报告")
        settings_btn = QPushButton("⚙️ 设置")
        
        # 布局
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(refresh_btn)
        header_layout.addWidget(export_btn)
        header_layout.addWidget(settings_btn)
        
        self.main_layout.addWidget(header_widget)
        
        # 连接信号
        refresh_btn.clicked.connect(self._refresh_data)
        export_btn.clicked.connect(self._show_export_dialog)
        settings_btn.clicked.connect(self._show_settings)
        
    def _create_main_content(self):
        """创建主内容区域"""
        # 水平分割器
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板：筛选器和控制
        self.left_panel = self._create_left_panel()
        main_splitter.addWidget(self.left_panel)
        
        # 中央面板：图表和可视化
        self.center_panel = self._create_center_panel()
        main_splitter.addWidget(self.center_panel)
        
        # 右侧面板：统计数据和详情
        self.right_panel = self._create_right_panel()
        main_splitter.addWidget(self.right_panel)
        
        # 设置分割比例
        main_splitter.setSizes([300, 800, 400])
        
        self.main_layout.addWidget(main_splitter)
        
    def _create_left_panel(self) -> QWidget:
        """创建左侧筛选面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 时间范围选择
        time_group = QGroupBox("📅 时间范围")
        time_layout = QVBoxLayout(time_group)
        
        self.time_range_widget = TimeRangeWidget()
        time_layout.addWidget(self.time_range_widget)
        
        # 项目选择
        project_group = QGroupBox("📁 项目筛选")
        project_layout = QVBoxLayout(project_group)
        
        self.project_combo = QComboBox()
        self.project_combo.addItems(["全部项目", "CAP1000", "华龙一号", "AP1000"])
        project_layout.addWidget(self.project_combo)
        
        # 数据筛选器
        filter_group = QGroupBox("🔍 数据筛选")
        filter_layout = QVBoxLayout(filter_group)
        
        self.filter_panel_widget = FilterPanelWidget()
        filter_layout.addWidget(self.filter_panel_widget)
        
        # 质量标准选择
        quality_group = QGroupBox("⭐ 质量标准")
        quality_layout = QVBoxLayout(quality_group)
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["标准", "严格", "宽松", "自定义"])
        quality_layout.addWidget(self.quality_combo)
        
        # 分析按钮
        analyze_btn = QPushButton("🔬 开始分析")
        analyze_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        analyze_btn.clicked.connect(self._start_analysis)
        
        # 添加到布局
        layout.addWidget(time_group)
        layout.addWidget(project_group)
        layout.addWidget(filter_group)
        layout.addWidget(quality_group)
        layout.addWidget(analyze_btn)
        layout.addStretch()
        
        return panel
        
    def _create_center_panel(self) -> QWidget:
        """创建中央图表面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 选项卡容器
        tab_widget = QTabWidget()
        
        # 趋势分析选项卡
        trend_tab = QWidget()
        trend_layout = QVBoxLayout(trend_tab)
        
        self.trend_chart_widget = TrendChartWidget()
        trend_layout.addWidget(self.trend_chart_widget)
        
        tab_widget.addTab(trend_tab, "📈 趋势分析")
        
        # 质量分布选项卡
        quality_tab = QWidget()
        quality_layout = QVBoxLayout(quality_tab)
        
        self.quality_dashboard_widget = QualityDashboardWidget()
        quality_layout.addWidget(self.quality_dashboard_widget)
        
        tab_widget.addTab(quality_tab, "📊 质量分布")
        
        # 对比分析选项卡
        compare_tab = QWidget()
        compare_layout = QVBoxLayout(compare_tab)
        
        compare_label = QLabel("对比分析功能开发中...")
        compare_layout.addWidget(compare_label)
        
        tab_widget.addTab(compare_tab, "⚖️ 对比分析")
        
        layout.addWidget(tab_widget)
        return panel
        
    def _create_right_panel(self) -> QWidget:
        """创建右侧统计面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 关键指标组
        metrics_group = QGroupBox("📊 关键指标")
        metrics_layout = QVBoxLayout(metrics_group)
        
        # 创建指标标签
        self.total_holes_label = QLabel("总孔位数: --")
        self.qualified_rate_label = QLabel("合格率: --%")
        self.defect_rate_label = QLabel("缺陷率: --%")
        self.avg_depth_label = QLabel("平均深度: -- mm")
        self.avg_diameter_label = QLabel("平均直径: -- mm")
        
        metrics_layout.addWidget(self.total_holes_label)
        metrics_layout.addWidget(self.qualified_rate_label)
        metrics_layout.addWidget(self.defect_rate_label)
        metrics_layout.addWidget(self.avg_depth_label)
        metrics_layout.addWidget(self.avg_diameter_label)
        
        # 详细统计表
        stats_group = QGroupBox("📋 详细统计")
        stats_layout = QVBoxLayout(stats_group)
        
        self.statistics_table_widget = StatisticsTableWidget()
        stats_layout.addWidget(self.statistics_table_widget)
        
        # 进度指示器
        progress_group = QGroupBox("⏳ 分析进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("就绪")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        
        # 添加到布局
        layout.addWidget(metrics_group)
        layout.addWidget(stats_group)
        layout.addWidget(progress_group)
        layout.addStretch()
        
        return panel
        
    def _create_status_bar(self):
        """创建状态栏"""
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        
        self.status_label = QLabel("历史统计页面就绪")
        self.data_count_label = QLabel("数据: 0 条")
        self.last_update_label = QLabel("最后更新: --")
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.data_count_label)
        status_layout.addWidget(self.last_update_label)
        
        self.main_layout.addWidget(status_widget)
        
    def _init_connections(self):
        """初始化信号连接"""
        # 时间范围变化
        if hasattr(self, 'time_range_widget'):
            self.time_range_widget.range_changed.connect(self._on_time_range_changed)
            
        # 项目选择变化
        self.project_combo.currentTextChanged.connect(self._on_project_changed)
        
        # 质量标准变化
        self.quality_combo.currentTextChanged.connect(self._on_quality_standard_changed)
        
        # 数据模型信号
        if self.history_data_model:
            self.history_data_model.data_loaded.connect(self._on_data_loaded)
            
        # 统计引擎信号
        if self.statistics_engine:
            self.statistics_engine.analysis_completed.connect(self._on_analysis_completed)
            
    def _load_initial_data(self):
        """加载初始数据"""
        try:
            self.logger.info("📊 加载初始历史数据...")
            
            # 设置默认时间范围（最近30天）
            end_date = QDate.currentDate()
            start_date = end_date.addDays(-30)
            self.selected_date_range = (start_date, end_date)
            
            # 加载数据
            if self.history_data_model:
                self.history_data_model.load_data_range(start_date, end_date)
                
            self.logger.info("✅ 初始数据加载完成")
            
        except Exception as e:
            self.logger.error(f"❌ 初始数据加载失败: {e}")
            
    def _start_analysis(self):
        """开始统计分析"""
        try:
            self.logger.info("🔬 开始历史数据分析...")
            
            # 更新进度
            self.progress_bar.setValue(0)
            self.progress_label.setText("准备分析...")
            
            # 获取筛选参数
            filters = self._get_current_filters()
            
            # 启动分析
            if self.statistics_engine:
                self.statistics_engine.start_analysis(filters)
                
        except Exception as e:
            self.logger.error(f"❌ 分析启动失败: {e}")
            
    def _get_current_filters(self) -> Dict[str, Any]:
        """获取当前筛选条件"""
        return {
            'time_range': self.selected_date_range,
            'project': self.project_combo.currentText(),
            'quality_standard': self.quality_combo.currentText(),
            'custom_filters': self.active_filters
        }
        
    def _on_time_range_changed(self, start_date, end_date):
        """时间范围变化处理"""
        self.selected_date_range = (start_date, end_date)
        self.logger.info(f"📅 时间范围更新: {start_date} - {end_date}")
        
    def _on_project_changed(self, project_name):
        """项目选择变化处理"""
        self.current_project = project_name
        self.logger.info(f"📁 项目切换: {project_name}")
        
    def _on_quality_standard_changed(self, standard):
        """质量标准变化处理"""
        self.logger.info(f"⭐ 质量标准更新: {standard}")
        
    def _on_data_loaded(self, data_info):
        """数据加载完成处理"""
        self.data_count_label.setText(f"数据: {data_info.get('count', 0)} 条")
        self.data_loaded.emit(data_info)
        
    def _on_analysis_completed(self, results):
        """分析完成处理"""
        try:
            # 更新关键指标
            self._update_key_metrics(results)
            
            # 更新图表
            self._update_charts(results)
            
            # 更新统计表
            self._update_statistics_table(results)
            
            # 完成进度
            self.progress_bar.setValue(100)
            self.progress_label.setText("分析完成")
            
            self.analysis_completed.emit(results)
            
        except Exception as e:
            self.logger.error(f"❌ 分析结果处理失败: {e}")
            
    def _update_key_metrics(self, results):
        """更新关键指标显示"""
        metrics = results.get('key_metrics', {})
        
        self.total_holes_label.setText(f"总孔位数: {metrics.get('total_holes', 0)}")
        self.qualified_rate_label.setText(f"合格率: {metrics.get('qualified_rate', 0):.1f}%")
        self.defect_rate_label.setText(f"缺陷率: {metrics.get('defect_rate', 0):.1f}%")
        self.avg_depth_label.setText(f"平均深度: {metrics.get('avg_depth', 0):.2f} mm")
        self.avg_diameter_label.setText(f"平均直径: {metrics.get('avg_diameter', 0):.2f} mm")
        
    def _update_charts(self, results):
        """更新图表显示"""
        # 更新趋势图表
        if hasattr(self, 'trend_chart_widget'):
            trend_data = results.get('trend_data', {})
            self.trend_chart_widget.update_data(trend_data)
            
        # 更新质量分布图表
        if hasattr(self, 'quality_dashboard_widget'):
            quality_data = results.get('quality_data', {})
            self.quality_dashboard_widget.update_data(quality_data)
            
    def _update_statistics_table(self, results):
        """更新统计表格"""
        if hasattr(self, 'statistics_table_widget'):
            table_data = results.get('table_data', [])
            self.statistics_table_widget.update_data(table_data)
            
    def _refresh_data(self):
        """刷新数据"""
        self.logger.info("🔄 刷新历史统计数据...")
        self._load_initial_data()
        
    def _show_export_dialog(self):
        """显示导出对话框"""
        self.logger.info("📤 显示导出对话框...")
        # TODO: 实现导出对话框
        
    def _show_settings(self):
        """显示设置对话框"""
        self.logger.info("⚙️ 显示设置对话框...")
        # TODO: 实现设置对话框
        
    def get_page_info(self) -> Dict[str, Any]:
        """获取页面信息"""
        return {
            'name': 'history_analytics',
            'title': '历史统计',
            'version': '1.0.0',
            'status': 'active',
            'data_count': self.history_data_model.get_data_count() if self.history_data_model else 0,
            'last_analysis': getattr(self, 'last_analysis_time', None)
        }