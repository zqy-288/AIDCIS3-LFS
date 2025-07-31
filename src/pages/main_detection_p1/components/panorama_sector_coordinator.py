"""
全景扇形交互协调器 - 独立高内聚模块
负责处理全景图与扇形区域的交互逻辑
"""

import logging
from typing import Optional, Dict, List, Any

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QWidget

from src.core_business.graphics.sector_types import SectorQuadrant
from src.core_business.models.hole_data import HoleCollection, HoleData
from .sector_assignment_manager import SectorAssignmentManager


class PanoramaSectorCoordinator(QObject):
    """全景扇形交互协调器 - 负责全景图与扇形交互逻辑"""
    
    # 信号定义
    sector_clicked = Signal(object)  # SectorQuadrant
    sector_holes_filtered = Signal(object)  # HoleCollection
    sector_stats_updated = Signal(dict)  # 扇形统计信息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # 状态管理
        self.current_sector = None
        self.hole_collection = None
        self.sector_holes_map = {}  # 扇形到孔位的映射
        
        # 组件引用
        self.panorama_widget = None
        self.graphics_view = None
        
        # 扇形分配管理器
        self.sector_assignment_manager = SectorAssignmentManager()
        self.sector_assignment_manager.sector_assignments_updated.connect(
            self._on_sector_assignments_updated
        )
        
        # 初始化
        self._initialize()
        
    def _initialize(self):
        """初始化协调器"""
        self.logger.info("✅ 全景扇形交互协调器初始化")
        
    def set_panorama_widget(self, panorama_widget):
        """设置全景图组件"""
        self.panorama_widget = panorama_widget
        
        # 连接全景图信号
        if hasattr(panorama_widget, 'sector_clicked'):
            panorama_widget.sector_clicked.connect(self._on_panorama_sector_clicked)
            
        self.logger.info("✅ 全景图组件已连接")
        
    def set_graphics_view(self, graphics_view):
        """设置中心图形视图"""
        self.graphics_view = graphics_view
        self.logger.info("✅ 图形视图已连接")
        
    def load_hole_collection(self, hole_collection: HoleCollection):
        """加载孔位集合数据"""
        self.hole_collection = hole_collection
        
        # 使用扇形分配管理器进行分配
        self.sector_assignment_manager.set_hole_collection(hole_collection)
        
        # 更新扇形孔位映射
        self._update_sector_holes_map()
        
        # 更新全景图显示
        if self.panorama_widget and hasattr(self.panorama_widget, 'load_complete_view'):
            self.panorama_widget.load_complete_view(hole_collection)
            
        self.logger.info(f"✅ 加载孔位集合: {len(hole_collection.holes)} 个孔位")
        
    def _update_sector_holes_map(self):
        """从扇形分配管理器更新扇形孔位映射"""
        self.sector_holes_map.clear()
        
        # 从管理器获取每个扇形的孔位
        for sector in SectorQuadrant:
            self.sector_holes_map[sector] = self.sector_assignment_manager.get_sector_holes(sector)
            
        # 记录扇形统计
        sector_counts = self.sector_assignment_manager.get_all_sector_counts()
        for sector, count in sector_counts.items():
            self.logger.info(f"扇形 {sector.value}: {count} 个孔位")
            
    def _on_sector_assignments_updated(self, update_data: dict):
        """处理扇形分配更新事件"""
        self.logger.info(f"扇形分配已更新: {update_data.get('sector_counts', {})}")
            
    def _on_panorama_sector_clicked(self, sector: SectorQuadrant):
        """处理全景图扇形点击事件"""
        self.logger.info(f"🖱️ 扇形点击: {sector.value}")
        
        # 更新当前扇形
        self.current_sector = sector
        
        # 获取扇形孔位
        sector_holes = self.sector_holes_map.get(sector, [])
        
        # 创建过滤后的孔位集合
        filtered_collection = self._create_filtered_collection(sector_holes)
        
        # 更新中心视图显示
        if self.graphics_view and filtered_collection:
            self._update_center_view(filtered_collection)
            
        # 发射信号
        self.sector_clicked.emit(sector)
        self.sector_holes_filtered.emit(filtered_collection)
        
        # 更新扇形统计信息
        stats = self._calculate_sector_stats(sector_holes)
        self.sector_stats_updated.emit(stats)
        
    def _create_filtered_collection(self, holes: List[HoleData]) -> HoleCollection:
        """创建过滤后的孔位集合"""
        if not holes:
            return None
            
        # 创建新的孔位集合
        holes_dict = {hole.hole_id: hole for hole in holes}
        filtered_collection = HoleCollection(holes_dict)
            
        return filtered_collection
        
    def _update_center_view(self, filtered_collection: HoleCollection):
        """更新中心视图显示过滤后的孔位（带强制刷新）"""
        if hasattr(self.graphics_view, 'load_holes'):
            # 使用新的加载方法
            self.graphics_view.load_holes(filtered_collection)
            self.logger.info(f"✅ 中心视图已更新: {len(filtered_collection.holes)} 个孔位")
        elif hasattr(self.graphics_view, 'scene'):
            # 使用场景过滤方法
            self._filter_scene_items(filtered_collection)
            
        # 强制刷新视图以确保扇形更新可见
        self._force_refresh_center_view(filtered_collection)
            
    def _filter_scene_items(self, filtered_collection: HoleCollection):
        """通过场景项过滤显示孔位"""
        # 获取场景
        scene = None
        if hasattr(self.graphics_view, 'scene'):
            scene = self.graphics_view.scene
        else:
            try:
                scene = self.graphics_view.scene()
            except:
                pass
                
    def _force_refresh_center_view(self, filtered_collection=None):
        """强制刷新中心视图以确保扇形更新可见"""
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
                    
                # 额外强制刷新：触发视图重绘
                if hasattr(self.graphics_view, 'update'):
                    self.graphics_view.update()
                    
                self.logger.info("✨ 强制刷新中心视图完成")
                    
        except Exception as e:
            self.logger.warning(f"强制刷新中心视图失败: {e}")
                
        if not scene or not filtered_collection:
            return
            
        # 获取过滤后的孔位ID集合
        filtered_ids = set(filtered_collection.holes.keys())
        
        # 遍历场景中的所有项
        visible_count = 0
        hidden_count = 0
        
        for item in scene.items():
            # 检查是否为孔位项
            hole_id = item.data(0)  # Qt.UserRole = 0
            if hole_id:
                if hole_id in filtered_ids:
                    item.setVisible(True)
                    visible_count += 1
                else:
                    item.setVisible(False)
                    hidden_count += 1
                    
        self.logger.info(f"场景过滤完成: 显示 {visible_count}, 隐藏 {hidden_count}")
        
    def _calculate_sector_stats(self, holes: List[HoleData]) -> dict:
        """计算扇形统计信息"""
        stats = {
            'total': len(holes),
            'qualified': 0,
            'defective': 0,
            'pending': 0,
            'blind': 0,
            'tie_rod': 0
        }
        
        for hole in holes:
            # 根据状态统计
            if hasattr(hole, 'status'):
                status = hole.status
                if status:
                    status_value = status.value if hasattr(status, 'value') else str(status)
                    if 'qualified' in status_value:
                        stats['qualified'] += 1
                    elif 'defective' in status_value:
                        stats['defective'] += 1
                    else:
                        stats['pending'] += 1
            elif hasattr(hole, 'status'):
                # 使用status属性
                status = hole.status
                if status:
                    status_value = status.value if hasattr(status, 'value') else str(status).lower()
                    if 'qualified' in status_value:
                        stats['qualified'] += 1
                    elif 'defective' in status_value:
                        stats['defective'] += 1
                    else:
                        stats['pending'] += 1
            else:
                # 默认为待检
                stats['pending'] += 1
                    
            # 根据类型统计
            if hasattr(hole, 'is_blind') and hole.is_blind:
                stats['blind'] += 1
            if hasattr(hole, 'is_tie_rod') and hole.is_tie_rod:
                stats['tie_rod'] += 1
                
        return stats
        
    def select_sector(self, sector: SectorQuadrant):
        """选择并切换到指定扇形（带强制刷新）"""
        self.logger.info(f"🎯 选择扇形: {sector.value}")
        
        # 更新当前扇形
        self.current_sector = sector
        
        # 触发扇形点击处理
        self._on_panorama_sector_clicked(sector)
        
        # 额外强制刷新以确保扇形切换可见
        self._force_refresh_center_view()
        
    def highlight_sector(self, sector: SectorQuadrant):
        """高亮指定扇形"""
        if self.panorama_widget and hasattr(self.panorama_widget, 'highlight_sector'):
            self.panorama_widget.highlight_sector(sector)
            
    def clear_highlight(self):
        """清除扇形高亮"""
        if self.panorama_widget and hasattr(self.panorama_widget, 'clear_highlight'):
            self.panorama_widget.clear_highlight()
            
    def get_current_sector_holes(self) -> List[HoleData]:
        """获取当前扇形的孔位列表"""
        if self.current_sector:
            return self.sector_holes_map.get(self.current_sector, [])
        return []
        
    def get_sector_stats_text(self, sector: SectorQuadrant) -> str:
        """获取扇形统计信息文本"""
        holes = self.sector_holes_map.get(sector, [])
        stats = self._calculate_sector_stats(holes)
        
        text = f"扇形 {sector.value}\n"
        text += f"总孔数: {stats['total']}\n"
        text += f"合格: {stats['qualified']}\n"
        text += f"异常: {stats['defective']}\n"
        text += f"待检: {stats['pending']}\n"
        text += f"盲孔: {stats['blind']}\n"
        text += f"拉杆: {stats['tie_rod']}"
        
        return text