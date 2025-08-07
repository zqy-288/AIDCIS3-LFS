"""
管孔ID映射工具
处理新旧管孔ID格式之间的转换
使用统一的AC/BC格式
"""

from typing import Dict, List, Optional
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.shared.utils.converters import HoleIDConverter

class HoleIdMapper:
    """管孔ID映射器 - 使用新的统一转换器"""
    
    def __init__(self):
        self.converter = HoleIDConverter()
    
    @classmethod
    def old_to_new(cls, old_id: str) -> str:
        """
        将旧格式ID转换为新格式ID (AC/BC格式)
        
        Args:
            old_id: 旧格式ID (如 H00001, C001R001, R001C001)
            
        Returns:
            str: 新格式ID (如 AC001R001, BC001R001)
        """
        converter = HoleIDConverter()
        try:
            return converter.convert(old_id)
        except ValueError:
            # 如果无法转换，返回原ID
            return old_id
    
    @classmethod
    def new_to_old(cls, new_id: str) -> str:
        """
        将新格式ID转换为旧格式ID
        注意：这个方法已经废弃，因为我们不再需要转换回旧格式
        
        Args:
            new_id: 新格式ID (如 AC001R001)
            
        Returns:
            str: 返回原ID（不再支持反向转换）
        """
        # 不再支持反向转换
        return new_id
    
    @classmethod
    def convert_list_old_to_new(cls, old_ids: List[str]) -> List[str]:
        """
        批量转换旧格式ID列表为新格式
        
        Args:
            old_ids: 旧格式ID列表
            
        Returns:
            List[str]: 新格式ID列表
        """
        return [cls.old_to_new(old_id) for old_id in old_ids]
    
    @classmethod
    def convert_list_new_to_old(cls, new_ids: List[str]) -> List[str]:
        """
        批量转换新格式ID列表为旧格式
        
        Args:
            new_ids: 新格式ID列表
            
        Returns:
            List[str]: 旧格式ID列表
        """
        return [cls.new_to_old(new_id) for new_id in new_ids]
    
    @classmethod
    def is_old_format(cls, hole_id: str) -> bool:
        """
        判断是否为旧格式ID
        
        Args:
            hole_id: 管孔ID
            
        Returns:
            bool: 是否为旧格式
        """
        return hole_id.startswith('H') and hole_id in cls.OLD_TO_NEW_MAPPING
    
    @classmethod
    def is_new_format(cls, hole_id: str) -> bool:
        """
        判断是否为新格式ID
        
        Args:
            hole_id: 管孔ID
            
        Returns:
            bool: 是否为新格式
        """
        return hole_id.startswith('R') and 'C' in hole_id and hole_id in cls.NEW_TO_OLD_MAPPING
    
    @classmethod
    def get_all_new_ids(cls) -> List[str]:
        """
        获取所有新格式ID
        
        Returns:
            List[str]: 所有新格式ID列表
        """
        return list(cls.NEW_TO_OLD_MAPPING.keys())
    
    @classmethod
    def get_all_old_ids(cls) -> List[str]:
        """
        获取所有旧格式ID
        
        Returns:
            List[str]: 所有旧格式ID列表
        """
        return list(cls.OLD_TO_NEW_MAPPING.keys())
    
    @classmethod
    def parse_new_id(cls, new_id: str) -> Optional[Dict[str, int]]:
        """
        解析新格式ID，提取行列信息
        
        Args:
            new_id: 新格式ID (如 R001C001)
            
        Returns:
            Optional[Dict[str, int]]: 包含row和col的字典，解析失败返回None
        """
        try:
            if not new_id.startswith('R') or 'C' not in new_id:
                return None
            
            # 分割R和C部分
            parts = new_id[1:].split('C')  # 去掉R前缀，按C分割
            if len(parts) != 2:
                return None
            
            row = int(parts[0])  # R后面的数字
            col = int(parts[1])  # C后面的数字
            
            return {'row': row, 'col': col}
            
        except (ValueError, IndexError):
            return None
    
    @classmethod
    def estimate_position_from_new_id(cls, new_id: str) -> tuple[float, float]:
        """
        根据新格式ID估算坐标位置
        
        Args:
            new_id: 新格式ID (如 R001C001)
            
        Returns:
            tuple[float, float]: (x, y) 坐标
        """
        parsed = cls.parse_new_id(new_id)
        if not parsed:
            return 0.0, 0.0
        
        row = parsed['row']
        col = parsed['col']
        
        # 估算坐标（基于标准间距）
        start_x, start_y = -140, -100
        spacing_x, spacing_y = 40, 35
        
        # 注意：行列从1开始编号
        x = start_x + (col - 1) * spacing_x
        y = start_y + (row - 1) * spacing_y
        
        return x, y
