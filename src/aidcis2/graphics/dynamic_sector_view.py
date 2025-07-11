"""
动态扇形区域图形管理器
根据检测进度动态显示对应扇形区域的DXF图形部分
"""

import math
from typing import Dict, List, Optional, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush

from aidcis2.graphics.graphics_view import OptimizedGraphicsView
from aidcis2.graphics.sector_manager import SectorManager, SectorQuadrant, SectorProgress
from aidcis2.models.hole_data import HoleData, HoleCollection


class SectorGraphicsManager:
    """扇形图形管理器 - 负责将DXF图形划分为4个扇形区域"""
    
    def __init__(self, hole_collection: HoleCollection):
        self.hole_collection = hole_collection
        self.center_point = self._calculate_center()
        self.sector_collections = self._create_sector_collections()
    
    def _calculate_center(self) -> QPointF:
        """计算DXF图形的中心点"""
        if not self.hole_collection:
            return QPointF(0, 0)
        
        bounds = self.hole_collection.get_bounds()
        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2
        return QPointF(center_x, center_y)
    
    def _create_sector_collections(self) -> Dict[SectorQuadrant, HoleCollection]:
        """为每个扇形区域创建独立的孔位集合"""
        sector_collections = {}
        
        for sector in SectorQuadrant:
            sector_holes = {}
            
            for hole_id, hole in self.hole_collection.holes.items():
                if self._is_hole_in_sector(hole, sector):
                    sector_holes[hole_id] = hole
            
            # 创建扇形专用的孔位集合
            sector_collection = HoleCollection(
                holes=sector_holes,
                metadata={
                    'sector': sector,
                    'source_file': self.hole_collection.metadata.get('source_file', ''),
                    'total_holes': len(sector_holes),
                    'sector_bounds': None  # 先设置为None，后续计算
                }
            )
            
            sector_collections[sector] = sector_collection
        
        # 现在计算每个扇形的边界并更新metadata
        for sector, collection in sector_collections.items():
            if collection and len(collection) > 0:
                bounds = collection.get_bounds()
                collection.metadata['sector_bounds'] = bounds
        
        return sector_collections
    
    def _is_hole_in_sector(self, hole: HoleData, sector: SectorQuadrant) -> bool:
        """判断孔位是否属于指定扇形区域"""
        dx = hole.center_x - self.center_point.x()
        dy = hole.center_y - self.center_point.y()
        
        # 计算角度
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 转换为0-360度范围
        if angle_deg < 0:
            angle_deg += 360
        
        # 判断属于哪个扇形
        if sector == SectorQuadrant.SECTOR_1:
            return 0 <= angle_deg < 90
        elif sector == SectorQuadrant.SECTOR_2:
            return 90 <= angle_deg < 180
        elif sector == SectorQuadrant.SECTOR_3:
            return 180 <= angle_deg < 270
        elif sector == SectorQuadrant.SECTOR_4:
            return 270 <= angle_deg < 360
        
        return False
    
    def _get_sector_bounds(self, sector: SectorQuadrant) -> Tuple[float, float, float, float]:
        """获取扇形区域的边界范围"""
        # 从已创建的扇形集合中获取边界，避免递归调用
        if sector in self.sector_collections:
            sector_collection = self.sector_collections[sector]
            if sector_collection and len(sector_collection) > 0:
                return sector_collection.get_bounds()
        
        # 如果扇形集合还未创建，直接计算该扇形的孔位边界
        sector_holes = []
        for hole_id, hole in self.hole_collection.holes.items():
            if self._is_hole_in_sector(hole, sector):
                sector_holes.append(hole)
        
        if not sector_holes:
            return (0, 0, 0, 0)
        
        min_x = min(hole.center_x for hole in sector_holes)
        max_x = max(hole.center_x for hole in sector_holes)
        min_y = min(hole.center_y for hole in sector_holes)
        max_y = max(hole.center_y for hole in sector_holes)
        
        return (min_x, min_y, max_x, max_y)
    
    def get_sector_collection(self, sector: SectorQuadrant) -> Optional[HoleCollection]:
        """获取指定扇形区域的孔位集合"""
        return self.sector_collections.get(sector)
    
    def get_all_sector_collections(self) -> Dict[SectorQuadrant, HoleCollection]:
        """获取所有扇形区域的孔位集合"""
        return self.sector_collections.copy()


class DynamicSectorDisplayWidget(QWidget):
    """动态扇形区域显示组件"""
    
    sector_changed = Signal(SectorQuadrant)  # 扇形切换信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sector_graphics_manager: Optional[SectorGraphicsManager] = None
        self.current_sector = SectorQuadrant.SECTOR_1
        self.sector_views = {}  # 缓存各扇形的图形视图
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 移除标题栏，直接显示图形区域
        # title_frame = QFrame()
        # title_frame.setFrameStyle(QFrame.StyledPanel)
        # title_frame.setMaximumHeight(40)
        # title_layout = QHBoxLayout(title_frame)
        # 
        # self.title_label = QLabel("动态扇形区域显示")
        # self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        # self.title_label.setAlignment(Qt.AlignCenter)
        # title_layout.addWidget(self.title_label)
        # 
        # layout.addWidget(title_frame)
        
        # 图形显示区域
        self.graphics_view = OptimizedGraphicsView()
        self.graphics_view.setFrameStyle(QFrame.StyledPanel)
        self.graphics_view.setMinimumSize(400, 400)
        
        layout.addWidget(self.graphics_view)
        
        # 状态信息 - 移除状态标签以避免不必要的显示
        # self.status_label = QLabel("等待数据加载...")
        # self.status_label.setAlignment(Qt.AlignCenter)
        # self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        # layout.addWidget(self.status_label)
    
    def set_hole_collection(self, hole_collection: HoleCollection):
        """设置孔位集合并创建扇形图形管理器"""
        self.sector_graphics_manager = SectorGraphicsManager(hole_collection)
        
        # 预创建所有扇形视图
        self._create_sector_views()
        
        # 显示初始扇形
        self.switch_to_sector(self.current_sector)
    
    def _create_sector_views(self):
        """预创建所有扇形区域的图形视图"""
        if not self.sector_graphics_manager:
            return
        
        for sector in SectorQuadrant:
            sector_collection = self.sector_graphics_manager.get_sector_collection(sector)
            if sector_collection and len(sector_collection) > 0:
                # 为该扇形创建独立的图形视图（不显示，仅预备）
                view = OptimizedGraphicsView()
                view.load_holes(sector_collection)
                view.ensure_vertical_orientation()
                view.switch_to_macro_view()
                
                self.sector_views[sector] = {
                    'view': view,
                    'collection': sector_collection,
                    'hole_count': len(sector_collection)
                }
    
    def switch_to_sector(self, sector: SectorQuadrant):
        """切换到指定扇形区域显示"""
        if not self.sector_graphics_manager:
            return
        
        self.current_sector = sector
        
        # 获取扇形数据
        sector_info = self.sector_views.get(sector)
        if not sector_info:
            # self.status_label.setText(f"扇形 {sector.value} 暂无数据")
            return
        
        # 加载扇形区域的孔位到主显示视图
        sector_collection = sector_info['collection']
        self.graphics_view.load_holes(sector_collection)
        self.graphics_view.ensure_vertical_orientation()
        self.graphics_view.switch_to_macro_view()
        
        # 更新标题和状态（移除，因为已删除标题栏）
        sector_names = {
            SectorQuadrant.SECTOR_1: "区域1 (右上)",
            SectorQuadrant.SECTOR_2: "区域2 (左上)", 
            SectorQuadrant.SECTOR_3: "区域3 (左下)",
            SectorQuadrant.SECTOR_4: "区域4 (右下)"
        }
        
        # self.title_label.setText(f"当前显示: {sector_names[sector]}")
        # self.status_label.setText(f"显示 {sector_info['hole_count']} 个孔位")
        
        # 发射切换信号
        self.sector_changed.emit(sector)
    
    def update_sector_progress(self, sector: SectorQuadrant, progress: SectorProgress):
        """更新扇形进度（可以根据进度自动切换显示）"""
        # 如果当前显示的扇形有进度更新，自动切换到该扇形
        if progress.completed_holes > 0:
            self.switch_to_sector(sector)
    
    def get_current_sector(self) -> SectorQuadrant:
        """获取当前显示的扇形区域"""
        return self.current_sector
    
    def get_sector_info(self, sector: SectorQuadrant) -> Optional[Dict]:
        """获取指定扇形的信息"""
        return self.sector_views.get(sector)


class CompletePanoramaWidget(QWidget):
    """完整全景图显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 移除标题，直接显示全景图形视图
        # title_label = QLabel("完整孔位全景图")
        # title_label.setAlignment(Qt.AlignCenter)
        # title_label.setFont(QFont("Arial", 12, QFont.Bold))
        # title_label.setStyleSheet("padding: 5px; background-color: #e3f2fd; border-radius: 3px;")
        # layout.addWidget(title_label)
        
        # 全景图形视图 - 增大尺寸以显示完整内容
        self.panorama_view = OptimizedGraphicsView()
        self.panorama_view.setFrameStyle(QFrame.StyledPanel)
        self.panorama_view.setMaximumSize(250, 280)  # 增大尺寸以显示完整的DXF图形
        self.panorama_view.setMinimumSize(220, 250)  # 增大最小尺寸
        
        layout.addWidget(self.panorama_view)
        
        # 信息标签 - 保留但简化
        self.info_label = QLabel("等待数据加载...")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("padding: 2px; font-size: 9px; color: #666;")
        layout.addWidget(self.info_label)
    
    def load_complete_view(self, hole_collection: HoleCollection):
        """加载完整的全景图"""
        if hole_collection and len(hole_collection) > 0:
            self.panorama_view.load_holes(hole_collection)
            self.panorama_view.ensure_vertical_orientation()
            self.panorama_view.switch_to_macro_view()
            
            # 确保显示全景 - 调用适应窗口方法
            self.panorama_view.fit_in_view()
            
            # 更新信息 - 确保显示正确的孔位数量
            hole_count = len(hole_collection)
            self.info_label.setText(f"全景: {hole_count} 个孔位")
        else:
            self.info_label.setText("暂无数据")