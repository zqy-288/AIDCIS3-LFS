"""
孔位ID格式转换工具
将所有旧格式的孔位ID统一转换为AC/BC格式
"""

import re
from typing import Optional, Dict, Tuple
from dataclasses import dataclass


@dataclass
class HolePosition:
    """孔位位置信息"""
    side: str  # A或B
    column: int  # 列号
    row: int  # 行号
    
    def to_standard_id(self) -> str:
        """转换为标准格式 AC097R001"""
        return f"{self.side}C{self.column:03d}R{self.row:03d}"


class HoleIDConverter:
    """孔位ID格式转换器"""
    
    # 默认的侧面分配规则
    DEFAULT_SIDE_MAPPING = {
        'A': range(1, 51),   # A侧：列号 1-50
        'B': range(51, 101)  # B侧：列号 51-100
    }
    
    def __init__(self, custom_side_mapping: Optional[Dict[str, range]] = None):
        """
        初始化转换器
        
        Args:
            custom_side_mapping: 自定义的侧面分配规则
        """
        self.side_mapping = custom_side_mapping or self.DEFAULT_SIDE_MAPPING
        
        # 编译正则表达式以提高性能
        self.patterns = {
            'ac_bc': re.compile(r'^([AB])C(\d{3})R(\d{3})$'),  # AC097R001
            'c_r': re.compile(r'^C(\d{3})R(\d{3})$'),          # C001R001
            'r_c': re.compile(r'^R(\d{3})C(\d{3})$'),          # R001C001
            'h_format': re.compile(r'^H(\d+)$'),               # H001
            'grid': re.compile(r'^(\d+),(\d+)$'),              # 1,1
            'simple': re.compile(r'^([A-Z])(\d+)$')            # A1
        }
        
        # H格式到位置的映射（可自定义）
        self.h_format_mapping = self._generate_h_format_mapping()
    
    def _generate_h_format_mapping(self) -> Dict[int, HolePosition]:
        """生成H格式编号到位置的映射"""
        mapping = {}
        h_number = 1
        
        # 按照蛇形路径生成映射
        for col in range(1, 101):
            side = 'A' if col <= 50 else 'B'
            actual_col = col if col <= 50 else col - 50
            
            if actual_col % 2 == 1:  # 奇数列从下往上
                for row in range(1, 9):
                    mapping[h_number] = HolePosition(side, actual_col, row)
                    h_number += 1
            else:  # 偶数列从上往下
                for row in range(8, 0, -1):
                    mapping[h_number] = HolePosition(side, actual_col, row)
                    h_number += 1
        
        return mapping
    
    def _determine_side(self, column: int) -> str:
        """根据列号确定侧面"""
        for side, col_range in self.side_mapping.items():
            if column in col_range:
                return side
        # 默认规则：列号 <= 50 为A侧，> 50 为B侧
        return 'A' if column <= 50 else 'B'
    
    def convert(self, old_id: str) -> str:
        """
        将任意格式的孔位ID转换为标准AC/BC格式
        
        Args:
            old_id: 旧格式的孔位ID
            
        Returns:
            标准格式的孔位ID
            
        Raises:
            ValueError: 如果ID格式无法识别
        """
        # 处理可能的非字符串输入
        if not isinstance(old_id, str):
            old_id = str(old_id)
        old_id = old_id.strip().upper()
        
        # 已经是标准格式
        if match := self.patterns['ac_bc'].match(old_id):
            return old_id
        
        # C001R001 格式
        if match := self.patterns['c_r'].match(old_id):
            col, row = int(match.group(1)), int(match.group(2))
            side = self._determine_side(col)
            # 如果是B侧，需要调整列号
            if side == 'B' and col > 50:
                col = col - 50
            return HolePosition(side, col, row).to_standard_id()
        
        # R001C001 格式
        if match := self.patterns['r_c'].match(old_id):
            row, col = int(match.group(1)), int(match.group(2))
            side = self._determine_side(col)
            # 如果是B侧，需要调整列号
            if side == 'B' and col > 50:
                col = col - 50
            return HolePosition(side, col, row).to_standard_id()
        
        # H001 格式
        if match := self.patterns['h_format'].match(old_id):
            h_number = int(match.group(1))
            if h_number in self.h_format_mapping:
                return self.h_format_mapping[h_number].to_standard_id()
            else:
                raise ValueError(f"H格式编号 {h_number} 超出映射范围")
        
        # 网格格式 1,1
        if match := self.patterns['grid'].match(old_id):
            row, col = int(match.group(1)), int(match.group(2))
            side = self._determine_side(col)
            # 如果是B侧，需要调整列号
            if side == 'B' and col > 50:
                col = col - 50
            return HolePosition(side, col, row).to_standard_id()
        
        # 简单格式 A1
        if match := self.patterns['simple'].match(old_id):
            letter = match.group(1)
            number = int(match.group(2))
            # 将字母转换为列号
            col = ord(letter) - ord('A') + 1
            row = number
            side = self._determine_side(col)
            return HolePosition(side, col, row).to_standard_id()
        
        raise ValueError(f"无法识别的孔位ID格式: {old_id}")
    
    def batch_convert(self, old_ids: list) -> Dict[str, str]:
        """
        批量转换孔位ID
        
        Args:
            old_ids: 旧格式ID列表
            
        Returns:
            旧ID到新ID的映射字典
        """
        mapping = {}
        for old_id in old_ids:
            try:
                new_id = self.convert(old_id)
                mapping[old_id] = new_id
            except ValueError as e:
                print(f"警告: {e}")
                mapping[old_id] = old_id  # 保持原样
        
        return mapping
    
    def parse_id(self, hole_id: str) -> Optional[HolePosition]:
        """
        解析任意格式的孔位ID，返回位置信息
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            HolePosition对象，如果无法解析则返回None
        """
        try:
            # 先转换为标准格式
            standard_id = self.convert(hole_id)
            # 解析标准格式
            match = self.patterns['ac_bc'].match(standard_id)
            if match:
                side, col, row = match.groups()
                return HolePosition(side, int(col), int(row))
        except ValueError:
            pass
        
        return None


# 全局转换器实例
default_converter = HoleIDConverter()


def convert_hole_id(old_id: str) -> str:
    """便捷函数：转换单个孔位ID"""
    return default_converter.convert(old_id)


def batch_convert_hole_ids(old_ids: list) -> Dict[str, str]:
    """便捷函数：批量转换孔位ID"""
    return default_converter.batch_convert(old_ids)


if __name__ == "__main__":
    # 测试代码
    test_ids = [
        "AC097R001",  # 已经是标准格式
        "BC098R002",  # 已经是标准格式
        "C001R001",   # C列R行格式
        "R001C001",   # R行C列格式
        "H001",       # H格式
        "H100",       # H格式
        "1,1",        # 网格格式
        "A1",         # 简单格式
        "C051R001",   # 应该转换为BC001R001
        "C100R008",   # 应该转换为BC050R008
    ]
    
    converter = HoleIDConverter()
    
    print("孔位ID格式转换测试：")
    print("-" * 50)
    for old_id in test_ids:
        try:
            new_id = converter.convert(old_id)
            position = converter.parse_id(new_id)
            print(f"{old_id:12} -> {new_id:12} (侧:{position.side}, 列:{position.column:03d}, 行:{position.row})")
        except ValueError as e:
            print(f"{old_id:12} -> 错误: {e}")