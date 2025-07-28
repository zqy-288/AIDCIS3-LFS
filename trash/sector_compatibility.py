"""
扇形角度计算向后兼容性保护
确保在优化过程中现有的检测功能和数据格式不受影响
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from src.core_business.models.hole_data import HoleData, HoleCollection
from src.core_business.graphics.sector_manager import SectorQuadrant, SectorManager
from src.core_business.graphics.enhanced_sector_manager import EnhancedSectorManager


class CompatibilityMode(Enum):
    """兼容性模式"""
    LEGACY = "legacy"           # 完全兼容模式
    HYBRID = "hybrid"           # 混合模式
    ENHANCED = "enhanced"       # 增强模式


@dataclass
class CompatibilityConfig:
    """兼容性配置"""
    mode: CompatibilityMode = CompatibilityMode.HYBRID
    enable_legacy_fallback: bool = True
    preserve_existing_data: bool = True
    validate_consistency: bool = True
    warn_on_differences: bool = True
    
    # 兼容性阈值
    angle_difference_threshold: float = 5.0  # 角度差异阈值(度)
    assignment_difference_threshold: float = 0.05  # 分配差异阈值(5%)


class SectorCompatibilityManager:
    """扇形兼容性管理器"""
    
    def __init__(self, config: CompatibilityConfig = None):
        self.config = config or CompatibilityConfig()
        self.logger = logging.getLogger(__name__)
        
        # 兼容性状态
        self._compatibility_warnings: List[str] = []
        self._validation_results: Dict[str, Any] = {}
        
    def create_compatible_manager(self, hole_collection: HoleCollection) -> Union[SectorManager, EnhancedSectorManager]:
        """
        创建兼容的扇形管理器
        
        Args:
            hole_collection: 孔位集合
            
        Returns:
            Union[SectorManager, EnhancedSectorManager]: 兼容的管理器
        """
        try:
            if self.config.mode == CompatibilityMode.LEGACY:
                return self._create_legacy_manager(hole_collection)
            elif self.config.mode == CompatibilityMode.ENHANCED:
                return self._create_enhanced_manager(hole_collection)
            else:  # HYBRID
                return self._create_hybrid_manager(hole_collection)
                
        except Exception as e:
            self.logger.error(f"创建兼容管理器失败: {e}")
            if self.config.enable_legacy_fallback:
                return self._create_legacy_manager(hole_collection)
            else:
                raise
    
    def _create_legacy_manager(self, hole_collection: HoleCollection) -> SectorManager:
        """创建传统扇形管理器"""
        try:
            manager = SectorManager()
            manager.load_hole_collection(hole_collection)
            self.logger.info("使用传统扇形管理器")
            return manager
        except Exception as e:
            self.logger.error(f"创建传统管理器失败: {e}")
            raise
    
    def _create_enhanced_manager(self, hole_collection: HoleCollection) -> EnhancedSectorManager:
        """创建增强型扇形管理器"""
        try:
            from src.core_business.graphics.enhanced_sector_manager import EnhancedSectorConfig
            
            config = EnhancedSectorConfig(
                use_adaptive_angles=True,
                fallback_to_default=self.config.enable_legacy_fallback,
                validate_angle_consistency=self.config.validate_consistency
            )
            
            manager = EnhancedSectorManager(config)
            manager.set_hole_collection(hole_collection)
            self.logger.info("使用增强型扇形管理器")
            return manager
        except Exception as e:
            self.logger.error(f"创建增强型管理器失败: {e}")
            raise
    
    def _create_hybrid_manager(self, hole_collection: HoleCollection) -> Union[SectorManager, EnhancedSectorManager]:
        """创建混合模式管理器"""
        try:
            # 首先尝试创建增强型管理器
            enhanced_manager = self._create_enhanced_manager(hole_collection)
            
            # 如果需要验证兼容性，创建传统管理器进行对比
            if self.config.validate_consistency:
                legacy_manager = self._create_legacy_manager(hole_collection)
                
                # 验证兼容性
                is_compatible = self._validate_compatibility(legacy_manager, enhanced_manager)
                
                if not is_compatible and self.config.enable_legacy_fallback:
                    self.logger.warning("兼容性验证失败，回退到传统管理器")
                    return legacy_manager
            
            return enhanced_manager
            
        except Exception as e:
            self.logger.error(f"创建混合模式管理器失败: {e}")
            
            if self.config.enable_legacy_fallback:
                return self._create_legacy_manager(hole_collection)
            else:
                raise
    
    def _validate_compatibility(self, legacy_manager: SectorManager, enhanced_manager: EnhancedSectorManager) -> bool:
        """
        验证兼容性
        
        Args:
            legacy_manager: 传统管理器
            enhanced_manager: 增强型管理器
            
        Returns:
            bool: 是否兼容
        """
        try:
            # 检查孔位分配一致性
            assignment_consistent = self._check_assignment_consistency(legacy_manager, enhanced_manager)
            
            # 检查角度配置合理性
            angle_reasonable = self._check_angle_reasonableness(enhanced_manager)
            
            # 检查扇形覆盖完整性
            coverage_complete = self._check_coverage_completeness(enhanced_manager)
            
            # 记录验证结果
            self._validation_results = {
                'assignment_consistent': assignment_consistent,
                'angle_reasonable': angle_reasonable,
                'coverage_complete': coverage_complete,
                'overall_compatible': assignment_consistent and angle_reasonable and coverage_complete
            }
            
            # 记录警告
            if not assignment_consistent:
                self._compatibility_warnings.append("孔位分配不一致")
            
            if not angle_reasonable:
                self._compatibility_warnings.append("角度配置不合理")
            
            if not coverage_complete:
                self._compatibility_warnings.append("扇形覆盖不完整")
            
            return self._validation_results['overall_compatible']
            
        except Exception as e:
            self.logger.error(f"兼容性验证失败: {e}")
            # 记录错误但不序列化对象
            self._validation_results = {
                'error': str(e),
                'overall_compatible': False
            }
            return False
    
    def _check_assignment_consistency(self, legacy_manager: SectorManager, enhanced_manager: EnhancedSectorManager) -> bool:
        """检查孔位分配一致性"""
        try:
            if not legacy_manager.hole_collection or not enhanced_manager.hole_collection:
                return False
            
            # 获取孔位分配
            legacy_assignments = {}
            enhanced_assignments = {}
            
            for hole_id in legacy_manager.hole_collection.holes:
                legacy_sector = legacy_manager.get_sector_for_hole(hole_id)
                enhanced_sector = enhanced_manager.get_sector_for_hole(hole_id)
                
                if legacy_sector:
                    legacy_assignments[hole_id] = legacy_sector
                if enhanced_sector:
                    enhanced_assignments[hole_id] = enhanced_sector
            
            # 计算差异
            total_holes = len(legacy_assignments)
            if total_holes == 0:
                return True
            
            different_assignments = 0
            for hole_id in legacy_assignments:
                if hole_id in enhanced_assignments:
                    if legacy_assignments[hole_id] != enhanced_assignments[hole_id]:
                        different_assignments += 1
            
            difference_rate = different_assignments / total_holes
            
            if difference_rate > self.config.assignment_difference_threshold:
                self.logger.warning(f"孔位分配差异过大: {difference_rate:.2%}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查分配一致性失败: {e}")
            return False
    
    def _check_angle_reasonableness(self, enhanced_manager: EnhancedSectorManager) -> bool:
        """检查角度配置合理性"""
        try:
            # 获取角度配置
            if not hasattr(enhanced_manager, 'sector_angles'):
                return False
            
            sector_angles = enhanced_manager.sector_angles
            
            # 检查每个扇形的角度
            for sector, angles in sector_angles.items():
                span_angle = angles.get('span_angle', 0)
                
                # 检查角度范围
                if span_angle <= 0 or span_angle > 180:  # 扇形角度应该在合理范围内
                    self.logger.warning(f"扇形 {sector.value} 角度不合理: {span_angle}°")
                    return False
            
            # 检查总覆盖率
            total_span = sum(angles.get('span_angle', 0) for angles in sector_angles.values())
            if abs(total_span - 360) > 20:  # 允许20度误差
                self.logger.warning(f"总角度覆盖率异常: {total_span}°")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查角度合理性失败: {e}")
            return False
    
    def _check_coverage_completeness(self, enhanced_manager: EnhancedSectorManager) -> bool:
        """检查扇形覆盖完整性"""
        try:
            # 检查是否所有孔位都被分配到扇形
            if not enhanced_manager.hole_collection:
                return True
            
            total_holes = len(enhanced_manager.hole_collection.holes)
            assigned_holes = len(enhanced_manager.sector_assignments)
            
            if assigned_holes < total_holes:
                self.logger.warning(f"孔位分配不完整: {assigned_holes}/{total_holes}")
                return False
            
            # 检查每个扇形是否都有孔位
            sector_counts = {}
            for sector in SectorQuadrant:
                holes = enhanced_manager.get_sector_holes(sector)
                sector_counts[sector] = len(holes)
            
            # 检查是否有空扇形
            empty_sectors = [sector for sector, count in sector_counts.items() if count == 0]
            if len(empty_sectors) > 1:  # 允许最多一个空扇形
                self.logger.warning(f"过多空扇形: {[s.value for s in empty_sectors]}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查覆盖完整性失败: {e}")
            return False
    
    def get_compatibility_warnings(self) -> List[str]:
        """获取兼容性警告"""
        return self._compatibility_warnings.copy()
    
    def get_validation_results(self) -> Dict[str, Any]:
        """获取验证结果"""
        return self._validation_results.copy()
    
    def clear_warnings(self) -> None:
        """清空警告"""
        self._compatibility_warnings.clear()
        self._validation_results.clear()
    
    def export_compatibility_report(self) -> Dict[str, Any]:
        """导出兼容性报告"""
        return {
            'config': {
                'mode': self.config.mode.value,
                'enable_legacy_fallback': self.config.enable_legacy_fallback,
                'validate_consistency': self.config.validate_consistency
            },
            'warnings': self._compatibility_warnings,
            'validation_results': self._validation_results,
            'thresholds': {
                'angle_difference': self.config.angle_difference_threshold,
                'assignment_difference': self.config.assignment_difference_threshold
            }
        }


def create_compatible_sector_manager(hole_collection: HoleCollection, 
                                   compatibility_mode: CompatibilityMode = CompatibilityMode.HYBRID) -> Union[SectorManager, EnhancedSectorManager]:
    """
    创建兼容的扇形管理器的便捷函数
    
    Args:
        hole_collection: 孔位集合
        compatibility_mode: 兼容性模式
        
    Returns:
        Union[SectorManager, EnhancedSectorManager]: 兼容的管理器
    """
    config = CompatibilityConfig(mode=compatibility_mode)
    compatibility_manager = SectorCompatibilityManager(config)
    
    return compatibility_manager.create_compatible_manager(hole_collection)