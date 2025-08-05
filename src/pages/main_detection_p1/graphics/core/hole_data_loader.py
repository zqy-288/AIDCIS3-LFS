"""
孔位数据加载服务
负责从各种数据源加载孔位数据，提供统一的数据访问接口
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal

from src.shared.models.hole_data import HoleCollection, HoleData
from src.pages.main_detection_p1.graphics.core.sector_controllers import UnifiedLogger


@dataclass
class DataLoadResult:
    """数据加载结果"""
    success: bool
    data: Optional[HoleCollection] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class HoleDataLoader(QObject):
    """孔位数据加载器"""
    
    # 信号
    data_loaded = Signal(DataLoadResult)
    loading_started = Signal()
    loading_progress = Signal(int)  # 0-100
    
    def __init__(self):
        super().__init__()
        self.logger = UnifiedLogger("HoleDataLoader")
        self._cached_data: Optional[HoleCollection] = None
        self._loading = False
        
    @property
    def is_loading(self) -> bool:
        """是否正在加载"""
        return self._loading
        
    @property
    def has_data(self) -> bool:
        """是否有缓存数据"""
        return self._cached_data is not None
        
    def get_cached_data(self) -> Optional[HoleCollection]:
        """获取缓存的数据"""
        return self._cached_data
        
    def load_from_collection(self, hole_collection: HoleCollection) -> DataLoadResult:
        """从已有的HoleCollection加载数据"""
        self.logger.info(f"从HoleCollection加载数据，孔位数: {len(hole_collection)}", "📥")
        
        try:
            self.loading_started.emit()
            self._loading = True
            
            # 验证数据
            if not hole_collection or len(hole_collection) == 0:
                result = DataLoadResult(
                    success=False,
                    error_message="孔位集合为空"
                )
                self.data_loaded.emit(result)
                return result
            
            # 缓存数据
            self._cached_data = hole_collection
            
            # 提取元数据
            metadata = {
                'total_holes': len(hole_collection),
                'bounds': hole_collection.get_bounds(),
                'has_numbering': all(h.hole_id for h in hole_collection.holes.values())
            }
            
            result = DataLoadResult(
                success=True,
                data=hole_collection,
                metadata=metadata
            )
            
            self.loading_progress.emit(100)
            self.data_loaded.emit(result)
            self.logger.info("数据加载成功", "✅")
            return result
            
        except Exception as e:
            self.logger.error(f"数据加载失败: {e}", "❌")
            result = DataLoadResult(
                success=False,
                error_message=str(e)
            )
            self.data_loaded.emit(result)
            return result
            
        finally:
            self._loading = False
            
    def load_from_dxf(self, dxf_path: str) -> DataLoadResult:
        """从DXF文件加载数据"""
        self.logger.info(f"从DXF文件加载: {dxf_path}", "📂")
        
        try:
            self.loading_started.emit()
            self._loading = True
            
            # 这里应该调用DXFParser，但为了演示，返回错误
            # 实际实现时需要：
            # parser = DXFParser()
            # hole_collection = parser.parse_file(dxf_path)
            
            result = DataLoadResult(
                success=False,
                error_message="DXF加载功能需要集成DXFParser"
            )
            self.data_loaded.emit(result)
            return result
            
        finally:
            self._loading = False
            
    def load_from_json(self, json_path: str) -> DataLoadResult:
        """从JSON文件加载数据"""
        # 类似的实现...
        pass
        
    def clear_cache(self):
        """清除缓存数据"""
        self._cached_data = None
        self.logger.info("缓存已清除", "🗑️")
        
    def validate_data(self, hole_collection: HoleCollection) -> List[str]:
        """验证数据完整性"""
        issues = []
        
        if not hole_collection:
            issues.append("数据集合为空")
            return issues
            
        # 检查孔位ID
        missing_ids = [h for h in hole_collection.holes.values() if not h.hole_id]
        if missing_ids:
            issues.append(f"{len(missing_ids)}个孔位缺少ID")
            
        # 检查坐标范围
        bounds = hole_collection.get_bounds()
        if bounds[0] == bounds[2] or bounds[1] == bounds[3]:
            issues.append("所有孔位在同一条线上")
            
        # 检查重复位置
        positions = set()
        duplicates = 0
        for hole in hole_collection.holes.values():
            pos = (hole.center_x, hole.center_y)
            if pos in positions:
                duplicates += 1
            positions.add(pos)
        if duplicates > 0:
            issues.append(f"{duplicates}个孔位位置重复")
            
        return issues