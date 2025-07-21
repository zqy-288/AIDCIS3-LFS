"""
蛇形双孔更新模拟逻辑
实现按列蛇形遍历，双孔并行检测，边界处理的模拟进度功能
"""

from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import logging

@dataclass
class HolePosition:
    """孔位位置数据类"""
    row: int
    col: int
    
    @property
    def hole_id(self) -> str:
        return f"C{self.col:03d}R{self.row:03d}"
    
    def __str__(self) -> str:
        return self.hole_id


class SnakePatternSimulation:
    """蛇形双孔更新模拟类"""
    
    def __init__(self, hole_collection):
        self.logger = logging.getLogger(__name__)
        self.hole_collection = hole_collection
        
        # 分析数据结构，获取每列的行范围
        self.column_ranges = self._analyze_column_ranges()
        
        # 初始化当前位置
        self.current_col = 1
        self.current_row = 1
        self.is_single_mode = False
        
        # 定义配对间隔
        self.PAIR_INTERVAL = 4
        
        # 时间设置
        self.BLUE_DISPLAY_TIME = 9500  # 9.5秒蓝色显示时间(毫秒)
        self.UPDATE_DELAY = 500        # 0.5秒后更新颜色(毫秒)
        
    def _analyze_column_ranges(self) -> Dict[int, Tuple[int, int]]:
        """分析每列的行范围"""
        column_ranges = {}
        
        for hole_id, hole in self.hole_collection.holes.items():
            # 解析孔位ID
            import re
            match = re.match(r'C(\d+)R(\d+)', hole_id)
            if match:
                col = int(match.group(1))
                row = int(match.group(2))
                
                if col not in column_ranges:
                    column_ranges[col] = (row, row)
                else:
                    min_row, max_row = column_ranges[col]
                    column_ranges[col] = (min(min_row, row), max(max_row, row))
        
        return column_ranges
    
    def get_column_direction(self, col: int) -> str:
        """获取列的遍历方向"""
        if col % 2 == 1:  # 奇数列
            return "ascending"  # 从小到大
        else:  # 偶数列
            return "descending"  # 从大到小
    
    def get_column_bounds(self, col: int) -> Tuple[int, int]:
        """获取指定列的边界"""
        if col in self.column_ranges:
            return self.column_ranges[col]
        return (1, 1)  # 默认值
    
    def get_next_holes(self) -> List[HolePosition]:
        """获取下一个要处理的孔位(们)"""
        direction = self.get_column_direction(self.current_col)
        min_row, max_row = self.get_column_bounds(self.current_col)
        
        # 创建当前孔位
        hole1 = HolePosition(self.current_row, self.current_col)
        holes = [hole1]
        
        # 检查是否需要双孔模式
        if not self.is_single_mode:
            if direction == "ascending":
                # 奇数列：从小到大，配对为当前+4
                paired_row = self.current_row + self.PAIR_INTERVAL
                if paired_row <= max_row:
                    hole2 = HolePosition(paired_row, self.current_col)
                    holes.append(hole2)
                else:
                    # 较大行号触碰边界，进入单孔模式
                    self.is_single_mode = True
                    self.logger.info(f"进入单孔模式 - 列{self.current_col}上边界")
            else:
                # 偶数列：从大到小，配对为当前-4
                paired_row = self.current_row - self.PAIR_INTERVAL
                if paired_row >= min_row:
                    hole2 = HolePosition(paired_row, self.current_col)
                    holes.append(hole2)
                else:
                    # 较小行号触碰边界，进入单孔模式
                    self.is_single_mode = True
                    self.logger.info(f"进入单孔模式 - 列{self.current_col}下边界")
        
        return holes
    
    def advance_position(self) -> bool:
        """前进到下一个位置，返回是否还有更多孔位"""
        direction = self.get_column_direction(self.current_col)
        min_row, max_row = self.get_column_bounds(self.current_col)
        
        if direction == "ascending":
            # 奇数列：从小到大
            self.current_row += 1
            
            if self.current_row > max_row:
                # 到达列顶部，切换到下一列
                self.current_col += 1
                self.is_single_mode = False  # 重置单孔模式
                
                if self.current_col in self.column_ranges:
                    # 偶数列从最大行开始
                    _, next_max_row = self.get_column_bounds(self.current_col)
                    self.current_row = next_max_row
                    self.logger.info(f"切换到列{self.current_col}(下降方向)")
                else:
                    # 没有更多列了
                    return False
        else:
            # 偶数列：从大到小
            self.current_row -= 1
            
            if self.current_row < min_row:
                # 到达列底部，切换到下一列
                self.current_col += 1
                self.is_single_mode = False  # 重置单孔模式
                
                if self.current_col in self.column_ranges:
                    # 奇数列从最小行开始
                    next_min_row, _ = self.get_column_bounds(self.current_col)
                    self.current_row = next_min_row
                    self.logger.info(f"切换到列{self.current_col}(上升方向)")
                else:
                    # 没有更多列了
                    return False
        
        return True
    
    def get_progress_info(self) -> Dict:
        """获取当前进度信息"""
        total_holes = len(self.hole_collection.holes)
        processed_holes = self._calculate_processed_holes()
        
        return {
            'current_col': self.current_col,
            'current_row': self.current_row,
            'direction': self.get_column_direction(self.current_col),
            'is_single_mode': self.is_single_mode,
            'total_holes': total_holes,
            'processed_holes': processed_holes,
            'progress_percent': (processed_holes / total_holes * 100) if total_holes > 0 else 0
        }
    
    def _calculate_processed_holes(self) -> int:
        """计算已处理的孔位数量"""
        processed = 0
        
        for col in range(1, self.current_col):
            if col in self.column_ranges:
                min_row, max_row = self.column_ranges[col]
                processed += (max_row - min_row + 1)
        
        # 当前列的处理数量
        if self.current_col in self.column_ranges:
            min_row, max_row = self.column_ranges[self.current_col]
            direction = self.get_column_direction(self.current_col)
            
            if direction == "ascending":
                processed += (self.current_row - min_row)
            else:
                processed += (max_row - self.current_row)
        
        return processed
    
    def validate_hole_exists(self, hole_position: HolePosition) -> bool:
        """验证孔位是否存在"""
        return hole_position.hole_id in self.hole_collection.holes
    
    def get_demonstration_sequence(self, limit: int = 20) -> List[List[str]]:
        """获取演示序列，用于预览"""
        sequence = []
        temp_col = self.current_col
        temp_row = self.current_row
        temp_single_mode = self.is_single_mode
        
        for _ in range(limit):
            holes = self.get_next_holes()
            hole_ids = [h.hole_id for h in holes]
            sequence.append(hole_ids)
            
            if not self.advance_position():
                break
        
        # 恢复原始状态
        self.current_col = temp_col
        self.current_row = temp_row
        self.is_single_mode = temp_single_mode
        
        return sequence