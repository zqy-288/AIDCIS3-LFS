"""
自适应角度计算器
根据DXF文件中的实际几何数据自动计算和调整角度
实现智能适应不同的管板布局
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import logging

from src.core_business.models.hole_data import HoleData, HoleCollection
from src.core_business.graphics.sector_manager import SectorQuadrant
from src.core.error_handler import get_error_handler, ErrorCategory


@dataclass
class GeometryBounds:
    """几何边界信息"""
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    center_x: float
    center_y: float
    width: float
    height: float


@dataclass
class AdaptiveAngleConfig:
    """自适应角度配置"""
    sector_count: int = 4  # 扇形区域数量
    min_angle_coverage: float = 85.0  # 最小角度覆盖率(度)
    max_angle_deviation: float = 5.0  # 最大角度偏差(度)
    center_detection_method: str = 'auto'  # 中心检测方法: 'auto', 'geometric', 'density'
    angle_precision: int = 2  # 角度精度(小数位)
    enable_angle_adjustment: bool = True  # 是否启用角度调整
    

class AdaptiveAngleCalculator:
    """自适应角度计算器"""
    
    def __init__(self, config: AdaptiveAngleConfig = None):
        self.config = config or AdaptiveAngleConfig()
        self.logger = logging.getLogger(__name__)
        self.error_handler = get_error_handler()
        
        # 计算结果缓存
        self._geometry_cache: Dict[str, GeometryBounds] = {}
        self._angle_cache: Dict[str, Dict[str, float]] = {}
        
    def analyze_hole_geometry(self, hole_collection: HoleCollection) -> GeometryBounds:
        """
        分析孔位几何布局
        
        Args:
            hole_collection: 孔位集合
            
        Returns:
            GeometryBounds: 几何边界信息
        """
        if not hole_collection.holes:
            raise ValueError("孔位集合为空")
            
        # 生成缓存键
        cache_key = f"geometry_{len(hole_collection.holes)}_{hash(frozenset(hole_collection.holes.keys()))}"
        
        if cache_key in self._geometry_cache:
            return self._geometry_cache[cache_key]
        
        holes = list(hole_collection.holes.values())
        
        # 计算边界
        x_coords = [hole.center_x for hole in holes]
        y_coords = [hole.center_y for hole in holes]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        # 计算中心点
        center_x, center_y = self._calculate_adaptive_center(holes)
        
        geometry = GeometryBounds(
            min_x=min_x,
            max_x=max_x,
            min_y=min_y,
            max_y=max_y,
            center_x=center_x,
            center_y=center_y,
            width=max_x - min_x,
            height=max_y - min_y
        )
        
        # 缓存结果
        self._geometry_cache[cache_key] = geometry
        
        self.logger.info(f"几何分析完成: 边界({min_x:.2f}, {min_y:.2f})-({max_x:.2f}, {max_y:.2f}), "
                        f"中心({center_x:.2f}, {center_y:.2f}), 尺寸({geometry.width:.2f}x{geometry.height:.2f})")
        
        return geometry
    
    def _calculate_adaptive_center(self, holes: List[HoleData]) -> Tuple[float, float]:
        """
        自适应计算中心点
        
        Args:
            holes: 孔位列表
            
        Returns:
            Tuple[float, float]: 中心点坐标
        """
        if self.config.center_detection_method == 'geometric':
            # 几何中心：边界中点
            x_coords = [hole.center_x for hole in holes]
            y_coords = [hole.center_y for hole in holes]
            center_x = (min(x_coords) + max(x_coords)) / 2
            center_y = (min(y_coords) + max(y_coords)) / 2
            
        elif self.config.center_detection_method == 'density':
            # 密度中心：基于孔位分布密度
            center_x, center_y = self._calculate_density_center(holes)
            
        else:  # auto
            # 自动选择：结合几何中心和质心
            geometric_center = self._calculate_geometric_center(holes)
            mass_center = self._calculate_mass_center(holes)
            
            # 加权平均
            center_x = (geometric_center[0] + mass_center[0]) / 2
            center_y = (geometric_center[1] + mass_center[1]) / 2
            
        return center_x, center_y
    
    def _calculate_geometric_center(self, holes: List[HoleData]) -> Tuple[float, float]:
        """计算几何中心"""
        x_coords = [hole.center_x for hole in holes]
        y_coords = [hole.center_y for hole in holes]
        center_x = (min(x_coords) + max(x_coords)) / 2
        center_y = (min(y_coords) + max(y_coords)) / 2
        return center_x, center_y
    
    def _calculate_mass_center(self, holes: List[HoleData]) -> Tuple[float, float]:
        """计算质心"""
        center_x = sum(hole.center_x for hole in holes) / len(holes)
        center_y = sum(hole.center_y for hole in holes) / len(holes)
        return center_x, center_y
    
    def _calculate_density_center(self, holes: List[HoleData]) -> Tuple[float, float]:
        """基于密度分布计算中心"""
        # 使用核密度估计找到最高密度点
        x_coords = np.array([hole.center_x for hole in holes])
        y_coords = np.array([hole.center_y for hole in holes])
        
        # 简化版本：使用加权平均，权重基于局部密度
        weights = []
        for i, hole in enumerate(holes):
            # 计算每个孔位周围的局部密度
            distances = np.sqrt((x_coords - hole.center_x)**2 + (y_coords - hole.center_y)**2)
            local_density = np.sum(distances < 50)  # 50单位内的邻居数量
            weights.append(local_density)
        
        weights = np.array(weights)
        if np.sum(weights) == 0:
            weights = np.ones(len(holes))
        
        center_x = np.average(x_coords, weights=weights)
        center_y = np.average(y_coords, weights=weights)
        
        return float(center_x), float(center_y)
    
    def calculate_adaptive_sector_angles(self, hole_collection: HoleCollection) -> Dict[SectorQuadrant, Dict[str, float]]:
        """
        计算自适应扇形区域角度
        
        Args:
            hole_collection: 孔位集合
            
        Returns:
            Dict[SectorQuadrant, Dict[str, float]]: 扇形区域角度配置
        """
        geometry = self.analyze_hole_geometry(hole_collection)
        
        # 生成缓存键
        cache_key = f"angles_{len(hole_collection.holes)}_{geometry.center_x:.2f}_{geometry.center_y:.2f}"
        
        if cache_key in self._angle_cache:
            return self._angle_cache[cache_key]
        
        # 计算每个孔位的角度
        hole_angles = self._calculate_hole_angles(hole_collection.holes, geometry)
        
        # 分析角度分布
        angle_distribution = self._analyze_angle_distribution(hole_angles)
        
        # 计算自适应扇形角度
        sector_angles = self._calculate_adaptive_sectors(angle_distribution, geometry)
        
        # 验证角度配置
        self._validate_angle_configuration(sector_angles)
        
        # 缓存结果
        self._angle_cache[cache_key] = sector_angles
        
        self.logger.info(f"自适应角度计算完成: {len(sector_angles)} 个扇形区域")
        for sector, angles in sector_angles.items():
            self.logger.info(f"  {sector.value}: {angles['start_angle']:.1f}° - {angles['end_angle']:.1f}° (跨度: {angles['span_angle']:.1f}°)")
        
        return sector_angles
    
    def _calculate_hole_angles(self, holes: Dict[str, HoleData], geometry: GeometryBounds) -> Dict[str, float]:
        """计算每个孔位相对于中心的角度"""
        hole_angles = {}
        
        for hole_id, hole in holes.items():
            # 计算相对于中心的角度
            dx = hole.center_x - geometry.center_x
            dy = hole.center_y - geometry.center_y
            
            # 使用atan2计算角度（弧度）
            angle_rad = math.atan2(dy, dx)
            
            # 转换为度数并标准化到0-360范围
            angle_deg = math.degrees(angle_rad)
            if angle_deg < 0:
                angle_deg += 360
            
            hole_angles[hole_id] = round(angle_deg, self.config.angle_precision)
        
        return hole_angles
    
    def _analyze_angle_distribution(self, hole_angles: Dict[str, float]) -> Dict[str, Any]:
        """分析角度分布"""
        angles = list(hole_angles.values())
        
        if not angles:
            return {}
        
        # 统计信息
        min_angle = min(angles)
        max_angle = max(angles)
        angle_range = max_angle - min_angle
        
        # 角度分布直方图
        angle_bins = np.linspace(0, 360, 37)  # 36个10度区间
        hist, _ = np.histogram(angles, bins=angle_bins)
        
        # 找到密度峰值
        peak_indices = self._find_distribution_peaks(hist)
        
        return {
            'angles': angles,
            'min_angle': min_angle,
            'max_angle': max_angle,
            'angle_range': angle_range,
            'histogram': hist,
            'bins': angle_bins,
            'peak_indices': peak_indices,
            'hole_count': len(angles)
        }
    
    def _find_distribution_peaks(self, histogram: np.ndarray) -> List[int]:
        """找到分布的峰值点"""
        peaks = []
        
        # 简单的峰值检测：找到局部最大值
        for i in range(1, len(histogram) - 1):
            if histogram[i] > histogram[i-1] and histogram[i] > histogram[i+1]:
                if histogram[i] > 0:  # 忽略零值
                    peaks.append(i)
        
        return peaks
    
    def _calculate_adaptive_sectors(self, distribution: Dict[str, Any], geometry: GeometryBounds) -> Dict[SectorQuadrant, Dict[str, float]]:
        """计算自适应扇形区域"""
        
        # 检查是否有足够的数据
        if not distribution or distribution['hole_count'] < 4:
            return self._get_default_sectors()
        
        # 根据几何形状和分布决定扇形划分策略
        aspect_ratio = geometry.width / geometry.height if geometry.height > 0 else 1.0
        
        if 0.8 <= aspect_ratio <= 1.2:
            # 近似正方形布局：使用标准四象限划分
            return self._calculate_quadrant_sectors(distribution, geometry)
        else:
            # 非正方形布局：使用自适应划分
            return self._calculate_adaptive_sectors_by_distribution(distribution, geometry)
    
    def _get_default_sectors(self) -> Dict[SectorQuadrant, Dict[str, float]]:
        """获取默认扇形配置"""
        return {
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
    
    def _calculate_quadrant_sectors(self, distribution: Dict[str, Any], geometry: GeometryBounds) -> Dict[SectorQuadrant, Dict[str, float]]:
        """计算四象限扇形区域"""
        angles = distribution['angles']
        
        # 分析四个象限的孔位分布
        quadrant_counts = [0, 0, 0, 0]  # 四个象限的孔位数量
        
        for angle in angles:
            if 315 <= angle or angle < 45:
                quadrant_counts[0] += 1  # 第一象限
            elif 45 <= angle < 135:
                quadrant_counts[1] += 1  # 第二象限
            elif 135 <= angle < 225:
                quadrant_counts[2] += 1  # 第三象限
            else:
                quadrant_counts[3] += 1  # 第四象限
        
        # 根据分布调整角度边界
        if self.config.enable_angle_adjustment:
            return self._adjust_quadrant_boundaries(quadrant_counts, distribution)
        else:
            return self._get_default_sectors()
    
    def _adjust_quadrant_boundaries(self, quadrant_counts: List[int], distribution: Dict[str, Any]) -> Dict[SectorQuadrant, Dict[str, float]]:
        """根据分布调整象限边界"""
        total_holes = sum(quadrant_counts)
        
        if total_holes == 0:
            return self._get_default_sectors()
        
        # 计算每个象限的权重
        weights = [count / total_holes for count in quadrant_counts]
        
        # 基于权重调整角度
        base_angles = [315, 45, 135, 225]  # 默认起始角度
        adjustments = []
        
        for i, weight in enumerate(weights):
            if weight > 0.3:  # 孔位密度较高
                adjustment = min(self.config.max_angle_deviation, 5.0)
            elif weight < 0.1:  # 孔位密度较低
                adjustment = -min(self.config.max_angle_deviation, 5.0)
            else:
                adjustment = 0.0
            adjustments.append(adjustment)
        
        # 应用调整
        adjusted_sectors = {}
        sectors = [SectorQuadrant.SECTOR_1, SectorQuadrant.SECTOR_2, SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4]
        
        for i, sector in enumerate(sectors):
            start_angle = (base_angles[i] + adjustments[i]) % 360
            end_angle = (base_angles[(i + 1) % 4] + adjustments[(i + 1) % 4]) % 360
            
            # 计算跨度角度
            if end_angle > start_angle:
                span_angle = end_angle - start_angle
            else:
                span_angle = (360 - start_angle) + end_angle
            
            adjusted_sectors[sector] = {
                'start_angle': round(start_angle, self.config.angle_precision),
                'end_angle': round(end_angle, self.config.angle_precision),
                'span_angle': round(span_angle, self.config.angle_precision)
            }
        
        return adjusted_sectors
    
    def _calculate_adaptive_sectors_by_distribution(self, distribution: Dict[str, Any], geometry: GeometryBounds) -> Dict[SectorQuadrant, Dict[str, float]]:
        """根据分布自适应计算扇形区域"""
        # 暂时返回默认配置，后续可以实现更复杂的自适应算法
        return self._get_default_sectors()
    
    def _validate_angle_configuration(self, sector_angles: Dict[SectorQuadrant, Dict[str, float]]) -> None:
        """验证角度配置的有效性"""
        
        # 检查角度范围
        for sector, angles in sector_angles.items():
            start_angle = angles['start_angle']
            end_angle = angles['end_angle']
            span_angle = angles['span_angle']
            
            # 验证角度范围
            if not (0 <= start_angle < 360):
                raise ValueError(f"扇形 {sector.value} 起始角度无效: {start_angle}")
            
            if not (0 <= end_angle < 360):
                raise ValueError(f"扇形 {sector.value} 结束角度无效: {end_angle}")
            
            if not (self.config.min_angle_coverage <= span_angle <= 360):
                raise ValueError(f"扇形 {sector.value} 跨度角度无效: {span_angle}")
        
        # 检查角度覆盖是否完整
        total_coverage = sum(angles['span_angle'] for angles in sector_angles.values())
        if abs(total_coverage - 360) > 10:  # 允许10度误差
            self.logger.warning(f"扇形角度覆盖率异常: {total_coverage}°")
    
    def get_sector_for_hole(self, hole: HoleData, geometry: GeometryBounds, sector_angles: Dict[SectorQuadrant, Dict[str, float]]) -> SectorQuadrant:
        """
        确定孔位所属的扇形区域
        
        Args:
            hole: 孔位数据
            geometry: 几何边界
            sector_angles: 扇形角度配置
            
        Returns:
            SectorQuadrant: 所属扇形区域
        """
        # 计算孔位角度
        dx = hole.center_x - geometry.center_x
        dy = hole.center_y - geometry.center_y
        
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        if angle_deg < 0:
            angle_deg += 360
        
        # 找到匹配的扇形
        for sector, angles in sector_angles.items():
            if self._angle_in_sector(angle_deg, angles):
                return sector
        
        # 如果没有匹配到，返回默认扇形
        return SectorQuadrant.SECTOR_1
    
    def _angle_in_sector(self, angle: float, sector_angles: Dict[str, float]) -> bool:
        """判断角度是否在扇形范围内"""
        start_angle = sector_angles['start_angle']
        end_angle = sector_angles['end_angle']
        
        if start_angle <= end_angle:
            return start_angle <= angle < end_angle
        else:  # 跨越0度
            return angle >= start_angle or angle < end_angle
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._geometry_cache.clear()
        self._angle_cache.clear()
        self.logger.info("自适应角度计算器缓存已清空")
    
    def get_calculation_stats(self) -> Dict[str, Any]:
        """获取计算统计信息"""
        return {
            'geometry_cache_size': len(self._geometry_cache),
            'angle_cache_size': len(self._angle_cache),
            'config': {
                'sector_count': self.config.sector_count,
                'center_detection_method': self.config.center_detection_method,
                'angle_precision': self.config.angle_precision,
                'enable_angle_adjustment': self.config.enable_angle_adjustment
            }
        }