"""
增强型扇形管理器
集成自适应角度计算功能，提供智能的扇形区域划分
"""

import math
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtGui import QColor

from src.core_business.models.hole_data import HoleData, HoleCollection
from src.core_business.graphics.sector_manager import SectorQuadrant, SectorProgress
from src.core_business.geometry.adaptive_angle_calculator import AdaptiveAngleCalculator, AdaptiveAngleConfig, GeometryBounds
from src.core.error_handler import get_error_handler, ErrorCategory


@dataclass
class EnhancedSectorConfig:
    """增强型扇形配置"""
    use_adaptive_angles: bool = True
    fallback_to_default: bool = True
    auto_adjust_center: bool = True
    validate_angle_consistency: bool = True
    
    # 自适应角度配置
    adaptive_config: AdaptiveAngleConfig = None
    
    def __post_init__(self):
        if self.adaptive_config is None:
            self.adaptive_config = AdaptiveAngleConfig()


class EnhancedSectorManager(QObject):
    """增强型扇形管理器"""
    
    # 信号定义
    sector_progress_updated = Signal(SectorQuadrant, SectorProgress)
    overall_progress_updated = Signal(dict)
    geometry_updated = Signal(GeometryBounds)
    angle_configuration_updated = Signal(dict)
    
    def __init__(self, config: EnhancedSectorConfig = None):
        super().__init__()
        self.config = config or EnhancedSectorConfig()
        self.logger = logging.getLogger(__name__)
        self.error_handler = get_error_handler()
        
        # 初始化自适应角度计算器
        self.angle_calculator = AdaptiveAngleCalculator(self.config.adaptive_config)
        
        # 数据存储
        self.hole_collection: Optional[HoleCollection] = None
        self.geometry_bounds: Optional[GeometryBounds] = None
        self.sector_angles: Dict[SectorQuadrant, Dict[str, float]] = {}
        self.sector_assignments: Dict[str, SectorQuadrant] = {}
        self.sector_progress: Dict[SectorQuadrant, SectorProgress] = {}
        
        # 中心点
        self.center_point: Optional[QPointF] = None
        
        # 向后兼容性
        self._legacy_mode: bool = False
        
    def set_hole_collection(self, hole_collection: HoleCollection) -> None:
        """
        设置孔位集合并进行自适应角度计算
        
        Args:
            hole_collection: 孔位集合
        """
        try:
            self.hole_collection = hole_collection
            
            if not hole_collection.holes:
                self.logger.warning("孔位集合为空")
                return
            
            # 分析几何布局
            self._analyze_geometry()
            
            # 计算自适应角度
            if self.config.use_adaptive_angles:
                self._calculate_adaptive_angles()
            else:
                self._use_default_angles()
            
            # 分配孔位到扇形
            self._assign_holes_to_sectors()
            
            # 初始化进度
            self._initialize_sector_progress()
            
            self.logger.info(f"扇形管理器初始化完成: {len(hole_collection.holes)} 个孔位, "
                           f"中心点({self.center_point.x():.2f}, {self.center_point.y():.2f})")
            
        except Exception as e:
            self.error_handler.handle_error(e, component="EnhancedSectorManager", 
                                          category=ErrorCategory.BUSINESS,
                                          context={"hole_count": len(hole_collection.holes) if hole_collection.holes else 0})
            
            # 回退到兼容模式
            if self.config.fallback_to_default:
                self._enable_legacy_mode()
            else:
                raise
    
    def _analyze_geometry(self) -> None:
        """分析几何布局"""
        if not self.hole_collection:
            return
        
        # 使用自适应角度计算器分析几何
        self.geometry_bounds = self.angle_calculator.analyze_hole_geometry(self.hole_collection)
        
        # 设置中心点
        if self.config.auto_adjust_center:
            self.center_point = QPointF(self.geometry_bounds.center_x, self.geometry_bounds.center_y)
        else:
            # 使用几何中心
            self.center_point = QPointF(
                (self.geometry_bounds.min_x + self.geometry_bounds.max_x) / 2,
                (self.geometry_bounds.min_y + self.geometry_bounds.max_y) / 2
            )
        
        # 发送几何更新信号
        self.geometry_updated.emit(self.geometry_bounds)
        
        self.logger.info(f"几何分析完成: 边界尺寸({self.geometry_bounds.width:.2f}x{self.geometry_bounds.height:.2f}), "
                        f"中心点({self.center_point.x():.2f}, {self.center_point.y():.2f})")
    
    def _calculate_adaptive_angles(self) -> None:
        """计算自适应角度"""
        if not self.hole_collection:
            return
        
        try:
            # 使用自适应角度计算器
            self.sector_angles = self.angle_calculator.calculate_adaptive_sector_angles(self.hole_collection)
            
            # 验证角度配置
            if self.config.validate_angle_consistency:
                self._validate_angle_configuration()
            
            # 发送角度配置更新信号
            self.angle_configuration_updated.emit(self.sector_angles)
            
            self.logger.info("自适应角度计算完成")
            
        except Exception as e:
            self.logger.error(f"自适应角度计算失败: {e}")
            
            if self.config.fallback_to_default:
                self._use_default_angles()
            else:
                raise
    
    def _use_default_angles(self) -> None:
        """使用默认角度配置"""
        self.sector_angles = {
            SectorQuadrant.SECTOR_1: {
                'start_angle': 315.0,
                'end_angle': 45.0,
                'span_angle': 90.0
            },
            SectorQuadrant.SECTOR_2: {
                'start_angle': 45.0,
                'end_angle': 135.0,
                'span_angle': 90.0
            },
            SectorQuadrant.SECTOR_3: {
                'start_angle': 135.0,
                'end_angle': 225.0,
                'span_angle': 90.0
            },
            SectorQuadrant.SECTOR_4: {
                'start_angle': 225.0,
                'end_angle': 315.0,
                'span_angle': 90.0
            }
        }
        
        self.logger.info("使用默认角度配置")
    
    def _assign_holes_to_sectors(self) -> None:
        """分配孔位到扇形区域"""
        if not self.hole_collection or not self.geometry_bounds:
            return
        
        self.sector_assignments.clear()
        
        for hole_id, hole in self.hole_collection.holes.items():
            sector = self.angle_calculator.get_sector_for_hole(hole, self.geometry_bounds, self.sector_angles)
            self.sector_assignments[hole_id] = sector
        
        # 统计分配结果
        sector_counts = {}
        for sector in SectorQuadrant:
            count = sum(1 for s in self.sector_assignments.values() if s == sector)
            sector_counts[sector] = count
        
        self.logger.info(f"孔位分配完成: {dict((s.value, c) for s, c in sector_counts.items())}")
    
    def _initialize_sector_progress(self) -> None:
        """初始化扇形进度"""
        for sector in SectorQuadrant:
            sector_holes = self.get_sector_holes(sector)
            
            progress = SectorProgress(
                sector=sector,
                total_holes=len(sector_holes),
                completed_holes=0,
                qualified_holes=0,
                defective_holes=0,
                progress_percentage=0.0,
                status_color=QColor(128, 128, 128)  # Default gray color
            )
            
            self.sector_progress[sector] = progress
            
            # Update progress based on actual hole statuses
            self._recalculate_sector_progress_data(sector)
    
    def _recalculate_sector_progress_data(self, sector: SectorQuadrant) -> None:
        """重新计算扇形进度数据"""
        if sector not in self.sector_progress:
            return
        
        progress = self.sector_progress[sector]
        sector_holes = self.get_sector_holes(sector)
        
        # Reset counters
        progress.completed_holes = 0
        progress.qualified_holes = 0
        progress.defective_holes = 0
        
        # Count based on actual hole statuses
        for hole in sector_holes:
            if hasattr(hole, 'status') and hole.status:
                status_value = hole.status.value if hasattr(hole.status, 'value') else str(hole.status)
                
                if 'completed' in status_value.lower():
                    progress.completed_holes += 1
                
                if 'qualified' in status_value.lower() or 'pass' in status_value.lower():
                    progress.qualified_holes += 1
                
                if 'defective' in status_value.lower() or 'fail' in status_value.lower():
                    progress.defective_holes += 1
        
        # Update progress_percentage
        progress.progress_percentage = (progress.completed_holes / progress.total_holes * 100) if progress.total_holes > 0 else 0.0
        
        # Update status_color based on progress
        if progress.progress_percentage >= 100:
            progress.status_color = QColor(0, 255, 0)  # Green for complete
        elif progress.progress_percentage >= 75:
            progress.status_color = QColor(255, 255, 0)  # Yellow for high progress
        elif progress.progress_percentage >= 25:
            progress.status_color = QColor(255, 165, 0)  # Orange for medium progress
        else:
            progress.status_color = QColor(128, 128, 128)  # Gray for low progress
    
    def _recalculate_sector_progress(self, sector: SectorQuadrant) -> None:
        """重新计算指定扇形区域的进度 - 对外接口"""
        self._recalculate_sector_progress_data(sector)
        
        # 发送进度更新信号
        if sector in self.sector_progress:
            self.sector_progress_updated.emit(sector, self.sector_progress[sector])
    
    def _validate_angle_configuration(self) -> None:
        """验证角度配置"""
        if not self.sector_angles:
            raise ValueError("角度配置为空")
        
        # 检查是否包含所有扇形
        expected_sectors = set(SectorQuadrant)
        actual_sectors = set(self.sector_angles.keys())
        
        if expected_sectors != actual_sectors:
            missing = expected_sectors - actual_sectors
            extra = actual_sectors - expected_sectors
            raise ValueError(f"角度配置不完整: 缺少 {missing}, 多余 {extra}")
        
        # 检查角度范围
        total_span = 0
        for sector, angles in self.sector_angles.items():
            span = angles['span_angle']
            if span <= 0 or span > 360:
                raise ValueError(f"扇形 {sector.value} 角度跨度无效: {span}")
            total_span += span
        
        # 检查总覆盖率
        if abs(total_span - 360) > 10:  # 允许10度误差
            self.logger.warning(f"角度总覆盖率异常: {total_span}°")
    
    def _enable_legacy_mode(self) -> None:
        """启用兼容模式"""
        self._legacy_mode = True
        self._use_default_angles()
        
        # 使用简单的象限分配
        if self.hole_collection:
            self._assign_holes_to_sectors_legacy()
        
        self.logger.info("已启用兼容模式")
    
    def _assign_holes_to_sectors_legacy(self) -> None:
        """兼容模式的孔位分配"""
        if not self.hole_collection or not self.center_point:
            return
        
        self.sector_assignments.clear()
        
        for hole_id, hole in self.hole_collection.holes.items():
            # 使用简单的象限判断
            dx = hole.center_x - self.center_point.x()
            dy = hole.center_y - self.center_point.y()
            
            if dx >= 0 and dy < 0:
                sector = SectorQuadrant.SECTOR_1  # 右上
            elif dx < 0 and dy < 0:
                sector = SectorQuadrant.SECTOR_2  # 左上
            elif dx < 0 and dy >= 0:
                sector = SectorQuadrant.SECTOR_3  # 左下
            else:  # dx >= 0 and dy >= 0
                sector = SectorQuadrant.SECTOR_4  # 右下
            
            self.sector_assignments[hole_id] = sector
    
    def get_sector_for_hole(self, hole_id: str) -> Optional[SectorQuadrant]:
        """
        获取孔位所属的扇形区域
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            Optional[SectorQuadrant]: 所属扇形区域
        """
        return self.sector_assignments.get(hole_id)
    
    def get_sector_holes(self, sector: SectorQuadrant) -> List[HoleData]:
        """
        获取指定扇形的所有孔位
        
        Args:
            sector: 扇形区域
            
        Returns:
            List[HoleData]: 孔位列表
        """
        if not self.hole_collection:
            return []
        
        sector_holes = []
        for hole_id, assigned_sector in self.sector_assignments.items():
            if assigned_sector == sector:
                hole = self.hole_collection.holes.get(hole_id)
                if hole:
                    sector_holes.append(hole)
        
        return sector_holes
    
    def get_sector_angle_config(self, sector: SectorQuadrant) -> Optional[Dict[str, float]]:
        """
        获取指定扇形的角度配置
        
        Args:
            sector: 扇形区域
            
        Returns:
            Optional[Dict[str, float]]: 角度配置
        """
        return self.sector_angles.get(sector)
    
    def get_sector_progress(self, sector: SectorQuadrant) -> Optional[SectorProgress]:
        """
        获取指定扇形的进度
        
        Args:
            sector: 扇形区域
            
        Returns:
            Optional[SectorProgress]: 进度信息
        """
        return self.sector_progress.get(sector)
    
    def get_overall_progress(self) -> Optional[Dict[str, Any]]:
        """
        获取整体进度信息
        
        Returns:
            Optional[Dict[str, Any]]: 整体进度统计
        """
        if not self.sector_progress:
            return None
            
        total_holes = sum(p.total_holes for p in self.sector_progress.values())
        completed_holes = sum(p.completed_holes for p in self.sector_progress.values())
        qualified_holes = sum(p.qualified_holes for p in self.sector_progress.values())
        defective_holes = sum(p.defective_holes for p in self.sector_progress.values())
        
        return {
            'total_holes': total_holes,
            'completed_holes': completed_holes,
            'qualified_holes': qualified_holes,
            'defective_holes': defective_holes,
            'completion_rate': (completed_holes / total_holes * 100) if total_holes > 0 else 0,
            'qualification_rate': (qualified_holes / completed_holes * 100) if completed_holes > 0 else 0
        }
    
    def update_hole_status(self, hole_id: str, status: Any) -> None:
        """
        更新孔位状态并更新进度
        
        Args:
            hole_id: 孔位ID
            status: 新状态
        """
        if not self.hole_collection or hole_id not in self.hole_collection.holes:
            return
        
        # 更新孔位状态
        hole = self.hole_collection.holes[hole_id]
        old_status = hole.status
        hole.status = status
        
        # 更新扇形进度
        sector = self.sector_assignments.get(hole_id)
        if sector and sector in self.sector_progress:
            self._update_sector_progress(sector, old_status, status)
            
            # 发送进度更新信号
            self.sector_progress_updated.emit(sector, self.sector_progress[sector])
            
            # 更新整体进度
            self._update_overall_progress()
    
    def _update_sector_progress(self, sector: SectorQuadrant, old_status: Any, new_status: Any) -> None:
        """更新扇形进度"""
        progress = self.sector_progress[sector]
        
        # 这里需要根据实际的状态定义来更新计数
        # 由于状态类型可能不同，这里提供一个通用的框架
        
        # 示例逻辑（需要根据实际状态定义调整）
        if hasattr(new_status, 'value'):
            status_value = new_status.value
        else:
            status_value = str(new_status)
        
        # 更新计数（具体逻辑需要根据状态定义调整）
        if 'completed' in status_value.lower():
            progress.completed_holes += 1
        
        if 'qualified' in status_value.lower() or 'pass' in status_value.lower():
            progress.qualified_holes += 1
        
        if 'defective' in status_value.lower() or 'fail' in status_value.lower():
            progress.defective_holes += 1
        
        # 更新progress_percentage
        progress.progress_percentage = (progress.completed_holes / progress.total_holes * 100) if progress.total_holes > 0 else 0.0
        
        # 更新status_color based on progress
        if progress.progress_percentage >= 100:
            progress.status_color = QColor(0, 255, 0)  # Green for complete
        elif progress.progress_percentage >= 75:
            progress.status_color = QColor(255, 255, 0)  # Yellow for high progress
        elif progress.progress_percentage >= 25:
            progress.status_color = QColor(255, 165, 0)  # Orange for medium progress
        else:
            progress.status_color = QColor(128, 128, 128)  # Gray for low progress
    
    def _update_overall_progress(self) -> None:
        """更新整体进度"""
        total_holes = sum(p.total_holes for p in self.sector_progress.values())
        completed_holes = sum(p.completed_holes for p in self.sector_progress.values())
        qualified_holes = sum(p.qualified_holes for p in self.sector_progress.values())
        defective_holes = sum(p.defective_holes for p in self.sector_progress.values())
        
        overall_stats = {
            'total_holes': total_holes,
            'completed_holes': completed_holes,
            'qualified_holes': qualified_holes,
            'defective_holes': defective_holes,
            'completion_rate': (completed_holes / total_holes * 100) if total_holes > 0 else 0,
            'qualification_rate': (qualified_holes / completed_holes * 100) if completed_holes > 0 else 0
        }
        
        self.overall_progress_updated.emit(overall_stats)
    
    def get_geometry_bounds(self) -> Optional[GeometryBounds]:
        """获取几何边界"""
        return self.geometry_bounds
    
    def get_center_point(self) -> Optional[QPointF]:
        """获取中心点"""
        return self.center_point
    
    def is_legacy_mode(self) -> bool:
        """检查是否为兼容模式"""
        return self._legacy_mode
    
    def get_angle_calculator_stats(self) -> Dict[str, Any]:
        """获取角度计算器统计信息"""
        return self.angle_calculator.get_calculation_stats()
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.angle_calculator.clear_cache()
    
    def export_configuration(self) -> Dict[str, Any]:
        """导出配置信息"""
        return {
            'geometry_bounds': {
                'center_x': self.geometry_bounds.center_x if self.geometry_bounds else None,
                'center_y': self.geometry_bounds.center_y if self.geometry_bounds else None,
                'width': self.geometry_bounds.width if self.geometry_bounds else None,
                'height': self.geometry_bounds.height if self.geometry_bounds else None
            },
            'sector_angles': self.sector_angles,
            'sector_assignments_count': {
                sector.value: sum(1 for s in self.sector_assignments.values() if s == sector)
                for sector in SectorQuadrant
            },
            'config': {
                'use_adaptive_angles': self.config.use_adaptive_angles,
                'legacy_mode': self._legacy_mode
            }
        }