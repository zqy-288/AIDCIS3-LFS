#!/usr/bin/env python3
"""
DXF文件到产品信息转换器
用于从DXF文件自动提取产品信息并创建产品记录
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from PySide6.QtCore import QObject, Signal

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.services.parsers.dxf_parser import DXFParser
from src.shared.models.hole_data import HoleCollection


class DXFToProductConverter(QObject):
    """DXF到产品信息转换器"""
    
    # 信号
    conversion_progress = Signal(int)  # 转换进度
    conversion_completed = Signal(dict)  # 转换完成，返回产品信息
    conversion_error = Signal(str)  # 转换错误
    
    def __init__(self):
        super().__init__()
        self.parser = DXFParser()
        
    def extract_product_name(self, file_path: str) -> str:
        """从文件路径提取产品名称"""
        # 获取文件名（不含扩展名）
        file_name = Path(file_path).stem
        
        # 移除常见的版本号、日期等后缀
        # 例如: "东重管板_v1.2" -> "东重管板"
        name = re.sub(r'[_-]v?\d+(\.\d+)*$', '', file_name)
        name = re.sub(r'[_-]\d{8}$', '', name)  # 移除日期后缀
        
        return name
    
    def generate_product_code(self, product_name: str) -> str:
        """生成产品编号"""
        # 提取名称中的字母作为前缀
        prefix = ''.join(re.findall(r'[A-Za-z]', product_name))
        if not prefix:
            prefix = 'PROD'
        
        # 添加时间戳
        timestamp = datetime.now().strftime('%Y%m%d%H%M')
        return f"{prefix.upper()}-{timestamp}"
    
    def determine_product_shape(self, hole_collection: HoleCollection) -> str:
        """根据孔位分布判断产品形状"""
        if not hole_collection.holes:
            return "unknown"
        
        # 获取边界信息
        bounds = hole_collection.get_bounds()
        width = bounds['width']
        height = bounds['height']
        
        # 判断形状
        aspect_ratio = width / height if height > 0 else 1
        
        if 0.9 <= aspect_ratio <= 1.1:
            return "circular"  # 圆形
        elif 0.5 <= aspect_ratio <= 2.0:
            return "elliptical"  # 椭圆形
        else:
            return "rectangular"  # 矩形
    
    def convert_dxf_to_product_info(self, dxf_path: str) -> Optional[Dict[str, Any]]:
        """
        将DXF文件转换为产品信息
        
        Args:
            dxf_path: DXF文件路径
            
        Returns:
            产品信息字典，包含所有可提取的信息，缺失信息为None
        """
        try:
            self.conversion_progress.emit(10)
            
            # 解析DXF文件
            hole_collection = self.parser.parse_file(dxf_path)
            if not hole_collection:
                self.conversion_error.emit("DXF文件解析失败")
                return None
            
            self.conversion_progress.emit(50)
            
            # 获取解析信息
            parse_info = self.parser.get_parse_info() if hasattr(self.parser, 'get_parse_info') else {}
            
            # 提取产品名称
            product_name = self.extract_product_name(dxf_path)
            
            # 生成产品编号
            product_code = self.generate_product_code(product_name)
            
            # 获取文件信息
            file_size = os.path.getsize(dxf_path) / (1024 * 1024)  # MB
            
            # 获取孔位统计信息
            total_holes = len(hole_collection.holes)
            
            # 计算最常见的半径
            if hole_collection.holes:
                radiuses = [hole.radius for hole in hole_collection.holes.values()]
                from collections import Counter
                radius_counter = Counter(radiuses)
                most_common_radius = radius_counter.most_common(1)[0][0]
            else:
                most_common_radius = 8.865
            
            # 判断产品形状
            shape = self.determine_product_shape(hole_collection)
            
            # 获取边界信息
            bounds = hole_collection.get_bounds()
            
            self.conversion_progress.emit(80)
            
            # 构建产品信息
            product_info = {
                # 基本信息（从DXF提取）
                'product_code': product_code,
                'product_name': product_name,
                'hole_count': total_holes,
                'hole_diameter': most_common_radius * 2,  # 直径 = 半径 * 2
                'shape': shape,
                'outer_diameter': bounds['width'],
                'inner_diameter': bounds['height'],
                
                # 文件相关信息
                'dxf_file_path': dxf_path,
                'dxf_file_size': file_size,
                'dxf_version': 'Unknown',  # DXFParser不提供版本信息
                
                # 分区配置（默认值）
                'sector_count': 4,  # 默认4分区
                
                # 缺失信息（置空）
                'material': None,
                'thickness': None,
                'weight': None,
                'manufacturer': None,
                'specifications': None,
                'remarks': None,
                
                # 元数据
                'created_from_dxf': True,
                'import_date': datetime.now(),
                'data_completeness': 'partial',  # 标记为部分数据
                
                # 原始解析信息（用于后续处理）
                '_hole_collection': hole_collection
            }
            
            self.conversion_progress.emit(100)
            self.conversion_completed.emit(product_info)
            
            return product_info
            
        except Exception as e:
            error_msg = f"转换失败: {str(e)}"
            self.conversion_error.emit(error_msg)
            return None
    
    def validate_product_info(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证产品信息完整性
        
        Returns:
            验证结果，包含是否有效和缺失字段列表
        """
        # 必需字段
        required_fields = ['product_code', 'product_name', 'hole_count']
        
        # 可选但重要的字段
        important_fields = ['hole_diameter', 'shape', 'material', 'thickness']
        
        missing_required = []
        missing_important = []
        
        for field in required_fields:
            if not product_info.get(field):
                missing_required.append(field)
        
        for field in important_fields:
            if product_info.get(field) is None:
                missing_important.append(field)
        
        return {
            'is_valid': len(missing_required) == 0,
            'missing_required': missing_required,
            'missing_important': missing_important,
            'completeness_score': self._calculate_completeness_score(product_info)
        }
    
    def _calculate_completeness_score(self, product_info: Dict[str, Any]) -> float:
        """计算数据完整性评分（0-100）"""
        # 定义字段权重
        field_weights = {
            'product_code': 10,
            'product_name': 10,
            'hole_count': 10,
            'hole_diameter': 8,
            'shape': 8,
            'outer_diameter': 6,
            'inner_diameter': 6,
            'material': 8,
            'thickness': 8,
            'weight': 4,
            'manufacturer': 4,
            'specifications': 4,
            'dxf_file_path': 10,
            'sector_count': 4
        }
        
        total_weight = sum(field_weights.values())
        achieved_weight = 0
        
        for field, weight in field_weights.items():
            if product_info.get(field) is not None:
                achieved_weight += weight
        
        return round((achieved_weight / total_weight) * 100, 1)