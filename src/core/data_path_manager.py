"""
数据路径管理器
统一管理AIDCIS3系统的所有数据存储路径
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class PathInfo:
    """路径信息类"""
    path: str
    exists: bool
    size: int = 0
    created_at: Optional[datetime] = None


class DataPathManager:
    """数据路径管理器"""
    
    def __init__(self, data_root: str = None):
        """
        初始化路径管理器
        
        Args:
            data_root: 数据根目录，默认为项目根目录下的Data文件夹
        """
        if data_root is None:
            # 获取项目根目录
            project_root = Path(__file__).parent.parent.parent
            data_root = project_root / "Data"
        
        self.data_root = Path(data_root)
        self.ensure_data_root()
    
    def ensure_data_root(self):
        """确保数据根目录存在"""
        self.data_root.mkdir(exist_ok=True)
        
        # 确保基本子目录存在
        products_dir = self.data_root / "Products"
        products_dir.mkdir(exist_ok=True)
    
    # ============ 产品相关路径 ============
    
    def get_product_root_path(self) -> str:
        """获取产品根目录路径"""
        return str(self.data_root / "Products")
    
    def get_product_path(self, product_id: str) -> str:
        """获取产品目录路径"""
        return str(self.data_root / "Products" / product_id)
    
    def get_product_info_path(self, product_id: str) -> str:
        """获取产品信息文件路径"""
        return str(self.data_root / "Products" / product_id / "product_info.json")
    
    def get_product_dxf_dir(self, product_id: str) -> str:
        """获取产品DXF目录路径"""
        return str(self.data_root / "Products" / product_id / "dxf")
    
    def get_product_dxf_path(self, product_id: str, filename: str = "original.dxf") -> str:
        """获取产品DXF文件路径"""
        return str(self.data_root / "Products" / product_id / "dxf" / filename)
    
    def resolve_dxf_path(self, dxf_path: str) -> str:
        """
        解析DXF文件路径
        
        Args:
            dxf_path: DXF文件路径（可能是绝对路径或相对路径）
            
        Returns:
            绝对路径
        """
        if not dxf_path:
            return ""
            
        # 如果是绝对路径且存在，直接返回
        if os.path.isabs(dxf_path) and os.path.exists(dxf_path):
            return dxf_path
            
        # 尝试作为相对于项目根目录的路径
        project_root = self.data_root.parent  # data_root是项目根目录下的Data，所以parent就是项目根目录
        abs_path_from_root = project_root / dxf_path
        if abs_path_from_root.exists():
            return str(abs_path_from_root)
            
        # 尝试作为相对于data_root的路径
        abs_path_from_data = self.data_root / dxf_path
        if abs_path_from_data.exists():
            return str(abs_path_from_data)
            
        # 如果都不存在，返回相对于项目根目录的绝对路径（便于调试）
        return str(abs_path_from_root)
    
    # ============ 检测批次相关路径 ============
    
    def get_inspections_dir(self, product_id: str) -> str:
        """获取产品检测目录（兼容方法）"""
        return self.get_inspection_batches_dir(product_id)
    
    def get_inspection_batches_dir(self, product_id: str) -> str:
        """获取产品检测批次记录目录"""
        return str(self.data_root / "Products" / product_id / "InspectionBatches")
    
    def get_inspection_batch_path(self, product_id: str, batch_id: str) -> str:
        """获取检测批次目录路径"""
        return str(self.data_root / "Products" / product_id / "InspectionBatches" / batch_id)
    
    def get_batch_info_path(self, product_id: str, batch_id: str) -> str:
        """获取批次信息文件路径"""
        return str(self.data_root / "Products" / product_id / "InspectionBatches" / batch_id / "batch_info.json")
    
    def get_batch_summary_path(self, product_id: str, batch_id: str) -> str:
        """获取批次汇总文件路径"""
        return str(self.data_root / "Products" / product_id / "InspectionBatches" / batch_id / "batch_summary.json")
    
    def get_data_batches_dir(self, product_id: str, batch_id: str) -> str:
        """获取数据批次目录路径（BatchDataManager使用）"""
        return str(self.data_root / "Products" / product_id / "InspectionBatches" / batch_id / "data_batches")
    
    # ============ 孔位检测结果路径 ============
    
    def get_hole_results_dir(self, product_id: str, batch_id: str) -> str:
        """获取孔位检测结果目录"""
        return str(self.data_root / "Products" / product_id / "InspectionBatches" / batch_id / "HoleResults")
    
    def get_holes_dir(self, product_id: str, batch_id: str) -> str:
        """获取孔位目录（兼容旧版本）"""
        return self.get_hole_results_dir(product_id, batch_id)
    
    def get_hole_path(self, product_id: str, batch_id: str, hole_id: str) -> str:
        """获取单个孔位目录路径"""
        return str(self.data_root / "Products" / product_id / "InspectionBatches" / batch_id / "HoleResults" / hole_id)
    
    def get_hole_bisdm_dir(self, product_id: str, batch_id: str, hole_id: str) -> str:
        """获取孔位BISDM(内窥镜)目录路径"""
        return str(self.data_root / "Products" / product_id / "InspectionBatches" / batch_id / "HoleResults" / hole_id / "BISDM")
    
    def get_hole_ccidm_dir(self, product_id: str, batch_id: str, hole_id: str) -> str:
        """获取孔位CCIDM(孔径检测)目录路径"""
        return str(self.data_root / "Products" / product_id / "InspectionBatches" / batch_id / "HoleResults" / hole_id / "CCIDM")
    
    def get_hole_bisdm_result_dir(self, product_id: str, batch_id: str, hole_id: str) -> str:
        """获取BISDM结果目录路径"""
        return str(self.data_root / "Products" / product_id / "InspectionBatches" / batch_id / "HoleResults" / hole_id / "BISDM" / "result")
    
    def get_hole_panorama_path(self, product_id: str, batch_id: str, hole_id: str) -> str:
        """获取孔位全景图路径"""
        return str(self.data_root / "Products" / product_id / "InspectionBatches" / batch_id / "HoleResults" / hole_id / "BISDM" / "panorama.png")
    
    def get_hole_measurement_path(self, product_id: str, batch_id: str, hole_id: str, 
                                 timestamp: str = None) -> str:
        """获取孔位测量数据路径"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%a_%b_%d_%H_%M_%S_%Y")
        filename = f"measurement_data_{timestamp}.csv"
        return str(self.data_root / "Products" / product_id / "Inspections" / batch_id / "Holes" / hole_id / "CCIDM" / filename)
    
    # ============ 兼容性方法（支持旧格式） ============
    
    def get_legacy_hole_path(self, hole_id: str) -> str:
        """获取遗留格式的孔位路径 (如: C001R001)"""
        return str(self.data_root / hole_id)
    
    def get_legacy_bisdm_path(self, hole_id: str) -> str:
        """获取遗留格式的BISDM路径"""
        return str(self.data_root / hole_id / "BISDM")
    
    def get_legacy_ccidm_path(self, hole_id: str) -> str:
        """获取遗留格式的CCIDM路径"""
        return str(self.data_root / hole_id / "CCIDM")
    
    # ============ 路径创建和管理 ============
    
    def create_product_structure(self, product_id: str) -> Dict[str, str]:
        """创建产品目录结构"""
        paths = {
            'product_dir': self.get_product_path(product_id),
            'dxf_dir': self.get_product_dxf_dir(product_id),
            'inspections_dir': self.get_inspections_dir(product_id)
        }
        
        for path in paths.values():
            Path(path).mkdir(parents=True, exist_ok=True)
        
        return paths
    
    def create_inspection_structure(self, product_id: str, batch_id: str) -> Dict[str, str]:
        """创建检测批次目录结构"""
        paths = {
            'batch_dir': self.get_inspection_batch_path(product_id, batch_id),
            'holes_dir': self.get_holes_dir(product_id, batch_id)
        }
        
        for path in paths.values():
            Path(path).mkdir(parents=True, exist_ok=True)
        
        return paths
    
    def create_hole_structure(self, product_id: str, batch_id: str, hole_id: str) -> Dict[str, str]:
        """创建孔位目录结构"""
        paths = {
            'hole_dir': self.get_hole_path(product_id, batch_id, hole_id),
            'bisdm_dir': self.get_hole_bisdm_dir(product_id, batch_id, hole_id),
            'bisdm_result_dir': self.get_hole_bisdm_result_dir(product_id, batch_id, hole_id),
            'ccidm_dir': self.get_hole_ccidm_dir(product_id, batch_id, hole_id)
        }
        
        for path in paths.values():
            Path(path).mkdir(parents=True, exist_ok=True)
        
        return paths
    
    # ============ 文件信息查询 ============
    
    def get_path_info(self, path: str) -> PathInfo:
        """获取路径信息"""
        path_obj = Path(path)
        exists = path_obj.exists()
        size = 0
        created_at = None
        
        if exists:
            if path_obj.is_file():
                size = path_obj.stat().st_size
            elif path_obj.is_dir():
                size = sum(f.stat().st_size for f in path_obj.rglob('*') if f.is_file())
            
            created_at = datetime.fromtimestamp(path_obj.stat().st_ctime)
        
        return PathInfo(
            path=str(path_obj),
            exists=exists,
            size=size,
            created_at=created_at
        )
    
    def list_products(self) -> List[str]:
        """列出所有产品ID"""
        products_dir = Path(self.get_product_root_path())
        if not products_dir.exists():
            return []
        
        return [d.name for d in products_dir.iterdir() if d.is_dir()]
    
    def list_inspection_batches(self, product_id: str) -> List[str]:
        """列出产品的所有检测批次"""
        inspections_dir = Path(self.get_inspections_dir(product_id))
        if not inspections_dir.exists():
            return []
        
        return [d.name for d in inspections_dir.iterdir() if d.is_dir()]
    
    def list_holes(self, product_id: str, batch_id: str) -> List[str]:
        """列出检测批次的所有孔位"""
        holes_dir = Path(self.get_holes_dir(product_id, batch_id))
        if not holes_dir.exists():
            return []
        
        return [d.name for d in holes_dir.iterdir() if d.is_dir()]
    
    # ============ 数据迁移和兼容性 ============
    
    def migrate_legacy_data(self, hole_id: str, product_id: str, batch_id: str) -> bool:
        """迁移遗留数据到新格式"""
        try:
            legacy_path = Path(self.get_legacy_hole_path(hole_id))
            if not legacy_path.exists():
                return False
            
            # 创建新的目录结构
            self.create_hole_structure(product_id, batch_id, hole_id)
            
            # 迁移BISDM数据
            legacy_bisdm = legacy_path / "BISDM"
            if legacy_bisdm.exists():
                new_bisdm = Path(self.get_hole_bisdm_dir(product_id, batch_id, hole_id))
                import shutil
                shutil.copytree(legacy_bisdm, new_bisdm / "legacy", dirs_exist_ok=True)
            
            # 迁移CCIDM数据
            legacy_ccidm = legacy_path / "CCIDM"
            if legacy_ccidm.exists():
                new_ccidm = Path(self.get_hole_ccidm_dir(product_id, batch_id, hole_id))
                import shutil
                shutil.copytree(legacy_ccidm, new_ccidm / "legacy", dirs_exist_ok=True)
            
            return True
            
        except Exception as e:
            print(f"迁移数据失败: {hole_id} -> {product_id}/{batch_id}, 错误: {e}")
            return False
    
    # ============ 工具方法 ============
    
    def generate_batch_id(self) -> str:
        """生成检测批次ID"""
        import random
        now = datetime.now()
        # 添加微秒和随机数确保唯一性
        microsecond_part = str(now.microsecond)[:3]  # 取前3位微秒
        random_part = str(random.randint(100, 999))
        return now.strftime(f"%Y%m%d_%H%M%S_{microsecond_part}{random_part}")
    
    def is_valid_product_id(self, product_id: str) -> bool:
        """验证产品ID是否有效"""
        # 产品ID不能包含路径分隔符和特殊字符
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        return product_id and not any(char in product_id for char in invalid_chars)
    
    def cleanup_empty_directories(self, root_path: str = None):
        """清理空目录"""
        if root_path is None:
            root_path = self.data_root
        
        root = Path(root_path)
        for path in sorted(root.rglob('*'), reverse=True):
            if path.is_dir() and not any(path.iterdir()):
                try:
                    path.rmdir()
                except OSError:
                    pass  # 目录可能不为空或权限不足


# 单例实例
_path_manager = None

def get_data_path_manager() -> DataPathManager:
    """获取数据路径管理器单例"""
    global _path_manager
    if _path_manager is None:
        _path_manager = DataPathManager()
    return _path_manager