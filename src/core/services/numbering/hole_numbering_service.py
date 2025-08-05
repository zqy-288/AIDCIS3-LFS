"""
孔位编号服务
负责为解析后的孔位分配A/B侧网格编号
基于东重管板的特定编号规则
"""

import logging
from typing import List, Dict, Optional
from collections import defaultdict

from src.shared.models.hole_data import HoleData, HoleCollection
from src.core.dependency_injection import injectable, ServiceLifetime



class ABSideNumberingStrategy:
    """
    A/B侧分区编号策略
    基于东重管板的A侧（y>0）和B侧（y<0）分区
    编号格式: AC{col:03d}R{row:03d}, BC{col:03d}R{row:03d}
    """
    
    def __init__(self, x_tolerance=None, y_tolerance=None):
        self.logger = logging.getLogger(__name__)
        self.center_y = None
        self.a_side_count = 0
        self.b_side_count = 0
        self.x_tolerance = x_tolerance
        self.y_tolerance = y_tolerance
        self.column_info = []
        self.a_row_info = []
        self.b_row_info = []
        
    def assign_numbers(self, holes: List[HoleData]) -> None:
        """
        为孔位分配A/B侧网格编号
        
        按照列编号(C001-Cxxx)和行编号(R001-Rxxx)进行网格化编号
        A区: AC{col:03d}R{row:03d}, B区: BC{col:03d}R{row:03d}
        """
        if not holes:
            return
            
        # 计算几何中心
        center_x = sum(h.center_x for h in holes) / len(holes)
        self.center_y = sum(h.center_y for h in holes) / len(holes)
        
        self.logger.info(f"📊 东重管板几何中心: ({center_x:.2f}, {self.center_y:.2f})")
        
        # 分类孔位
        a_side_holes = [h for h in holes if h.center_y > self.center_y]
        b_side_holes = [h for h in holes if h.center_y < self.center_y]
        center_holes = [h for h in holes if h.center_y == self.center_y]
        
        self.a_side_count = len(a_side_holes)
        self.b_side_count = len(b_side_holes)
        center_count = len(center_holes)
        
        self.logger.info(f"📊 A/B侧分区统计:")
        self.logger.info(f"   A侧(上侧, y>{self.center_y:.2f}): {self.a_side_count} 个孔")
        self.logger.info(f"   B侧(下侧, y<{self.center_y:.2f}): {self.b_side_count} 个孔")
        self.logger.info(f"   中心线(y={self.center_y:.2f}): {center_count} 个孔")
        
        # 分析坐标分布并确定容差
        self._analyze_coordinate_distribution(holes)
        
        # 分配列编号（全局统一）
        column_assignments = self._assign_column_numbers(holes)
        
        # 分配A区行编号
        if a_side_holes:
            a_row_assignments = self._assign_a_side_row_numbers(a_side_holes)
            self._generate_hole_ids(a_side_holes, column_assignments, a_row_assignments, "A")
            
        # 分配B区行编号
        if b_side_holes:
            b_row_assignments = self._assign_b_side_row_numbers(b_side_holes)
            self._generate_hole_ids(b_side_holes, column_assignments, b_row_assignments, "B")
            
        # 中心线孔位编号（如果有）
        for i, hole in enumerate(sorted(center_holes, key=lambda h: h.center_x)):
            hole.hole_id = f"C{i+1:03d}"
            
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "ABSideNumbering"
        
    def _analyze_coordinate_distribution(self, holes: List[HoleData]) -> None:
        """分析坐标分布并确定容差"""
        # 分析X坐标分布
        x_coords = sorted([h.center_x for h in holes])
        x_diffs = [x_coords[i+1] - x_coords[i] for i in range(len(x_coords)-1) if x_coords[i+1] - x_coords[i] > 1]
        
        if x_diffs:
            # 使用最小间距的一宊作为X容差
            self.x_tolerance = min(x_diffs) / 2
        else:
            self.x_tolerance = 5.0  # 默认值
            
        # 分析Y坐标分布
        y_coords = sorted([abs(h.center_y) for h in holes if h.center_y != 0])
        y_diffs = [y_coords[i+1] - y_coords[i] for i in range(len(y_coords)-1) if y_coords[i+1] - y_coords[i] > 1]
        
        if y_diffs:
            self.y_tolerance = min(y_diffs) / 2
        else:
            self.y_tolerance = 5.0  # 默认值
            
        self.logger.info(f"📈 坐标分析结果: X容差={self.x_tolerance:.2f}, Y容差={self.y_tolerance:.2f}")
    
    def _assign_column_numbers(self, holes: List[HoleData]) -> dict:
        """分配列编号（全局统一）"""
        # 按X坐标分组
        from collections import defaultdict
        x_groups = defaultdict(list)
        
        for hole in holes:
            # 找到最近的X坐标组
            found_group = False
            for existing_x in x_groups.keys():
                if abs(hole.center_x - existing_x) <= self.x_tolerance:
                    x_groups[existing_x].append(hole)
                    found_group = True
                    break
            if not found_group:
                x_groups[hole.center_x].append(hole)
        
        # 按X坐标排序分配列号
        sorted_x_groups = sorted(x_groups.items())
        column_assignments = {}
        
        for col_num, (x_coord, group_holes) in enumerate(sorted_x_groups, 1):
            for hole in group_holes:
                column_assignments[id(hole)] = col_num
                
        self.column_info = [(x_coord, len(group_holes)) for x_coord, group_holes in sorted_x_groups]
        self.logger.info(f"📋 列分配完成: {len(sorted_x_groups)} 列")
        
        return column_assignments
    
    def _assign_a_side_row_numbers(self, a_holes: List[HoleData]) -> dict:
        """分配A区行编号（Y坐标从小到大）"""
        from collections import defaultdict
        y_groups = defaultdict(list)
        
        for hole in a_holes:
            found_group = False
            for existing_y in y_groups.keys():
                if abs(hole.center_y - existing_y) <= self.y_tolerance:
                    y_groups[existing_y].append(hole)
                    found_group = True
                    break
            if not found_group:
                y_groups[hole.center_y].append(hole)
        
        # A区按Y坐标升序排列（从中心线向上）
        sorted_y_groups = sorted(y_groups.items())
        row_assignments = {}
        
        for row_num, (y_coord, group_holes) in enumerate(sorted_y_groups, 1):
            for hole in group_holes:
                row_assignments[id(hole)] = row_num
                
        self.a_row_info = [(y_coord, len(group_holes)) for y_coord, group_holes in sorted_y_groups]
        self.logger.info(f"📋 A区行分配完成: {len(sorted_y_groups)} 行")
        
        return row_assignments
    
    def _assign_b_side_row_numbers(self, b_holes: List[HoleData]) -> dict:
        """分配B区行编号（按|Y|坐标从小到大）"""
        from collections import defaultdict
        y_groups = defaultdict(list)
        
        for hole in b_holes:
            abs_y = abs(hole.center_y)
            found_group = False
            for existing_abs_y in y_groups.keys():
                if abs(abs_y - existing_abs_y) <= self.y_tolerance:
                    y_groups[existing_abs_y].append(hole)
                    found_group = True
                    break
            if not found_group:
                y_groups[abs_y].append(hole)
        
        # B区按|Y|坐标升序排列（从中心线向下）  
        sorted_y_groups = sorted(y_groups.items())
        row_assignments = {}
        
        for row_num, (abs_y_coord, group_holes) in enumerate(sorted_y_groups, 1):
            for hole in group_holes:
                row_assignments[id(hole)] = row_num
                
        self.b_row_info = [(abs_y_coord, len(group_holes)) for abs_y_coord, group_holes in sorted_y_groups]
        self.logger.info(f"📋 B区行分配完成: {len(sorted_y_groups)} 行")
        
        return row_assignments
    
    def _generate_hole_ids(self, holes: List[HoleData], column_assignments: dict, 
                          row_assignments: dict, side_prefix: str) -> None:
        """生成孔位ID"""
        for hole in holes:
            col_num = column_assignments[id(hole)]
            row_num = row_assignments[id(hole)]
            hole.hole_id = f"{side_prefix}C{col_num:03d}R{row_num:03d}"
    
    def get_statistics(self) -> dict:
        """获取A/B侧统计信息"""
        return {
            'center_y': self.center_y,
            'a_side_count': self.a_side_count,
            'b_side_count': self.b_side_count,
            'total_count': self.a_side_count + self.b_side_count,
            'x_tolerance': getattr(self, 'x_tolerance', None),
            'y_tolerance': getattr(self, 'y_tolerance', None),
            'column_count': len(self.column_info),
            'a_row_count': len(self.a_row_info),
            'b_row_count': len(self.b_row_info)
        }



@injectable(ServiceLifetime.SINGLETON)
class HoleNumberingService:
    """
    孔位编号服务
    
    专门为东重管板提供A/B侧网格编号
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 创建A/B侧编号策略实例
        self.numbering_strategy = ABSideNumberingStrategy()
        
    def apply_numbering(self, hole_collection: HoleCollection) -> None:
        """
        应用A/B侧网格编号
        
        Args:
            hole_collection: 孔位集合
        """
        
        # 检查是否是无ID的孔位集合
        if hole_collection.metadata.get('no_ids', False):
            # 直接从字典值中获取孔位列表
            holes_list = list(hole_collection.holes.values())
        else:
            holes_list = list(hole_collection.holes.values())
        
        self.logger.info(f"应用A/B侧网格编号 (共 {len(holes_list)} 个孔位)")
        
        # 应用编号
        self.numbering_strategy.assign_numbers(holes_list)
        
        # 更新hole_collection的字典键（使用新生成的ID）
        new_holes_dict = {}
        for hole in holes_list:
            if hole.hole_id:
                new_holes_dict[hole.hole_id] = hole
            else:
                # 如果仍然没有ID，使用坐标作为键
                key = f"({hole.center_x:.3f},{hole.center_y:.3f})"
                new_holes_dict[key] = hole
            
        hole_collection.holes = new_holes_dict
        
        # 清除no_ids标记
        if 'no_ids' in hole_collection.metadata:
            del hole_collection.metadata['no_ids']
        
        # 更新元数据
        if 'numbering_strategy' not in hole_collection.metadata:
            hole_collection.metadata['numbering_strategy'] = 'ABSideNumbering'
            
    def get_statistics(self) -> dict:
        """获取编号统计信息"""
        return self.numbering_strategy.get_statistics()