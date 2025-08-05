"""
最终版A/B区域独立编号映射器
实现正确的编号逻辑：
- A区域 (X < 0.1): 独立编号 C001R001, C001R003, C001R005...
- B区域 (X >= 0.1): 独立编号 C001R001, C001R003, C001R005...  
- 两个区域可能存在相同编号，通过A/B标签区分
"""

import json
from typing import Tuple, Dict, List
from dataclasses import dataclass
import math


@dataclass 
class FinalMappingRule:
    """最终映射规则"""
    original_id: str
    target_id: str
    label: str  # A或B标签
    x_coord: float
    y_coord: float
    row_index: int      # 行索引(从1开始)
    ab_sequence: int    # 在A或B区域内的序号


class FinalABHoleMapper:
    """A/B区域独立编号映射器"""
    
    def __init__(self):
        self.mapping_rules: List[FinalMappingRule] = []
        self.a_boundary = 0.1  # A/B区域分界线
        
    def load_training_data(self, json_file_path: str):
        """
        从DXF数据文件加载并生成A/B区域独立编号映射
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
        
        print(f"🔄 处理 {len(sorted_y_keys)} 行数据，A/B区域独立编号")
        print(f"   A区域: X < {self.a_boundary}, B区域: X >= {self.a_boundary}")
        
        for row_index, y_key in enumerate(sorted_y_keys, 1):
            row_holes = y_groups[y_key]
            
            # 分离A/B区域孔位
            a_holes = []
            b_holes = []
            
            for hole in row_holes:
                x_coord = hole['coordinates']['x_mm']
                if x_coord < self.a_boundary:  # A区域
                    a_holes.append(hole)
                else:  # B区域
                    b_holes.append(hole)
            
            # A区域按X坐标排序（从左到右）
            a_holes.sort(key=lambda h: h['coordinates']['x_mm'])
            # B区域按X坐标排序（从左到右）
            b_holes.sort(key=lambda h: h['coordinates']['x_mm'])
            
            # 为A区域孔位分配编号（独立编号系统）
            for ab_seq, hole in enumerate(a_holes, 1):
                target_id = self._generate_target_id_for_area('A', row_index, ab_seq)
                
                rule = FinalMappingRule(
                    original_id=hole['hole_id'],
                    target_id=target_id,
                    label='A',
                    x_coord=hole['coordinates']['x_mm'],
                    y_coord=hole['coordinates']['y_mm'],
                    row_index=row_index,
                    ab_sequence=ab_seq
                )
                self.mapping_rules.append(rule)
            
            # 为B区域孔位分配编号（独立编号系统）
            for ab_seq, hole in enumerate(b_holes, 1):
                target_id = self._generate_target_id_for_area('B', row_index, ab_seq)
                
                rule = FinalMappingRule(
                    original_id=hole['hole_id'],
                    target_id=target_id,
                    label='B',
                    x_coord=hole['coordinates']['x_mm'],
                    y_coord=hole['coordinates']['y_mm'],
                    row_index=row_index,
                    ab_sequence=ab_seq
                )
                self.mapping_rules.append(rule)
        
        print(f"✅ 已生成 {len(self.mapping_rules)} 个A/B区域独立映射")
    
    def _generate_target_id_for_area(self, area: str, row_index: int, sequence: int) -> str:
        """
        为指定区域生成目标编号
        
        A区域和B区域都有独立的编号系统：
        - 第1行：奇数行号 R001, R003, R005, R007...
        - 第2行：偶数行号 R002, R004, R006, R008...
        """
        col = "C001"  # 列号固定
        
        if row_index % 2 == 1:  # 奇数行
            # 使用奇数行号：R001, R003, R005, R007...
            row_num = 1 + (sequence - 1) * 2
        else:  # 偶数行  
            # 使用偶数行号：R002, R004, R006, R008...
            row_num = 2 + (sequence - 1) * 2
        
        row = f"R{row_num:03d}"
        return f"{col}{row}"
    
    def map_hole_id(self, original_id: str, x_coord: float, y_coord: float) -> Tuple[str, str]:
        """
        映射孔位编号
        """
        # 在映射规则中查找
        for rule in self.mapping_rules:
            if rule.original_id == original_id:
                return rule.target_id, rule.label
        
        # 如果没找到，返回估算值
        label = "A" if x_coord < self.a_boundary else "B"
        return "C001R999", label  # 占位符
    
    def verify_key_mappings(self):
        """
        验证关键映射是否符合用户需求
        """
        print("🧪 验证关键映射:")
        
        key_holes = ['C007R001', 'C008R001', 'C006R001', 'C009R001']
        
        for original_id in key_holes:
            rule = next((r for r in self.mapping_rules if r.original_id == original_id), None)
            if rule:
                print(f"  {original_id} → {rule.target_id} (标签:{rule.label}, 行{rule.row_index}, {rule.label}区第{rule.ab_sequence}个)")
    
    def find_duplicate_target_ids(self):
        """
        查找重复的目标编号（应该存在，因为A/B区域独立编号）
        """
        target_id_count = {}
        for rule in self.mapping_rules:
            tid = rule.target_id
            if tid not in target_id_count:
                target_id_count[tid] = []
            target_id_count[tid].append(rule)
        
        duplicates = {tid: rules for tid, rules in target_id_count.items() if len(rules) > 1}
        
        print(f"🔍 重复的目标编号分析:")
        print(f"   总共 {len(duplicates)} 个编号在A/B区域重复")
        
        # 显示几个重复编号的例子
        for i, (tid, rules) in enumerate(list(duplicates.items())[:5]):
            print(f"   {tid}:")
            for rule in rules:
                print(f"     {rule.original_id} ({rule.label}区) X={rule.x_coord:.1f}")
        
        return duplicates
    
    def analyze_ab_distribution(self):
        """
        分析A/B区域的分布情况
        """
        print("📊 A/B区域分布分析:")
        
        # 统计每行每区域的孔位数
        row_stats = {}
        for rule in self.mapping_rules:
            row = rule.row_index
            if row not in row_stats:
                row_stats[row] = {'A': [], 'B': []}
            row_stats[row][rule.label].append(rule.target_id)
        
        # 显示前几行的分布
        for row in sorted(row_stats.keys())[:3]:
            print(f"\n第{row}行:")
            print(f"  A区域: {len(row_stats[row]['A'])}个 → {row_stats[row]['A'][:3]}...")
            print(f"  B区域: {len(row_stats[row]['B'])}个 → {row_stats[row]['B'][:3]}...")
    
    def get_mapping_statistics(self) -> Dict:
        """
        获取映射统计信息
        """
        if not self.mapping_rules:
            return {}
        
        a_count = sum(1 for rule in self.mapping_rules if rule.label == 'A')
        b_count = sum(1 for rule in self.mapping_rules if rule.label == 'B')
        
        # 分析行号分布
        a_target_rows = [int(rule.target_id[5:8]) for rule in self.mapping_rules if rule.label == 'A']
        b_target_rows = [int(rule.target_id[5:8]) for rule in self.mapping_rules if rule.label == 'B']
        
        return {
            "total_holes": len(self.mapping_rules),
            "a_area_holes": a_count,
            "b_area_holes": b_count,
            "a_area_row_range": (min(a_target_rows), max(a_target_rows)) if a_target_rows else (0, 0),
            "b_area_row_range": (min(b_target_rows), max(b_target_rows)) if b_target_rows else (0, 0),
            "boundary": f"X < {self.a_boundary} = A区域, X >= {self.a_boundary} = B区域"
        }
    
    def export_final_mapping(self, output_file: str):
        """
        导出最终映射结果
        """
        # 查找重复编号
        duplicates = {}
        target_id_count = {}
        for rule in self.mapping_rules:
            tid = rule.target_id
            if tid not in target_id_count:
                target_id_count[tid] = []
            target_id_count[tid].append(rule)
        
        duplicates = {tid: rules for tid, rules in target_id_count.items() if len(rules) > 1}
        
        final_data = {
            "mapping_logic": "A/B区域独立编号系统",
            "description": "A区域和B区域各自有独立的编号，可能存在相同编号但通过A/B标签区分",
            "boundary_rule": f"X < {self.a_boundary} = A区域, X >= {self.a_boundary} = B区域",
            "statistics": self.get_mapping_statistics(),
            "duplicate_count": len(duplicates),
            "key_mappings": [],
            "duplicate_examples": []
        }
        
        # 添加关键映射
        key_holes = ['C007R001', 'C008R001', 'C006R001', 'C009R001']
        for original_id in key_holes:
            rule = next((r for r in self.mapping_rules if r.original_id == original_id), None)
            if rule:
                final_data["key_mappings"].append({
                    "original_id": rule.original_id,
                    "target_id": rule.target_id,
                    "label": rule.label,
                    "coordinates": {"x_mm": rule.x_coord, "y_mm": rule.y_coord},
                    "area_sequence": rule.ab_sequence
                })
        
        # 添加重复编号示例
        for tid, rules in list(duplicates.items())[:3]:
            final_data["duplicate_examples"].append({
                "target_id": tid,
                "occurrences": [
                    {
                        "original_id": rule.original_id,
                        "label": rule.label,
                        "coordinates": {"x_mm": rule.x_coord, "y_mm": rule.y_coord}
                    }
                    for rule in rules
                ]
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 最终映射已导出到: {output_file}")


# 测试和演示
if __name__ == "__main__":
    print("🚀 最终版A/B区域独立编号映射器测试")
    print("=" * 60)
    
    mapper = FinalABHoleMapper()
    
    try:
        json_file = "assets/dxf/DXF Graph/dongzhong_hole_grid.json"
        mapper.load_training_data(json_file)
        
        # 验证关键映射
        mapper.verify_key_mappings()
        
        # 分析重复编号
        duplicates = mapper.find_duplicate_target_ids()
        
        # 分析分布
        mapper.analyze_ab_distribution()
        
        # 统计信息
        stats = mapper.get_mapping_statistics()
        print(f"\n📊 最终统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 导出结果
        mapper.export_final_mapping("final_ab_mapping.json")
        
        print(f"\n🎊 测试完成！A/B区域独立编号系统已实现")
        
    except FileNotFoundError:
        print("⚠️ 数据文件未找到")
    except Exception as e:
        print(f"❌ 测试失败: {e}")