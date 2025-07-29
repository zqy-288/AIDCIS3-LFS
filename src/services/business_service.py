"""
业务服务层
封装所有业务逻辑，减少MainWindow的直接业务依赖
"""

from typing import Optional, Dict, Any, List
from pathlib import Path

# 业务服务接口
class BusinessService:
    """
    统一的业务服务接口
    聚合所有业务功能，提供简洁的API
    """
    
    def __init__(self):
        # 延迟初始化各个服务组件
        self._dxf_parser = None
        self._data_adapter = None
        self._status_manager = None
        self._hole_numbering_service = None
        self._product_manager = None
        self._shared_data_manager = None
        self._path_manager = None
        self.current_product = None  # 当前选择的产品
        
    @property
    def dxf_parser(self):
        """获取DXF解析器（延迟加载）"""
        if self._dxf_parser is None:
            from src.core_business.dxf_parser import DXFParser
            self._dxf_parser = DXFParser()
        return self._dxf_parser
        
    @property
    def data_adapter(self):
        """获取数据适配器（延迟加载）"""
        if self._data_adapter is None:
            from src.core_business.data_adapter import DataAdapter
            self._data_adapter = DataAdapter()
        return self._data_adapter
        
    @property
    def status_manager(self):
        """获取状态管理器（延迟加载）"""
        if self._status_manager is None:
            from src.core_business.models.status_manager import StatusManager
            self._status_manager = StatusManager()
        return self._status_manager
        
    @property
    def hole_numbering_service(self):
        """获取孔位编号服务（延迟加载）"""
        if self._hole_numbering_service is None:
            from src.core_business.hole_numbering_service import HoleNumberingService
            self._hole_numbering_service = HoleNumberingService()
        return self._hole_numbering_service
        
    @property
    def product_manager(self):
        """获取产品管理器（延迟加载）"""
        if self._product_manager is None:
            from src.models.product_model import ProductModelManager
            # 创建ProductModelManager实例
            self._product_manager = ProductModelManager()
        return self._product_manager
        
    @property
    def shared_data_manager(self):
        """获取共享数据管理器（延迟加载）"""
        if self._shared_data_manager is None:
            from src.core.shared_data_manager import SharedDataManager
            self._shared_data_manager = SharedDataManager()
        return self._shared_data_manager
    
    @property
    def path_manager(self):
        """获取路径管理器（延迟加载）"""
        if self._path_manager is None:
            from src.models.data_path_manager import DataPathManager
            self._path_manager = DataPathManager()
        return self._path_manager
        
    # 业务方法封装
    def parse_dxf_file(self, file_path: str) -> Optional[Any]:
        """
        解析DXF文件
        
        Args:
            file_path: DXF文件路径
            
        Returns:
            解析后的孔位集合
        """
        try:
            # 使用正确的方法名 parse_file 而不是 parse
            return self.dxf_parser.parse_file(file_path)
        except Exception as e:
            print(f"Error parsing DXF file: {e}")
            return None
            
    def update_hole_status(self, hole_id: str, status: str) -> bool:
        """
        更新孔位状态
        
        Args:
            hole_id: 孔位ID
            status: 新状态
            
        Returns:
            是否更新成功
        """
        try:
            self.status_manager.update_status(hole_id, status)
            return True
        except Exception as e:
            print(f"Error updating hole status: {e}")
            return False
            
    def get_product_list(self) -> List[str]:
        """获取产品列表"""
        try:
            # 使用get_all_products方法获取所有产品
            products = self.product_manager.get_all_products()
            # 返回产品名称列表
            return [product.model_name for product in products]
        except Exception as e:
            print(f"Error getting product list: {e}")
            return []
        
    def select_product(self, product_name: str) -> bool:
        """选择产品"""
        try:
            # ProductModelManager没有select_product方法，使用get_product_by_name代替
            product = self.product_manager.get_product_by_name(product_name)
            if product:
                # 保存当前选择的产品
                self.current_product = product
                # 可以在shared_data_manager中保存当前产品信息
                if hasattr(self.shared_data_manager, 'set_current_product'):
                    self.shared_data_manager.set_current_product(product)
                
                # 如果产品有关联的DXF文件，自动加载
                if product.dxf_file_path:
                    # 使用路径管理器解析DXF路径
                    resolved_path = self.path_manager.resolve_dxf_path(product.dxf_file_path)
                    if resolved_path and Path(resolved_path).exists():
                        print(f"自动加载产品关联的DXF文件: {resolved_path}")
                        hole_collection = self.parse_dxf_file(resolved_path)
                        if hole_collection:
                            # 应用孔位编号
                            hole_collection = self.apply_hole_numbering(hole_collection, strategy="grid")
                            # 保存到shared_data_manager
                            self.set_hole_collection(hole_collection)
                            print(f"✅ 成功加载 {len(hole_collection.holes)} 个孔位")
                            # 通知数据已加载
                            self.shared_data_manager.data_changed.emit("hole_collection", hole_collection)
                    else:
                        print(f"产品关联的DXF文件不存在: {product.dxf_file_path}")
                
                return True
            else:
                print(f"Product not found: {product_name}")
                return False
        except Exception as e:
            print(f"Error selecting product: {e}")
            return False
            
    def get_hole_collection(self) -> Optional[Any]:
        """获取当前孔位集合"""
        return self.shared_data_manager.get_hole_collection()
        
    def set_hole_collection(self, collection: Any) -> bool:
        """设置孔位集合"""
        try:
            self.shared_data_manager.set_hole_collection(collection)
            return True
        except Exception as e:
            print(f"Error setting hole collection: {e}")
            return False
            
    def apply_hole_numbering(self, collection: Any, strategy: str = "grid") -> Any:
        """
        应用孔位编号
        
        Args:
            collection: 孔位集合
            strategy: 编号策略
            
        Returns:
            编号后的孔位集合
        """
        try:
            # apply_numbering 只接受一个参数
            self.hole_numbering_service.apply_numbering(collection)
            return collection
        except Exception as e:
            print(f"Error applying hole numbering: {e}")
            return collection
            
    def cleanup(self):
        """清理资源"""
        # 清理各个服务的资源
        if self._status_manager:
            self._status_manager.cleanup()
        if self._shared_data_manager:
            self._shared_data_manager.cleanup()
            
            
# 全局业务服务实例
_global_business_service = None


def get_business_service() -> BusinessService:
    """获取全局业务服务实例"""
    global _global_business_service
    if _global_business_service is None:
        _global_business_service = BusinessService()
    return _global_business_service