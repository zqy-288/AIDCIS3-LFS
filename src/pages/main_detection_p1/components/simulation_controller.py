"""
模拟控制器 - 独立高内聚模块
负责管理蛇形路径模拟检测逻辑
"""

import logging
from typing import Optional, List, Dict, Any
import random

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor

from src.core_business.models.hole_data import HoleCollection, HoleData, HoleStatus
from src.pages.shared.components.snake_path import PathStrategy
from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, HolePair
from src.core_business.graphics.sector_types import SectorQuadrant


class SimulationController(QObject):
    """模拟控制器 - 管理蛇形路径模拟检测"""
    
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
        
        
        # 模拟定时器 - 按照用户需求设置为10秒间隔
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._process_next_pair)
        self.simulation_timer.setInterval(10000)  # 10秒/对（用户需求）
        
        # 状态变化定时器 - 9.5秒后变为最终状态（用户需求：蓝色9.5秒）
        self.status_change_timer = QTimer()
        self.status_change_timer.timeout.connect(self._finalize_current_pair_status)
        self.status_change_timer.setSingleShot(True)  # 单次触发
        
        # 模拟参数 - 按照用户需求设置
        self.pair_detection_time = 10000  # 10秒/对（用户需求）
        self.status_change_time = 9500    # 9.5秒变为最终状态（用户需求：蓝色9.5秒）
        self.success_rate = 0.995         # 99.5%成功率
        
        # 当前检测状态
        self.current_detecting_pair = None  # 当前检测中的配对
        
        self._initialize()
        
    def _initialize(self):
        """初始化控制器"""
        
        self.logger.info("✅ 模拟控制器初始化完成")
        
    def set_graphics_view(self, graphics_view):
        """设置图形视图（中间放大视图）"""
        self.graphics_view = graphics_view
        self.logger.info("✅ 中间放大视图已设置")
        
    def set_panorama_widget(self, panorama_widget):
        """设置全景图组件（左侧全景视图）"""
        self.panorama_widget = panorama_widget
        self.logger.info("✅ 左侧全景视图已设置")
        
    def set_sector_assignment_manager(self, sector_assignment_manager):
        """设置扇形分配管理器"""
        self.sector_assignment_manager = sector_assignment_manager
        self.logger.info("✅ 扇形分配管理器已设置")
        
    def load_hole_collection(self, hole_collection: HoleCollection):
        """加载孔位集合"""
        self.hole_collection = hole_collection
        self.logger.info(f"✅ 加载孔位集合: {len(hole_collection.holes)} 个孔位")
        
    def start_simulation(self):
        """开始模拟检测"""
        if not self.hole_collection:
            self.logger.warning("❌ 没有加载孔位数据")
            return
            
        self.logger.info("🚀 开始模拟检测")
        
        # 恢复HolePair配对检测算法
        snake_path_renderer = SnakePathRenderer()
        # 为路径渲染器设置虚拟场景（只用于生成检测单元，不渲染路径）
        from PySide6.QtWidgets import QGraphicsScene
        scene = QGraphicsScene()
        snake_path_renderer.set_graphics_scene(scene)
        snake_path_renderer.set_hole_collection(self.hole_collection)
        
        # 尝试生成HolePair检测单元
        self.logger.info(f"🔍 开始生成蛇形路径，数据源: {len(self.hole_collection.holes)} 个孔位")
        try:
            self.detection_units = snake_path_renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
            if self.detection_units:
                self.logger.info(f"✅ 成功生成HolePair检测单元: {len(self.detection_units)} 个")
            else:
                raise Exception("生成的检测单元为空")
        except Exception as e:
            self.logger.error(f"❌ HolePair生成失败: {e}")
            self.logger.error("❌ 无法生成双孔检测单元，模拟无法继续")
            return
            
        # 提取所有个体孔位（仅HolePair对象）
        self.snake_sorted_holes = []
        for unit in self.detection_units:
            self.snake_sorted_holes.extend(unit.holes)
                
        self.logger.info(f"📊 检测单元统计: {len(self.detection_units)} 个单元 -> {len(self.snake_sorted_holes)} 个个体孔位")
            
            
        # 重置状态
        self.current_index = 0
        self.is_running = True
        self.is_paused = False
        
        # 重置所有孔位状态为待检
        self.logger.info(f"🔄 开始重置 {len(self.snake_sorted_holes)} 个孔位状态为待检")
        for hole in self.snake_sorted_holes:
            self._update_hole_status(hole.hole_id, HoleStatus.PENDING)
            
        # 启动定时器
        self.simulation_timer.start()
        
        # 立即处理第一个孔位，提供即时的视觉反馈
        if self.detection_units:
            self.logger.info(f"🚀 立即开始第一个检测单元（总共 {len(self.detection_units)} 个单元）")
            self._process_next_pair()
        else:
            self.logger.error("❌ 没有检测单元可处理")
        
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
        """处理下一个检测配对 - 新的时序控制"""
        if not self.is_running or self.is_paused:
            self.logger.debug("⏸️ 模拟已停止或暂停")
            return
            
        if self.current_index >= len(self.detection_units):
            # 模拟完成
            self.logger.info(f"🏁 模拟完成！处理了 {self.current_index}/{len(self.detection_units)} 个检测单元")
            self._complete_simulation()
            return
            
        # 每10个单元输出一次进度
        if (self.current_index + 1) % 10 == 0 or self.current_index == 0:
            self.logger.info(f"🔍 处理检测单元 {self.current_index + 1}/{len(self.detection_units)}")
        else:
            self.logger.debug(f"🔍 处理检测单元 {self.current_index + 1}/{len(self.detection_units)}")
            
        # 获取当前检测单元
        current_unit = self.detection_units[self.current_index]
        
        # 处理扇形聚焦
        self._focus_on_sector(current_unit)
        
        # 设置当前检测孔位
        self.current_detecting_pair = current_unit
        
        # 开始检测：仅HolePair检测
        self._start_pair_detection(current_unit)
            
        # 启动状态变化定时器（9.5秒后变为最终状态）
        self.logger.info(f"⏰ 启动状态变化定时器，{self.status_change_time/1000}秒后更新最终状态")
        self.status_change_timer.start(self.status_change_time)
            
            
        # 发射进度信号
        progress_current = self.current_index + 1
        progress_total = len(self.detection_units)
        self.simulation_progress.emit(progress_current, progress_total)
        # 每10%输出一次进度
        progress_percent = progress_current/progress_total*100 if progress_total > 0 else 0
        if int(progress_percent) % 10 == 0 and int(progress_percent) != int((progress_current-1)/progress_total*100 if progress_current > 0 and progress_total > 0 else -1):
            self.logger.info(f"📈 进度更新: {progress_current}/{progress_total} ({progress_percent:.1f}%)")
        else:
            self.logger.debug(f"📈 进度更新: {progress_current}/{progress_total} ({progress_percent:.1f}%)")
        
        # 移动到下一个检测单元
        self.current_index += 1
        
    def _start_pair_detection(self, hole_pair: HolePair):
        """开始HolePair配对检测 - 同时设置两个孔位为蓝色状态"""
        self.logger.info(f"🔵 开始配对检测: {[h.hole_id for h in hole_pair.holes]}")
        for hole in hole_pair.holes:
            self.logger.info(f"🔵 设置孔位 {hole.hole_id} 为蓝色检测状态")
            self._update_hole_status(hole.hole_id, HoleStatus.PENDING, color_override=QColor(33, 150, 243))  # 蓝色
        
    def _finalize_current_pair_status(self):
        """9.5秒后确定当前孔位的最终状态"""
        self.logger.info(f"🔄 开始更新检测单元的最终状态")
        if not self.current_detecting_pair:
            self.logger.warning("⚠️ 没有当前检测配对，跳过状态更新")
            return
            
        current_unit = self.current_detecting_pair
        
        # 处理HolePair检测的最终状态
        # HolePair检测：两个孔位同时完成
        self.logger.info(f"🎯 处理配对单元，包含 {len(current_unit.holes)} 个孔位")
        for hole in current_unit.holes:
            final_status = self._simulate_detection_result()
            # 更新到最终状态，不使用颜色覆盖（清除蓝色）
            self.logger.info(f"📋 更新孔位 {hole.hole_id}: 清除蓝色，设置最终状态 {final_status.value}")
            self._update_hole_status(hole.hole_id, final_status, color_override=None)
            status_text = "✅ 合格" if final_status == HoleStatus.QUALIFIED else "❌ 不合格"
            self.logger.info(f"📋 配对检测 {hole.hole_id}: {status_text}")
            
        # 清除当前检测配对
        self.current_detecting_pair = None
        
        # 额外的强制刷新，确保蓝色被清除
        QTimer.singleShot(50, self._force_refresh_all_views)
        
    def _focus_on_sector(self, detection_unit):
        """扇形聚焦机制 - 根据检测单元确定并聚焦到相应扇形"""
        # HolePair：使用第一个孔位作为主要参考
        primary_hole = detection_unit.holes[0]
            
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
            
            
    def _process_single_hole(self, hole: HoleData):
        """处理单个孔位检测"""
        self.logger.info(f"🔍 检测单个孔位: {hole.hole_id}")
        
        status = self._simulate_detection_result()
        self._update_hole_status(hole.hole_id, status)
        
    def _simulate_detection_result(self) -> HoleStatus:
        """模拟检测结果"""
        # 根据成功率随机生成结果
        if random.random() < self.success_rate:
            return HoleStatus.QUALIFIED
        else:
            return HoleStatus.DEFECTIVE
            
    def _update_hole_status(self, hole_id: str, status: HoleStatus, color_override=None):
        """更新孔位状态，支持颜色覆盖（用于蓝色检测中状态）"""
        if color_override is not None:
            color_info = f"蓝色 (RGB: {color_override.red()}, {color_override.green()}, {color_override.blue()})"
        else:
            color_info = "清除颜色覆盖 (color_override=None)"
        self.logger.info(f"🔄 更新孔位状态: {hole_id} -> {status.value if hasattr(status, 'value') else status} ({color_info})")
        
        # 更新数据模型
        if self.hole_collection and hole_id in self.hole_collection.holes:
            old_status = self.hole_collection.holes[hole_id].status
            self.hole_collection.holes[hole_id].status = status
            self.logger.debug(f"   数据模型更新: {old_status.value if hasattr(old_status, 'value') else old_status} -> {status.value if hasattr(status, 'value') else status}")
        else:
            self.logger.warning(f"   ⚠️ 孔位 {hole_id} 不在数据集合中")
            
        # 更新图形显示（支持颜色覆盖）
        if self.graphics_view:
            # 优先使用graphics_view的标准接口
            if hasattr(self.graphics_view, 'update_hole_status'):
                self.graphics_view.update_hole_status(hole_id, status, color_override)
                self.logger.debug(f"   ✅ graphics_view已更新")
            else:
                # 备用方案：直接更新图形项
                self._update_graphics_item_status(hole_id, status, color_override)
                self.logger.debug(f"   ✅ 使用备用图形项更新")
            # 强制刷新视图以确保状态同步
            self._force_refresh_graphics_view()
        else:
            self.logger.warning(f"   ⚠️ graphics_view 不可用")
            
        # 更新全景图（包含颜色覆盖）
        if self.panorama_widget and hasattr(self.panorama_widget, 'update_hole_status'):
            self.panorama_widget.update_hole_status(hole_id, status, color_override)
            self.logger.debug(f"   ✅ panorama_widget已更新")
            
        # 发射信号
        self.hole_status_updated.emit(hole_id, status)
        self.logger.debug(f"   📡 状态更新信号已发射")
        
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
                
    def _force_refresh_graphics_view(self):
        """强制刷新图形视图以确保状态同步"""
        try:
            if self.graphics_view:
                # 强制重绘视图
                self.graphics_view.viewport().update()
                
                # 如果有场景，也更新场景
                scene = None
                if hasattr(self.graphics_view, 'scene'):
                    scene = self.graphics_view.scene
                else:
                    try:
                        scene = self.graphics_view.scene()
                    except:
                        pass
                        
                if scene:
                    scene.update()
                    
        except Exception as e:
            self.logger.warning(f"强制刷新视图失败: {e}")
    
    def _force_refresh_all_views(self):
        """强制刷新所有视图，确保蓝色状态被清除"""
        try:
            # 刷新中间的图形视图
            if self.graphics_view:
                self.graphics_view.viewport().repaint()  # 使用 repaint 而不是 update
                if hasattr(self.graphics_view, 'scene') and self.graphics_view.scene:
                    if callable(self.graphics_view.scene):
                        scene = self.graphics_view.scene()
                    else:
                        scene = self.graphics_view.scene
                    if scene:
                        scene.update()
            
            # 刷新左侧的全景图
            if self.panorama_widget:
                self.panorama_widget.repaint()  # 强制重绘整个widget
                if hasattr(self.panorama_widget, 'panorama_view'):
                    self.panorama_widget.panorama_view.viewport().repaint()
            
            self.logger.debug("执行了强制刷新所有视图")
        except Exception as e:
            self.logger.warning(f"强制刷新所有视图失败: {e}")
                
    def _complete_simulation(self):
        """完成模拟"""
        self.is_running = False
        self.simulation_timer.stop()
        
        # 计算统计信息
        stats = self._calculate_simulation_stats()
        
        self.logger.info(f"🏆 模拟完成统计：")
        self.logger.info(f"   检测单元: {len(self.detection_units)} 个")
        self.logger.info(f"   总孔位数: {stats['total']} 个")
        self.logger.info(f"   合格: {stats['qualified']} 个 ({stats['qualified']/stats['total']*100:.1f}%)")
        self.logger.info(f"   异常: {stats['defective']} 个 ({stats['defective']/stats['total']*100:.1f}%)")
        self.logger.info(f"   待检: {stats['pending']} 个")
        
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
            if hole.status == HoleStatus.QUALIFIED:
                stats['qualified'] += 1
            elif hole.status == HoleStatus.DEFECTIVE:
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