"""
P1页面主窗口控制器
负责P1页面特定的UI状态管理和交互逻辑

职责范围：
- P1页面的UI状态协调
- 页面特定的用户交互处理
- 与系统级控制器和shared服务的集成
- 页面级的业务流程控制
"""

import logging
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox, QFileDialog

from src.shared.services import get_business_service, get_graphics_service
from src.shared.components.factories import get_ui_factory
from src.shared.services.business_coordinator import get_business_coordinator


class MainWindowController(QObject):
    """
    主窗口控制器
    处理所有业务逻辑和组件协调
    """
    
    # 信号定义
    status_updated = Signal(str, str)  # hole_id, status
    detection_started = Signal()
    detection_stopped = Signal()
    detection_progress = Signal(int, int)  # current, total
    file_loaded = Signal(str)  # file_path
    error_occurred = Signal(str)  # error_message
    batch_created = Signal(str)  # batch_id
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 系统级业务协调器
        self.business_coordinator = get_business_coordinator()
        
        # P1页面特定服务
        self.business_service = get_business_service()
        self.graphics_service = get_graphics_service()
        self.ui_factory = get_ui_factory()
        
        # P1页面特定状态管理（UI相关）
        self._batch_manager = None
        self._detection_service = None
        
        # P1页面UI状态（不包含业务数据）
        self.current_batch_id: Optional[str] = None
        self.current_product = None
        self.current_product_id: Optional[int] = None
        self.ui_state = {
            'panorama_view_mode': 'default',
            'sector_highlighting_enabled': True,
            'color_legend_visible': True,
            'simulation_controls_visible': False
        }
        
        # 检测状态
        self.detection_running = False
        self.detection_paused = False
        self.detection_holes = []
        self.detection_index = 0
        
        # 定时器
        self.detection_timer = QTimer()
        self.detection_timer.timeout.connect(self._process_detection_step)
        
        # 蛇形路径相关
        self.snake_path_coordinator = None
        self.snake_sorted_holes = []
        self.snake_simulation_index = 0
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._process_simulation_step)
        self.is_simulation_running = False
        self.is_simulation_paused = False
    
    @property
    def batch_service(self):
        """延迟加载批次服务"""
        if self._batch_manager is None:
            from src.core.domain.services.batch_service import BatchService
            from src.core.infrastructure.repositories.batch_repository_impl import BatchRepositoryImpl
            repository = BatchRepositoryImpl()
            self._batch_manager = BatchService(repository)
        return self._batch_manager
    
    @property
    def detection_service(self):
        """延迟加载检测服务"""
        if self._detection_service is None:
            from src.shared.services.detection_service import DetectionService
            self._detection_service = DetectionService()
            self._detection_service.set_batch_service(self.batch_service)
        return self._detection_service
        
    def initialize(self):
        """初始化控制器"""
        self.logger.info("Initializing MainWindow controller")
        
        # 预加载关键组件
        # 注意：history_viewer 已在主窗口中直接创建，不需要预加载
        self.ui_factory.preload_components(['realtime_chart'])
        
        # 初始化蛇形路径协调器
        self.snake_path_coordinator = self.graphics_service.create_snake_path_coordinator()
        
        # 连接系统级协调器信号
        self._connect_business_coordinator_signals()
    
    def _connect_business_coordinator_signals(self):
        """连接系统级业务协调器信号"""
        try:
            # 文件操作信号
            self.business_coordinator.operation_completed.connect(self._on_business_operation_completed)
            self.business_coordinator.operation_failed.connect(self._on_business_operation_failed)
            self.business_coordinator.data_updated.connect(self._on_business_data_updated)
            
            self.logger.debug("Connected to BusinessCoordinator signals")
        except Exception as e:
            self.logger.error(f"Failed to connect business coordinator signals: {e}")
        
        # 连接shared_data_manager的信号
        try:
            from src.core.shared_data_manager import SharedDataManager
            shared_data = SharedDataManager()
            shared_data.data_changed.connect(self._on_shared_data_changed)
            self.logger.info("Connected to SharedDataManager signals")
        except Exception as e:
            self.logger.warning(f"Could not connect to SharedDataManager: {e}")
        
    def load_dxf_file(self, file_path: Optional[str] = None) -> bool:
        """
        P1页面加载DXF文件（委托给系统级控制器）
        
        Args:
            file_path: 文件路径，如果为None则显示文件选择对话框
            
        Returns:
            是否加载成功
        """
        try:
            if not file_path:
                file_path, _ = QFileDialog.getOpenFileName(
                    None,
                    "选择DXF文件",
                    "",
                    "DXF Files (*.dxf);;All Files (*)"
                )
                
            if not file_path:
                return False
            
            # 委托给系统级协调器处理业务逻辑
            self.business_coordinator.load_dxf_file(file_path)
            
            self.logger.info(f"P1 requested DXF file load: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"P1 DXF file load request failed: {e}")
            self.error_occurred.emit(str(e))
            return False
    
    def _on_shared_data_changed(self, data_type: str, data: Any):
        """处理共享数据变化（P1页面UI状态同步）"""
        if data_type == "hole_collection" and data:
            self.logger.info(f"P1 received hole_collection: {len(data.holes)} holes")
            # 更新P1页面UI状态
            self.ui_state['hole_count'] = len(data.holes)
            # 发射文件加载信号，通知P1页面UI更新
            self.file_loaded.emit("CAP1000.dxf")
    
    def _on_business_operation_completed(self, operation_name: str, result: Dict[str, Any]):
        """处理业务操作完成信号"""
        if operation_name == "load_file":
            file_path = result.get('file_path', '')
            self.file_loaded.emit(file_path)
            self.logger.info(f"P1 UI updated for file load: {file_path}")
        elif operation_name == "load_product":
            product_name = result.get('product_name', '')
            self.logger.info(f"P1 UI updated for product load: {product_name}")
    
    def _on_business_operation_failed(self, operation_name: str, error_message: str):
        """处理业务操作失败信号"""
        self.error_occurred.emit(f"{operation_name}: {error_message}")
        self.logger.error(f"P1 received business operation failure: {operation_name} - {error_message}")
    
    def _on_business_data_updated(self, data_type: str, data: Any):
        """处理业务数据更新信号"""
        if data_type == "hole_collection":
            # 通知P1页面更新显示
            self.logger.debug(f"P1 UI notified of hole collection update")
        elif data_type == "hole_status":
            hole_id = data.get('hole_id')
            status = data.get('status')
            if hole_id and status:
                self.status_updated.emit(hole_id, status)
            
    def select_product(self, product_name: str) -> bool:
        """P1页面选择产品（委托给系统级控制器）"""
        try:
            # 委托给系统级协调器处理
            self.business_coordinator.load_product(product_name)
            
            self.logger.info(f"P1 requested product load: {product_name}")
            return True
        except Exception as e:
            self.logger.error(f"P1 product load request failed: {e}")
            self.error_occurred.emit(str(e))
            return False
    
    def check_resumable_batch(self, is_mock: bool = False) -> Optional[Dict]:
        """检查是否有可恢复的批次（P1页面特定功能）"""
        try:
            # 获取当前产品信息（从系统级控制器）
            current_state = self.main_business_controller.get_current_state()
            if not current_state.get('current_product'):
                return None
            
            # 获取产品ID（通过business_service）
            current_product = self.business_service.current_product
            if not current_product or not hasattr(current_product, 'id'):
                return None
                
            batch = self.batch_service.get_resumable_batch(current_product.id, is_mock)
            if batch:
                return {
                    'batch_id': batch.batch_id,
                    'detection_number': batch.detection_number,
                    'completed_holes': batch.completed_holes,
                    'total_holes': batch.total_holes,
                    'pause_time': batch.updated_at
                }
            return None
        except Exception as e:
            self.logger.error(f"Failed to check resumable batch: {e}")
            return None
            
    def start_detection(self, is_mock: bool = False):
        """开始检测（P1页面特定功能，委托给系统级控制器）"""
        try:
            # 检查是否有数据
            current_state = self.business_coordinator.get_current_state()
            if not current_state.get('has_hole_collection'):
                self.error_occurred.emit("请先加载DXF文件")
                return
                
            if not current_state.get('current_product'):
                self.error_occurred.emit("请先选择产品")
                return
            
            # 获取产品ID用于批次创建
            current_product = self.business_service.current_product
            if not current_product or not hasattr(current_product, 'id'):
                self.error_occurred.emit("产品信息不完整")
                return
            
            # 创建批次（P1页面特定功能）
            product_name = getattr(current_product, 'model_name', str(current_product))
            batch = self.batch_service.create_batch(
                product_id=current_product.id,
                product_name=product_name,
                is_mock=is_mock
            )
            self.current_batch_id = batch.batch_id
            
            # 更新P1页面UI状态
            self.detection_running = True
            self.detection_paused = False
            self.detection_index = 0
            
            # 获取孔位数据用于检测
            hole_collection = self.business_service.get_hole_collection()
            if hole_collection:
                self.detection_holes = list(hole_collection.holes.values())
                
                # 使用检测服务（P1页面特定）
                self.detection_service.start_detection(
                    self.detection_holes,
                    batch_id=self.current_batch_id,
                    is_mock=is_mock
                )
                
                # 启动P1页面检测显示
                self.detection_started.emit()
                self.detection_timer.start(100)
                
                self.logger.info(f"P1 detection started with batch: {batch.batch_id}")
            else:
                self.error_occurred.emit("无法获取孔位数据")
                
        except Exception as e:
            self.logger.error(f"P1 detection start failed: {e}")
            self.error_occurred.emit(f"检测启动失败: {str(e)}")
    
    def continue_detection(self, batch_id: str):
        """继续检测"""
        # 加载批次状态
        detection_state = self.batch_service.resume_batch(batch_id)
        if not detection_state:
            self.error_occurred.emit("无法恢复检测状态")
            return
            
        self.current_batch_id = batch_id
        
        # 使用检测服务恢复
        if self.detection_service.resume_detection(detection_state):
            self.detection_running = True
            self.detection_paused = False
            self.detection_started.emit()
        else:
            self.error_occurred.emit("恢复检测失败")
        
    def pause_detection(self):
        """暂停检测"""
        self.detection_paused = True
        self.detection_timer.stop()
        
        # 使用检测服务暂停
        if self.detection_service.pause_detection():
            self.logger.info("Detection paused and state saved")
        
    def resume_detection(self):
        """恢复检测（简单恢复，推荐使用continue_detection进行完整恢复）"""
        if self.detection_running and self.detection_paused:
            self.detection_paused = False
            self.detection_timer.start(100)
            
    def stop_detection(self):
        """停止检测（终止）"""
        self.detection_running = False
        self.detection_paused = False
        self.detection_timer.stop()
        
        # 终止批次
        if self.current_batch_id:
            self.batch_service.terminate_batch(self.current_batch_id)
            
        self.detection_stopped.emit()
        
    def _process_detection_step(self):
        """处理单个检测步骤（P1页面UI显示逻辑）"""
        if not self.detection_running or self.detection_paused:
            return
            
        if self.detection_index >= len(self.detection_holes):
            # 检测完成
            self.stop_detection()
            return
            
        # 处理当前孔位（P1页面显示逻辑）
        current_hole = self.detection_holes[self.detection_index]
        
        # 模拟检测结果（P1页面特定功能）
        import random
        status = random.choice(['qualified', 'defective', 'blind'])
        
        # 委托给系统级协调器更新状态
        self.business_coordinator.update_hole_status(current_hole.hole_id, status)
        
        # P1页面UI更新
        self.status_updated.emit(current_hole.hole_id, status)
        self.detection_progress.emit(self.detection_index + 1, len(self.detection_holes))
        
        # 移动到下一个孔位
        self.detection_index += 1
        
    def start_snake_simulation(self):
        """开始蛇形路径模拟"""
        if not self.hole_collection or not self.snake_path_coordinator:
            self.error_occurred.emit("请先加载DXF文件")
            return
            
        # 计算蛇形路径
        holes = list(self.hole_collection.holes.values())
        self.snake_sorted_holes = self.snake_path_coordinator.calculate_snake_path(holes)
        self.snake_simulation_index = 0
        
        # 开始模拟
        self._simulate_snake_movement()
        
    def _simulate_snake_movement(self):
        """模拟蛇形路径移动"""
        if self.snake_simulation_index < len(self.snake_sorted_holes):
            current_hole = self.snake_sorted_holes[self.snake_simulation_index]
            
            # 更新当前孔位状态
            self.business_service.update_hole_status(current_hole.hole_id, "processing")
            self.status_updated.emit(current_hole.hole_id, "processing")
            
            # 继续下一个
            self.snake_simulation_index += 1
            QTimer.singleShot(50, self._simulate_snake_movement)
            
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息（委托给系统级控制器）"""
        try:
            # 使用系统级协调器获取统计信息
            return self.business_coordinator.get_completion_statistics()
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {
                'total_holes': 0,
                'qualified': 0,
                'defective': 0,
                'blind': 0,
                'pending': 0
            }
    
    def start_simulation(self):
        """开始蛇形路径模拟检测"""
        try:
            if not self.hole_collection:
                self.logger.warning("没有加载孔位数据，无法开始模拟")
                self.error_occurred.emit("请先加载DXF文件或选择产品")
                return
                
            if not self.snake_path_coordinator:
                self.logger.warning("蛇形路径协调器未初始化")
                return
                
            self.logger.info(f"🐍 开始蛇形路径模拟，共 {len(self.hole_collection.holes)} 个孔位")
            
            # 获取蛇形路径排序后的孔位
            holes_list = list(self.hole_collection.holes.values())
            self.snake_sorted_holes = self.snake_path_coordinator.get_snake_path_order(holes_list)
            
            if not self.snake_sorted_holes:
                self.error_occurred.emit("无法生成蛇形路径")
                return
                
            # 重置索引
            self.snake_simulation_index = 0
            self.is_simulation_running = True
            self.is_simulation_paused = False
            
            # 启动定时器，每100ms处理一个孔位
            self.simulation_timer.start(100)
            
            self.logger.info(f"✅ 模拟开始，路径包含 {len(self.snake_sorted_holes)} 个孔位")
            
        except Exception as e:
            self.logger.error(f"启动模拟失败: {e}")
            self.error_occurred.emit(f"启动模拟失败: {e}")
    
    def pause_simulation(self):
        """暂停模拟"""
        if self.is_simulation_running and not self.is_simulation_paused:
            self.is_simulation_paused = True
            self.simulation_timer.stop()
            self.logger.info("⏸️ 模拟已暂停")
    
    def resume_simulation(self):
        """恢复模拟"""  
        if self.is_simulation_running and self.is_simulation_paused:
            self.is_simulation_paused = False
            self.simulation_timer.start(100)
            self.logger.info("▶️ 模拟已恢复")
    
    def stop_simulation(self):
        """停止模拟"""
        self.is_simulation_running = False
        self.is_simulation_paused = False
        self.simulation_timer.stop()
        self.snake_simulation_index = 0
        self.logger.info("⏹️ 模拟已停止")
        
        # 重置所有孔位状态
        if self.hole_collection:
            from src.shared.models.hole_data import HoleStatus
            for hole in self.hole_collection.holes.values():
                hole.status = HoleStatus.PENDING
    
    def _process_simulation_step(self):
        """处理模拟检测的单个步骤"""
        try:
            if not self.is_simulation_running or self.is_simulation_paused:
                return
                
            if self.snake_simulation_index >= len(self.snake_sorted_holes):
                # 模拟完成
                self.stop_simulation()
                self.logger.info("✅ 模拟检测完成")
                return
                
            # 获取当前孔位
            current_hole = self.snake_sorted_holes[self.snake_simulation_index]
            
            # 模拟检测结果（99.5%合格率）
            import random
            if random.random() < 0.995:
                status = "qualified"
            else:
                status = "defective"
                
            # 更新孔位状态
            current_hole.status = status
            self.status_updated.emit(current_hole.hole_id, status)
            
            # 更新进度
            progress = int((self.snake_simulation_index + 1) / len(self.snake_sorted_holes) * 100)
            self.detection_progress.emit(self.snake_simulation_index + 1, len(self.snake_sorted_holes))
            
            # 移动到下一个孔位
            self.snake_simulation_index += 1
            
        except Exception as e:
            self.logger.error(f"模拟步骤处理失败: {e}")
            self.stop_simulation()
    
    def load_product(self, product):
        """加载产品及其关联的DXF文件"""
        try:
            self.logger.info(f"开始加载产品: {product}")
            
            # 设置当前产品
            self.current_product = product
            self.current_product_id = product.id if hasattr(product, 'id') else None
            
            # 如果产品有关联的DXF文件，自动加载
            if hasattr(product, 'dxf_file_path') and product.dxf_file_path:
                # 解析DXF路径
                from src.core.data_path_manager import DataPathManager
                path_manager = DataPathManager()
                dxf_path = path_manager.resolve_dxf_path(product.dxf_file_path)
                
                if os.path.exists(dxf_path):
                    # 加载DXF文件
                    self.logger.info(f"加载产品关联的DXF文件: {dxf_path}")
                    self.load_dxf_file(dxf_path)
                else:
                    self.logger.warning(f"产品关联的DXF文件不存在: {dxf_path}")
                    # 尝试查找相对路径
                    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                    alt_path = os.path.join(project_root, product.dxf_file_path)
                    if os.path.exists(alt_path):
                        self.logger.info(f"找到DXF文件替代路径: {alt_path}")
                        self.load_dxf_file(alt_path)
                    else:
                        self.error_occurred.emit(f"DXF文件不存在: {dxf_path}")
            else:
                self.logger.info("产品未关联DXF文件")
            
            # 发射产品加载完成信号
            product_name = product.model_name if hasattr(product, 'model_name') else str(product)
            self.file_loaded.emit(f"产品: {product_name}")
            self.logger.info(f"✅ 产品加载完成: {product_name}")
            
        except Exception as e:
            self.logger.error(f"加载产品失败: {e}")
            self.error_occurred.emit(f"加载产品失败: {str(e)}")
        
    def search_hole(self, query: str) -> List[str]:
        """
        搜索孔位
        
        Args:
            query: 搜索查询字符串
            
        Returns:
            匹配的孔位ID列表
        """
        try:
            self.logger.info(f"🔍 控制器接收到搜索请求: '{query}'")
            print(f"🔍 [DEBUG] 业务协调器存在: {self.business_coordinator is not None}")
            
            if self.business_coordinator:
                results = self.business_coordinator.search_holes(query)
                self.logger.info(f"✅ 控制器搜索完成: '{query}' -> {len(results)} 个结果")
                return results
            else:
                print(f"🔍 [DEBUG] 业务协调器未初始化")
                self.logger.warning("⚠️ 业务协调器未初始化，搜索功能不可用")
                return []
                
        except Exception as e:
            self.logger.error(f"搜索孔位失败: {e}")
            self.error_occurred.emit(f"搜索失败: {e}")
            return []
    
    def cleanup(self):
        """清理P1页面资源"""
        try:
            # 停止P1页面特定的定时器
            self.detection_timer.stop()
            self.simulation_timer.stop()
            
            # 清理P1页面特定服务
            if hasattr(self, 'business_service'):
                self.business_service.cleanup()
            if hasattr(self, 'graphics_service'):
                self.graphics_service.cleanup()
            
            # 清理系统级协调器（在应用关闭时）
            if hasattr(self, 'business_coordinator'):
                self.business_coordinator.cleanup()
            
            self.logger.info("P1 MainWindow controller cleaned up")
        except Exception as e:
            self.logger.error(f"P1 cleanup failed: {e}")