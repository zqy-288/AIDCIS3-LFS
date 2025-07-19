"""
产品型号数据模型
支持产品型号的管理，包括型号名称、标准直径、公差范围等信息
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import json
import os

Base = declarative_base()

class ProductModel(Base):
    """产品型号数据模型"""
    __tablename__ = 'product_models'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(100), nullable=False, unique=True, comment='产品型号名称')
    model_code = Column(String(50), nullable=True, comment='产品型号代码')
    standard_diameter = Column(Float, nullable=False, comment='标准直径(mm)')
    tolerance_upper = Column(Float, nullable=False, comment='公差上限(mm)')
    tolerance_lower = Column(Float, nullable=False, comment='公差下限(mm)')
    description = Column(Text, nullable=True, comment='产品描述')
    is_active = Column(Boolean, default=True, comment='是否启用')
    dxf_file_path = Column(String(500), nullable=True, comment='关联的DXF文件路径')
    sector_count = Column(Integer, default=4, nullable=False, comment='扇形分区数量(2-12)')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def __repr__(self):
        return f"<ProductModel(id={self.id}, model_name='{self.model_name}', standard_diameter={self.standard_diameter})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'model_name': self.model_name,
            'model_code': self.model_code,
            'standard_diameter': self.standard_diameter,
            'tolerance_upper': self.tolerance_upper,
            'tolerance_lower': self.tolerance_lower,
            'description': self.description,
            'is_active': self.is_active,
            'dxf_file_path': self.dxf_file_path,
            'sector_count': self.sector_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def tolerance_range(self):
        """获取公差范围文本"""
        return f"+{self.tolerance_upper:.3f}/-{abs(self.tolerance_lower):.3f}"
    
    @property
    def diameter_range(self):
        """获取直径范围"""
        return (
            self.standard_diameter + self.tolerance_lower,
            self.standard_diameter + self.tolerance_upper
        )
    
    def is_diameter_in_range(self, diameter):
        """检查直径是否在公差范围内"""
        min_diameter, max_diameter = self.diameter_range
        return min_diameter <= diameter <= max_diameter

class ProductModelManager:
    """产品型号管理器"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            # 默认数据库路径
            db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'product_models.db')
        
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # 初始化默认数据
        self._init_default_data()
    
    def _init_default_data(self):
        """初始化默认产品型号数据"""
        if self.session.query(ProductModel).count() == 0:
            default_products = [
                {
                    'model_name': 'TP-001',
                    'model_code': 'TP001',
                    'standard_diameter': 10.0,
                    'tolerance_upper': 0.05,
                    'tolerance_lower': -0.05,
                    'description': '标准孔径10mm产品型号'
                },
                {
                    'model_name': 'TP-002',
                    'model_code': 'TP002',
                    'standard_diameter': 12.0,
                    'tolerance_upper': 0.08,
                    'tolerance_lower': -0.08,
                    'description': '标准孔径12mm产品型号'
                },
                {
                    'model_name': 'TP-003',
                    'model_code': 'TP003',
                    'standard_diameter': 15.0,
                    'tolerance_upper': 0.10,
                    'tolerance_lower': -0.10,
                    'description': '标准孔径15mm产品型号'
                }
            ]
            
            for product_data in default_products:
                product = ProductModel(**product_data)
                self.session.add(product)
            
            self.session.commit()
    
    def get_all_products(self, active_only=True):
        """获取所有产品型号"""
        query = self.session.query(ProductModel)
        if active_only:
            query = query.filter(ProductModel.is_active == True)
        return query.order_by(ProductModel.model_name).all()
    
    def get_product_by_id(self, product_id):
        """根据ID获取产品型号"""
        return self.session.query(ProductModel).filter(ProductModel.id == product_id).first()
    
    def get_product_by_name(self, model_name):
        """根据名称获取产品型号"""
        return self.session.query(ProductModel).filter(ProductModel.model_name == model_name).first()
    
    def create_product(self, model_name, standard_diameter, tolerance_upper, tolerance_lower, 
                      model_code=None, description=None, dxf_file_path=None, sector_count=4):
        """创建新产品型号"""
        # 验证输入参数
        if not model_name or not model_name.strip():
            raise ValueError("产品型号名称不能为空")
        if standard_diameter <= 0:
            raise ValueError("标准孔径必须大于0")
        
        # 检查型号名称是否已存在
        existing = self.get_product_by_name(model_name)
        if existing:
            raise ValueError(f"产品型号 '{model_name}' 已存在")
        
        product = ProductModel(
            model_name=model_name,
            model_code=model_code,
            standard_diameter=standard_diameter,
            tolerance_upper=tolerance_upper,
            tolerance_lower=tolerance_lower,
            description=description,
            dxf_file_path=dxf_file_path,
            sector_count=sector_count
        )
        
        self.session.add(product)
        self.session.commit()
        return product
    
    def update_product(self, product_id, **kwargs):
        """更新产品型号"""
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"产品型号 ID {product_id} 不存在")
        
        # 检查型号名称是否重复
        if 'model_name' in kwargs:
            existing = self.get_product_by_name(kwargs['model_name'])
            if existing and existing.id != product_id:
                raise ValueError(f"产品型号 '{kwargs['model_name']}' 已存在")
        
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        
        product.updated_at = datetime.now()
        self.session.commit()
        return product
    
    def delete_product(self, product_id):
        """删除产品型号"""
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"产品型号 ID {product_id} 不存在")
        
        self.session.delete(product)
        self.session.commit()
        return True
    
    def activate_product(self, product_id):
        """激活产品型号"""
        return self.update_product(product_id, is_active=True)
    
    def deactivate_product(self, product_id):
        """停用产品型号"""
        return self.update_product(product_id, is_active=False)
    
    def search_products(self, keyword):
        """搜索产品型号"""
        query = self.session.query(ProductModel).filter(
            (ProductModel.model_name.contains(keyword)) |
            (ProductModel.model_code.contains(keyword)) |
            (ProductModel.description.contains(keyword))
        ).filter(ProductModel.is_active == True)
        return query.order_by(ProductModel.model_name).all()
    
    def get_products_by_diameter_range(self, min_diameter, max_diameter):
        """根据直径范围获取产品型号"""
        query = self.session.query(ProductModel).filter(
            ProductModel.standard_diameter >= min_diameter,
            ProductModel.standard_diameter <= max_diameter,
            ProductModel.is_active == True
        )
        return query.order_by(ProductModel.standard_diameter).all()
    
    def close(self):
        """关闭数据库连接"""
        self.session.close()

# 单例实例
_product_manager = None

def get_product_manager():
    """获取产品型号管理器单例"""
    global _product_manager
    if _product_manager is None:
        _product_manager = ProductModelManager()
    return _product_manager