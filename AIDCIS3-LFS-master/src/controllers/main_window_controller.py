"""
[DEPRECATED] 主窗口控制器 - 已废弃
负责协调MainWindow的所有业务逻辑，实现UI与业务的分离

⚠️ 此文件已被重构后的新架构替代：
- 重构控制器: /src/controllers/main_window_controller_refactored.py
- 用例层: /src/application/use_cases/batch_detection_use_case.py
- 事件总线: /src/infrastructure/event_bus.py

新架构采用DDD设计，具有更好的解耦性和可测试性。
请使用新的控制器实现，本文件仅保留用于向后兼容。
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QMessageBox, QFileDialog

from src.services import get_business_service, get_graphics_service
from src.ui.factories import get_ui_factory


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
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 服务层
        self.business_service = get_business_service()
        self.graphics_service = get_graphics_service()
        self.ui_factory = get_ui_factory()
        
        # 批次管理器（延迟加载）
        self._batch_manager = None
        self._detection_service = None
        
        # 状态管理
        self.current_file_path: Optional[str] = None
        self.current_product: Optional[str] = None
        self.current_product_id: Optional[int] = None
        self.hole_collection = None
        self.current_batch_id: Optional[str] = None
        
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
    
    @property
    def batch_manager(self):
        """延迟加载批次管理器"""
        if self._batch_manager is None:
            from src.models.inspection_batch_model import get_batch_manager
            self._batch_manager = get_batch_manager()
        return self._batch_manager
    
    @property
    def detection_service(self):
        """延迟加载检测服务"""
        if self._detection_service is None:
            from src.services.detection_service import DetectionService
            self._detection_service = DetectionService()
            self._detection_service.set_batch_manager(self.batch_manager)
        return self._detection_service
        
    def initialize(self):
        """初始化控制器"""
        self.logger.info("Initializing MainWindow controller")
        
        # 预加载关键组件
        # 注意：history_viewer 已在主窗口中直接创建，不需要预加载
        self.ui_factory.preload_components(['realtime_chart'])
        
        # 初始化蛇形路径协调器
        self.snake_path_coordinator = self.graphics_service.create_snake_path_coordinator()
        
    def load_dxf_file(self, file_path: Optional[str] = None) -> bool:
        """
        加载DXF文件
        
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
                
            # 解析DXF文件
            self.hole_collection = self.business_service.parse_dxf_file(file_path)
            
            if not self.hole_collection:
                self.error_occurred.emit("无法解析DXF文件")
                return False
                
            # 应用孔位编号
            self.hole_collection = self.business_service.apply_hole_numbering(
                self.hole_collection, 
                strategy="grid"
            )
            
            # 设置到共享数据管理器
            self.business_service.set_hole_collection(self.hole_collection)
            
            # 调试信息
            print(f"[DEBUG Controller] hole_collection 包含 {len(self.hole_collection.holes)} 个孔位")
            test_collection = self.business_service.get_hole_collection()
            if test_collection:
                print(f"[DEBUG Controller] business_service 返回 {len(test_collection.holes)} 个孔位")
            else:
                print("[DEBUG Controller] business_service.get_hole_collection() 返回 None")
            
            # 更新状态
            self.current_file_path = file_path
            self.file_loaded.emit(file_path)
            
            self.logger.info(f"Successfully loaded DXF file: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading DXF file: {e}")
            self.error_occurred.emit(str(e))
            return False
            
    def select_product(self, product_name: str) -> bool:
        """选择产品"""
        try:
            if self.business_service.select_product(product_name):
                self.current_product = product_name
                # 获取产品实例以保存ID
                if hasattr(self.business_service, 'current_product') and self.business_service.current_product:
                    self.current_product_id = self.business_service.current_product.id
                self.logger.info(f"Selected product: {product_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error selecting product: {e}")
            self.error_occurred.emit(str(e))
            return False
    
    def check_resumable_batch(self, is_mock: bool = False) -> Optional[Dict]:
        """检查是否有可恢复的批次"""
        if not self.current_product_id:
            return None
            
        batch = self.batch_manager.get_resumable_batch(self.current_product_id, is_mock)
        if batch:
            return {
                'batch_id': batch.batch_id,
                'detection_number': batch.detection_number,
                'completed_holes': batch.completed_holes,
                'total_holes': batch.total_holes,
                'pause_time': batch.updated_at
            }
        return None
            
    def start_detection(self, is_mock: bool = False):
        """开始检测"""
        if not self.hole_collection:
            self.error_occurred.emit("请先加载DXF文件")
            return
            
        if not self.current_product_id:
            self.error_occurred.emit("请先选择产品")
            return
            
        # 创建新批次
        try:
            batch = self.batch_manager.create_batch(
                product_id=self.current_product_id,
                is_mock=is_mock
            )
            self.current_batch_id = batch.batch_id
            self.logger.info(f"Created batch: {batch.batch_id}")
        except Exception as e:
            self.error_occurred.emit(f"创建批次失败: {str(e)}")
            return
            
        self.detection_running = True
        self.detection_paused = False
        self.detection_index = 0
        
        # 获取所有待检测的孔位
        self.detection_holes = list(self.hole_collection.holes.values())
        
        # 使用检测服务
        self.detection_service.start_detection(
            self.detection_holes,
            batch_id=self.current_batch_id,
            is_mock=is_mock
        )
        
        # 开始检测
        self.detection_started.emit()
        self.detection_timer.start(100)  # 每100ms处理一个孔位
    
    def continue_detection(self, batch_id: str):
        """继续检测"""
        # 加载批次状态
        detection_state = self.batch_manager.resume_batch(batch_id)
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
        """恢复检测（已废弃，使用continue_detection）"""
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
            self.batch_manager.terminate_batch(self.current_batch_id)
            
        self.detection_stopped.emit()
        
    def _process_detection_step(self):
        """处理单个检测步骤"""
        if not self.detection_running or self.detection_paused:
            return
            
        if self.detection_index >= len(self.detection_holes):
            # 检测完成
            self.stop_detection()
            return
            
        # 处理当前孔位
        current_hole = self.detection_holes[self.detection_index]
        
        # 模拟检测结果
        import random
        status = random.choice(['qualified', 'defective', 'blind'])
        
        # 更新状态
        self.business_service.update_hole_status(current_hole.hole_id, status)
        self.status_updated.emit(current_hole.hole_id, status)
        
        # 更新进度
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
        """获取统计信息"""
        if not self.hole_collection:
            return {
                'total_holes': 0,
                'qualified': 0,
                'defective': 0,
                'blind': 0,
                'pending': 0
            }
            
        stats = {
            'total_holes': len(self.hole_collection.holes),
            'qualified': 0,
            'defective': 0,
            'blind': 0,
            'pending': 0
        }
        
        for hole in self.hole_collection.holes.values():
            status = getattr(hole, 'status', 'pending')
            # 如果status是枚举类型，获取其值
            if hasattr(status, 'value'):
                status = status.value
            # 转换为字符串并小写
            status = str(status).lower()
            if status in stats:
                stats[status] += 1
            else:
                stats['pending'] += 1
                
        return stats
        
    def cleanup(self):
        """清理资源"""
        self.detection_timer.stop()
        self.business_service.cleanup()
        self.graphics_service.cleanup()
        self.logger.info("MainWindow controller cleaned up")