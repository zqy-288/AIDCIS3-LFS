"""
主检测协调器
负责协调侧边栏控制器、检测控制器等各个子控制器之间的交互
"""

import logging
from typing import Dict, Any, Optional, List

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout

from src.core.dependency_injection import injectable, DependencyContainer
from src.core.application import EventBus, ApplicationEvent
from src.core_business.models.hole_data import HoleData, HoleStatus

from .sidebar_controller import SidebarController
from .detection_controller import DetectionController, DetectionState


@injectable()
class MainDetectionCoordinator(QObject):
    """
    主检测协调器类
    协调各个控制器之间的通信和业务逻辑流程
    """
    
    # 协调器信号
    coordination_started = Signal()
    coordination_error = Signal(str, str)  # error_type, error_message
    
    def __init__(self, event_bus: EventBus, container: DependencyContainer, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.event_bus = event_bus
        self.container = container
        self.logger = logging.getLogger(__name__)
        
        # 子控制器实例
        self.sidebar_controller: Optional[SidebarController] = None
        self.detection_controller: Optional[DetectionController] = None
        
        # UI组件实例 - 关键修复点
        self._main_view: Optional[QWidget] = None
        
        # 协调状态
        self._is_coordinating = False
        self._coordination_config = {}
        
        # 初始化子控制器
        self._initialize_controllers()
        
        # 设置协调逻辑
        self._setup_coordination()
        
        # 订阅全局事件
        self._setup_global_event_subscriptions()
        
        self.logger.info("主检测协调器初始化完成")
    
    def _initialize_controllers(self):
        """初始化四个子控制器实例"""
        try:
            # 创建侧边栏控制器
            self.sidebar_controller = SidebarController(self.event_bus, self)
            
            # 创建检测控制器
            self.detection_controller = DetectionController(self.event_bus, self)
            
            # 将控制器注册到依赖容器（可选）
            self.container.register_instance(SidebarController, self.sidebar_controller)
            self.container.register_instance(DetectionController, self.detection_controller)
            
            self.logger.info("所有子控制器创建完成")
            
        except Exception as e:
            self.logger.error(f"初始化子控制器失败: {e}")
            self.coordination_error.emit("INITIALIZATION_ERROR", str(e))
    
    def _setup_coordination(self):
        """设置控制器间的协调逻辑"""
        try:
            # 1. 侧边栏控制器 -> 检测控制器的协调
            self._setup_sidebar_to_detection_coordination()
            
            # 2. 检测控制器 -> 侧边栏控制器的协调
            self._setup_detection_to_sidebar_coordination()
            
            # 3. 设置双向协调
            self._setup_bidirectional_coordination()
            
            self.logger.debug("控制器协调设置完成")
            
        except Exception as e:
            self.logger.error(f"设置控制器协调失败: {e}")
            self.coordination_error.emit("COORDINATION_SETUP_ERROR", str(e))
    
    def _setup_sidebar_to_detection_coordination(self):
        """设置侧边栏到检测控制器的协调"""
        if not self.sidebar_controller or not self.detection_controller:
            return
        
        # 侧边栏过滤器变化影响检测范围
        self.sidebar_controller.status_filter_changed.connect(
            self._on_sidebar_filter_changed
        )
        
        # 侧边栏孔位信息请求可能触发检测
        self.sidebar_controller.hole_info_requested.connect(
            self._on_sidebar_hole_info_requested
        )
    
    def _setup_detection_to_sidebar_coordination(self):
        """设置检测控制器到侧边栏的协调"""
        if not self.sidebar_controller or not self.detection_controller:
            return
        
        # 检测开始时更新侧边栏状态
        self.detection_controller.detection_started.connect(
            self._on_detection_started
        )
        
        # 检测进度更新侧边栏统计
        self.detection_controller.detection_progress.connect(
            self._on_detection_progress
        )
        
        # 检测完成更新侧边栏
        self.detection_controller.detection_completed.connect(
            self._on_detection_completed
        )
        
        # 检测暂停/恢复更新侧边栏状态
        self.detection_controller.detection_paused.connect(
            self._on_detection_paused
        )
        self.detection_controller.detection_resumed.connect(
            self._on_detection_resumed
        )
        
        # 检测错误时更新侧边栏
        self.detection_controller.detection_error.connect(
            self._on_detection_error
        )
    
    def _setup_bidirectional_coordination(self):
        """设置双向协调逻辑"""
        # 这里可以设置需要双向通信的协调逻辑
        # 例如：状态同步、数据一致性检查等
        pass
    
    def _setup_global_event_subscriptions(self):
        """设置全局事件订阅"""
        # 订阅应用程序级别的事件
        self.event_bus.subscribe("APPLICATION_SHUTDOWN", self._on_application_shutdown)
        self.event_bus.subscribe("FILE_LOADED", self._on_file_loaded)
        self.event_bus.subscribe("BATCH_CHANGED", self._on_batch_changed)
        self.event_bus.subscribe("USER_ACTION", self._on_user_action)
        
        self.logger.debug("全局事件订阅设置完成")
    
    def start_coordination(self, config: Optional[Dict[str, Any]] = None):
        """启动协调器"""
        try:
            if self._is_coordinating:
                self.logger.warning("协调器已在运行中")
                return False
            
            self._coordination_config = config or {}
            self._is_coordinating = True
            
            # 通知所有子控制器协调开始
            self._notify_controllers("coordination_started", self._coordination_config)
            
            # 发出协调开始信号
            self.coordination_started.emit()
            
            # 发布协调开始事件
            event = ApplicationEvent("COORDINATION_STARTED", {
                "coordinator": "MainDetectionCoordinator",
                "config": self._coordination_config
            })
            self.event_bus.post_event(event)
            
            self.logger.info("主检测协调器已启动")
            return True
            
        except Exception as e:
            self.logger.error(f"启动协调器失败: {e}")
            self.coordination_error.emit("START_ERROR", str(e))
            return False
    
    def stop_coordination(self):
        """停止协调器"""
        try:
            if not self._is_coordinating:
                self.logger.warning("协调器未在运行中")
                return False
            
            self._is_coordinating = False
            
            # 通知所有子控制器协调停止
            self._notify_controllers("coordination_stopped", {})
            
            # 发布协调停止事件
            event = ApplicationEvent("COORDINATION_STOPPED", {
                "coordinator": "MainDetectionCoordinator"
            })
            self.event_bus.post_event(event)
            
            self.logger.info("主检测协调器已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止协调器失败: {e}")
            self.coordination_error.emit("STOP_ERROR", str(e))
            return False
    
    def get_coordination_status(self) -> Dict[str, Any]:
        """获取协调器状态"""
        status = {
            "is_coordinating": self._is_coordinating,
            "config": self._coordination_config,
            "controllers": {}
        }
        
        # 获取各子控制器状态
        if self.sidebar_controller:
            status["controllers"]["sidebar"] = {
                "status_filter": self.sidebar_controller.get_status_filter(),
                "current_statistics": self.sidebar_controller.get_current_statistics()
            }
        
        if self.detection_controller:
            status["controllers"]["detection"] = {
                "state": self.detection_controller.get_detection_state().value,
                "progress": self.detection_controller.get_detection_progress()
            }
        
        return status
    
    def execute_coordinated_detection(self, holes: List[HoleData], config: Optional[Dict[str, Any]] = None):
        """执行协调检测"""
        try:
            if not self.detection_controller:
                self.logger.error("检测控制器未初始化")
                return False
            
            # 检查当前检测状态
            current_state = self.detection_controller.get_detection_state()
            if current_state != DetectionState.IDLE:
                self.logger.warning(f"检测控制器忙碌，当前状态: {current_state.value}")
                return False
            
            # 应用过滤器
            filtered_holes = self._apply_sidebar_filter(holes)
            
            if not filtered_holes:
                self.logger.warning("经过过滤后没有孔位需要检测")
                return False
            
            # 更新侧边栏显示即将开始的检测
            self._prepare_sidebar_for_detection(filtered_holes)
            
            # 启动检测
            detection_config = config or {}
            detection_config.update(self._coordination_config.get("detection", {}))
            
            success = self.detection_controller.start_detection(filtered_holes, detection_config)
            
            if success:
                self.logger.info(f"协调检测启动成功，孔位数量: {len(filtered_holes)}")
            else:
                self.logger.error("协调检测启动失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"执行协调检测失败: {e}")
            self.coordination_error.emit("COORDINATED_DETECTION_ERROR", str(e))
            return False
    
    # 私有协调方法
    def _apply_sidebar_filter(self, holes: List[HoleData]) -> List[HoleData]:
        """根据侧边栏过滤器过滤孔位"""
        if not self.sidebar_controller:
            return holes
        
        filter_type = self.sidebar_controller.get_status_filter()
        
        if filter_type == "all":
            return holes
        
        # 根据状态过滤
        status_mapping = {
            "pending": HoleStatus.PENDING,
            "qualified": HoleStatus.QUALIFIED,
            "defective": HoleStatus.DEFECTIVE,
            "blind": HoleStatus.BLIND,
            "tie_rod": HoleStatus.TIE_ROD,
            "processing": HoleStatus.PROCESSING
        }
        
        target_status = status_mapping.get(filter_type)
        if target_status:
            return [hole for hole in holes if hole.status == target_status]
        
        return holes
    
    def _prepare_sidebar_for_detection(self, holes: List[HoleData]):
        """为检测准备侧边栏显示"""
        if not self.sidebar_controller:
            return
        
        # 强制更新统计信息
        self.sidebar_controller.update_statistics(force_update=True)
    
    def _notify_controllers(self, event_type: str, data: Dict[str, Any]):
        """通知所有子控制器"""
        controllers = [
            self.sidebar_controller,
            self.detection_controller
        ]
        
        for controller in controllers:
            if controller and hasattr(controller, '_on_coordination_event'):
                try:
                    controller._on_coordination_event(event_type, data)
                except Exception as e:
                    self.logger.error(f"通知控制器 {type(controller).__name__} 失败: {e}")
    
    # 事件处理方法
    def _on_sidebar_filter_changed(self, filter_type: str):
        """处理侧边栏过滤器变化"""
        try:
            self.logger.debug(f"侧边栏过滤器变化: {filter_type}")
            
            # 如果检测正在进行中，可能需要相应调整
            if (self.detection_controller and 
                self.detection_controller.get_detection_state() == DetectionState.RUNNING):
                
                # 这里可以根据需要添加过滤器变化时的协调逻辑
                # 例如：暂停当前检测、应用新过滤器、重新开始检测
                pass
                
        except Exception as e:
            self.logger.error(f"处理侧边栏过滤器变化失败: {e}")
    
    def _on_sidebar_hole_info_requested(self, hole_id: str):
        """处理侧边栏孔位信息请求"""
        try:
            self.logger.debug(f"侧边栏请求孔位信息: {hole_id}")
            
            # 发布孔位信息请求事件，让其他组件响应
            event = ApplicationEvent("HOLE_INFO_REQUESTED", {
                "hole_id": hole_id,
                "source": "sidebar_controller"
            })
            self.event_bus.post_event(event)
            
        except Exception as e:
            self.logger.error(f"处理侧边栏孔位信息请求失败: {e}")
    
    def _on_detection_started(self, start_info: Dict[str, Any]):
        """处理检测开始"""
        try:
            self.logger.info("协调器收到检测开始通知")
            
            # 更新侧边栏显示检测开始状态
            if self.sidebar_controller:
                self.sidebar_controller.update_statistics(force_update=True)
                
        except Exception as e:
            self.logger.error(f"处理检测开始失败: {e}")
    
    def _on_detection_progress(self, progress_info: Dict[str, Any]):
        """处理检测进度更新"""
        try:
            # 定期更新侧边栏统计信息
            if self.sidebar_controller:
                self.sidebar_controller.update_statistics()
                
        except Exception as e:
            self.logger.error(f"处理检测进度更新失败: {e}")
    
    def _on_detection_completed(self, completion_info: Dict[str, Any]):
        """处理检测完成"""
        try:
            self.logger.info("协调器收到检测完成通知")
            
            # 更新侧边栏显示最终结果
            if self.sidebar_controller:
                self.sidebar_controller.update_statistics(force_update=True)
            
            # 发布协调完成事件
            event = ApplicationEvent("COORDINATED_DETECTION_COMPLETED", {
                "completion_info": completion_info,
                "coordinator": "MainDetectionCoordinator"
            })
            self.event_bus.post_event(event)
            
        except Exception as e:
            self.logger.error(f"处理检测完成失败: {e}")
    
    def _on_detection_paused(self, pause_info: Dict[str, Any]):
        """处理检测暂停"""
        try:
            self.logger.info("协调器收到检测暂停通知")
            
            # 更新侧边栏显示暂停状态
            if self.sidebar_controller:
                self.sidebar_controller.update_statistics(force_update=True)
                
        except Exception as e:
            self.logger.error(f"处理检测暂停失败: {e}")
    
    def _on_detection_resumed(self, resume_info: Dict[str, Any]):
        """处理检测恢复"""
        try:
            self.logger.info("协调器收到检测恢复通知")
            
            # 更新侧边栏显示恢复状态
            if self.sidebar_controller:
                self.sidebar_controller.update_statistics(force_update=True)
                
        except Exception as e:
            self.logger.error(f"处理检测恢复失败: {e}")
    
    def _on_detection_error(self, error_info: Dict[str, Any]):
        """处理检测错误"""
        try:
            error_type = error_info.get("error_type", "UNKNOWN")
            error_message = error_info.get("error_message", "Unknown error")
            
            self.logger.error(f"协调器收到检测错误通知: {error_type} - {error_message}")
            
            # 发出协调器错误信号
            self.coordination_error.emit(f"DETECTION_{error_type}", error_message)
            
        except Exception as e:
            self.logger.error(f"处理检测错误失败: {e}")
    
    def _on_application_shutdown(self, event: ApplicationEvent):
        """处理应用程序关闭"""
        try:
            self.logger.info("应用程序关闭，清理协调器资源")
            self.cleanup()
        except Exception as e:
            self.logger.error(f"处理应用程序关闭失败: {e}")
    
    def _on_file_loaded(self, event: ApplicationEvent):
        """处理文件加载"""
        try:
            file_path = event.data.get("file_path")
            self.logger.info(f"协调器收到文件加载通知: {file_path}")
            
            # 通知所有子控制器文件已加载
            self._notify_controllers("file_loaded", event.data)
            
        except Exception as e:
            self.logger.error(f"处理文件加载失败: {e}")
    
    def _on_batch_changed(self, event: ApplicationEvent):
        """处理批次变化"""
        try:
            batch_info = event.data
            self.logger.info(f"协调器收到批次变化通知")
            
            # 通知所有子控制器批次已变化
            self._notify_controllers("batch_changed", batch_info)
            
        except Exception as e:
            self.logger.error(f"处理批次变化失败: {e}")
    
    def _on_user_action(self, event: ApplicationEvent):
        """处理用户操作"""
        try:
            action = event.data.get("action")
            self.logger.debug(f"协调器收到用户操作: {action}")
            
            # 根据用户操作协调各控制器
            if action == "start_detection":
                holes = event.data.get("holes", [])
                config = event.data.get("config", {})
                if holes:
                    self.execute_coordinated_detection(holes, config)
            
        except Exception as e:
            self.logger.error(f"处理用户操作失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止协调
            self.stop_coordination()
            
            # 清理子控制器
            if self.sidebar_controller:
                self.sidebar_controller.cleanup()
            
            if self.detection_controller:
                self.detection_controller.cleanup()
            
            # 取消全局事件订阅
            self.event_bus.unsubscribe("APPLICATION_SHUTDOWN", self._on_application_shutdown)
            self.event_bus.unsubscribe("FILE_LOADED", self._on_file_loaded)
            self.event_bus.unsubscribe("BATCH_CHANGED", self._on_batch_changed)
            self.event_bus.unsubscribe("USER_ACTION", self._on_user_action)
            
            self.logger.info("主检测协调器资源清理完成")
            
        except Exception as e:
            self.logger.error(f"清理协调器资源失败: {e}")
    
    def get_view(self) -> QWidget:
        """
        【关键修复点】提供主检测界面的UI视图
        组装和返回包含所有UI元素的容器QWidget
        """
        # [DIAGNOSTIC LOG] 记录get_view()被调用
        self.logger.info("🔍 [DIAGNOSTIC] MainDetectionCoordinator.get_view() 被调用")
        self.logger.info(f"🔍 [DIAGNOSTIC] 检查依赖 - event_bus: {self.event_bus}, container: {self.container}")
        self.logger.info(f"🔍 [DIAGNOSTIC] 检查子控制器 - sidebar_controller: {self.sidebar_controller}, detection_controller: {self.detection_controller}")
        
        if self._main_view is not None:
            # [DIAGNOSTIC LOG] 记录返回缓存视图
            self.logger.info(f"🔍 [DIAGNOSTIC] 返回已缓存的主视图: {self._main_view}")
            return self._main_view
        
        try:
            # [DIAGNOSTIC LOG] 记录开始创建视图容器
            self.logger.info("🔍 [DIAGNOSTIC] 开始创建主视图容器")
            
            # 创建主视图容器
            self._main_view = QWidget()
            main_layout = QHBoxLayout(self._main_view)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(5)
            
            # [DIAGNOSTIC LOG] 记录容器创建成功
            self.logger.info(f"🔍 [DIAGNOSTIC] 主视图容器创建成功: {self._main_view}")
            
            # 暂时跳过侧边栏视图，直接添加主检测视图
            # TODO: 在SidebarController实现get_view方法后启用
            # if self.sidebar_controller:
            #     sidebar_view = self.sidebar_controller.get_view()
            #     if sidebar_view:
            #         main_layout.addWidget(sidebar_view)
            #         self.logger.debug("已添加侧边栏视图到主检测界面")
            
            # [DIAGNOSTIC LOG] 记录即将导入MainDetectionView
            self.logger.info("🔍 [DIAGNOSTIC] 即将导入MainDetectionView模块")
            
            # 添加主检测视图
            from src.modules.main_detection_view import MainDetectionView
            
            # [DIAGNOSTIC LOG] 记录导入成功，即将实例化
            self.logger.info("🔍 [DIAGNOSTIC] MainDetectionView模块导入成功，即将实例化")
            
            main_detection_view = MainDetectionView()
            
            # [DIAGNOSTIC LOG] 记录MainDetectionView实例创建成功
            self.logger.info(f"🔍 [DIAGNOSTIC] MainDetectionView 实例创建成功: {main_detection_view}")
            
            main_layout.addWidget(main_detection_view, 1)  # 占据更多空间
            
            # [DIAGNOSTIC LOG] 记录添加到布局成功
            self.logger.info("🔍 [DIAGNOSTIC] MainDetectionView已成功添加到布局")
            
            # 设置视图属性
            self._main_view.setObjectName("MainDetectionCoordinatorView")
            
            # [DIAGNOSTIC LOG] 记录最终成功
            self.logger.info(f"🔍 [DIAGNOSTIC] 主检测协调器视图创建完成，最终视图: {self._main_view}")
            return self._main_view
            
        except Exception as e:
            # [DIAGNOSTIC LOG] 记录完整的错误堆栈信息
            self.logger.error("🔍 [DIAGNOSTIC] 创建主检测视图时发生严重错误:", exc_info=True)
            self.logger.error(f"🔍 [DIAGNOSTIC] 错误详情: {e}")
            
            # 创建错误显示视图作为降级方案
            error_view = QWidget()
            error_layout = QHBoxLayout(error_view)
            from PySide6.QtWidgets import QLabel
            from PySide6.QtCore import Qt
            
            error_label = QLabel(f"主检测界面加载失败:\n{str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
            error_layout.addWidget(error_label)
            
            self._main_view = error_view
            return self._main_view