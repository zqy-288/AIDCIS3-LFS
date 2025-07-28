"""
修正的孔位编号映射器
正确实现用户需求的编号体系:
- 列号(C) = 行数 (第1行=C001, 第2行=C002, ...)  
- 行号(R) = 该行内序号 (每行内从左到右R001, R002, R003, ...)
"""

import numpy as np
import json
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass
import math

try:
    import tensorflow as tf
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False
    tf = None


@dataclass 
class CorrectedHoleMappingRule:
    """修正的孔位映射规则"""
    original_id: str
    target_id: str
    label: str  # A或B标签
    x_coord: float
    y_coord: float
    row_index: int      # 行索引(从1开始)
    pos_in_row: int     # 行内位置(从1开始)


class CorrectedHoleIdMapper:
    """修正的孔位编号映射器"""
    
    def __init__(self, mapping_mode: str = "function"):
        """
        初始化映射器
        
        Args:
            mapping_mode: 映射模式，"function" 或 "neural_network"
        """
        self.mapping_mode = mapping_mode
        self.mapping_rules: List[CorrectedHoleMappingRule] = []
        self.mlp_model = None
        
    def load_training_data(self, json_file_path: str):
        """
        从DXF数据文件加载训练数据并生成正确的映射
        """
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        holes_data = data.get('holes', [])
        self.mapping_rules.clear()
        
        # 按Y坐标分组，形成行
        y_groups = {}
        for hole in holes_data:
            y_key = round(hole['coordinates']['y_mm'], 1)  # 容差0.1mm
            if y_key not in y_groups:
                y_groups[y_key] = []
            y_groups[y_key].append(hole)
        
        # 按Y坐标排序（从上到下）
        sorted_y_keys = sorted(y_groups.keys(), reverse=True)
        
        print(f"🔄 按行处理孔位数据，共{len(sorted_y_keys)}行")
        
        for row_index, y_key in enumerate(sorted_y_keys, 1):
            row_holes = y_groups[y_key]
            # 每行内按X坐标排序（从左到右）
            row_holes.sort(key=lambda h: h['coordinates']['x_mm'])
            
            for pos_in_row, hole in enumerate(row_holes, 1):
                original_id = hole['hole_id']
                x_coord = hole['coordinates']['x_mm']
                y_coord = hole['coordinates']['y_mm']
                
                # 生成新的编号：C{行数}R{行内位置}
                target_col = f"C{row_index:03d}"
                target_row = f"R{pos_in_row:03d}"
                target_id = f"{target_col}{target_row}"
                
                # A/B标签分配（使用优化的分界线）
                label = "A" if x_coord < 0.1 else "B"
                
                rule = CorrectedHoleMappingRule(
                    original_id=original_id,
                    target_id=target_id,
                    label=label,
                    x_coord=x_coord,
                    y_coord=y_coord,
                    row_index=row_index,
                    pos_in_row=pos_in_row
                )
                self.mapping_rules.append(rule)
        
        print(f"✅ 已生成 {len(self.mapping_rules)} 个孔位的修正映射")
    
    def map_hole_id(self, original_id: str, x_coord: float, y_coord: float) -> Tuple[str, str]:
        """
        映射孔位编号
        
        Args:
            original_id: 原始编号 (如 "C007R001")
            x_coord: X坐标
            y_coord: Y坐标
            
        Returns:
            (target_id, label): 目标编号和A/B标签
        """
        # 在已有映射规则中查找
        for rule in self.mapping_rules:
            if rule.original_id == original_id:
                return rule.target_id, rule.label
        
        # 如果没找到，使用算法估算
        return self._estimate_mapping(original_id, x_coord, y_coord)
    
    def _estimate_mapping(self, original_id: str, x_coord: float, y_coord: float) -> Tuple[str, str]:
        """
        估算映射（当查找表中没有时）
        """
        # 根据Y坐标估算行号
        # 找到最接近的Y坐标对应的行
        min_distance = float('inf')
        estimated_row = 1
        
        for rule in self.mapping_rules:
            distance = abs(rule.y_coord - y_coord)
            if distance < min_distance:
                min_distance = distance
                estimated_row = rule.row_index
        
        # 估算行内位置（简化处理）
        estimated_pos = 1
        target_id = f"C{estimated_row:03d}R{estimated_pos:03d}"
        label = "A" if x_coord < 0.1 else "B"
        
        return target_id, label
    
    def get_row_info(self, row_index: int) -> Dict:
        """
        获取指定行的信息
        """
        row_rules = [r for r in self.mapping_rules if r.row_index == row_index]
        
        if not row_rules:
            return {}
        
        a_count = len([r for r in row_rules if r.label == 'A'])
        b_count = len([r for r in row_rules if r.label == 'B'])
        
        return {
            'row_index': row_index,
            'total_holes': len(row_rules),
            'a_labels': a_count,
            'b_labels': b_count,
            'y_coordinate': row_rules[0].y_coord,
            'x_range': (min(r.x_coord for r in row_rules), max(r.x_coord for r in row_rules)),
            'target_ids': [r.target_id for r in row_rules]
        }
    
    def get_mapping_statistics(self) -> Dict:
        """
        获取映射统计信息
        """
        if not self.mapping_rules:
            return {}
        
        # 统计总体信息
        a_labels = sum(1 for rule in self.mapping_rules if rule.label == 'A')
        b_labels = sum(1 for rule in self.mapping_rules if rule.label == 'B')
        
        # 统计行信息
        max_row = max(rule.row_index for rule in self.mapping_rules)
        row_hole_counts = {}
        for rule in self.mapping_rules:
            row = rule.row_index
            if row not in row_hole_counts:
                row_hole_counts[row] = 0
            row_hole_counts[row] += 1
        
        return {
            "total_holes": len(self.mapping_rules),
            "total_rows": max_row,
            "a_labels": a_labels,
            "b_labels": b_labels,
            "holes_per_row_range": (min(row_hole_counts.values()), max(row_hole_counts.values())),
            "mapping_mode": self.mapping_mode
        }
    
    def test_key_mappings(self):
        """
        测试关键映射案例，验证新的编号逻辑
        """
        print("🧪 新编号逻辑验证:")
        
        # 获取前几行的示例
        for row_idx in range(1, 6):  # 前5行
            row_info = self.get_row_info(row_idx)
            if row_info:
                print(f"\n第{row_idx}行 (Y={row_info['y_coordinate']:.1f}):")
                print(f"  总孔位: {row_info['total_holes']}个")
                print(f"  编号范围: {row_info['target_ids'][0]} ~ {row_info['target_ids'][-1]}")
                print(f"  A/B分布: {row_info['a_labels']}A + {row_info['b_labels']}B")
        
        # 验证关键点
        key_tests = []
        
        # 找第一行的第一个孔
        first_row_rules = [r for r in self.mapping_rules if r.row_index == 1]
        if first_row_rules:
            first_hole = min(first_row_rules, key=lambda r: r.pos_in_row)
            key_tests.append((first_hole.original_id, first_hole.x_coord, first_hole.y_coord, "第一行第一个孔"))
        
        # 找第一行的第二个孔  
        if len(first_row_rules) >= 2:
            second_hole = sorted(first_row_rules, key=lambda r: r.pos_in_row)[1]
            key_tests.append((second_hole.original_id, second_hole.x_coord, second_hole.y_coord, "第一行第二个孔"))
        
        print(f"\n🎯 关键点验证:")
        for original_id, x, y, desc in key_tests:
            target_id, label = self.map_hole_id(original_id, x, y)
            print(f"  {original_id} → {target_id} (标签: {label}) - {desc}")
    
    def export_mapping_table(self, output_file: str, max_rows: int = 10):
        """
        导出映射表（限制行数避免文件过大）
        """
        mapping_data = {
            "mapping_logic": "C{行数}R{行内位置}",
            "description": "列号=行数，行号=该行内从左到右的位置序号",
            "statistics": self.get_mapping_statistics(),
            "sample_mappings": []
        }
        
        # 只导出前几行作为示例
        for row_idx in range(1, min(max_rows + 1, 11)):
            row_rules = [r for r in self.mapping_rules if r.row_index == row_idx]
            if row_rules:
                mapping_data["sample_mappings"].extend([
                    {
                        "original_id": rule.original_id,
                        "target_id": rule.target_id,
                        "label": rule.label,
                        "coordinates": {
                            "x_mm": rule.x_coord,
                            "y_mm": rule.y_coord
                        },
                        "row_index": rule.row_index,
                        "position_in_row": rule.pos_in_row
                    }
                    for rule in row_rules[:10]  # 每行最多10个示例
                ])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 映射表已导出到: {output_file}")


# 使用示例和测试
if __name__ == "__main__":
    print("🚀 修正的孔位编号映射器测试")
    print("=" * 60)
    
    mapper = CorrectedHoleIdMapper(mapping_mode="function")
    
    try:
        json_file = "assets/dxf/DXF Graph/dongzhong_hole_grid.json"
        print(f"📁 加载数据: {json_file}")
        mapper.load_training_data(json_file)
        
        stats = mapper.get_mapping_statistics()
        print(f"\n📊 映射统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 测试关键映射
        mapper.test_key_mappings()
        
        # 导出示例映射表
        mapper.export_mapping_table("corrected_hole_mapping.json")
        
    except FileNotFoundError:
        print("⚠️ 数据文件未找到")
    except Exception as e:
        print(f"❌ 测试失败: {e}")