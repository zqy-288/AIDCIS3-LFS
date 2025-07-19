"""
选项卡管理器
负责管理应用程序的所有选项卡，包括创建、切换、动态添加/删除等功能
"""

import logging
from typing import Optional, Dict, Any, List, Callable
from enum import Enum
from PySide6.QtWidgets import (
    QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTabBar, QMenu, QMessageBox, QSplitter, QFrame,
    QToolButton, QApplication
)
from PySide6.QtCore import QObject, Signal, Qt, QTimer, QEvent
from PySide6.QtGui import QIcon, QPixmap, QAction, QFont

from src.controllers.realtime_controller import RealtimeController
from src.controllers.history_controller import HistoryController
from src.controllers.report_controller import ReportController


class TabType(Enum):
    """选项卡类型枚举"""
    MAIN_DETECTION = "main_detection"
    REALTIME_PREVIEW = "realtime_preview"
    HISTORY_VIEW = "history_view"
    REPORT_OUTPUT = "report_output"
    CUSTOM = "custom"


class TabInfo:
    """选项卡信息类"""
    
    def __init__(self, tab_id: str, tab_type: TabType, title: str, 
                 widget: QWidget, controller: Optional[QObject] = None,
                 closable: bool = True, removable: bool = True):
        self.tab_id = tab_id
        self.tab_type = tab_type
        self.title = title
        self.widget = widget
        self.controller = controller
        self.closable = closable
        self.removable = removable
        self.is_active = False
        self.data = {}  # 附加数据
        self.created_time = None
        self.last_accessed_time = None


class TabManager(QObject):
    """选项卡管理器类"""
    
    # 信号定义
    tab_created = Signal(str, object)  # tab_id, tab_info
    tab_removed = Signal(str)  # tab_id
    tab_switched = Signal(str, str)  # old_tab_id, new_tab_id
    tab_closed = Signal(str)  # tab_id
    tab_data_changed = Signal(str, dict)  # tab_id, data
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        
        # 核心组件
        self._tab_widget: Optional[QTabWidget] = None
        self._tabs: Dict[str, TabInfo] = {}
        self._controllers: Dict[str, QObject] = {}
        
        # 状态管理
        self._current_tab_id: Optional[str] = None
        self._tab_counter = 0
        self._max_tabs = 10  # 最大选项卡数量
        
        # 延迟加载配置
        self._lazy_loading = True
        self._loaded_tabs: set = set()
        
        # UI增强
        self._tab_context_menu: Optional[QMenu] = None
        self._close_buttons: Dict[str, QPushButton] = {}
        
        # 定时器用于延迟操作
        self._switch_timer = QTimer()
        self._switch_timer.setSingleShot(True)
        self._switch_timer.timeout.connect(self._handle_delayed_switch)
        
        self.logger.info("选项卡管理器初始化完成")
    
    def create_tabs(self, parent: Optional[QWidget] = None) -> QTabWidget:
        """创建选项卡组件"""
        if self._tab_widget is not None:
            return self._tab_widget
        
        self._tab_widget = QTabWidget(parent)
        self._setup_tab_widget()
        self._connect_signals()
        
        # 创建默认选项卡
        self._create_default_tabs()
        
        self.logger.info("选项卡组件创建完成")
        return self._tab_widget
    
    def _setup_tab_widget(self):
        """设置选项卡组件"""
        if not self._tab_widget:
            return
        
        # 设置选项卡属性
        self._tab_widget.setTabsClosable(True)
        self._tab_widget.setMovable(True)
        self._tab_widget.setUsesScrollButtons(True)
        self._tab_widget.setElideMode(Qt.ElideRight)
        
        # 设置样式
        self._tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404552;
                background-color: #2C313C;
            }
            QTabWidget::tab-bar {
                alignment: left;
            }
            QTabBar::tab {
                background-color: #313642;
                color: #D3D8E0;
                border: 1px solid #404552;
                border-bottom: none;
                padding: 8px 12px;
                margin-right: 2px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background-color: #007ACC;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #4A90E2;
            }
            QTabBar::close-button {
                image: url(:/icons/close.png);
                subcontrol-position: right;
            }
            QTabBar::close-button:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 3px;
            }
        """)
        
        # 创建上下文菜单
        self._create_context_menu()
    
    def _connect_signals(self):
        """连接信号"""
        if not self._tab_widget:
            return
        
        # 连接选项卡信号
        self._tab_widget.currentChanged.connect(self._on_tab_changed)
        self._tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)
        self._tab_widget.tabBarDoubleClicked.connect(self._on_tab_double_clicked)
        
        # 安装事件过滤器以处理右键菜单
        self._tab_widget.tabBar().installEventFilter(self)
        
        # 连接内部信号
        self.tab_switched.connect(self._on_tab_switched)
    
    def _create_default_tabs(self):
        """创建默认选项卡"""
        try:
            # 【关键修复点】主检测选项卡 - 通过MainDetectionCoordinator获取视图
            main_detection_widget = self._create_main_detection_widget()
            main_tab_id = self.add_tab(
                TabType.MAIN_DETECTION,
                "主检测",
                main_detection_widget,
                closable=False,
                removable=False
            )
            
            # 实时预览选项卡
            realtime_controller = RealtimeController()
            realtime_widget = realtime_controller.create_widget()
            realtime_tab_id = self.add_tab(
                TabType.REALTIME_PREVIEW,
                "实时预览",
                realtime_widget,
                controller=realtime_controller
            )
            
            # 历史查看选项卡
            history_controller = HistoryController()
            history_widget = history_controller.create_widget()
            history_tab_id = self.add_tab(
                TabType.HISTORY_VIEW,
                "历史查看",
                history_widget,
                controller=history_controller
            )
            
            # 报告输出选项卡
            report_controller = ReportController()
            report_widget = report_controller.create_widget()
            report_tab_id = self.add_tab(
                TabType.REPORT_OUTPUT,
                "报告输出",
                report_widget,
                controller=report_controller
            )
            
            # 设置默认激活选项卡
            self.switch_tab(main_tab_id)
            
            self.logger.info("默认选项卡创建完成")
            
        except Exception as e:
            self.logger.error(f"创建默认选项卡失败: {e}")
            # 【修复点】如果主检测选项卡创建失败，创建一个错误显示选项卡
            error_widget = self._create_error_widget("主检测", str(e))
            main_tab_id = self.add_tab(
                TabType.MAIN_DETECTION,
                "主检测",
                error_widget,
                closable=False,
                removable=False
            )
            # 确保至少设置了一个默认选项卡
            if main_tab_id:
                self.switch_tab(main_tab_id)
    
    def _create_placeholder_widget(self, title: str) -> QWidget:
        """创建占位符组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel(f"{title}\n\n该选项卡内容将由主窗口提供")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: #D3D8E0;
                font-size: 16px;
                padding: 20px;
            }
        """)
        
        layout.addWidget(label)
        return widget
    
    def _create_context_menu(self):
        """创建上下文菜单"""
        self._tab_context_menu = QMenu()
        
        # 关闭选项卡
        close_action = QAction("关闭", self._tab_context_menu)
        close_action.triggered.connect(lambda: self._close_current_tab())
        self._tab_context_menu.addAction(close_action)
        
        # 关闭其他选项卡
        close_others_action = QAction("关闭其他", self._tab_context_menu)
        close_others_action.triggered.connect(lambda: self._close_other_tabs())
        self._tab_context_menu.addAction(close_others_action)
        
        # 关闭所有选项卡
        close_all_action = QAction("关闭所有", self._tab_context_menu)
        close_all_action.triggered.connect(lambda: self._close_all_tabs())
        self._tab_context_menu.addAction(close_all_action)
        
        self._tab_context_menu.addSeparator()
        
        # 刷新选项卡
        refresh_action = QAction("刷新", self._tab_context_menu)
        refresh_action.triggered.connect(lambda: self._refresh_current_tab())
        self._tab_context_menu.addAction(refresh_action)
        
        # 重新加载选项卡
        reload_action = QAction("重新加载", self._tab_context_menu)
        reload_action.triggered.connect(lambda: self._reload_current_tab())
        self._tab_context_menu.addAction(reload_action)
        
        self._tab_context_menu.addSeparator()
        
        # 复制选项卡
        duplicate_action = QAction("复制选项卡", self._tab_context_menu)
        duplicate_action.triggered.connect(lambda: self._duplicate_current_tab())
        self._tab_context_menu.addAction(duplicate_action)
    
    def add_tab(self, tab_type: TabType, title: str, widget: QWidget,
                controller: Optional[QObject] = None, closable: bool = True,
                removable: bool = True, data: Optional[Dict] = None) -> str:
        """添加选项卡"""
        if len(self._tabs) >= self._max_tabs:
            self.logger.warning(f"已达到最大选项卡数量: {self._max_tabs}")
            return ""
        
        try:
            # 生成选项卡ID
            self._tab_counter += 1
            tab_id = f"{tab_type.value}_{self._tab_counter}"
            
            # 创建选项卡信息
            tab_info = TabInfo(
                tab_id=tab_id,
                tab_type=tab_type,
                title=title,
                widget=widget,
                controller=controller,
                closable=closable,
                removable=removable
            )
            
            if data:
                tab_info.data.update(data)
            
            # 添加到选项卡组件
            tab_index = self._tab_widget.addTab(widget, title)
            
            # 设置选项卡属性
            if not closable:
                # 隐藏关闭按钮 - 创建一个空的 QWidget 来替代 None
                empty_widget = QWidget()
                empty_widget.resize(0, 0)
                self._tab_widget.tabBar().setTabButton(
                    tab_index, 
                    QTabBar.RightSide, 
                    empty_widget
                )
            
            # 存储选项卡信息
            self._tabs[tab_id] = tab_info
            if controller:
                self._controllers[tab_id] = controller
            
            # 设置工具提示
            self._tab_widget.setTabToolTip(tab_index, f"{title}\nID: {tab_id}")
            
            # 延迟加载处理
            if self._lazy_loading and tab_type != TabType.MAIN_DETECTION:
                self._setup_lazy_loading(tab_id)
            else:
                self._loaded_tabs.add(tab_id)
            
            # 发出信号
            self.tab_created.emit(tab_id, tab_info)
            
            self.logger.info(f"选项卡已添加: {tab_id} ({title})")
            return tab_id
            
        except Exception as e:
            self.logger.error(f"添加选项卡失败: {e}")
            return ""
    
    def remove_tab(self, tab_id: str) -> bool:
        """移除选项卡"""
        if tab_id not in self._tabs:
            self.logger.warning(f"选项卡不存在: {tab_id}")
            return False
        
        tab_info = self._tabs[tab_id]
        
        if not tab_info.removable:
            self.logger.warning(f"选项卡不可移除: {tab_id}")
            return False
        
        try:
            # 获取选项卡索引
            tab_index = self._get_tab_index(tab_id)
            if tab_index < 0:
                return False
            
            # 移除选项卡
            self._tab_widget.removeTab(tab_index)
            
            # 清理控制器
            if tab_id in self._controllers:
                controller = self._controllers[tab_id]
                if hasattr(controller, 'cleanup'):
                    controller.cleanup()
                del self._controllers[tab_id]
            
            # 清理选项卡信息
            del self._tabs[tab_id]
            self._loaded_tabs.discard(tab_id)
            
            # 如果移除的是当前选项卡，切换到下一个
            if self._current_tab_id == tab_id:
                if self._tabs:
                    next_tab_id = list(self._tabs.keys())[0]
                    self.switch_tab(next_tab_id)
                else:
                    self._current_tab_id = None
            
            # 发出信号
            self.tab_removed.emit(tab_id)
            
            self.logger.info(f"选项卡已移除: {tab_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除选项卡失败: {e}")
            return False
    
    def switch_tab(self, tab_id: str) -> bool:
        """切换选项卡"""
        if tab_id not in self._tabs:
            self.logger.warning(f"选项卡不存在: {tab_id}")
            return False
        
        try:
            # 获取选项卡索引
            tab_index = self._get_tab_index(tab_id)
            if tab_index < 0:
                return False
            
            # 延迟加载检查
            if self._lazy_loading and tab_id not in self._loaded_tabs:
                self._load_tab_content(tab_id)
            
            # 切换选项卡
            old_tab_id = self._current_tab_id
            self._tab_widget.setCurrentIndex(tab_index)
            self._current_tab_id = tab_id
            
            # 更新选项卡状态
            for tid, tab_info in self._tabs.items():
                tab_info.is_active = (tid == tab_id)
            
            # 发出信号
            if old_tab_id != tab_id:
                self.tab_switched.emit(old_tab_id or "", tab_id)
            
            self.logger.info(f"选项卡已切换: {old_tab_id} -> {tab_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"切换选项卡失败: {e}")
            return False
    
    def close_tab(self, tab_id: str) -> bool:
        """关闭选项卡"""
        if tab_id not in self._tabs:
            return False
        
        tab_info = self._tabs[tab_id]
        
        if not tab_info.closable:
            self.logger.warning(f"选项卡不可关闭: {tab_id}")
            return False
        
        # 检查是否有未保存的更改
        if not self._check_unsaved_changes(tab_id):
            return False
        
        # 发出关闭信号
        self.tab_closed.emit(tab_id)
        
        # 移除选项卡
        return self.remove_tab(tab_id)
    
    def update_tab_title(self, tab_id: str, title: str):
        """更新选项卡标题"""
        if tab_id not in self._tabs:
            return
        
        tab_index = self._get_tab_index(tab_id)
        if tab_index >= 0:
            self._tab_widget.setTabText(tab_index, title)
            self._tabs[tab_id].title = title
    
    def update_tab_data(self, tab_id: str, data: Dict[str, Any]):
        """更新选项卡数据"""
        if tab_id not in self._tabs:
            return
        
        self._tabs[tab_id].data.update(data)
        self.tab_data_changed.emit(tab_id, data)
    
    def get_tab_info(self, tab_id: str) -> Optional[TabInfo]:
        """获取选项卡信息"""
        return self._tabs.get(tab_id)
    
    def get_current_tab_id(self) -> Optional[str]:
        """获取当前选项卡ID"""
        return self._current_tab_id
    
    def get_all_tab_ids(self) -> List[str]:
        """获取所有选项卡ID"""
        return list(self._tabs.keys())
    
    def get_tab_count(self) -> int:
        """获取选项卡数量"""
        return len(self._tabs)
    
    def _get_tab_index(self, tab_id: str) -> int:
        """获取选项卡索引"""
        if tab_id not in self._tabs:
            return -1
        
        widget = self._tabs[tab_id].widget
        return self._tab_widget.indexOf(widget)
    
    def _setup_lazy_loading(self, tab_id: str):
        """设置延迟加载"""
        # 这里可以实现延迟加载逻辑
        # 例如：只在选项卡被激活时才初始化其内容
        pass
    
    def _load_tab_content(self, tab_id: str):
        """加载选项卡内容"""
        if tab_id in self._loaded_tabs:
            return
        
        try:
            tab_info = self._tabs[tab_id]
            controller = self._controllers.get(tab_id)
            
            # 如果有控制器，执行初始化
            if controller and hasattr(controller, 'initialize'):
                controller.initialize()
            
            self._loaded_tabs.add(tab_id)
            self.logger.info(f"选项卡内容已加载: {tab_id}")
            
        except Exception as e:
            self.logger.error(f"加载选项卡内容失败: {e}")
    
    def _check_unsaved_changes(self, tab_id: str) -> bool:
        """检查未保存的更改"""
        controller = self._controllers.get(tab_id)
        
        if controller and hasattr(controller, 'has_unsaved_changes'):
            if controller.has_unsaved_changes():
                reply = QMessageBox.question(
                    self._tab_widget,
                    "确认",
                    "选项卡中有未保存的更改，确定要关闭吗？",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Save:
                    if hasattr(controller, 'save_changes'):
                        return controller.save_changes()
                elif reply == QMessageBox.Cancel:
                    return False
        
        return True
    
    def _on_tab_changed(self, index: int):
        """处理选项卡改变事件"""
        if index < 0:
            return
        
        widget = self._tab_widget.widget(index)
        tab_id = None
        
        # 找到对应的选项卡ID
        for tid, tab_info in self._tabs.items():
            if tab_info.widget == widget:
                tab_id = tid
                break
        
        if tab_id:
            # 延迟切换以避免频繁切换
            self._switch_timer.stop()
            self._switch_timer.start(100)  # 100ms延迟
    
    def _on_tab_close_requested(self, index: int):
        """处理选项卡关闭请求"""
        widget = self._tab_widget.widget(index)
        tab_id = None
        
        # 找到对应的选项卡ID
        for tid, tab_info in self._tabs.items():
            if tab_info.widget == widget:
                tab_id = tid
                break
        
        if tab_id:
            self.close_tab(tab_id)
    
    def _on_tab_double_clicked(self, index: int):
        """处理选项卡双击事件"""
        # 可以实现双击重命名等功能
        pass
    
    def _on_tab_switched(self, old_tab_id: str, new_tab_id: str):
        """处理选项卡切换"""
        # 更新访问时间
        if new_tab_id in self._tabs:
            from datetime import datetime
            self._tabs[new_tab_id].last_accessed_time = datetime.now()
    
    def _handle_delayed_switch(self):
        """处理延迟切换"""
        current_index = self._tab_widget.currentIndex()
        if current_index >= 0:
            widget = self._tab_widget.widget(current_index)
            
            for tab_id, tab_info in self._tabs.items():
                if tab_info.widget == widget:
                    if tab_id != self._current_tab_id:
                        old_tab_id = self._current_tab_id
                        self._current_tab_id = tab_id
                        
                        # 延迟加载检查
                        if self._lazy_loading and tab_id not in self._loaded_tabs:
                            self._load_tab_content(tab_id)
                        
                        # 更新状态
                        for tid, tinfo in self._tabs.items():
                            tinfo.is_active = (tid == tab_id)
                        
                        # 发出信号
                        self.tab_switched.emit(old_tab_id or "", tab_id)
                    break
    
    def _close_current_tab(self):
        """关闭当前选项卡"""
        if self._current_tab_id:
            self.close_tab(self._current_tab_id)
    
    def _close_other_tabs(self):
        """关闭其他选项卡"""
        if not self._current_tab_id:
            return
        
        tabs_to_close = []
        for tab_id, tab_info in self._tabs.items():
            if tab_id != self._current_tab_id and tab_info.closable:
                tabs_to_close.append(tab_id)
        
        for tab_id in tabs_to_close:
            self.close_tab(tab_id)
    
    def _close_all_tabs(self):
        """关闭所有选项卡"""
        tabs_to_close = []
        for tab_id, tab_info in self._tabs.items():
            if tab_info.closable:
                tabs_to_close.append(tab_id)
        
        for tab_id in tabs_to_close:
            self.close_tab(tab_id)
    
    def _refresh_current_tab(self):
        """刷新当前选项卡"""
        if not self._current_tab_id:
            return
        
        controller = self._controllers.get(self._current_tab_id)
        if controller and hasattr(controller, 'refresh'):
            controller.refresh()
    
    def _reload_current_tab(self):
        """重新加载当前选项卡"""
        if not self._current_tab_id:
            return
        
        tab_id = self._current_tab_id
        self._loaded_tabs.discard(tab_id)
        self._load_tab_content(tab_id)
    
    def _duplicate_current_tab(self):
        """复制当前选项卡"""
        if not self._current_tab_id:
            return
        
        # 这里可以实现选项卡复制逻辑
        self.logger.info("复制选项卡功能待实现")
    
    def _create_main_detection_widget(self) -> QWidget:
        """
        【关键修复点】创建主检测组件 - 通过MainDetectionCoordinator获取视图
        """
        # [DIAGNOSTIC LOG] 记录开始创建主检测视图
        self.logger.info("🔍 [DIAGNOSTIC] 开始创建主检测视图")
        self.logger.info(f"🔍 [DIAGNOSTIC] Parent对象: {self.parent}, 类型: {type(self.parent)}")
        
        try:
            # 尝试从依赖容器获取MainDetectionCoordinator实例
            from src.core.dependency_injection import DependencyContainer
            from src.controllers.main_detection_coordinator import MainDetectionCoordinator
            from src.core.application import EventBus
            
            # 创建或获取核心组件
            if hasattr(self.parent, 'container') and self.parent.container:
                container = self.parent.container
                # [DIAGNOSTIC LOG] 记录容器来源
                self.logger.info(f"🔍 [DIAGNOSTIC] 使用Parent的容器: {container}")
            else:
                container = DependencyContainer()
                # [DIAGNOSTIC LOG] 记录容器创建
                self.logger.info(f"🔍 [DIAGNOSTIC] 创建新的容器: {container}")
            
            if hasattr(self.parent, 'event_bus') and self.parent.event_bus:
                event_bus = self.parent.event_bus
                # [DIAGNOSTIC LOG] 记录事件总线来源
                self.logger.info(f"🔍 [DIAGNOSTIC] 使用Parent的事件总线: {event_bus}")
            else:
                event_bus = EventBus()
                # [DIAGNOSTIC LOG] 记录事件总线创建
                self.logger.info(f"🔍 [DIAGNOSTIC] 创建新的事件总线: {event_bus}")
            
            # 总是创建新的MainDetectionCoordinator实例，避免依赖注入参数为None的问题
            # [DIAGNOSTIC LOG] 记录创建参数
            self.logger.info(f"🔍 [DIAGNOSTIC] 创建MainDetectionCoordinator参数 - event_bus: {event_bus}, container: {container}, parent: {self.parent}")
            coordinator = MainDetectionCoordinator(event_bus, container, self.parent)
            # [DIAGNOSTIC LOG] 记录创建成功
            self.logger.info(f"🔍 [DIAGNOSTIC] 创建新的MainDetectionCoordinator实例成功: {coordinator}")
            
            # [DIAGNOSTIC LOG] 记录即将调用get_view
            self.logger.info(f"🔍 [DIAGNOSTIC] 即将调用coordinator.get_view(), coordinator: {coordinator}")
            
            # 获取视图
            main_view = coordinator.get_view()
            
            # [DIAGNOSTIC LOG] 记录获取视图成功
            self.logger.info(f"🔍 [DIAGNOSTIC] 成功获取主检测视图: {main_view}, 类型: {type(main_view)}")
            return main_view
            
        except Exception as e:
            # [DIAGNOSTIC LOG] 记录完整的错误堆栈信息
            self.logger.error("🔍 [DIAGNOSTIC] 创建主检测组件时发生严重错误:", exc_info=True)
            self.logger.error(f"🔍 [DIAGNOSTIC] 错误详情: {e}")
            # 降级方案：创建错误显示组件
            return self._create_error_widget("主检测", str(e))
    
    def _create_error_widget(self, title: str, error_message: str) -> QWidget:
        """创建错误显示组件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        error_label = QLabel(f"{title}加载失败\n\n错误信息:\n{error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("""
            QLabel {
                color: #D32F2F;
                font-size: 14px;
                padding: 20px;
                background-color: #FFEBEE;
                border: 1px solid #FFCDD2;
                border-radius: 4px;
            }
        """)
        
        layout.addWidget(error_label)
        return widget
    
    def eventFilter(self, obj, event):
        """事件过滤器"""
        if obj == self._tab_widget.tabBar() and event.type() == QEvent.ContextMenu:
            # 显示上下文菜单
            self._tab_context_menu.exec_(event.globalPos())
            return True
        
        return super().eventFilter(obj, event)
    
    def set_max_tabs(self, max_tabs: int):
        """设置最大选项卡数量"""
        self._max_tabs = max(1, max_tabs)
    
    def enable_lazy_loading(self, enabled: bool):
        """启用/禁用延迟加载"""
        self._lazy_loading = enabled
    
    def cleanup(self):
        """清理资源"""
        # 清理所有控制器
        for controller in self._controllers.values():
            if hasattr(controller, 'cleanup'):
                controller.cleanup()
        
        self._controllers.clear()
        self._tabs.clear()
        self._loaded_tabs.clear()
        
        if self._tab_widget:
            self._tab_widget.deleteLater()
        
        self.logger.info("选项卡管理器清理完成")