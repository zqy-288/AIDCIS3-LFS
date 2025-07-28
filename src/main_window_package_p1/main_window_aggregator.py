"""
主窗口聚合器
负责聚合四个页面并提供统一的主窗口接口
"""

import sys
import logging
import traceback
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QSplitter, QApplication, QLabel
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

# 导入页面组件
from .pages.main_detection import MainDetectionPage
from .pages.realtime_monitoring import RealtimeMonitoringPage
from .pages.history_analytics_p3 import HistoryAnalyticsPage
from .pages.report_generation_p4 import ReportGenerationPage

# 导入共享组件
from .shared import SharedComponents, ViewModelManager


class MainWindowAggregator(QMainWindow):
    """
    主窗口聚合器
    将四个页面聚合为统一的主窗口界面
    """
    
    # 窗口信号
    tab_changed = Signal(int)
    window_closed = Signal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 共享组件管理器
        self.shared_components = SharedComponents()
        self.view_model_manager = ViewModelManager()
        
        # 页面实例
        self.main_detection_page = None
        self.realtime_monitoring_page = None
        self.history_analytics_page = None
        self.report_generation_page = None
        
        # UI组件
        self.central_widget = None
        self.tab_widget = None
        
        # 初始化
        self.setup_ui()
        self.setup_pages()
        self.setup_connections()
        
    def setup_ui(self):
        """设置基础UI结构"""
        self.setWindowTitle("AIDCIS3-LFS 主窗口 (P1架构)")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建选项卡容器
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 设置菜单栏和状态栏
        self._setup_menu_bar()
        self._setup_status_bar()
        
    def setup_pages(self):
        """设置所有页面"""
        try:
            self.logger.info("🔄 开始创建页面...")
            
            # 1. 主检测视图页面
            self.logger.info("📋 创建主检测视图页面...")
            self.main_detection_page = MainDetectionPage(
                shared_components=self.shared_components,
                view_model=self.view_model_manager.get_view_model()
            )
            self.tab_widget.addTab(self.main_detection_page, "主检测视图")
            self.logger.info("✅ 主检测视图页面创建成功")
            
            # 2. 实时监控页面
            self.logger.info("📋 创建实时监控页面...")
            self.realtime_monitoring_page = RealtimeMonitoringPage(
                shared_components=self.shared_components,
                view_model=self.view_model_manager.get_view_model()
            )
            self.tab_widget.addTab(self.realtime_monitoring_page, "实时监控")
            self.logger.info("✅ 实时监控页面创建成功")
            
            # 3. 历史统计页面
            self.logger.info("📋 创建历史统计页面...")
            self.history_analytics_page = HistoryAnalyticsPage(
                shared_components=self.shared_components,
                view_model=self.view_model_manager.get_view_model()
            )
            self.tab_widget.addTab(self.history_analytics_page, "历史统计")
            self.logger.info("✅ 历史统计页面创建成功")
            
            # 4. 报告生成页面
            self.logger.info("📋 创建报告生成页面...")
            self.report_generation_page = ReportGenerationPage(
                shared_components=self.shared_components,
                view_model=self.view_model_manager.get_view_model()
            )
            self.tab_widget.addTab(self.report_generation_page, "报告生成")
            self.logger.info("✅ 报告生成页面创建成功")
            
            # 设置默认选项卡
            self.tab_widget.setCurrentIndex(0)
            self.logger.info("🎉 所有页面创建完成!")
            
        except Exception as e:
            self.logger.error(f"❌ 页面创建失败: {e}")
            self.logger.error(f"❌ 详细错误: {traceback.format_exc()}")
            self._create_error_fallback()
            
    def _create_error_fallback(self):
        """创建错误回退界面"""
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        error_label = QLabel("页面加载失败，请检查日志")
        error_layout.addWidget(error_label)
        self.tab_widget.addTab(error_widget, "错误")
        
    def setup_connections(self):
        """设置信号连接"""
        # 选项卡切换信号
        self.tab_widget.currentChanged.connect(self.tab_changed)
        
        # 页面间通信
        self._setup_page_communication()
        
    def _setup_page_communication(self):
        """设置页面间通信"""
        # 这里可以设置页面间的数据共享和通信
        pass
        
    def _setup_menu_bar(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        open_action = QAction("打开DXF", self)
        open_action.triggered.connect(self._on_load_dxf)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        help_menu.addAction(about_action)
        
    def _setup_status_bar(self):
        """设置状态栏"""
        self.statusBar().showMessage("P1架构主窗口就绪")
        
    def _on_load_dxf(self):
        """处理加载DXF事件"""
        # 委托给主检测页面处理
        if self.main_detection_page and hasattr(self.main_detection_page, 'load_dxf'):
            self.main_detection_page.load_dxf()
            
    def get_current_page(self):
        """获取当前活跃页面"""
        current_index = self.tab_widget.currentIndex()
        return self.tab_widget.widget(current_index)
        
    def switch_to_page(self, page_name: str):
        """切换到指定页面"""
        page_mapping = {
            'main_detection': 0,
            'realtime_monitoring': 1, 
            'history_analytics': 2,
            'report_generation': 3
        }
        
        if page_name in page_mapping:
            self.tab_widget.setCurrentIndex(page_mapping[page_name])
            
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.window_closed.emit()
        
        # 清理资源
        if self.shared_components:
            self.shared_components.cleanup()
            
        event.accept()


# 向后兼容别名
MainWindowEnhanced = MainWindowAggregator
MainWindow = MainWindowAggregator