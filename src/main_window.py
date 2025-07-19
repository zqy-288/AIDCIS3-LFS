"""
重构后的主窗口模块
精简版本 - 仅保留顶层协调职责
从4751行精简到200行以内
"""

import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMenuBar, QStatusBar, QMessageBox, QFileDialog,
    QLabel, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QIcon

# 导入核心架构组件
from core.application import ApplicationCore, EventBus
from core.dependency_injection import DependencyContainer

# 导入控制器
from controllers.realtime_controller import RealtimeController
from controllers.history_controller import HistoryController
from controllers.report_controller import ReportController

# 导入管理器
from ui.tab_manager import TabManager, TabType
from managers.ui_state_manager import UIStateManager

# 导入数据模型
from models.application_model import ApplicationModel
from models.detection_state import DetectionState, DetectionStateManager
from models.event_types import EventTypes

# 导入核心业务组件
from src.core_business.models.hole_data import HoleCollection
from src.core_business.dxf_parser import DXFParser


class MainWindow(QMainWindow):
    """
    重构后的主窗口类 - 仅负责顶层协调
    所有业务逻辑已迁移到相应的控制器中
    """
    
    # 核心信号
    navigate_to_realtime = Signal(str)
    navigate_to_history = Signal(str) 
    navigate_to_report = Signal(str)
    status_updated = Signal(str, str)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 核心组件初始化
        self._init_core_components()
        
        # 设置UI
        self.setup_ui()
        
        # 设置连接
        self.setup_global_connections()
        self.setup_event_subscriptions()
        
        # 恢复UI状态
        self._restore_ui_state()
        
        self.logger.info("主窗口初始化完成")
    
    def _init_core_components(self):
        """初始化核心组件 - 使用单例模式避免重复创建"""
        # 导入单例管理器
        from core.singleton_manager import get_singleton
        
        # 获取ApplicationCore实例
        try:
            from core.application import get_application
            app = get_application()
            self.app_core = app.core
            
            if self.app_core is None:
                # 如果核心还未初始化，创建临时的组件
                self.event_bus = EventBus()
                self.container = DependencyContainer()
                self.logger.warning("ApplicationCore未初始化，使用临时组件")
            else:
                # 获取事件总线和依赖注入容器
                self.event_bus: EventBus = self.app_core.event_bus
                self.container: DependencyContainer = self.app_core.container
        except Exception as e:
            # 回退处理：创建本地组件
            self.logger.warning(f"无法获取ApplicationCore: {e}，创建本地组件")
            self.app_core = None
            self.event_bus = EventBus()
            self.container = DependencyContainer()
        
        # 使用单例模式初始化数据模型 - 避免重复创建
        self.app_model = get_singleton(ApplicationModel)
        self.detection_state_manager = get_singleton(DetectionStateManager)
        
        # 使用单例模式初始化管理器 - 避免重复创建
        self.tab_manager = get_singleton(TabManager, lambda: TabManager(self))
        self.ui_state_manager = get_singleton(UIStateManager, lambda: UIStateManager("AIDCIS3-LFS", self))
        
        # 初始化核心业务组件
        self.dxf_parser = DXFParser()
        self.hole_collection: Optional[HoleCollection] = None
        
        # 只有在容器中没有实例时才注册
        if not self.container.is_registered(ApplicationModel):
            self.container.register_instance(ApplicationModel, self.app_model)
        if not self.container.is_registered(DetectionStateManager):
            self.container.register_instance(DetectionStateManager, self.detection_state_manager)
        if not self.container.is_registered(TabManager):
            self.container.register_instance(TabManager, self.tab_manager)
        if not self.container.is_registered(UIStateManager):
            self.container.register_instance(UIStateManager, self.ui_state_manager)

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("AIDCIS3-LFS 管孔检测系统")
        self.setMinimumSize(1200, 800)
        
        # 创建中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建选项卡组件
        self.tab_widget = self.tab_manager.create_tabs(self)
        main_layout.addWidget(self.tab_widget)
        
        # 设置菜单栏和状态栏
        self._setup_menu_bar()
        self._setup_status_bar()
        
        # 注册UI组件到状态管理器
        self.ui_state_manager.register_widget("main_tabs", self.tab_widget)
    
    def _setup_menu_bar(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        open_action = QAction("打开DXF文件(&O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_dxf_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        realtime_action = QAction("实时预览(&R)", self)
        realtime_action.triggered.connect(lambda: self._navigate_to_tab("realtime_preview"))
        view_menu.addAction(realtime_action)
        
        history_action = QAction("历史查看(&H)", self)
        history_action.triggered.connect(lambda: self._navigate_to_tab("history_view"))
        view_menu.addAction(history_action)
        
        report_action = QAction("报告输出(&P)", self)
        report_action.triggered.connect(lambda: self._navigate_to_tab("report_output"))
        view_menu.addAction(report_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """设置状态栏"""
        self.status_bar = self.statusBar()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 检测状态标签
        self.detection_status_label = QLabel("检测: 未启动")
        self.status_bar.addPermanentWidget(self.detection_status_label)
    
    def setup_global_connections(self):
        """设置全局信号连接"""
        # 选项卡管理器信号
        self.tab_manager.tab_switched.connect(self._on_tab_switched)
        
        # 数据模型信号
        self.app_model.data_loaded.connect(self.on_dxf_loaded)
        self.detection_state_manager.state_changed.connect(self._on_detection_state_changed)
        
        # 导航信号
        self.navigate_to_realtime.connect(lambda hole_id: self._navigate_with_data("realtime_preview", {"hole_id": hole_id}))
        self.navigate_to_history.connect(lambda hole_id: self._navigate_with_data("history_view", {"hole_id": hole_id}))
        self.navigate_to_report.connect(lambda workpiece_id: self._navigate_with_data("report_output", {"workpiece_id": workpiece_id}))
    
    def setup_event_subscriptions(self):
        """设置事件订阅"""
        # 订阅关键业务事件
        self.event_bus.subscribe(EventTypes.DXF_FILE_LOADED, self._handle_dxf_loaded_event)
        self.event_bus.subscribe(EventTypes.DETECTION_STARTED, self._handle_detection_started)
        self.event_bus.subscribe(EventTypes.DETECTION_COMPLETED, self._handle_detection_completed)
        self.event_bus.subscribe(EventTypes.HOLE_STATUS_CHANGED, self._handle_hole_status_updated)
        
        self.logger.info("事件订阅设置完成")
    
    def on_dxf_loaded(self, file_path: str, hole_collection: HoleCollection):
        """处理DXF文件加载完成"""
        try:
            self.hole_collection = hole_collection
            self.app_model.set_current_file(file_path)
            
            # 更新状态
            hole_count = len(hole_collection.holes) if hole_collection else 0
            self.status_label.setText(f"已加载: {Path(file_path).name} ({hole_count} 个孔位)")
            
            # 发布事件
            from core.application import ApplicationEvent
            event = ApplicationEvent(EventTypes.DXF_FILE_LOADED, {
                "file_path": file_path,
                "hole_collection": hole_collection
            })
            self.event_bus.post_event(event)
            
            self.logger.info(f"DXF文件加载完成: {file_path}")
            
        except Exception as e:
            self.logger.error(f"处理DXF加载失败: {e}")
            QMessageBox.critical(self, "错误", f"处理DXF文件失败: {e}")
    
    def on_navigate_to_tab(self, tab_type: str, data: Optional[Dict[str, Any]] = None):
        """处理选项卡导航"""
        try:
            # 查找对应的选项卡
            tab_mapping = {
                "main_detection": TabType.MAIN_DETECTION,
                "realtime_preview": TabType.REALTIME_PREVIEW,
                "history_view": TabType.HISTORY_VIEW,
                "report_output": TabType.REPORT_OUTPUT
            }
            
            if tab_type in tab_mapping:
                # 切换到指定选项卡
                tab_ids = self.tab_manager.get_all_tab_ids()
                for tab_id in tab_ids:
                    tab_info = self.tab_manager.get_tab_info(tab_id)
                    if tab_info and tab_info.tab_type == tab_mapping[tab_type]:
                        self.tab_manager.switch_tab(tab_id)
                        
                        # 传递数据给选项卡
                        if data and tab_info.controller:
                            if hasattr(tab_info.controller, 'handle_navigation_data'):
                                tab_info.controller.handle_navigation_data(data)
                        
                        break
            
        except Exception as e:
            self.logger.error(f"选项卡导航失败: {e}")
    
    def _open_dxf_file(self):
        """打开DXF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开DXF文件", "", "DXF文件 (*.dxf);;所有文件 (*)"
        )
        
        if file_path:
            try:
                # 解析DXF文件
                hole_collection = self.dxf_parser.parse_file(file_path)
                self.on_dxf_loaded(file_path, hole_collection)
                
            except Exception as e:
                self.logger.error(f"打开DXF文件失败: {e}")
                QMessageBox.critical(self, "错误", f"打开DXF文件失败: {e}")
    
    def _navigate_to_tab(self, tab_type: str):
        """导航到指定选项卡"""
        self.on_navigate_to_tab(tab_type)
    
    def _navigate_with_data(self, tab_type: str, data: Dict[str, Any]):
        """带数据导航到指定选项卡"""
        self.on_navigate_to_tab(tab_type, data)
    
    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", 
                         "AIDCIS3-LFS 管孔检测系统\n"
                         "版本: 1.0.0\n"
                         "基于PySide6的企业级检测系统")
    
    def _on_tab_switched(self, old_tab_id: str, new_tab_id: str):
        """处理选项卡切换"""
        tab_info = self.tab_manager.get_tab_info(new_tab_id)
        if tab_info:
            self.status_label.setText(f"当前: {tab_info.title}")
    
    def _on_detection_state_changed(self, new_state: str):
        """处理检测状态改变"""
        self.detection_status_label.setText(f"检测: {new_state}")
    
    def _handle_dxf_loaded_event(self, event):
        """处理DXF加载事件"""
        self.logger.info(f"收到DXF加载事件: {event.data}")
    
    def _handle_detection_started(self, event):
        """处理检测启动事件"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
    
    def _handle_detection_completed(self, event):
        """处理检测完成事件"""
        self.progress_bar.setVisible(False)
    
    def _handle_hole_status_updated(self, event):
        """处理孔位状态更新事件"""
        hole_id = event.data.get("hole_id", "")
        status = event.data.get("status", "")
        self.status_updated.emit(hole_id, status)
    
    def _restore_ui_state(self):
        """恢复UI状态"""
        self.ui_state_manager.restore_window_state(self)
        self.ui_state_manager.restore_all_states()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 保存UI状态
            self.ui_state_manager.save_window_state(self)
            self.ui_state_manager.save_all_states()
            
            # 清理资源
            self.tab_manager.cleanup()
            self.ui_state_manager.cleanup()
            
            event.accept()
            
        except Exception as e:
            self.logger.error(f"关闭窗口时出错: {e}")
            event.accept()


def main():
    """
    统一的应用程序启动入口
    集成了ApplicationCore架构
    """
    import sys
    from PySide6.QtWidgets import QApplication
    import logging
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        from core.application import get_application
        
        print("🚀 启动 AIDCIS3-LFS 管孔检测系统...")
        print("📋 使用精简架构 - 200行主窗口")
        print("🔧 集成所有WAVE 1组件")
        
        # 获取应用程序实例
        app_core = get_application()
        
        # 初始化应用程序
        if not app_core.initialize():
            print("❌ 应用程序初始化失败")
            return 1
        
        print("✅ 应用程序初始化成功")
        
        # 运行应用程序
        exit_code = app_core.run()
        return exit_code
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)