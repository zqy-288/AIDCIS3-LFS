#!/usr/bin/env python3
"""
只显示孔位圆点的模拟控制器
禁用路径连线渲染，只关注孔位本身的颜色变化

专注功能：
1. 显示所有孔位圆点
2. 禁用路径连线渲染
3. 保持间隔4列S形检测逻辑
4. 支持蓝色检测中状态
"""

import logging
from typing import Optional, List, Dict, Any
import random

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor

from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.pages.shared.components.snake_path import SnakePathCoordinator, PathStrategy
from src.pages.shared.components.snake_path import SnakePathRenderer, PathRenderStyle
from src.pages.shared.components.snake_path.snake_path_renderer import HolePair
from src.core_business.graphics.sector_types import SectorQuadrant


class HoleOnlySimulationController(QObject):
    """只显示孔位圆点的模拟控制器 - 无路径连线干扰"""
    
    # 信号定义
    simulation_started = Signal()
    simulation_paused = Signal()
    simulation_stopped = Signal()
    simulation_progress = Signal(int, int)  # current, total
    hole_status_updated = Signal(str, object)  # hole_id, status
    simulation_completed = Signal()
    sector_focused = Signal(object)  # SectorQuadrant - 扇形聚焦信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 模拟状态
        self.is_running = False
        self.is_paused = False
        self.current_index = 0
        self.snake_sorted_holes = []
        self.detection_units = []  # 检测单元列表（HoleData或HolePair）
        self.current_sector = None  # 当前聚焦的扇形
        
        # 组件引用
        self.hole_collection = None
        self.graphics_view = None
        self.panorama_widget = None
        self.sector_assignment_manager = None  # 扇形分配管理器
        
        # 蛇形路径组件
        self.snake_path_coordinator = SnakePathCoordinator()
        self.snake_path_renderer = SnakePathRenderer()
        
        # 模拟定时器 - 支持配对检测时序
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._process_next_pair)
        self.simulation_timer.setInterval(10000)  # 10秒/对
        
        # 状态变化定时器 - 9.5秒后变为最终状态
        self.status_change_timer = QTimer()
        self.status_change_timer.timeout.connect(self._finalize_current_pair_status)
        self.status_change_timer.setSingleShot(True)  # 单次触发
        
        # 模拟参数
        self.pair_detection_time = 10000  # 10秒/对
        self.status_change_time = 9500    # 9.5秒变为最终状态
        self.success_rate = 0.995         # 99.5%成功率
        
        # 当前检测状态
        self.current_detecting_pair = None  # 当前检测中的配对
        
        self._initialize()
        
    def _initialize(self):
        """初始化控制器"""
        # 设置蛇形路径策略为间隔4列S形扫描
        self.snake_path_coordinator.set_path_strategy(PathStrategy.INTERVAL_FOUR_S_SHAPE)
        # 注意：这里我们不设置渲染样式，因为不需要渲染路径
        
        self.logger.info("✅ 孔位专用模拟控制器初始化完成 - 无路径连线干扰")
        
    def set_graphics_view(self, graphics_view):
        """设置图形视图"""
        self.graphics_view = graphics_view
        self.logger.info("✅ 图形视图已设置")
        
    def set_panorama_widget(self, panorama_widget):
        """设置全景图组件"""
        self.panorama_widget = panorama_widget
        self.logger.info("✅ 全景图组件已设置")
        
    def set_sector_assignment_manager(self, sector_assignment_manager):
        """设置扇形分配管理器"""
        self.sector_assignment_manager = sector_assignment_manager
        self.logger.info("✅ 扇形分配管理器已设置")
        
    def load_hole_collection(self, hole_collection: HoleCollection):
        """加载孔位集合"""
        self.hole_collection = hole_collection
        self.snake_path_coordinator.set_hole_collection(hole_collection)
        self.logger.info(f"✅ 加载孔位集合: {len(hole_collection.holes)} 个孔位")
        
    def start_simulation(self):
        """开始模拟检测 - 只关注孔位圆点，不渲染路径"""
        if not self.hole_collection:
            self.logger.warning("❌ 没有加载孔位数据")
            return
            
        self.logger.info("🚀 开始孔位专用模拟检测（无路径连线）")
        
        # 获取间隔4列S形检测单元（HolePair列表）
        self.snake_path_renderer.set_hole_collection(self.hole_collection)
        self.detection_units = self.snake_path_renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
        
        if not self.detection_units:
            self.logger.warning("❌ 无法生成间隔4列S形检测路径")
            return
            
        # 保持向后兼容，提取所有个体孔位
        self.snake_sorted_holes = []
        for unit in self.detection_units:
            if isinstance(unit, HolePair):
                self.snake_sorted_holes.extend(unit.holes)
            else:
                self.snake_sorted_holes.append(unit)
            
        # 重要：这里不调用路径渲染，只显示孔位圆点
        self.logger.info("🎯 专注孔位圆点显示，跳过路径连线渲染")
            
        # 重置状态
        self.current_index = 0
        self.is_running = True
        self.is_paused = False
        
        # 重置所有孔位状态为待检（灰色圆点）
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
            self.status_change_timer.stop()  # 同时停止状态变化定时器
            self.simulation_paused.emit()
            self.logger.info("⏸️ 模拟已暂停")
            
    def resume_simulation(self):
        """恢复模拟"""
        if self.is_running and self.is_paused:
            self.is_paused = False
            self.simulation_timer.start()
            # 注意：状态变化定时器需要根据剩余时间重新启动
            self.logger.info("▶️ 模拟已恢复")
            
    def stop_simulation(self):
        """停止模拟"""
        if self.is_running:
            self.is_running = False
            self.is_paused = False
            self.simulation_timer.stop()
            self.status_change_timer.stop()  # 停止状态变化定时器
            self.current_detecting_pair = None  # 清除当前检测配对
            
            self.simulation_stopped.emit()
            self.logger.info("⏹️ 模拟已停止")
            
    def _process_next_pair(self):
        """处理下一个检测配对 - 只更新孔位圆点颜色"""
        if not self.is_running or self.is_paused:
            return
            
        if self.current_index >= len(self.detection_units):
            # 模拟完成
            self._complete_simulation()
            return
            
        # 获取当前检测单元
        current_unit = self.detection_units[self.current_index]
        
        # 处理扇形聚焦
        self._focus_on_sector(current_unit)
        
        # 设置当前检测配对
        self.current_detecting_pair = current_unit
        
        # 开始检测：设置为蓝色状态（检测中）- 这里是关键！
        if isinstance(current_unit, HolePair):
            self._start_pair_detection(current_unit)
        else:
            self._start_single_hole_detection(current_unit)
            
        # 启动状态变化定时器（9.5秒后变为最终状态）
        self.status_change_timer.start(self.status_change_time)
            
        # 发射进度信号
        self.simulation_progress.emit(self.current_index + 1, len(self.detection_units))
        
        # 移动到下一个检测单元
        self.current_index += 1
        
    def _start_pair_detection(self, hole_pair: HolePair):
        """开始配对检测 - 设置为蓝色圆点"""
        blue_color = QColor(33, 150, 243)  # 蓝色
        for hole in hole_pair.holes:
            self._update_hole_status(hole.hole_id, HoleStatus.PENDING, color_override=blue_color)
        self.logger.info(f"🔵 开始检测配对: {' + '.join(hole_pair.get_hole_ids())}")
        
    def _start_single_hole_detection(self, hole):
        """开始单孔检测 - 设置为蓝色圆点"""
        blue_color = QColor(33, 150, 243)  # 蓝色
        self._update_hole_status(hole.hole_id, HoleStatus.PENDING, color_override=blue_color)
        self.logger.info(f"🔵 开始检测孔位: {hole.hole_id}")
        
    def _finalize_current_pair_status(self):
        """9.5秒后确定当前配对的最终状态 - 更新为绿色/红色圆点"""
        if not self.current_detecting_pair:
            return
            
        current_unit = self.current_detecting_pair
        
        if isinstance(current_unit, HolePair):
            # 处理配对
            for hole in current_unit.holes:
                final_status = self._simulate_detection_result()
                self._update_hole_status(hole.hole_id, final_status)  # 不传color_override，使用标准颜色
                status_text = "✅ 合格" if final_status == HoleStatus.QUALIFIED else "❌ 不合格"
                self.logger.info(f"📋 {hole.hole_id}: {status_text}")
        else:
            # 处理单孔
            final_status = self._simulate_detection_result()
            self._update_hole_status(current_unit.hole_id, final_status)
            status_text = "✅ 合格" if final_status == HoleStatus.QUALIFIED else "❌ 不合格"
            self.logger.info(f"📋 {current_unit.hole_id}: {status_text}")
            
        # 清除当前检测配对
        self.current_detecting_pair = None
        
    def _focus_on_sector(self, detection_unit):
        """扇形聚焦机制 - 根据检测单元确定并聚焦到相应扇形"""
        # 获取主要孔位用于扇形判断
        primary_hole = None
        if isinstance(detection_unit, HolePair):
            primary_hole = detection_unit.primary_hole
        else:
            primary_hole = detection_unit
            
        # 确定扇形（需要扇形分配管理器）
        sector = self._determine_sector(primary_hole)
        
        # 如果扇形发生变化，进行扇形切换
        if sector != self.current_sector:
            self.current_sector = sector
            self.logger.info(f"🎯 聚焦到扇形: {sector.value if sector else 'None'}")
            
            # 发射扇形聚焦信号
            if sector:
                self.sector_focused.emit(sector)
                
            # 通知全景图高亮扇形
            if self.panorama_widget and hasattr(self.panorama_widget, 'highlight_sector'):
                self.panorama_widget.highlight_sector(sector)
                
    def _determine_sector(self, hole: HoleData) -> Optional[SectorQuadrant]:
        """确定孔位所属扇形"""
        if not hole:
            return None
            
        # 优先使用扇形分配管理器
        if self.sector_assignment_manager:
            return self.sector_assignment_manager.get_hole_sector(hole.hole_id)
            
        # 备用简化逻辑：使用几何中心进行象限判断
        center_x, center_y = 0, 0
        if self.hole_collection and hasattr(self.hole_collection, 'get_bounds'):
            bounds = self.hole_collection.get_bounds()
            center_x = (bounds[0] + bounds[2]) / 2
            center_y = (bounds[1] + bounds[3]) / 2
        
        dx = hole.center_x - center_x
        dy = hole.center_y - center_y
        
        # Qt坐标系扇形分配
        if dx >= 0 and dy <= 0:
            return SectorQuadrant.SECTOR_1  # 右上
        elif dx < 0 and dy <= 0:
            return SectorQuadrant.SECTOR_2  # 左上
        elif dx < 0 and dy > 0:
            return SectorQuadrant.SECTOR_3  # 左下
        else:  # dx >= 0 and dy > 0
            return SectorQuadrant.SECTOR_4  # 右下
            
    def _simulate_detection_result(self) -> HoleStatus:
        """模拟检测结果"""
        # 根据成功率随机生成结果
        if random.random() < self.success_rate:
            return HoleStatus.QUALIFIED
        else:
            return HoleStatus.DEFECTIVE
            
    def _update_hole_status(self, hole_id: str, status: HoleStatus, color_override=None):
        """更新孔位状态，支持颜色覆盖（用于蓝色检测中状态）"""
        # 更新数据模型
        if self.hole_collection and hole_id in self.hole_collection.holes:
            self.hole_collection.holes[hole_id].detection_status = status
            
        # 更新全景图（包含颜色覆盖）- 这是关键的孔位圆点颜色更新
        if self.panorama_widget and hasattr(self.panorama_widget, 'update_hole_status'):
            self.panorama_widget.update_hole_status(hole_id, status, color_override)
            
        # 发射信号
        self.hole_status_updated.emit(hole_id, status)
        
    def _complete_simulation(self):
        """完成模拟"""
        self.is_running = False
        self.simulation_timer.stop()
        
        # 计算统计信息
        stats = self._calculate_simulation_stats()
        
        self.logger.info(f"✅ 模拟完成: 检测 {len(self.detection_units)} 个单元, "
                        f"共 {stats['total']} 个孔位, 合格 {stats['qualified']}, 异常 {stats['defective']}")
        
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
        
    def get_progress(self) -> tuple:
        """获取当前进度"""
        total = len(self.detection_units)
        return (self.current_index, total)
        
    def is_simulation_running(self) -> bool:
        """检查模拟是否正在运行"""
        return self.is_running and not self.is_paused
        
    def get_current_detection_unit(self):
        """获取当前检测单元"""
        if 0 <= self.current_index < len(self.detection_units):
            return self.detection_units[self.current_index]
        return None
        
    def get_detection_units_count(self) -> int:
        """获取检测单元总数"""
        return len(self.detection_units)
        
    def get_total_holes_count(self) -> int:
        """获取总孔位数"""
        return len(self.snake_sorted_holes)