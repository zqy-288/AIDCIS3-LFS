"""
重构后的主窗口控制器
使用用例层和事件总线实现低耦合设计
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox, QFileDialog

from src.domain.services.batch_service import BatchService
from src.infrastructure.repositories.batch_repository_impl import BatchRepositoryImpl
from src.application.use_cases.batch_detection_use_case import (
    BatchDetectionUseCase,
    StartDetectionRequest,
    PauseDetectionRequest,
    ContinueDetectionRequest
)
from src.infrastructure.event_bus import (
    get_event_bus, EventType, Event, publish_event
)
from src.services import get_business_service, get_graphics_service
from src.ui.factories import get_ui_factory


class MainWindowControllerRefactored(QObject):
    """
    重构后的主窗口控制器
    通过用例层协调业务逻辑，使用事件总线进行组件通信
    """
    
    # 保留必要的信号用于UI更新
    status_updated = Signal(str, str)
    detection_started = Signal()
    detection_stopped = Signal()
    detection_progress = Signal(int, int)
    file_loaded = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 初始化基础服务
        self._init_services()
        
        # 初始化状态
        self._init_state()
        
        # 订阅事件
        self._subscribe_events()
        
        # 初始化检测定时器
        self._init_timers()
    
    def _init_services(self):
        """初始化服务层"""
        # 基础服务
        self.business_service = get_business_service()
        self.graphics_service = get_graphics_service()
        self.ui_factory = get_ui_factory()
        
        # 批次管理服务
        repository = BatchRepositoryImpl()
        batch_service = BatchService(repository)
        self.batch_use_case = BatchDetectionUseCase(batch_service)
        
        # 事件总线
        self.event_bus = get_event_bus()
    
    def _init_state(self):
        """初始化状态"""
        self.current_file_path: Optional[str] = None
        self.current_product: Optional[str] = None
        self.current_product_id: Optional[int] = None
        self.hole_collection = None
        self.current_batch_id: Optional[str] = None
        
        # 检测状态
        self.detection_running = False
        self.detection_paused = False
        self.detection_index = 0
        self.detection_results: Dict[str, Any] = {}
        self.pending_holes: List[str] = []
        self.simulation_params: Dict[str, Any] = {}
    
    def _subscribe_events(self):
        """订阅事件"""
        # 批次事件
        self.event_bus.subscribe(EventType.BATCH_CREATED, self._on_batch_created, self)
        self.event_bus.subscribe(EventType.BATCH_STARTED, self._on_batch_started, self)
        self.event_bus.subscribe(EventType.BATCH_PAUSED, self._on_batch_paused, self)
        self.event_bus.subscribe(EventType.BATCH_RESUMED, self._on_batch_resumed, self)
        self.event_bus.subscribe(EventType.BATCH_TERMINATED, self._on_batch_terminated, self)
        
        # 检测事件
        self.event_bus.subscribe(EventType.DETECTION_PROGRESS, self._on_detection_progress, self)
        self.event_bus.subscribe(EventType.HOLE_DETECTED, self._on_hole_detected, self)
    
    def _init_timers(self):
        """初始化定时器"""
        self.detection_timer = QTimer()
        self.detection_timer.timeout.connect(self._simulate_detection_step)
        self.detection_timer.setInterval(500)  # 500ms
    
    # ==================== 公共方法 ====================
    
    def load_dxf_file(self, file_path: str) -> bool:
        """加载DXF文件"""
        try:
            if not Path(file_path).exists():
                self._show_error("文件不存在")
                return False
            
            # 解析DXF文件
            self.hole_collection = self.business_service.parse_dxf_file(file_path)
            
            if not self.hole_collection:
                self._show_error("DXF文件解析失败")
                return False
            
            self.current_file_path = file_path
            self.file_loaded.emit(file_path)
            
            # 发布事件
            publish_event(EventType.UI_DXF_LOADED, {
                'file_path': file_path,
                'hole_count': len(self.hole_collection)
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"加载DXF文件失败: {e}")
            self._show_error(f"加载失败: {str(e)}")
            return False
    
    def start_detection(self, is_mock: bool = False):
        """开始检测"""
        if not self._validate_detection_start():
            return
        
        # 创建开始检测请求
        request = StartDetectionRequest(
            product_id=self.current_product_id,
            product_name=self.current_product,
            is_mock=is_mock
        )
        
        # 调用用例
        response = self.batch_use_case.start_detection(request)
        
        if response.success:
            self.current_batch_id = response.batch_id
            self._start_detection_process(is_mock)
            
            # 发布事件
            publish_event(EventType.DETECTION_STARTED, {
                'batch_id': response.batch_id,
                'product_id': self.current_product_id,
                'is_mock': is_mock
            })
        else:
            self._show_error(response.error_message or "无法开始检测")
    
    def pause_detection(self):
        """暂停检测"""
        if not self.detection_running or self.detection_paused:
            return
        
        # 停止定时器
        self.detection_timer.stop()
        
        # 创建暂停请求
        request = PauseDetectionRequest(
            batch_id=self.current_batch_id,
            current_index=self.detection_index,
            detection_results=self.detection_results,
            pending_holes=self.pending_holes,
            simulation_params=self.simulation_params
        )
        
        # 调用用例
        if self.batch_use_case.pause_detection(request):
            self.detection_paused = True
            
            # 发布事件
            publish_event(EventType.DETECTION_PAUSED, {
                'batch_id': self.current_batch_id,
                'current_index': self.detection_index
            })
            
            self._show_info("检测已暂停")
        else:
            self._show_error("暂停失败")
    
    def continue_detection(self, batch_id: str):
        """继续检测"""
        # 创建继续检测请求
        request = ContinueDetectionRequest(batch_id=batch_id)
        
        # 调用用例
        response = self.batch_use_case.continue_detection(request)
        
        if response.success:
            self.current_batch_id = batch_id
            
            # 恢复状态
            state = response.detection_state
            self.detection_index = state.get('current_index', 0)
            self.detection_results = state.get('detection_results', {})
            self.pending_holes = state.get('pending_holes', [])
            self.simulation_params = state.get('simulation_params', {})
            
            # 继续检测
            self._resume_detection_process()
            
            # 发布事件
            publish_event(EventType.DETECTION_RESUMED, {
                'batch_id': batch_id,
                'current_index': self.detection_index
            })
        else:
            self._show_error(response.error_message or "无法继续检测")
    
    def stop_detection(self):
        """停止检测"""
        if not self.detection_running:
            return
        
        # 停止定时器
        self.detection_timer.stop()
        
        # 终止批次
        if self.current_batch_id:
            self.batch_use_case.terminate_detection(self.current_batch_id)
            
            # 发布事件
            publish_event(EventType.DETECTION_STOPPED, {
                'batch_id': self.current_batch_id,
                'completed_holes': len(self.detection_results)
            })
        
        # 重置状态
        self._reset_detection_state()
        self.detection_stopped.emit()
    
    def check_resumable_batch(self, is_mock: bool = False) -> Optional[Dict[str, Any]]:
        """检查可恢复的批次"""
        if not self.current_product_id:
            return None
        
        response = self.batch_use_case.check_resumable_batch(
            self.current_product_id, is_mock
        )
        
        if response.has_resumable:
            return {
                'batch_id': response.batch_id,
                'detection_number': response.detection_number,
                'pause_time': response.pause_time,
                'progress': response.progress
            }
        
        return None
    
    # ==================== 事件处理 ====================
    
    def _on_batch_created(self, event: Event):
        """批次创建事件处理"""
        self.logger.info(f"批次已创建: {event.data.get('batch_id')}")
    
    def _on_batch_started(self, event: Event):
        """批次开始事件处理"""
        self.detection_started.emit()
    
    def _on_batch_paused(self, event: Event):
        """批次暂停事件处理"""
        self.logger.info(f"批次已暂停: {event.data.get('batch_id')}")
    
    def _on_batch_resumed(self, event: Event):
        """批次恢复事件处理"""
        self.logger.info(f"批次已恢复: {event.data.get('batch_id')}")
    
    def _on_batch_terminated(self, event: Event):
        """批次终止事件处理"""
        self.logger.info(f"批次已终止: {event.data.get('batch_id')}")
    
    def _on_detection_progress(self, event: Event):
        """检测进度事件处理"""
        current = event.data.get('current', 0)
        total = event.data.get('total', 0)
        self.detection_progress.emit(current, total)
    
    def _on_hole_detected(self, event: Event):
        """孔位检测事件处理"""
        hole_id = event.data.get('hole_id')
        status = event.data.get('status')
        self.status_updated.emit(hole_id, status)
    
    # ==================== 私有方法 ====================
    
    def _validate_detection_start(self) -> bool:
        """验证是否可以开始检测"""
        if self.detection_running:
            self._show_warning("检测正在进行中")
            return False
        
        if not self.current_product_id:
            self._show_warning("请先选择产品")
            return False
        
        if not self.hole_collection:
            self._show_warning("请先加载DXF文件")
            return False
        
        return True
    
    def _start_detection_process(self, is_mock: bool):
        """开始检测流程"""
        self.detection_running = True
        self.detection_paused = False
        self.detection_index = 0
        self.detection_results.clear()
        
        # 设置待检测孔位
        self.pending_holes = list(self.hole_collection.keys())
        
        # 如果是模拟检测，设置参数
        if is_mock:
            self.simulation_params = {
                'qualified_rate': 0.8,
                'detection_speed': 500
            }
        
        # 更新批次总孔数
        self.batch_use_case.update_detection_progress(
            self.current_batch_id,
            total_holes=len(self.pending_holes)
        )
        
        # 启动定时器
        self.detection_timer.start()
        
        # 发布批次开始事件
        publish_event(EventType.BATCH_STARTED, {
            'batch_id': self.current_batch_id
        })
    
    def _resume_detection_process(self):
        """恢复检测流程"""
        self.detection_running = True
        self.detection_paused = False
        
        # 启动定时器
        self.detection_timer.start()
    
    def _simulate_detection_step(self):
        """模拟检测步骤"""
        if self.detection_index >= len(self.pending_holes):
            self._complete_detection()
            return
        
        # 获取当前孔位
        hole_id = self.pending_holes[self.detection_index]
        
        # 模拟检测结果
        import random
        is_qualified = random.random() < self.simulation_params.get('qualified_rate', 0.8)
        
        # 保存结果
        self.detection_results[hole_id] = {
            'status': 'qualified' if is_qualified else 'defective',
            'timestamp': Path.ctime(Path())
        }
        
        # 添加到批次
        self.batch_use_case.add_hole_result(
            self.current_batch_id,
            hole_id,
            is_qualified
        )
        
        # 发布事件
        publish_event(EventType.HOLE_DETECTED, {
            'hole_id': hole_id,
            'status': 'qualified' if is_qualified else 'defective'
        })
        
        # 更新进度
        self.detection_index += 1
        publish_event(EventType.DETECTION_PROGRESS, {
            'current': self.detection_index,
            'total': len(self.pending_holes)
        })
    
    def _complete_detection(self):
        """完成检测"""
        self.detection_timer.stop()
        
        # 完成批次
        self.batch_use_case.complete_batch(self.current_batch_id)
        
        # 发布事件
        publish_event(EventType.BATCH_COMPLETED, {
            'batch_id': self.current_batch_id,
            'total_holes': len(self.pending_holes),
            'qualified_holes': sum(1 for r in self.detection_results.values() 
                                 if r['status'] == 'qualified')
        })
        
        self._reset_detection_state()
        self.detection_stopped.emit()
        self._show_info("检测完成")
    
    def _reset_detection_state(self):
        """重置检测状态"""
        self.detection_running = False
        self.detection_paused = False
        self.detection_index = 0
        self.detection_results.clear()
        self.pending_holes.clear()
        self.simulation_params.clear()
    
    def _show_info(self, message: str):
        """显示信息"""
        QMessageBox.information(None, "提示", message)
    
    def _show_warning(self, message: str):
        """显示警告"""
        QMessageBox.warning(None, "警告", message)
    
    def _show_error(self, message: str):
        """显示错误"""
        self.error_occurred.emit(message)
        QMessageBox.critical(None, "错误", message)