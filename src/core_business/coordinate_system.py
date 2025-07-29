"""
统一坐标管理系统
负责所有坐标转换、旋转、扇形分配的统一管理
解决多个模块间坐标系不一致的问题
"""

import math
import time
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from collections import Counter, defaultdict
from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtGui import QColor

from src.core_business.models.hole_data import HoleData, HoleCollection
from src.core_business.unified_id_manager import UnifiedIDManager, IDFormat
from src.core_business.hole_numbering_service import HoleNumberingService
from src.core_business.graphics.sector_types import SectorQuadrant, SectorProgress


class CoordinateSystem(Enum):
    """坐标系类型"""
    DXF_ORIGINAL = "dxf_original"      # DXF原始坐标系
    ROTATED = "rotated"                # 旋转后坐标系
    DISPLAY = "display"                # 显示坐标系


@dataclass
class CoordinateConfig:
    """坐标系配置"""
    # 旋转配置 - 已禁用所有旋转功能
    rotation_enabled: bool = False  # 禁用旋转
    rotation_angle: float = 0.0  # 度 - 已设为0
    rotation_center_mode: str = "geometric_center"  # "geometric_center" 或 "custom"
    custom_rotation_center: Optional[Tuple[float, float]] = None
    
    # 扇形分配配置
    sector_center_mode: str = "geometric_center"  # "geometric_center" 或 "custom"
    custom_sector_center: Optional[Tuple[float, float]] = None
    
    # 调试配置
    debug_enabled: bool = False
    debug_sample_count: int = 5


@dataclass 
class SectorInfo:
    """扇形区域信息"""
    sector: SectorQuadrant
    center_point: QPointF
    hole_count: int
    quadrant_definition: str  # dx>=0,dy<0 等
    color: QColor
    sample_holes: List[Dict[str, Any]]  # 样本孔位用于调试


class UnifiedCoordinateManager(QObject):
    """统一坐标管理器"""
    
    # 信号定义
    coordinate_system_changed = Signal(CoordinateSystem)
    sector_assignments_updated = Signal(dict)  # sector -> hole_count
    debug_info_updated = Signal(str)
    
    def __init__(self, config: CoordinateConfig = None):
        super().__init__()
        self.config = config or CoordinateConfig()
        
        # 数据存储
        self.hole_collection: Optional[HoleCollection] = None
        self.current_coordinate_system = CoordinateSystem.DXF_ORIGINAL
        
        # ID管理器 - REMOVED: HoleNumberingService已处理ID统一
        # self.id_manager = UnifiedIDManager()
        # self.unified_id_mappings: Dict[str, str] = {}  # 原始ID -> 统一ID
        
        # 扇形中心（唯一需要的坐标数据）
        self.sector_center: Optional[QPointF] = None
        
        # 扇形分配数据
        self.sector_assignments: Dict[str, SectorQuadrant] = {}  # hole_id -> sector
        self.sector_info: Dict[SectorQuadrant, SectorInfo] = {}
        
        # 简化的性能统计
        self.stats = {
            'total_operations': 0,
            'total_time': 0.0,
            'sector_assignments': 0
        }
    
    def initialize_from_hole_collection(self, hole_collection: HoleCollection) -> None:
        """
        从孔位集合初始化坐标管理器
        
        Args:
            hole_collection: 孔位集合
        """
        start_time = time.perf_counter()
        # 检查是否已经初始化过相同的数据
        if hasattr(self, '_last_hole_count') and self._last_hole_count == len(hole_collection.holes):
            hole_ids = sorted(hole_collection.holes.keys())
            if hasattr(self, '_last_hole_ids') and self._last_hole_ids == hole_ids[:10]:
                if self.config.debug_enabled:
                    self._debug_print("🎯 跳过重复初始化，使用已有的坐标变换结果")
                return
        
        
        if self.config.debug_enabled:
            self._debug_print("🚀 初始化统一坐标管理器")
        
        self.hole_collection = hole_collection
        self.current_coordinate_system = CoordinateSystem.DXF_ORIGINAL
        
        # 核心功能：扇形分配（基于已处理的坐标数据）
        # 注意：坐标处理和ID统一已由DXFParser和HoleNumberingService完成
        
        # 1. 计算扇形中心（基于已处理的坐标）
        self._calculate_sector_center()
        
        # 2. 执行扇形分配
        self._perform_sector_assignment()
        
        # 4. 生成统计信息
        self._generate_statistics()
        
        elapsed_time = time.perf_counter() - start_time
        self.stats['total_time'] += elapsed_time
        self.stats['total_operations'] += 1
        
        if self.config.debug_enabled:
            self._debug_print(f"✅ 坐标管理器初始化完成，耗时{elapsed_time:.3f}秒")
        
        # 发射信号
        self.coordinate_system_changed.emit(self.current_coordinate_system)
        
        # 保存状态用于重复检查
        self._last_hole_count = len(hole_collection.holes)
        self._last_hole_ids = sorted(hole_collection.holes.keys())[:10]
        
        self._emit_sector_assignments_update()
    
    def _analyze_and_unify_ids(self) -> None:
        """分析和统一ID格式"""
        if not self.hole_collection or not self.hole_collection.holes:
            return
        
        if self.config.debug_enabled:
            self._debug_print("🔍 开始ID格式分析和统一")
        
        # 分析ID格式
        analysis_result = self.id_manager.analyze_hole_collection(self.hole_collection)
        
        # 创建统一映射
        self.unified_id_mappings = self.id_manager.create_unified_mappings(
            self.hole_collection, 
            target_format=IDFormat.STANDARD_CRR
        )
        
        # 更新孔位集合中的ID
        self._apply_unified_ids_to_collection()
        
        if self.config.debug_enabled:
            self._debug_print(f"✅ ID统一完成: {len(self.unified_id_mappings)} 个映射")
    
    def _apply_unified_ids_to_collection(self) -> None:
        """将统一ID应用到孔位集合"""
        if not self.unified_id_mappings:
            return
        
        # 创建新的孔位字典
        new_holes = {}
        
        for original_id, hole_data in self.hole_collection.holes.items():
            unified_id = self.unified_id_mappings.get(original_id, original_id)
            
            # 更新孔位的ID
            hole_data.hole_id = unified_id
            new_holes[unified_id] = hole_data
        
        # 替换孔位集合
        self.hole_collection.holes = new_holes
        
        if self.config.debug_enabled:
            self._debug_print(f"🔄 孔位集合ID更新完成: {len(new_holes)} 个孔位")
    
    # REMOVED: _analyze_original_coordinates() - 功能重复
    # 边界计算已由HoleCollection.get_bounds()提供
    # 几何中心计算已由_calculate_sector_center()提供
    
    def _calculate_sector_center(self) -> None:
        """获取扇形中心（直接读取DXFParser已计算的几何中心）"""
        if not self.hole_collection or not self.hole_collection.holes:
            if self.config.debug_enabled:
                self._debug_print("❌ 无法获取扇形中心：无孔位数据")
            return
        
        # 优先使用DXFParser已保存的几何中心，避免重复计算
        geometric_center = self.hole_collection.metadata.get('geometric_center')
        
        if geometric_center:
            center_x, center_y = geometric_center
            self.sector_center = QPointF(center_x, center_y)
            if self.config.debug_enabled:
                self._debug_print(f"🎯 使用DXFParser已计算的几何中心: ({center_x:.2f}, {center_y:.2f})")
        else:
            # 降级方案：使用边界计算（通常不会执行）
            min_x, min_y, max_x, max_y = self.hole_collection.get_bounds()
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            self.sector_center = QPointF(center_x, center_y)
            if self.config.debug_enabled:
                self._debug_print(f"⚠️ 降级使用边界计算扇形中心: ({center_x:.2f}, {center_y:.2f})")
                self._debug_print(f"📊 边界数据: X[{min_x:.2f}, {max_x:.2f}], Y[{min_y:.2f}, {max_y:.2f}]")
    
    # 已注释掉旋转功能 - 不再执行任何坐标旋转
    # def _apply_coordinate_rotation(self) -> None:
    #     """应用坐标旋转 - 已禁用"""
    #     if not self.hole_collection or not self.rotation_center:
    #         return
    #     
    #     holes = list(self.hole_collection.holes.values())
    #     rotation_angle = self.config.rotation_angle
    #     
    #     if self.config.debug_enabled:
    #         self._debug_print(f"🔄 执行坐标旋转: {rotation_angle}度，中心({self.rotation_center.x():.2f}, {self.rotation_center.y():.2f})")
    #         
    #         # 记录旋转前样本坐标
    #         sample_holes = holes[:self.config.debug_sample_count]
    #         self._debug_print("📐 旋转前样本坐标:")
    #         for i, hole in enumerate(sample_holes):
    #             self._debug_print(f"   {hole.hole_id}: ({hole.center_x:.2f}, {hole.center_y:.2f})")
    #     
    #     # 计算旋转参数
    #     rotation_rad = math.radians(rotation_angle)
    #     cos_angle = math.cos(rotation_rad)
    #     sin_angle = math.sin(rotation_rad)
    #     center_x = self.rotation_center.x()
    #     center_y = self.rotation_center.y()
    #     
    #     # 执行旋转变换
    #     for hole in holes:
    #         # 记录原始坐标
    #         original_x, original_y = hole.center_x, hole.center_y
    #         
    #         # 平移到原点
    #         x = original_x - center_x
    #         y = original_y - center_y
    #         
    #         # 应用旋转变换
    #         new_x = x * cos_angle - y * sin_angle
    #         new_y = x * sin_angle + y * cos_angle
    #         
    #         # 平移回原位置
    #         hole.center_x = new_x + center_x
    #         hole.center_y = new_y + center_y
    #         
    #         # 记录变换信息
    #         self.coordinate_transformations[hole.hole_id] = {
    #             'original_coords': (original_x, original_y),
    #             'rotated_coords': (hole.center_x, hole.center_y),
    #             'transformation': 'rotation',
    #             'rotation_angle': rotation_angle,
    #             'rotation_center': (center_x, center_y)
    #         }
    #     
    #     self.stats['coordinate_transforms'] += len(holes)
    #     
    #     if self.config.debug_enabled:
    #         # 记录旋转后样本坐标
    #         sample_holes = holes[:self.config.debug_sample_count]
    #         self._debug_print("📐 旋转后样本坐标:")
    #         for i, hole in enumerate(sample_holes):
    #             self._debug_print(f"   {hole.hole_id}: ({hole.center_x:.2f}, {hole.center_y:.2f})")
        
    
    def _perform_sector_assignment(self) -> None:
        """执行扇形分配"""
        if self.config.debug_enabled:
            self._debug_print(f"🔍 扇形分配前检查:")
            self._debug_print(f"   hole_collection存在: {self.hole_collection is not None}")
            self._debug_print(f"   sector_center存在: {self.sector_center is not None}")
            if self.hole_collection:
                self._debug_print(f"   孔位数量: {len(self.hole_collection.holes)}")
            if self.sector_center:
                self._debug_print(f"   扇形中心: ({self.sector_center.x():.2f}, {self.sector_center.y():.2f})")
                
        if not self.hole_collection or not self.sector_center:
            if self.config.debug_enabled:
                self._debug_print("❌ 扇形分配跳过：缺少必要条件")
            return
        
        if self.config.debug_enabled:
            self._debug_print(f"🎯 执行扇形分配: 中心({self.sector_center.x():.2f}, {self.sector_center.y():.2f})")
            self._debug_print("🧭 扇形定义（Qt坐标系）:")
            self._debug_print("   SECTOR_1 (右上): dx>=0, dy<=0  [Qt显示的右上]")
            self._debug_print("   SECTOR_2 (左上): dx<0,  dy<=0  [Qt显示的左上]")
            self._debug_print("   SECTOR_3 (左下): dx<0,  dy>0   [Qt显示的左下]")
            self._debug_print("   SECTOR_4 (右下): dx>=0, dy>0   [Qt显示的右下]")
        
        self.sector_assignments.clear()
        center_x = self.sector_center.x()
        center_y = self.sector_center.y()
        
        # 用于调试的样本收集
        sector_samples = {sector: [] for sector in SectorQuadrant}
        
        # 执行分配
        for hole_id, hole in self.hole_collection.holes.items():
            # 计算相对坐标
            dx = hole.center_x - center_x
            dy = hole.center_y - center_y
            
            # 确定扇形（考虑Qt坐标系Y轴向下）
            # 在数据中 y>0 表示上方，但在Qt显示中会在下方
            if dx >= 0 and dy <= 0:
                sector = SectorQuadrant.SECTOR_1  # Qt显示的右上（y<0在屏幕上方）
            elif dx < 0 and dy <= 0:
                sector = SectorQuadrant.SECTOR_2  # Qt显示的左上（y<0在屏幕上方）
            elif dx < 0 and dy > 0:
                sector = SectorQuadrant.SECTOR_3  # Qt显示的左下（y>0在屏幕下方）
            else:  # dx >= 0 and dy > 0
                sector = SectorQuadrant.SECTOR_4  # Qt显示的右下（y>0在屏幕下方）
            
            self.sector_assignments[hole_id] = sector
            
            # 收集调试样本
            if self.config.debug_enabled and len(sector_samples[sector]) < self.config.debug_sample_count:
                sector_samples[sector].append({
                    'hole_id': hole_id,
                    'abs_coords': (hole.center_x, hole.center_y),
                    'rel_coords': (dx, dy),
                    'conditions': f"dx={dx:.1f}{'>=0' if dx >= 0 else '<0'}, dy={dy:.1f}{'>=0' if dy >= 0 else '<0'}"
                })
        
        self.stats['sector_assignments'] += len(self.sector_assignments)
        
        # 生成扇形信息
        self._generate_sector_info(sector_samples)
        
        if self.config.debug_enabled:
            self._debug_sector_assignments(sector_samples)
    
    def _generate_sector_info(self, sector_samples: Dict) -> None:
        """生成扇形区域信息"""
        sector_counts = Counter(self.sector_assignments.values())
        
        # 扇形颜色配置
        sector_colors = {
            SectorQuadrant.SECTOR_1: QColor(76, 175, 80),   # 绿色 - 右上
            SectorQuadrant.SECTOR_2: QColor(33, 150, 243),  # 蓝色 - 左上
            SectorQuadrant.SECTOR_3: QColor(255, 152, 0),   # 橙色 - 左下
            SectorQuadrant.SECTOR_4: QColor(156, 39, 176),  # 紫色 - 右下
        }
        
        # 象限定义（Qt坐标系）
        quadrant_definitions = {
            SectorQuadrant.SECTOR_1: "dx>=0, dy<=0 (Qt右上)",
            SectorQuadrant.SECTOR_2: "dx<0,  dy<=0 (Qt左上)",
            SectorQuadrant.SECTOR_3: "dx<0,  dy>0  (Qt左下)",
            SectorQuadrant.SECTOR_4: "dx>=0, dy>0  (Qt右下)"
        }
        
        for sector in SectorQuadrant:
            self.sector_info[sector] = SectorInfo(
                sector=sector,
                center_point=self.sector_center,
                hole_count=sector_counts.get(sector, 0),
                quadrant_definition=quadrant_definitions[sector],
                color=sector_colors[sector],
                sample_holes=sector_samples.get(sector, [])
            )
    
    def _debug_sector_assignments(self, sector_samples: Dict) -> None:
        """调试扇形分配结果"""
        self._debug_print("🔍 各扇形分配样本:")
        for sector, samples in sector_samples.items():
            if samples:
                sector_info = self.sector_info[sector]
                self._debug_print(f"   {sector.value} ({sector_info.quadrant_definition}):")
                for sample in samples:
                    self._debug_print(f"     {sample['hole_id']}: "
                                    f"绝对({sample['abs_coords'][0]:.1f},{sample['abs_coords'][1]:.1f}) → "
                                    f"相对({sample['rel_coords'][0]:.1f},{sample['rel_coords'][1]:.1f}) "
                                    f"[{sample['conditions']}]")
        
        # 统计结果
        sector_counts = Counter(self.sector_assignments.values())
        self._debug_print(f"📊 扇形分配统计: {dict((s.value, c) for s, c in sector_counts.items())}")
    
    def _generate_statistics(self) -> None:
        """生成统计信息"""
        if not self.hole_collection:
            return
        
        total_holes = len(self.hole_collection.holes)
        sector_counts = Counter(self.sector_assignments.values())
        
        stats_info = [
            f"总孔位数: {total_holes}",
            f"扇形中心: ({self.sector_center.x():.2f}, {self.sector_center.y():.2f})" if self.sector_center else "无"
        ]
        
        for sector in SectorQuadrant:
            count = sector_counts.get(sector, 0)
            percentage = (count / total_holes * 100) if total_holes > 0 else 0
            stats_info.append(f"{sector.value}: {count}个 ({percentage:.1f}%)")
        
        if self.config.debug_enabled:
            self._debug_print("📈 统计信息:")
            for info in stats_info:
                self._debug_print(f"   {info}")
    
    def _emit_sector_assignments_update(self) -> None:
        """发射扇形分配更新信号"""
        sector_counts = Counter(self.sector_assignments.values())
        update_data = {
            'sector_counts': dict((s.value, c) for s, c in sector_counts.items()),
            'sector_info': {s.value: {
                'hole_count': info.hole_count,
                'quadrant_definition': info.quadrant_definition,
                'center_point': (info.center_point.x(), info.center_point.y()),
                'color': info.color.name()
            } for s, info in self.sector_info.items()},
            'coordinate_system': self.current_coordinate_system.value,
            'total_holes': len(self.hole_collection.holes) if self.hole_collection else 0
        }
        
        self.sector_assignments_updated.emit(update_data)
    
    def _debug_print(self, message: str) -> None:
        """调试输出"""
        print(f"[统一坐标管理器] {message}")
        self.debug_info_updated.emit(message)
    
    # 公共接口方法
    
    def get_hole_sector(self, hole_id: str) -> Optional[SectorQuadrant]:
        """获取孔位所属扇形"""
        return self.sector_assignments.get(hole_id)
    
    def get_sector_holes(self, sector: SectorQuadrant) -> List[HoleData]:
        """获取指定扇形的所有孔位"""
        if not self.hole_collection:
            return []
        
        return [
            self.hole_collection.holes[hole_id]
            for hole_id, assigned_sector in self.sector_assignments.items()
            if assigned_sector == sector and hole_id in self.hole_collection.holes
        ]
    
    def get_sector_count(self, sector: SectorQuadrant) -> int:
        """获取指定扇形的孔位数量"""
        return sum(1 for s in self.sector_assignments.values() if s == sector)
    
    def get_all_sector_counts(self) -> Dict[SectorQuadrant, int]:
        """获取所有扇形的孔位数量"""
        return dict(Counter(self.sector_assignments.values()))
    
    # REMOVED: get_coordinate_transformation - 坐标变换由DXFParser处理
    
    def get_sector_info(self, sector: SectorQuadrant) -> Optional[SectorInfo]:
        """获取扇形信息"""
        return self.sector_info.get(sector)
    
    def get_all_sector_info(self) -> Dict[SectorQuadrant, SectorInfo]:
        """获取所有扇形信息"""
        return self.sector_info.copy()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self.stats.copy()
    
    def enable_debug(self, enabled: bool = True) -> None:
        """启用/禁用调试模式"""
        self.config.debug_enabled = enabled
    
    def reconfigure(self, new_config: CoordinateConfig) -> None:
        """重新配置坐标管理器"""
        self.config = new_config
        
        # 如果有数据，重新初始化
        if self.hole_collection:
            self.initialize_from_hole_collection(self.hole_collection)
    
    def clear(self) -> None:
        """清空所有数据"""
        self.hole_collection = None
        self.sector_assignments.clear()
        self.sector_info.clear()
        self.sector_center = None
        
        # 统计重置
        self.stats['sector_assignments'] = 0