#!/usr/bin/env python3
"""
产品导入服务
提供从DXF文件导入产品的业务逻辑
"""

import os
from typing import Dict, Optional, Any, List
from datetime import datetime

from PySide6.QtCore import QObject, Signal
from sqlalchemy.orm import Session

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modules.dxf_product_converter import DXFProductConverter
from src.models.product_model import ProductModel, get_product_manager


class ProductImportService(QObject):
    """产品导入服务"""
    
    # 信号
    import_started = Signal(str)  # 导入开始，参数为文件路径
    import_progress = Signal(int)  # 导入进度
    import_completed = Signal(dict)  # 导入完成，返回产品信息
    import_error = Signal(str)  # 导入错误
    
    def __init__(self):
        super().__init__()
        self.converter = DXFProductConverter()
        self.product_manager = get_product_manager()
    
    def import_from_dxf(self, dxf_path: str, **kwargs) -> Optional[ProductModel]:
        """
        从DXF文件导入产品
        
        Args:
            dxf_path: DXF文件路径
            **kwargs: 可选参数，用于覆盖自动生成的值
                - product_name: 产品名称
                - product_code: 产品编号
                - standard_diameter: 标准直径
                - tolerance_upper: 上公差
                - tolerance_lower: 下公差
                - sector_count: 分区数量
                
        Returns:
            创建的产品模型对象，失败返回None
        """
        try:
            self.import_started.emit(dxf_path)
            
            # 步骤1：转换DXF文件
            self.import_progress.emit(20)
            product_info = self.converter.convert_dxf_to_product_info(dxf_path)
            
            if not product_info:
                self.import_error.emit("DXF文件转换失败")
                return None
            
            # 步骤2：应用用户自定义值
            self.import_progress.emit(40)
            self._apply_user_overrides(product_info, kwargs)
            
            # 步骤3：检查产品是否已存在
            self.import_progress.emit(60)
            existing_product = self._check_existing_product(product_info)
            
            if existing_product and not kwargs.get('force_update', False):
                self.import_error.emit(f"产品编号 {product_info['product_code']} 已存在")
                return None
            
            # 步骤4：创建或更新产品
            self.import_progress.emit(80)
            product = self._create_or_update_product(product_info, existing_product)
            
            # 步骤5：完成
            self.import_progress.emit(100)
            self.import_completed.emit({
                'product': product,
                'product_info': product_info,
                'validation': self.converter.validate_product_info(product_info)
            })
            
            return product
            
        except Exception as e:
            error_msg = f"导入失败: {str(e)}"
            self.import_error.emit(error_msg)
            return None
    
    def preview_dxf_import(self, dxf_path: str) -> Optional[Dict[str, Any]]:
        """
        预览DXF导入结果，不执行实际导入
        
        Returns:
            预览信息字典
        """
        try:
            # 转换DXF
            product_info = self.converter.convert_dxf_to_product_info(dxf_path)
            
            if not product_info:
                return None
            
            # 验证信息
            validation = self.converter.validate_product_info(product_info)
            
            # 检查是否已存在
            existing_product = self._check_existing_product(product_info)
            
            return {
                'product_info': product_info,
                'validation': validation,
                'existing_product': existing_product is not None,
                'existing_product_id': existing_product.id if existing_product else None
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _apply_user_overrides(self, product_info: Dict[str, Any], overrides: Dict[str, Any]):
        """应用用户自定义值"""
        # 可覆盖的字段
        override_fields = [
            'product_name', 'product_code', 'standard_diameter',
            'tolerance_upper', 'tolerance_lower', 'sector_count',
            'material', 'thickness', 'weight', 'manufacturer',
            'specifications', 'remarks'
        ]
        
        for field in override_fields:
            if field in overrides and overrides[field] is not None:
                # 特殊处理标准直径
                if field == 'standard_diameter':
                    product_info['hole_diameter'] = overrides[field]
                else:
                    product_info[field] = overrides[field]
    
    def _check_existing_product(self, product_info: Dict[str, Any]) -> Optional[ProductModel]:
        """检查产品是否已存在"""
        # 按产品编号查找
        if 'product_code' in product_info:
            products = self.product_manager.search_products(product_info['product_code'])
            
            for product in products:
                if hasattr(product, 'model_code') and product.model_code == product_info['product_code']:
                    return product
        
        # 按产品名称查找
        if 'product_name' in product_info:
            products = self.product_manager.search_products(product_info['product_name'])
            
            for product in products:
                if hasattr(product, 'model_name') and product.model_name == product_info['product_name']:
                    return product
        
        return None
    
    def _create_or_update_product(self, product_info: Dict[str, Any], 
                                existing_product: Optional[ProductModel] = None) -> ProductModel:
        """创建或更新产品"""
        # 准备产品数据
        product_data = {
            'model_name': product_info['product_name'],
            'model_code': product_info.get('product_code'),
            'standard_diameter': product_info['hole_diameter'],
            'tolerance_upper': product_info.get('tolerance_upper', 0.1),
            'tolerance_lower': product_info.get('tolerance_lower', -0.1),
            'description': self._generate_description(product_info),
            'dxf_file_path': product_info['dxf_file_path'],
            'sector_count': product_info.get('sector_count', 4),  # 默认使用4扇形
            'is_active': True
        }
        
        if existing_product:
            # 更新现有产品
            for key, value in product_data.items():
                if value is not None:
                    setattr(existing_product, key, value)
            
            existing_product.updated_at = datetime.now()
            self.product_manager.session.commit()
            
            return existing_product
        else:
            # 创建新产品
            return self.product_manager.create_product(**product_data)
    
    def _generate_description(self, product_info: Dict[str, Any]) -> str:
        """生成产品描述"""
        parts = []
        
        # 基本信息
        parts.append(f"从DXF文件导入: {os.path.basename(product_info['dxf_file_path'])}")
        parts.append(f"孔位数量: {product_info['hole_count']}")
        parts.append(f"孔径: {product_info['hole_diameter']:.2f}mm")
        parts.append(f"形状: {product_info['shape']}")
        
        # 尺寸信息
        parts.append(f"外形尺寸: {product_info['outer_diameter']:.1f} x {product_info['inner_diameter']:.1f}mm")
        
        # 完整性信息
        validation = self.converter.validate_product_info(product_info)
        parts.append(f"数据完整性: {validation['completeness_score']}%")
        
        # 缺失信息
        if validation['missing_important']:
            parts.append(f"缺失信息: {', '.join(validation['missing_important'])}")
        
        return '\n'.join(parts)
    
    def batch_import_from_directory(self, directory: str, pattern: str = "*.dxf") -> List[Dict[str, Any]]:
        """
        批量导入目录中的DXF文件
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            
        Returns:
            导入结果列表
        """
        results = []
        dxf_files = list(Path(directory).glob(pattern))
        
        for i, dxf_file in enumerate(dxf_files):
            try:
                # 发送总体进度
                overall_progress = int((i / len(dxf_files)) * 100)
                self.import_progress.emit(overall_progress)
                
                # 导入单个文件
                product = self.import_from_dxf(str(dxf_file))
                
                results.append({
                    'file': str(dxf_file),
                    'success': product is not None,
                    'product': product,
                    'error': None
                })
                
            except Exception as e:
                results.append({
                    'file': str(dxf_file),
                    'success': False,
                    'product': None,
                    'error': str(e)
                })
        
        return results