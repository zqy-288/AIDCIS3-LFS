"""
模拟控制器 - 独立高内聚模块
负责管理蛇形路径模拟检测逻辑
"""

import logging
from typing import Optional, List, Dict, Any
import random

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QWidget

from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.core_business.graphics.snake_path_coordinator import SnakePathCoordinator, PathStrategy
from src.core_business.graphics.snake_path_renderer import SnakePathRenderer, PathRenderStyle


class SimulationController(QObject):
    """模拟控制器 - 管理蛇形路径模拟检测"""
    
    # 信号定义
    simulation_started = Signal()
    simulation_paused = Signal()
    simulation_stopped = Signal()
    simulation_progress = Signal(int, int)  # current, total
    hole_status_updated = Signal(str, object)  # hole_id, status
    simulation_completed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 模拟状态
        self.is_running = False
        self.is_paused = False
        self.current_index = 0
        self.snake_sorted_holes = []
        
        # 组件引用
        self.hole_collection = None
        self.graphics_view = None
        self.panorama_widget = None
        
        # 蛇形路径组件
        self.snake_path_coordinator = SnakePathCoordinator()
        self.snake_path_renderer = SnakePathRenderer()
        
        # 模拟定时器
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._process_next_hole)
        self.simulation_timer.setInterval(100)  # 100ms/孔
        
        # 模拟参数
        self.simulation_speed = 100  # ms/hole
        self.success_rate = 0.995  # 99.5%成功率
        
        self._initialize()
        
    def _initialize(self):
        """初始化控制器"""
        # 设置蛇形路径策略
        self.snake_path_coordinator.set_path_strategy(PathStrategy.HYBRID)
        self.snake_path_renderer.set_render_style(PathRenderStyle.SNAKE_FLOW)
        # 设置场景（snake_path_renderer需要场景）
        from PySide6.QtWidgets import QGraphicsScene
        self.snake_path_renderer.set_graphics_scene(QGraphicsScene())
        
        self.logger.info("✅ 模拟控制器初始化完成")
        
    def set_graphics_view(self, graphics_view):
        """设置图形视图"""
        self.graphics_view = graphics_view
        # 设置场景而不是视图
        if hasattr(graphics_view, 'scene'):
            scene = graphics_view.scene if graphics_view.scene else graphics_view.scene()
            self.snake_path_renderer.set_graphics_scene(scene)
        self.logger.info("✅ 图形视图已设置")
        
    def set_panorama_widget(self, panorama_widget):
        """设置全景图组件"""
        self.panorama_widget = panorama_widget
        self.logger.info("✅ 全景图组件已设置")
        
    def load_hole_collection(self, hole_collection: HoleCollection):
        """加载孔位集合"""
        self.hole_collection = hole_collection
        self.snake_path_coordinator.set_hole_collection(hole_collection)
        self.logger.info(f"✅ 加载孔位集合: {len(hole_collection.holes)} 个孔位")
        
    def start_simulation(self):
        """开始模拟检测"""
        if not self.hole_collection:
            self.logger.warning("❌ 没有加载孔位数据")
            return
            
        self.logger.info("🚀 开始蛇形路径模拟检测")
        
        # 获取蛇形路径顺序
        holes_list = list(self.hole_collection.holes.values())
        self.snake_sorted_holes = self.snake_path_coordinator.get_snake_path_order(holes_list)
        
        if not self.snake_sorted_holes:
            self.logger.warning("❌ 无法生成蛇形路径")
            return
            
        # 渲染蛇形路径
        if self.graphics_view:
            self.snake_path_renderer.render_path(self.snake_sorted_holes)
            
        # 重置状态
        self.current_index = 0
        self.is_running = True
        self.is_paused = False
        
        # 重置所有孔位状态为待检
        for hole in self.snake_sorted_holes:
            self._update_hole_status(hole.hole_id, HoleStatus.PENDING)
            
        # 启动定时器
        self.simulation_timer.start()
        
        # 发射信号
        self.simulation_started.emit()
        
    def pause_simulation(self):
        """暂停模拟"""
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.simulation_timer.stop()
            self.simulation_paused.emit()
            self.logger.info("⏸️ 模拟已暂停")
            
    def resume_simulation(self):
        """恢复模拟"""
        if self.is_running and self.is_paused:
            self.is_paused = False
            self.simulation_timer.start()
            self.logger.info("▶️ 模拟已恢复")
            
    def stop_simulation(self):
        """停止模拟"""
        if self.is_running:
            self.is_running = False
            self.is_paused = False
            self.simulation_timer.stop()
            
            # 清除路径渲染
            if self.graphics_view:
                self.snake_path_renderer.clear_path()
                
            self.simulation_stopped.emit()
            self.logger.info("⏹️ 模拟已停止")
            
    def _process_next_hole(self):
        """处理下一个孔位"""
        if not self.is_running or self.is_paused:
            return
            
        if self.current_index >= len(self.snake_sorted_holes):
            # 模拟完成
            self._complete_simulation()
            return
            
        # 获取当前孔位
        current_hole = self.snake_sorted_holes[self.current_index]
        
        # 模拟检测结果
        status = self._simulate_detection_result()
        
        # 更新孔位状态
        self._update_hole_status(current_hole.hole_id, status)
        
        # 更新路径渲染进度
        if self.graphics_view:
            self.snake_path_renderer.update_progress(self.current_index)
            
        # 发射进度信号
        self.simulation_progress.emit(self.current_index + 1, len(self.snake_sorted_holes))
        
        # 移动到下一个孔位
        self.current_index += 1
        
    def _simulate_detection_result(self) -> HoleStatus:
        """模拟检测结果"""
        # 根据成功率随机生成结果
        if random.random() < self.success_rate:
            return HoleStatus.QUALIFIED
        else:
            return HoleStatus.DEFECTIVE
            
    def _update_hole_status(self, hole_id: str, status: HoleStatus):
        """更新孔位状态"""
        # 更新数据模型
        if self.hole_collection and hole_id in self.hole_collection.holes:
            self.hole_collection.holes[hole_id].detection_status = status
            
        # 更新图形显示
        if self.graphics_view:
            self._update_graphics_item_status(hole_id, status)
            
        # 更新全景图
        if self.panorama_widget and hasattr(self.panorama_widget, 'update_hole_status'):
            self.panorama_widget.update_hole_status(hole_id, status)
            
        # 发射信号
        self.hole_status_updated.emit(hole_id, status)
        
    def _update_graphics_item_status(self, hole_id: str, status: HoleStatus):
        """更新图形项状态"""
        # 获取场景
        scene = None
        if hasattr(self.graphics_view, 'scene'):
            scene = self.graphics_view.scene
        else:
            try:
                scene = self.graphics_view.scene()
            except:
                pass
                
        if not scene:
            return
            
        # 查找对应的图形项
        for item in scene.items():
            if item.data(0) == hole_id:  # Qt.UserRole = 0
                # 更新颜色
                from PySide6.QtGui import QBrush, QColor
                color_map = {
                    HoleStatus.QUALIFIED: QColor(76, 175, 80),    # 绿色
                    HoleStatus.DEFECTIVE: QColor(244, 67, 54),    # 红色
                    HoleStatus.PENDING: QColor(200, 200, 200),    # 灰色
                }
                
                color = color_map.get(status, QColor(200, 200, 200))
                if hasattr(item, 'setBrush'):
                    item.setBrush(QBrush(color))
                break
                
    def _complete_simulation(self):
        """完成模拟"""
        self.is_running = False
        self.simulation_timer.stop()
        
        # 计算统计信息
        stats = self._calculate_simulation_stats()
        
        self.logger.info(f"✅ 模拟完成: 检测 {stats['total']} 个孔位, "
                        f"合格 {stats['qualified']}, 异常 {stats['defective']}")
        
        self.simulation_completed.emit()
        
    def _calculate_simulation_stats(self) -> dict:
        """计算模拟统计信息"""
        stats = {
            'total': len(self.snake_sorted_holes),
            'qualified': 0,
            'defective': 0,
            'pending': 0
        }
        
        for hole in self.snake_sorted_holes:
            if hole.detection_status == HoleStatus.QUALIFIED:
                stats['qualified'] += 1
            elif hole.detection_status == HoleStatus.DEFECTIVE:
                stats['defective'] += 1
            else:
                stats['pending'] += 1
                
        return stats
        
    def set_simulation_speed(self, ms_per_hole: int):
        """设置模拟速度"""
        self.simulation_speed = ms_per_hole
        self.simulation_timer.setInterval(ms_per_hole)
        self.logger.info(f"模拟速度设置为: {ms_per_hole}ms/孔")
        
    def set_success_rate(self, rate: float):
        """设置成功率"""
        self.success_rate = max(0.0, min(1.0, rate))
        self.logger.info(f"成功率设置为: {self.success_rate * 100:.1f}%")
        
    def get_progress(self) -> tuple:
        """获取当前进度"""
        total = len(self.snake_sorted_holes)
        return (self.current_index, total)
        
    def is_simulation_running(self) -> bool:
        """检查模拟是否正在运行"""
        return self.is_running and not self.is_paused