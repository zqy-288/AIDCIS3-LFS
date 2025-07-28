"""
适配新标号体系的高级蛇形路径算法
针对C001RxxxX+A/B标签体系优化的检测路径规划
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import math

from advanced_hole_id_mapper import AdvancedHoleIdMapper, HoleMappingRule


class PathStrategy(Enum):
    """路径策略"""
    LABEL_BASED = "label_based"      # 基于A/B标签的路径
    ROW_BASED = "row_based"          # 基于行号的路径
    SPATIAL_SNAKE = "spatial_snake"  # 基于空间位置的蛇形路径
    HYBRID = "hybrid"                # 混合策略


@dataclass
class PathSegment:
    """路径段"""
    holes: List[HoleMappingRule]
    segment_type: str  # 'A', 'B', 'row', 'spatial'
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    total_distance: float


class AdvancedSnakePath:
    """适配新标号体系的高级蛇形路径规划器"""
    
    def __init__(self, hole_mapper: AdvancedHoleIdMapper):
        """
        初始化路径规划器
        
        Args:
            hole_mapper: 已加载数据的孔位映射器
        """
        self.hole_mapper = hole_mapper
        self.mapping_rules = hole_mapper.mapping_rules
        
    def generate_path(self, strategy: PathStrategy = PathStrategy.HYBRID) -> List[HoleMappingRule]:
        """
        生成检测路径
        
        Args:
            strategy: 路径策略
            
        Returns:
            按检测顺序排列的孔位规则列表
        """
        if strategy == PathStrategy.LABEL_BASED:
            return self._generate_label_based_path()
        elif strategy == PathStrategy.ROW_BASED:
            return self._generate_row_based_path()
        elif strategy == PathStrategy.SPATIAL_SNAKE:
            return self._generate_spatial_snake_path()
        elif strategy == PathStrategy.HYBRID:
            return self._generate_hybrid_path()
        else:
            raise ValueError(f"不支持的路径策略: {strategy}")
    
    def _generate_label_based_path(self) -> List[HoleMappingRule]:
        """
        基于A/B标签的路径策略
        策略：先检测A区域，再检测B区域，每个区域内按目标行号排序
        """
        print("🏷️ 使用标签基础路径策略")
        
        # 分离A/B标签
        a_holes = [rule for rule in self.mapping_rules if rule.label == 'A']
        b_holes = [rule for rule in self.mapping_rules if rule.label == 'B']
        
        # 在每个标签区域内按目标行号排序
        a_holes.sort(key=lambda r: int(r.target_id[5:8]))  # 按R后面的数字排序
        b_holes.sort(key=lambda r: int(r.target_id[5:8]))
        
        print(f"  A区域: {len(a_holes)}个孔位")
        print(f"  B区域: {len(b_holes)}个孔位")
        
        # 组合路径：A区域 → B区域
        return a_holes + b_holes
    
    def _generate_row_based_path(self) -> List[HoleMappingRule]:
        """
        基于目标行号的路径策略
        策略：严格按照C001R001, C001R002, C001R003...的顺序
        """
        print("📊 使用行号基础路径策略")
        
        # 按目标行号排序
        sorted_holes = sorted(self.mapping_rules, 
                            key=lambda r: int(r.target_id[5:8]))
        
        print(f"  行号范围: R{int(sorted_holes[0].target_id[5:8]):03d} - R{int(sorted_holes[-1].target_id[5:8]):03d}")
        return sorted_holes
    
    def _generate_spatial_snake_path(self) -> List[HoleMappingRule]:
        """
        基于空间位置的蛇形路径
        策略：按实际几何位置进行蛇形扫描，忽略新编号
        """
        print("🐍 使用空间蛇形路径策略")
        
        # 按Y坐标分组（行）
        y_groups = {}
        for rule in self.mapping_rules:
            y_key = round(rule.y_coord, 1)  # 容差0.1mm
            if y_key not in y_groups:
                y_groups[y_key] = []
            y_groups[y_key].append(rule)
        
        # 按Y坐标排序（从上到下）
        sorted_y_keys = sorted(y_groups.keys(), reverse=True)
        
        snake_path = []
        reverse = False
        
        for y_key in sorted_y_keys:
            row_holes = y_groups[y_key]
            # 按X坐标排序
            row_holes.sort(key=lambda r: r.x_coord, reverse=reverse)
            snake_path.extend(row_holes)
            reverse = not reverse  # 下一行反向
        
        print(f"  处理了 {len(y_groups)} 行数据")
        return snake_path
    
    def _generate_hybrid_path(self) -> List[HoleMappingRule]:
        """
        混合策略路径
        策略：结合标签分组和空间优化
        1. 先按A/B标签分组
        2. 在每个标签内按空间位置优化路径
        """
        print("🔄 使用混合路径策略")
        
        hybrid_path = []
        
        # 分离A/B标签
        a_holes = [rule for rule in self.mapping_rules if rule.label == 'A']
        b_holes = [rule for rule in self.mapping_rules if rule.label == 'B']
        
        for label, holes in [('A', a_holes), ('B', b_holes)]:
            print(f"  处理{label}区域: {len(holes)}个孔位")
            
            # 在每个标签区域内进行空间优化
            optimized_holes = self._optimize_spatial_order(holes)
            hybrid_path.extend(optimized_holes)
        
        return hybrid_path
    
    def _optimize_spatial_order(self, holes: List[HoleMappingRule]) -> List[HoleMappingRule]:
        """
        在给定孔位列表内优化空间顺序
        使用最近邻算法减少移动距离
        """
        if not holes:
            return []
        
        # 找到起始点（最左上角）
        start_hole = min(holes, key=lambda r: (r.y_coord, r.x_coord))
        
        optimized_path = [start_hole]
        remaining_holes = [h for h in holes if h != start_hole]
        
        current_hole = start_hole
        
        while remaining_holes:
            # 找到距离当前孔位最近的下一个孔位
            next_hole = min(remaining_holes, 
                          key=lambda r: math.sqrt(
                              (r.x_coord - current_hole.x_coord)**2 + 
                              (r.y_coord - current_hole.y_coord)**2
                          ))
            
            optimized_path.append(next_hole)
            remaining_holes.remove(next_hole)
            current_hole = next_hole
        
        return optimized_path
    
    def calculate_path_metrics(self, path: List[HoleMappingRule]) -> Dict:
        """
        计算路径指标
        """
        if not path:
            return {}
        
        total_distance = 0.0
        max_jump = 0.0
        
        for i in range(1, len(path)):
            prev_hole = path[i-1]
            curr_hole = path[i]
            
            distance = math.sqrt(
                (curr_hole.x_coord - prev_hole.x_coord)**2 + 
                (curr_hole.y_coord - prev_hole.y_coord)**2
            )
            
            total_distance += distance
            max_jump = max(max_jump, distance)
        
        # 分析标签切换次数
        label_switches = 0
        for i in range(1, len(path)):
            if path[i].label != path[i-1].label:
                label_switches += 1
        
        # 分析目标行号的跳跃
        row_jumps = []
        for i in range(1, len(path)):
            prev_row = int(path[i-1].target_id[5:8])
            curr_row = int(path[i].target_id[5:8])
            row_jumps.append(abs(curr_row - prev_row))
        
        return {
            'total_distance_mm': total_distance,
            'average_step_mm': total_distance / len(path) if len(path) > 1 else 0,
            'max_jump_mm': max_jump,
            'label_switches': label_switches,
            'max_row_jump': max(row_jumps) if row_jumps else 0,
            'average_row_jump': sum(row_jumps) / len(row_jumps) if row_jumps else 0,
            'total_holes': len(path)
        }
    
    def export_path_analysis(self, strategies: List[PathStrategy] = None) -> Dict:
        """
        导出多种策略的路径分析对比
        """
        if strategies is None:
            strategies = [PathStrategy.LABEL_BASED, PathStrategy.ROW_BASED, 
                         PathStrategy.SPATIAL_SNAKE, PathStrategy.HYBRID]
        
        analysis = {}
        
        for strategy in strategies:
            print(f"\n🔍 分析策略: {strategy.value}")
            path = self.generate_path(strategy)
            metrics = self.calculate_path_metrics(path)
            
            analysis[strategy.value] = {
                'path_length': len(path),
                'metrics': metrics,
                'first_10_holes': [
                    {
                        'original_id': rule.original_id,
                        'target_id': rule.target_id,
                        'label': rule.label,
                        'position': (rule.x_coord, rule.y_coord)
                    }
                    for rule in path[:10]
                ]
            }
            
            print(f"  总距离: {metrics['total_distance_mm']:.1f}mm")
            print(f"  平均步长: {metrics['average_step_mm']:.1f}mm")
            print(f"  标签切换: {metrics['label_switches']}次")
            print(f"  最大行号跳跃: {metrics['max_row_jump']}")
        
        return analysis


# 测试和演示
if __name__ == "__main__":
    print("🚀 高级蛇形路径算法测试")
    print("=" * 60)
    
    # 初始化映射器和路径规划器
    mapper = AdvancedHoleIdMapper(mapping_mode="function")
    
    try:
        mapper.load_training_data("assets/dxf/DXF Graph/dongzhong_hole_grid.json")
        
        path_planner = AdvancedSnakePath(mapper)
        
        # 测试所有策略
        analysis = path_planner.export_path_analysis()
        
        # 输出最佳策略推荐
        print("\n📈 策略性能对比:")
        best_distance = float('inf')
        best_strategy = None
        
        for strategy_name, data in analysis.items():
            metrics = data['metrics']
            distance = metrics['total_distance_mm']
            
            print(f"\n{strategy_name}:")
            print(f"  总移动距离: {distance:.0f}mm")
            print(f"  平均步长: {metrics['average_step_mm']:.1f}mm")
            print(f"  标签切换次数: {metrics['label_switches']}")
            print(f"  最大单次跳跃: {metrics['max_jump_mm']:.1f}mm")
            
            if distance < best_distance:
                best_distance = distance
                best_strategy = strategy_name
        
        print(f"\n🏆 推荐策略: {best_strategy}")
        print(f"   最短总距离: {best_distance:.0f}mm")
        
    except FileNotFoundError:
        print("❌ 数据文件未找到，请确保dongzhong_hole_grid.json文件存在")
    except Exception as e:
        print(f"❌ 测试失败: {e}")