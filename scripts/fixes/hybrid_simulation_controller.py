#!/usr/bin/env python3
"""
混合模拟控制器
支持孔位圆点 + 可选的低透明度路径显示

功能特点：
1. 主要关注孔位圆点颜色变化（灰色→蓝色→绿色/红色）
2. 可选显示间隔4列S形路径，透明度很低（1%-30%）
3. 确保路径与DXF完全对应
4. 避免路径干扰孔位观察
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


class OptimizedSnakePathRenderer(SnakePathRenderer):
    """优化的蛇形路径渲染器，支持透明度控制"""
    
    def __init__(self):
        super().__init__()
        self._path_opacity = 0.05  # 默认5%透明度
        self._show_paths = False   # 默认不显示路径
        
    def set_path_opacity(self, opacity: float):
        """设置路径透明度（0.0-1.0）"""
        self._path_opacity = max(0.0, min(1.0, opacity))
        
    def set_path_visibility(self, visible: bool):
        """设置路径显示开关"""
        self._show_paths = visible
        
    def render_path(self, holes: List[HoleData]):
        """渲染路径 - 支持透明度和可见性控制"""
        if not self._show_paths:
            # 如果不显示路径，直接清空路径项
            self.clear_paths()
            return
            
        # 调用父类方法渲染路径
        super().render_path(holes)
        
        # 应用透明度设置
        self._apply_path_transparency()
        
    def _apply_path_transparency(self):
        """应用路径透明度设置"""
        if not hasattr(self, 'path_items') or not self.path_items:
            return
            
        alpha = int(255 * self._path_opacity)  # 转换为0-255
        
        for item in self.path_items:
            # 获取当前颜色
            pen = item.pen()
            color = pen.color()
            
            # 设置透明度
            color.setAlpha(alpha)
            pen.setColor(color)
            item.setPen(pen)
            
            # 如果有填充色，也设置透明度
            brush = item.brush()
            if brush.style() != brush.NoBrush:
                brush_color = brush.color()
                brush_color.setAlpha(alpha)
                brush.setColor(brush_color)
                item.setBrush(brush)


class HybridSimulationController(QObject):
    """混合模拟控制器 - 孔位圆点 + 可选透明路径"""
    
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
        
        # 蛇形路径组件 - 使用优化版本
        self.snake_path_coordinator = SnakePathCoordinator()
        self.snake_path_renderer = OptimizedSnakePathRenderer()
        
        # 模拟定时器 - 支持配对检测时序  
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._start_next_detection)
        self.simulation_timer.setInterval(10000)  # 10秒/对
        
        # 状态变化定时器 - 9.5秒后变为最终状态
        self.status_change_timer = QTimer()
        self.status_change_timer.timeout.connect(self._finalize_current_pair_status)
        self.status_change_timer.setSingleShot(True)  # 单次触发
        
        # 下一配对定时器 - 确保0.5秒显示最终状态
        self.next_pair_timer = QTimer()
        self.next_pair_timer.timeout.connect(self._process_next_pair)
        self.next_pair_timer.setSingleShot(True)  # 单次触发
        
        # 模拟参数
        self.pair_detection_time = 10000  # 10秒/对
        self.status_change_time = 9500    # 9.5秒变为最终状态
        self.final_display_time = 500     # 0.5秒显示最终状态
        self.success_rate = 0.995         # 99.5%成功率
        
        # 当前检测状态
        self.current_detecting_pair = None  # 当前检测中的配对
        
        self._initialize()
        
    def _initialize(self):
        """初始化控制器"""
        # 设置蛇形路径策略为间隔4列S形扫描
        self.snake_path_coordinator.set_path_strategy(PathStrategy.INTERVAL_FOUR_S_SHAPE)
        self.snake_path_renderer.set_render_style(PathRenderStyle.SNAKE_FLOW)
        
        # 设置场景（snake_path_renderer需要场景）
        from PySide6.QtWidgets import QGraphicsScene
        self.snake_path_renderer.set_graphics_scene(QGraphicsScene())
        
        self.logger.info("✅ 混合模拟控制器初始化完成 - 支持孔位+透明路径")
        
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
        
    def set_sector_assignment_manager(self, sector_assignment_manager):
        """设置扇形分配管理器"""
        self.sector_assignment_manager = sector_assignment_manager
        self.logger.info("✅ 扇形分配管理器已设置")
        
    def set_path_visibility(self, visible: bool):
        """设置路径显示开关"""
        self.snake_path_renderer.set_path_visibility(visible)
        self.logger.info(f"🛤️  路径显示: {'开启' if visible else '关闭'}")
        
    def set_path_opacity(self, opacity: float):
        """设置路径透明度（0.0-1.0）"""
        self.snake_path_renderer.set_path_opacity(opacity)
        self.logger.info(f"🌫️  路径透明度: {opacity:.1%}")
        
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
            
        self.logger.info("🚀 开始混合模拟检测（孔位+可选透明路径）")
        
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
            
        # 渲染间隔4列S形检测路径（可选显示，低透明度）
        if self.graphics_view:
            # 将检测单元转换为孔位列表
            holes_to_render = []
            for unit in self.detection_units:
                if isinstance(unit, HolePair):
                    holes_to_render.extend(unit.holes)
                else:
                    holes_to_render.append(unit)
            self.snake_path_renderer.render_path(holes_to_render)
            
        # 重置状态
        self.current_index = 0
        self.is_running = True
        self.is_paused = False
        
        # 重置所有孔位状态为待检（灰色圆点）
        for hole in self.snake_sorted_holes:
            self._update_hole_status(hole.hole_id, HoleStatus.PENDING)
            
        # 立即开始第一个检测，不等定时器
        self._start_next_detection()
        
        # 发射信号
        self.simulation_started.emit()
        
    def pause_simulation(self):
        """暂停模拟"""
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.simulation_timer.stop()
            self.status_change_timer.stop()  # 同时停止状态变化定时器
            self.next_pair_timer.stop()      # 停止下一配对定时器
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
            self.next_pair_timer.stop()      # 停止下一配对定时器
            self.current_detecting_pair = None  # 清除当前检测配对
            
            # 清除路径渲染
            if self.graphics_view:
                self.snake_path_renderer.clear_paths()
                
            self.simulation_stopped.emit()
            self.logger.info("⏹️ 模拟已停止")
            
    def _start_next_detection(self):
        """开始下一个检测配对 - 设置蓝色状态"""
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
        
        # 开始检测：设置为蓝色状态（检测中）
        if isinstance(current_unit, HolePair):
            self._start_pair_detection(current_unit)
        else:
            self._start_single_hole_detection(current_unit)
            
        # 启动状态变化定时器（9.5秒后变为最终状态）
        self.status_change_timer.start(self.status_change_time)
            
        # 更新路径渲染进度
        if self.graphics_view:
            self.snake_path_renderer.update_progress(self.current_index)
            
        # 发射进度信号
        self.simulation_progress.emit(self.current_index + 1, len(self.detection_units))
        
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
        """9.5秒后确定当前配对的最终状态"""
        if not self.current_detecting_pair:
            return
            
        current_unit = self.current_detecting_pair
        
        if isinstance(current_unit, HolePair):
            # 处理配对
            for hole in current_unit.holes:
                final_status = self._simulate_detection_result()
                # 清除蓝色覆盖，显示最终状态颜色
                self._update_hole_status(hole.hole_id, final_status, color_override=None)
                status_text = "✅ 合格" if final_status == HoleStatus.QUALIFIED else "❌ 不合格"
                self.logger.info(f"📋 {hole.hole_id}: {status_text}")
        else:
            # 处理单孔
            final_status = self._simulate_detection_result()
            # 清除蓝色覆盖，显示最终状态颜色
            self._update_hole_status(current_unit.hole_id, final_status, color_override=None)
            status_text = "✅ 合格" if final_status == HoleStatus.QUALIFIED else "❌ 不合格"
            self.logger.info(f"📋 {current_unit.hole_id}: {status_text}")
            
        # 清除当前检测配对
        self.current_detecting_pair = None
        
        # 启动延迟定时器，0.5秒后进入下一个检测
        self.next_pair_timer.start(self.final_display_time)
        
    def _process_next_pair(self):
        """0.5秒延迟后移动到下一个检测配对"""
        if not self.is_running or self.is_paused:
            return
            
        # 移动到下一个检测单元
        self.current_index += 1
        
        # 检查是否完成所有检测
        if self.current_index >= len(self.detection_units):
            self._complete_simulation()
            return
            
        # 立即开始下一个检测（不等10秒定时器）
        self._start_next_detection()
        
    def _focus_on_sector(self, detection_unit):
        """扇形聚焦机制"""
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
            
        # 更新图形显示（支持颜色覆盖）
        if self.graphics_view:
            self._update_graphics_item_status(hole_id, status, color_override)
            
        # 更新全景图（包含颜色覆盖）
        if self.panorama_widget and hasattr(self.panorama_widget, 'update_hole_status'):
            self.panorama_widget.update_hole_status(hole_id, status, color_override)
            
        # 发射信号
        self.hole_status_updated.emit(hole_id, status)
        
    def _update_graphics_item_status(self, hole_id: str, status: HoleStatus, color_override=None):
        """更新图形项状态，支持颜色覆盖"""
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
                
                if color_override:
                    # 使用覆盖颜色（如蓝色检测中状态）
                    color = color_override
                else:
                    # 使用标准状态颜色
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