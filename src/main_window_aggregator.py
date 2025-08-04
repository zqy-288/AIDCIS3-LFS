"""
主窗口聚合器 - 新平级P包架构
将四个平级P页面聚合为统一的主窗口界面
"""

import sys
import logging
import traceback
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QSplitter, QApplication, QLabel
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

# 导入平级P页面组件
from src.pages.main_detection_p1 import MainDetectionPage
from src.pages.realtime_monitoring_p2 import RealtimeMonitoringPage
from src.modules.unified_history_viewer import UnifiedHistoryViewer
from src.pages.report_generation_p4 import ReportGenerationPage


class MainWindowAggregator(QMainWindow):
    """
    主窗口聚合器 - 新架构
    聚合四个平级P页面：P1检测、P2实时、P3统计、P4报告
    """
    
    # 窗口信号
    tab_changed = Signal(int)
    window_closed = Signal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 页面实例（恢复原版本的名称）
        self.main_detection_widget = None
        self.realtime_tab = None
        self.history_tab = None
        self.report_tab = None
        
        # UI组件
        self.central_widget = None
        self.tab_widget = None
        
        # 初始化
        self.setup_ui()
        self.setup_pages()
        self.setup_connections()
        
    def setup_ui(self):
        """设置基础UI结构"""
        self.setWindowTitle("AIDCIS3-LFS 主窗口")
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
        """设置所有P级页面"""
        try:
            self.logger.info("🔄 开始创建P级页面...")
            
            # 主检测视图页面（使用原版本的变量名）
            self.logger.info("📋 创建主检测视图页面...")
            self.main_detection_widget = MainDetectionPage()
            self.tab_widget.addTab(self.main_detection_widget, "主检测视图")
            self.logger.info("✅ 主检测视图页面创建成功")
            
            # 实时监控页面（恢复使用功能完整的组件）
            self.logger.info("📋 创建实时监控页面...")
            self.realtime_tab = RealtimeMonitoringPage()
            self.tab_widget.addTab(self.realtime_tab, "实时监控")
            self.logger.info("✅ 实时监控页面创建成功")
            
            # 历史数据页面（保持原版本设计）
            self.logger.info("📋 创建历史数据页面...")
            self.history_tab = UnifiedHistoryViewer()
            self.tab_widget.addTab(self.history_tab, "历史数据")
            self.logger.info("✅ 历史数据页面创建成功")
            
            # 报告输出页面（恢复使用功能完整的组件）
            self.logger.info("📋 创建报告输出页面...")
            self.report_tab = ReportGenerationPage()
            self.tab_widget.addTab(self.report_tab, "报告输出")
            self.logger.info("✅ 报告输出页面创建成功")
            
            # 设置默认选项卡
            self.tab_widget.setCurrentIndex(0)
            self.logger.info("🎉 所有P级页面创建完成!")
            
        except Exception as e:
            self.logger.error(f"❌ P级页面创建失败: {e}")
            self.logger.error(f"❌ 详细错误: {traceback.format_exc()}")
            self._create_error_fallback()
            
    def _create_error_fallback(self):
        """创建错误回退界面"""
        error_widget = QWidget()
        error_layout = QVBoxLayout(error_widget)
        error_label = QLabel("P级页面加载失败，请检查日志")
        error_layout.addWidget(error_label)
        self.tab_widget.addTab(error_widget, "错误")
        
    def setup_connections(self):
        """设置信号连接"""
        # 选项卡切换信号
        self.tab_widget.currentChanged.connect(self.tab_changed)
        
        # P级页面间通信
        self._setup_page_communication()
        
    def _setup_page_communication(self):
        """设置P级页面间通信"""
        try:
            # 连接主检测页面的导航信号到历史数据页面（恢复原版本功能）
            if self.main_detection_widget and self.history_tab:
                self.main_detection_widget.navigate_to_history.connect(self.navigate_to_history_from_main_view)
                self.logger.info("✅ 历史数据导航信号连接成功")
                
            # 连接主检测页面到实时监控页面
            if self.main_detection_widget and self.realtime_tab:
                self.main_detection_widget.navigate_to_realtime.connect(self.navigate_to_realtime_from_main_view)
                self.logger.info("✅ 实时监控导航信号连接成功")
                
            # 连接主检测页面到报告生成页面
            if self.main_detection_widget and self.report_tab:
                if hasattr(self.main_detection_widget, 'native_view'):
                    self.main_detection_widget.native_view.navigate_to_report.connect(self.navigate_to_report_from_main_view)
                    self.logger.info("✅ 报告生成导航信号连接成功")
                
        except Exception as e:
            self.logger.error(f"页面通信设置失败: {e}")
            
    def navigate_to_history_from_main_view(self, hole_id: str):
        """从主视图导航到历史数据（恢复原版本功能）"""
        try:
            # 切换到历史数据选项卡
            self.tab_widget.setCurrentIndex(2)
            
            # 加载孔位数据到历史查看器
            if hasattr(self.history_tab, 'load_data_for_hole'):
                self.history_tab.load_data_for_hole(hole_id)
                
            self.logger.info(f"导航到历史数据: {hole_id}")
            
        except Exception as e:
            self.logger.error(f"导航到历史数据失败: {e}")
            
    def navigate_to_realtime_from_main_view(self, hole_data: str):
        """从主视图导航到实时监控"""
        try:
            # 切换到实时监控选项卡
            self.tab_widget.setCurrentIndex(1)
            
            # 加载孔位数据到实时监控页面
            if hasattr(self.realtime_tab, 'load_data_for_hole'):
                self.realtime_tab.load_data_for_hole(hole_data)
                
            self.logger.info(f"导航到实时监控: {hole_data}")
            
        except Exception as e:
            self.logger.error(f"导航到实时监控失败: {e}")
            
    def navigate_to_report_from_main_view(self):
        """从主视图导航到报告生成"""
        try:
            # 切换到报告生成选项卡 (P4是第4个标签，索引为3)
            self.tab_widget.setCurrentIndex(3)
            self.logger.info("导航到报告生成")
            
        except Exception as e:
            self.logger.error(f"导航到报告生成失败: {e}")
        
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
        
        # P级页面切换子菜单
        page_menu = view_menu.addMenu("P级页面")
        
        p1_action = QAction("P1-主检测", self)
        p1_action.triggered.connect(lambda: self.switch_to_page('p1'))
        page_menu.addAction(p1_action)
        
        p2_action = QAction("P2-实时监控", self)
        p2_action.triggered.connect(lambda: self.switch_to_page('p2'))
        page_menu.addAction(p2_action)
        
        p3_action = QAction("P3-历史统计", self)
        p3_action.triggered.connect(lambda: self.switch_to_page('p3'))
        page_menu.addAction(p3_action)
        
        p4_action = QAction("P4-报告生成", self)
        p4_action.triggered.connect(lambda: self.switch_to_page('p4'))
        page_menu.addAction(p4_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于P级架构", self)
        help_menu.addAction(about_action)
        
    def _setup_status_bar(self):
        """设置状态栏"""
        self.statusBar().showMessage("新P级架构主窗口就绪")
        
    def _on_load_dxf(self):
        """处理加载DXF事件"""
        # 委托给P1主检测页面处理
        if self.main_detection_p1 and hasattr(self.main_detection_p1, 'load_dxf'):
            self.main_detection_p1.load_dxf()
            
    def get_current_page(self):
        """获取当前活跃P级页面"""
        current_index = self.tab_widget.currentIndex()
        return self.tab_widget.widget(current_index)
        
    def switch_to_page(self, page_level: str):
        """切换到指定P级页面"""
        page_mapping = {
            'p1': 0,  # P1主检测
            'p2': 1,  # P2实时监控
            'p3': 2,  # P3历史统计
            'p4': 3   # P4报告生成
        }
        
        if page_level in page_mapping:
            self.tab_widget.setCurrentIndex(page_mapping[page_level])
            self.logger.info(f"🔄 切换到{page_level.upper()}页面")
            
    def get_architecture_info(self):
        """获取P级架构信息"""
        return {
            'architecture': 'Flat P-Level Architecture',
            'pages': {
                'p1': 'main_detection_p1',
                'p2': 'realtime_monitoring_p2', 
                'p3': 'history_analytics_p3',
                'p4': 'report_generation_p4'
            },
            'version': '2.0.0',
            'features': [
                '平级P包结构',
                '清晰级别标识',
                '独立功能模块',
                '统一聚合接口'
            ]
        }
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.window_closed.emit()
        
        # 清理P级页面资源
        for page in [self.main_detection_p1, self.realtime_monitoring_p2, 
                     self.history_analytics_p3, self.report_generation_p4]:
            if page and hasattr(page, 'cleanup'):
                page.cleanup()
                
        event.accept()


# 向后兼容别名
MainWindowEnhanced = MainWindowAggregator
MainWindow = MainWindowAggregator


def main():
    """主函数 - 运行主窗口聚合器"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    try:
        # 创建主窗口
        logging.info("🚀 启动主窗口聚合器...")
        window = MainWindowAggregator()
        window.show()
        
        logging.info("✅ 主窗口聚合器启动成功")
        
        # 运行应用程序
        sys.exit(app.exec())
        
    except Exception as e:
        logging.error(f"❌ 应用程序启动失败: {e}")
        logging.error(f"❌ 详细错误: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()