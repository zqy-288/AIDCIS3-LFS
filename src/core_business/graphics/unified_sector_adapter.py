"""
统一扇形管理适配器
为现有系统提供向后兼容的接口，同时使用新的统一坐标管理系统
"""

from typing import Dict, List, Optional, Any
from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtGui import QColor

from src.core_business.coordinate_system import (
    UnifiedCoordinateManager, CoordinateConfig, CoordinateSystem
)
from src.core_business.graphics.sector_types import SectorQuadrant, SectorProgress
from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus
from src.core_business.geometry.adaptive_angle_calculator import AdaptiveAngleCalculator, AdaptiveAngleConfig


class UnifiedSectorAdapter(QObject):
    """
    统一扇形管理适配器
    提供与现有SectorManager兼容的接口，内部使用UnifiedCoordinateManager
    使用单例模式避免重复初始化和数据处理
    """
    
    # 单例模式
    _instance = None
    _initialized = False
    
    # 兼容性信号 - DEPRECATED: 计划在下个版本移除
    sector_progress_updated = Signal(SectorQuadrant, SectorProgress)  # DEPRECATED
    overall_progress_updated = Signal(dict)  # DEPRECATED
    
    # 新增信号
    coordinate_system_changed = Signal(CoordinateSystem)
    unified_debug_info = Signal(str)
    
    def __new__(cls, parent=None, debug_enabled: bool = True):
        """单例模式：确保全局只有一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, parent=None, debug_enabled: bool = True):
        # 避免重复初始化
        if self._initialized:
            return
            
        super().__init__(parent)
        
        # 数据缓存
        self._cache = {
            'processed_collection': None,
            'coordinate_manager': None,
            'last_rotation': None,
            'last_center': None,
            'hole_collection_hash': None,
            'adaptive_angles': None,  # 缓存自适应角度计算结果
            'geometry_bounds': None   # 缓存几何边界信息
        }
        
        # 旋转功能已全面禁用，注释掉相关代码
        # # from src.core_business.graphics.rotation_stub import get_rotation_manager  # 旋转功能已禁用
        # # rotation_manager = get_rotation_manager()  # 旋转功能已禁用
        
        # 创建统一坐标管理器 - 旋转功能已禁用
        config = CoordinateConfig(
            rotation_enabled=False,  # 旋转功能已禁用
            rotation_angle=0.0,      # 角度设为0
            rotation_center_mode="geometric_center",
            sector_center_mode="geometric_center",
            debug_enabled=debug_enabled,
            debug_sample_count=5
        )
        
        # 使用类级别的坐标管理器，确保所有实例共享同一个
        if not hasattr(self.__class__, '_unified_manager'):
            self.__class__._unified_manager = UnifiedCoordinateManager(config)
        self.unified_manager = self.__class__._unified_manager
        
        # 创建自适应角度计算器 - 使用单例模式
        if not hasattr(self.__class__, '_angle_calculator'):
            angle_config = AdaptiveAngleConfig(
                sector_count=4,
                center_detection_method='auto',
                angle_precision=2,
                enable_angle_adjustment=True
            )
            self.__class__._angle_calculator = AdaptiveAngleCalculator(angle_config)
        self.angle_calculator = self.__class__._angle_calculator
        
        # 连接信号
        self.unified_manager.coordinate_system_changed.connect(self.coordinate_system_changed.emit)
        self.unified_manager.sector_assignments_updated.connect(self._on_sector_assignments_updated)
        self.unified_manager.debug_info_updated.connect(self.unified_debug_info.emit)
        
        # 兼容性数据
        self.hole_collection: Optional[HoleCollection] = None
        self.center_point: Optional[QPointF] = None
        self.sector_assignments: Dict[str, SectorQuadrant] = {}
        self.sector_progresses: Dict[SectorQuadrant, SectorProgress] = {}
        
        # 扇形颜色配置（保持与原系统兼容）
        self.sector_colors = {
            SectorQuadrant.SECTOR_1: QColor(76, 175, 80),   # 绿色 - 右上
            SectorQuadrant.SECTOR_2: QColor(33, 150, 243),  # 蓝色 - 左上
            SectorQuadrant.SECTOR_3: QColor(255, 152, 0),   # 橙色 - 左下
            SectorQuadrant.SECTOR_4: QColor(156, 39, 176),  # 紫色 - 右下
        }
        
        # 兼容性属性
        self._dynamic_mode_enabled = False
        self._dynamic_sector_count = 4
        self._enhanced_mode_enabled = True
        
        # 标记已初始化
        self._initialized = True
    
    def load_hole_collection(self, hole_collection: HoleCollection):
        """
        DEPRECATED: 请使用SharedDataManager.load_and_process_data()替代
        此方法仅供SharedDataManager内部调用，不应直接使用
        """
        print("⚠️ [UnifiedSectorAdapter] load_hole_collection()应该仅由SharedDataManager调用")
        # 计算数据哈希值用于缓存判断
        data_hash = self._calculate_data_hash(hole_collection)
        
        # 检查缓存
        if self._is_cached_data_valid(data_hash):
            print(f"🎯 [统一适配器] 使用缓存数据: {len(hole_collection.holes)} 个孔位")
            self.hole_collection = hole_collection
            # 缓存命中时，不需要重新初始化坐标管理器
            # 只需要确保扇形分配等数据是最新的
            if hasattr(self, 'sector_assignments') and self.sector_assignments:
                print(f"📊 [统一适配器] 缓存命中，跳过坐标变换，当前扇形分配: {len(self.sector_assignments)} 个")
            return
        
        print(f"🔄 [统一适配器] 开始加载孔位集合: {len(hole_collection.holes)} 个孔位")
        
        self.hole_collection = hole_collection
        
        # 使用统一坐标管理器处理
        print(f"🔍 [统一适配器] 调用 unified_manager.initialize_from_hole_collection")
        self.unified_manager.initialize_from_hole_collection(hole_collection)
        print(f"🔍 [统一适配器] 初始化完成，sector_assignments: {len(self.unified_manager.sector_assignments)}")
        
        # 计算自适应角度（使用缓存）
        self._calculate_adaptive_angles(hole_collection)
        
        # 同步数据到兼容性接口
        self._sync_compatibility_data()
        
        # 初始化进度统计
        self._initialize_sector_progress()
        
        # 更新缓存
        self._update_cache(hole_collection, data_hash)
        
        print(f"✅ [统一适配器] 孔位集合加载完成")
    
    def _sync_compatibility_data(self):
        """同步数据到兼容性接口"""
        # 同步扇形分配
        self.sector_assignments = self.unified_manager.sector_assignments.copy()
        
        # 同步中心点
        self.center_point = self.unified_manager.sector_center
        
        print(f"🔄 [统一适配器] 数据同步完成: {len(self.sector_assignments)} 个扇形分配")
    
    def _on_sector_assignments_updated(self, update_data: dict):
        """处理扇形分配更新"""
        print(f"📊 [统一适配器] 扇形分配更新: {update_data['sector_counts']}")
        
        # 更新进度信息
        for sector in SectorQuadrant:
            if sector in self.sector_progresses:
                self._recalculate_sector_progress(sector)
        
        # 发射整体进度更新
        self._emit_overall_progress()
    
    def _initialize_sector_progress(self):
        """初始化各扇形区域的进度统计"""
        sector_counts = self.unified_manager.get_all_sector_counts()
        
        # 创建进度对象
        for sector in SectorQuadrant:
            hole_count = sector_counts.get(sector, 0)
            
            self.sector_progresses[sector] = SectorProgress(
                sector=sector,
                total_holes=hole_count,
                completed_holes=0,
                qualified_holes=0,
                defective_holes=0,
                progress_percentage=0.0,
                status_color=self.sector_colors[sector]
            )
        
        print(f"📈 [统一适配器] 进度统计初始化完成")
    
    def _recalculate_sector_progress(self, sector: SectorQuadrant):
        """重新计算指定扇形区域的进度"""
        if not self.hole_collection or sector not in self.sector_progresses:
            return
        
        # 获取该扇形的所有孔位
        sector_holes = self.unified_manager.get_sector_holes(sector)
        
        # 统计各状态数量
        completed = 0
        qualified = 0
        defective = 0
        
        for hole in sector_holes:
            if hole.status in [HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE, 
                             HoleStatus.BLIND, HoleStatus.TIE_ROD]:
                completed += 1
                
                if hole.status == HoleStatus.QUALIFIED:
                    qualified += 1
                elif hole.status == HoleStatus.DEFECTIVE:
                    defective += 1
        
        # 更新进度数据
        progress = self.sector_progresses[sector]
        progress.completed_holes = completed
        progress.qualified_holes = qualified
        progress.defective_holes = defective
        progress.progress_percentage = progress.completion_rate
        
        # 根据进度更新状态颜色
        progress.status_color = self._get_progress_color(progress.completion_rate)
    
    def _get_progress_color(self, completion_rate: float) -> QColor:
        """根据完成率获取状态颜色"""
        if completion_rate >= 90:
            return QColor(76, 175, 80)    # 绿色 - 完成度高
        elif completion_rate >= 60:
            return QColor(255, 193, 7)    # 黄色 - 完成度中等
        elif completion_rate >= 30:
            return QColor(255, 152, 0)    # 橙色 - 完成度较低
        else:
            return QColor(244, 67, 54)    # 红色 - 完成度低
    
    def _emit_overall_progress(self):
        """发射整体进度更新信号"""
        overall_stats = {
            'total_holes': sum(p.total_holes for p in self.sector_progresses.values()),
            'completed_holes': sum(p.completed_holes for p in self.sector_progresses.values()),
            'qualified_holes': sum(p.qualified_holes for p in self.sector_progresses.values()),
            'defective_holes': sum(p.defective_holes for p in self.sector_progresses.values()),
            'sector_progresses': self.sector_progresses.copy()
        }
        
        self.overall_progress_updated.emit(overall_stats)
    
    # =================================
    # 兼容性接口方法（与原SectorManager接口兼容）
    # =================================
    
    def update_hole_status(self, hole_id: str, new_status: HoleStatus):
        """更新孔位状态并重新计算区域进度"""
        if hole_id not in self.sector_assignments:
            return
        
        sector = self.sector_assignments[hole_id]
        self._recalculate_sector_progress(sector)
        
        # 发射更新信号
        self.sector_progress_updated.emit(sector, self.sector_progresses[sector])
        self._emit_overall_progress()
    
    def get_sector_holes(self, sector: SectorQuadrant) -> List[HoleData]:
        """获取指定扇形区域的所有孔位 - 修复循环依赖"""
        try:
            # 修复循环依赖：使用内部数据而不是反向依赖SharedDataManager
            if not hasattr(self, '_current_hole_collection') or not self._current_hole_collection:
                print(f"⚠️ [UnifiedSectorAdapter] 没有可用的孔位数据")
                return []
            
            # 从内部缓存的扇形分配中获取
            sector_hole_ids = [hole_id for hole_id, assigned_sector in self.unified_manager.sector_assignments.items() 
                              if assigned_sector == sector]
            
            sector_holes = [self._current_hole_collection.holes[hole_id] 
                           for hole_id in sector_hole_ids 
                           if hole_id in self._current_hole_collection.holes]
            
            print(f"✅ [UnifiedSectorAdapter] 从内部缓存获取扇形 {sector.name}: {len(sector_holes)} 个孔位")
            return sector_holes
            
        except Exception as e:
            error_msg = f"❌ [UnifiedSectorAdapter] 获取扇形数据失败: {e}"
            print(error_msg)
            raise RuntimeError(error_msg) from e
    
    def get_hole_sector(self, hole_id: str) -> Optional[SectorQuadrant]:
        """获取孔位所属的扇形区域 - 修复循环依赖"""
        try:
            # 修复循环依赖：使用内部扇形分配数据
            if not hasattr(self.unified_manager, 'sector_assignments'):
                print(f"⚠️ [UnifiedSectorAdapter] 扇形分配数据未初始化")
                return None
            
            # 从内部扇形分配中查找
            assigned_sector = self.unified_manager.sector_assignments.get(hole_id)
            if assigned_sector:
                print(f"✅ [UnifiedSectorAdapter] 孔位 {hole_id} 属于扇形 {assigned_sector.name}")
            else:
                print(f"⚠️ [UnifiedSectorAdapter] 孔位 {hole_id} 未分配到任何扇形")
            
            return assigned_sector
            
        except Exception as e:
            error_msg = f"❌ [UnifiedSectorAdapter] 获取孔位扇形失败: {e}"
            print(error_msg)
            raise RuntimeError(error_msg) from e
    
    def get_sector_progress(self, sector: SectorQuadrant) -> Optional[SectorProgress]:
        """获取指定扇形区域的进度信息"""
        return self.sector_progresses.get(sector)
    
    def get_all_sector_progresses(self) -> Dict[SectorQuadrant, SectorProgress]:
        """获取所有扇形区域的进度信息"""
        return self.sector_progresses.copy()
    
    def get_center_point(self) -> Optional[QPointF]:
        """获取管板中心点"""
        return self.center_point
    
    def get_overall_progress(self) -> Dict:
        """获取整体进度信息"""
        return {
            'total_holes': sum(p.total_holes for p in self.sector_progresses.values()),
            'completed_holes': sum(p.completed_holes for p in self.sector_progresses.values()),
            'qualified_holes': sum(p.qualified_holes for p in self.sector_progresses.values()),
            'defective_holes': sum(p.defective_holes for p in self.sector_progresses.values()),
            'sector_progresses': self.sector_progresses.copy()
        }
    
    def get_sector_for_hole(self, hole_id: str) -> Optional[SectorQuadrant]:
        """获取指定孔位所属的扇形区域"""
        return self.unified_manager.get_hole_sector(hole_id)
    
    def cleanup_resources(self) -> None:
        """清理资源"""
        self.unified_manager.clear()
        self.sector_assignments.clear()
        self.sector_progresses.clear()
        self.hole_collection = None
        self.center_point = None
        
        print(f"🧹 [统一适配器] 资源清理完成")
    
    # =================================
    # 新增的统一管理功能
    # =================================
    
    def get_coordinate_system(self) -> CoordinateSystem:
        """获取当前坐标系"""
        return self.unified_manager.current_coordinate_system
    
    def get_coordinate_transformation(self, hole_id: str) -> Optional[Dict]:
        """获取孔位的坐标变换信息"""
        return self.unified_manager.get_coordinate_transformation(hole_id)
    
    def get_unified_sector_info(self, sector: SectorQuadrant):
        """获取统一的扇形信息"""
        return self.unified_manager.get_sector_info(sector)
    
    def get_all_unified_sector_info(self):
        """获取所有统一的扇形信息"""
        return self.unified_manager.get_all_sector_info()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        unified_stats = self.unified_manager.get_performance_stats()
        return {
            **unified_stats,
            'adapter_info': {
                'sector_assignments': len(self.sector_assignments),
                'sector_progresses': len(self.sector_progresses),
                'compatibility_mode': True
            }
        }
    
    def enable_debug(self, enabled: bool = True):
        """启用/禁用调试模式"""
        self.unified_manager.enable_debug(enabled)
    
    def reconfigure_coordinate_system(self, config: CoordinateConfig):
        """重新配置坐标系统"""
        self.unified_manager.reconfigure(config)
        self._sync_compatibility_data()
        self._initialize_sector_progress()
    
    def set_dynamic_mode(self, enabled: bool, sector_count: int = 4):
        """设置是否使用动态扇形模式（兼容性方法）"""
        # 注意：当前统一坐标管理器默认使用4扇形，未来可扩展支持动态扇形数
        if enabled and sector_count != 4:
            print(f"⚠️ [统一适配器] 暂不支持{sector_count}扇形动态模式，使用标准4扇形")
        else:
            print(f"✅ [统一适配器] 使用标准4扇形模式")
        
        # 记录动态模式配置（为未来扩展保留）
        self._dynamic_mode_enabled = enabled
        self._dynamic_sector_count = sector_count
    
    def set_enhanced_mode(self, enabled: bool, compatibility_mode=None):
        """设置是否使用增强模式（兼容性方法）"""
        print(f"✅ [统一适配器] 统一坐标管理器已集成增强功能")
        self._enhanced_mode_enabled = enabled
    
    def has_data(self) -> bool:
        """检查是否有数据"""
        return self.hole_collection is not None and len(self.sector_assignments) > 0
    
    def get_manager_type(self) -> str:
        """获取管理器类型"""
        return "UnifiedCoordinateManager"
    
    def is_enhanced_mode(self) -> bool:
        """是否为增强模式"""
        return True  # 统一管理器默认为增强模式
    
    def get_enhanced_manager(self):
        """获取增强管理器"""
        return self.unified_manager
    
    def get_sector_by_index(self, index: int):
        """根据索引获取扇形"""
        sectors = list(SectorQuadrant)
        if 0 <= index < len(sectors):
            return sectors[index]
        return None
    
    def get_sector_count(self) -> int:
        """获取扇形数量"""
        return len(SectorQuadrant)
    
    def get_manager(self):
        """获取管理器实例"""
        return self.unified_manager
    
    def export_debug_report(self) -> Dict[str, Any]:
        """导出调试报告"""
        unified_info = self.unified_manager.get_all_sector_info()
        
        report = {
            'coordinate_system': self.get_coordinate_system().value,
            'center_point': {
                'x': self.center_point.x() if self.center_point else None,
                'y': self.center_point.y() if self.center_point else None
            },
            'sector_assignments': {
                sector.value: {
                    'hole_count': self.unified_manager.get_sector_count(sector),
                    'quadrant_definition': info.quadrant_definition if info else 'Unknown',
                    'sample_holes': [sample['hole_id'] for sample in info.sample_holes[:3]] if info else []
                }
                for sector, info in unified_info.items()
            },
            'performance_stats': self.get_performance_stats(),
            'total_holes': len(self.sector_assignments)
        }
        
        return report
    
    # =================================
    # 缓存系统方法
    # =================================
    
    def _calculate_data_hash(self, hole_collection: HoleCollection) -> str:
        """
        计算孔位集合的哈希值，用于缓存判断
        注意：基于原始孔位ID和数量计算，不包含坐标数据（因为坐标会被旋转修改）
        """
        # 使用孔位ID和数量生成唯一标识
        hole_ids = sorted(hole_collection.holes.keys())
        hash_data = f"{len(hole_ids)}_{'_'.join(hole_ids[:10])}"  # 使用前10个ID作为样本
        
        import hashlib
        return hashlib.md5(hash_data.encode()).hexdigest()[:8]
    
    def _is_cached_data_valid(self, data_hash: str) -> bool:
        """检查缓存数据是否有效"""
        if self._cache['hole_collection_hash'] != data_hash:
            return False
            
        # 检查关键数据是否存在
        return (self._cache['processed_collection'] is not None and
                len(self.sector_assignments) > 0 and
                self.center_point is not None)
    
    def _update_cache(self, hole_collection: HoleCollection, data_hash: str):
        """更新缓存数据"""
        self._cache.update({
            'processed_collection': hole_collection,
            'coordinate_manager': self.unified_manager,
            'last_rotation': 90.0,  # 当前固定旋转角度
            'last_center': self.center_point,
            'hole_collection_hash': data_hash
        })
        
        print(f"💾 [统一适配器] 缓存已更新: 哈希={data_hash[:8]}...")
    
    def clear_cache(self):
        """清空缓存"""
        self._cache = {
            'processed_collection': None,
            'coordinate_manager': None,
            'last_rotation': None,
            'last_center': None,
            'hole_collection_hash': None
        }
        print(f"🧹 [统一适配器] 缓存已清空")
    
    def get_shared_data(self) -> Dict[str, Any]:
        """获取共享数据，供其他组件使用"""
        return {
            'hole_collection': self.hole_collection,
            'sector_assignments': self.sector_assignments.copy(),
            'center_point': self.center_point,
            'sector_progresses': self.sector_progresses.copy(),
            'coordinate_manager': self.unified_manager,
            'is_cached': self._cache['hole_collection_hash'] is not None,
            'adaptive_angles': self._cache.get('adaptive_angles'),  # 提供自适应角度数据
            'geometry_bounds': self._cache.get('geometry_bounds')   # 提供几何边界数据
        }
    
    # =================================
    # 自适应角度计算方法
    # =================================
    
    def _calculate_adaptive_angles(self, hole_collection: HoleCollection):
        """计算并缓存自适应角度"""
        try:
            print(f"🎯 [自适应角度] 开始计算扇形角度...")
            
            # 分析几何布局
            geometry = self.angle_calculator.analyze_hole_geometry(hole_collection)
            self._cache['geometry_bounds'] = geometry
            
            # 计算自适应扇形角度
            adaptive_angles = self.angle_calculator.calculate_adaptive_sector_angles(hole_collection)
            self._cache['adaptive_angles'] = adaptive_angles
            
            print(f"✅ [自适应角度] 角度计算完成:")
            for sector, angles in adaptive_angles.items():
                print(f"   {sector.value}: {angles['start_angle']:.1f}° - {angles['end_angle']:.1f}° (跨度: {angles['span_angle']:.1f}°)")
                
        except Exception as e:
            print(f"⚠️ [自适应角度] 计算失败，使用默认角度: {e}")
            # 使用默认角度配置
            self._cache['adaptive_angles'] = self._get_default_adaptive_angles()
    
    def _get_default_adaptive_angles(self) -> Dict[SectorQuadrant, Dict[str, float]]:
        """获取默认自适应角度配置"""
        return {
            SectorQuadrant.SECTOR_1: {
                'start_angle': 0.0,
                'end_angle': 90.0,
                'span_angle': 90.0
            },
            SectorQuadrant.SECTOR_2: {
                'start_angle': 270.0,
                'end_angle': 360.0,
                'span_angle': 90.0
            },
            SectorQuadrant.SECTOR_3: {
                'start_angle': 180.0,
                'end_angle': 270.0,
                'span_angle': 90.0
            },
            SectorQuadrant.SECTOR_4: {
                'start_angle': 90.0,
                'end_angle': 180.0,
                'span_angle': 90.0
            }
        }
    
    def get_adaptive_angles(self) -> Optional[Dict[SectorQuadrant, Dict[str, float]]]:
        """获取自适应角度配置"""
        return self._cache.get('adaptive_angles')
    
    def get_geometry_bounds(self):
        """获取几何边界信息"""
        return self._cache.get('geometry_bounds')
    
    def get_sector_from_angle(self, angle: float) -> SectorQuadrant:
        """根据角度确定扇形区域（使用自适应角度）"""
        adaptive_angles = self.get_adaptive_angles()
        
        if adaptive_angles:
            # 使用自适应角度计算
            for sector, angles in adaptive_angles.items():
                start_angle = angles['start_angle']
                end_angle = angles['end_angle']
                
                # 处理跨越0度的情况
                if start_angle > end_angle:
                    if angle >= start_angle or angle < end_angle:
                        return sector
                else:
                    if start_angle <= angle < end_angle:
                        return sector
        
        # 回退到默认逻辑（基于坐标的判断，更可靠）
        if 0 <= angle < 90:
            return SectorQuadrant.SECTOR_1     # 右上
        elif 90 <= angle < 180:
            return SectorQuadrant.SECTOR_4     # 右下  
        elif 180 <= angle < 270:
            return SectorQuadrant.SECTOR_3     # 左下
        else:
            return SectorQuadrant.SECTOR_2     # 左上