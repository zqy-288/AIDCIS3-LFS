"""
基于A/B标签的奇偶行编号映射器
实现用户需求的特殊编号逻辑：
- A标签: R001, R005, R009, R013... (奇数，间隔4)
- B标签: R003, R007, R011, R015... (奇数，间隔4，起始R003)
- 第二行使用偶数：A用R002,R006,R010... B用R004,R008,R012...
"""

import json
from typing import Tuple, Dict, List
from dataclasses import dataclass
import math


@dataclass 
class ABLabelMappingRule:
    """A/B标签映射规则"""
    original_id: str
    target_id: str
    label: str  # A或B标签
    x_coord: float
    y_coord: float
    row_index: int      # 行索引(从1开始)
    ab_sequence: int    # 在A或B标签内的序号


class ABLabelHoleMapper:
    """基于A/B标签的孔位编号映射器"""
    
    def __init__(self):
        self.mapping_rules: List[ABLabelMappingRule] = []
        
    def load_training_data(self, json_file_path: str):
        """
        从DXF数据文件加载并生成A/B标签编号映射
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
        
        print(f"🔄 处理 {len(sorted_y_keys)} 行数据，应用A/B标签奇偶编号逻辑")
        
        for row_index, y_key in enumerate(sorted_y_keys, 1):
            row_holes = y_groups[y_key]
            # 每行内按X坐标排序（从左到右）
            row_holes.sort(key=lambda h: h['coordinates']['x_mm'])
            
            # 分离A/B标签孔位
            a_holes = []
            b_holes = []
            
            for hole in row_holes:
                x_coord = hole['coordinates']['x_mm']
                if x_coord < 0.1:  # A标签
                    a_holes.append(hole)
                else:  # B标签
                    b_holes.append(hole)
            
            # 为A标签孔位分配编号
            for ab_seq, hole in enumerate(a_holes, 1):
                target_id = self._generate_target_id('A', row_index, ab_seq)
                
                rule = ABLabelMappingRule(
                    original_id=hole['hole_id'],
                    target_id=target_id,
                    label='A',
                    x_coord=hole['coordinates']['x_mm'],
                    y_coord=hole['coordinates']['y_mm'],
                    row_index=row_index,
                    ab_sequence=ab_seq
                )
                self.mapping_rules.append(rule)
            
            # 为B标签孔位分配编号
            for ab_seq, hole in enumerate(b_holes, 1):
                target_id = self._generate_target_id('B', row_index, ab_seq)
                
                rule = ABLabelMappingRule(
                    original_id=hole['hole_id'],
                    target_id=target_id,
                    label='B',
                    x_coord=hole['coordinates']['x_mm'],
                    y_coord=hole['coordinates']['y_mm'],
                    row_index=row_index,
                    ab_sequence=ab_seq
                )
                self.mapping_rules.append(rule)
        
        print(f"✅ 已生成 {len(self.mapping_rules)} 个A/B标签映射")
    
    def _generate_target_id(self, label: str, row_index: int, ab_sequence: int) -> str:
        """
        生成目标编号
        
        编号逻辑：
        - 列号固定为 C001
        - A标签行号：第1行用 R001,R005,R009... 第2行用 R002,R006,R010...
        - B标签行号：第1行用 R003,R007,R011... 第2行用 R004,R008,R012...
        """
        col = "C001"
        
        if label == 'A':
            if row_index % 2 == 1:  # 奇数行
                # A标签奇数行：R001, R005, R009, R013...
                row_num = 1 + (ab_sequence - 1) * 4
            else:  # 偶数行
                # A标签偶数行：R002, R006, R010, R014...
                row_num = 2 + (ab_sequence - 1) * 4
        else:  # B标签
            if row_index % 2 == 1:  # 奇数行
                # B标签奇数行：R003, R007, R011, R015...
                row_num = 3 + (ab_sequence - 1) * 4
            else:  # 偶数行
                # B标签偶数行：R004, R008, R012, R016...
                row_num = 4 + (ab_sequence - 1) * 4
        
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
        label = "A" if x_coord < 0.1 else "B"
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
                print(f"  {original_id} → {rule.target_id} (标签:{rule.label}, 行{rule.row_index}, {rule.label}序号{rule.ab_sequence})")
    
    def analyze_ab_distribution(self):
        """
        分析A/B标签的分布情况
        """
        print("📊 A/B标签分布分析:")
        
        # 统计每行的A/B分布
        row_stats = {}
        for rule in self.mapping_rules:
            row = rule.row_index
            if row not in row_stats:
                row_stats[row] = {'A': [], 'B': []}
            row_stats[row][rule.label].append(rule.target_id)
        
        # 显示前几行的分布
        for row in sorted(row_stats.keys())[:5]:
            print(f"\n第{row}行:")
            print(f"  A标签: {len(row_stats[row]['A'])}个 → {row_stats[row]['A'][:3]}...")
            print(f"  B标签: {len(row_stats[row]['B'])}个 → {row_stats[row]['B'][:3]}...")
    
    def get_mapping_statistics(self) -> Dict:
        """
        获取映射统计信息
        """
        if not self.mapping_rules:
            return {}
        
        a_count = sum(1 for rule in self.mapping_rules if rule.label == 'A')
        b_count = sum(1 for rule in self.mapping_rules if rule.label == 'B')
        
        # 分析行号分布
        target_rows = [int(rule.target_id[5:8]) for rule in self.mapping_rules]
        
        return {
            "total_holes": len(self.mapping_rules),
            "a_labels": a_count,
            "b_labels": b_count,
            "target_row_range": (min(target_rows), max(target_rows)),
            "unique_target_rows": len(set(target_rows))
        }
    
    def export_sample_mappings(self, output_file: str):
        """
        导出示例映射
        """
        # 获取前几行的映射作为示例
        sample_data = {
            "mapping_logic": "A/B标签奇偶行编号系统",
            "description": {
                "A标签_奇数行": "R001, R005, R009, R013...",
                "A标签_偶数行": "R002, R006, R010, R014...", 
                "B标签_奇数行": "R003, R007, R011, R015...",
                "B标签_偶数行": "R004, R008, R012, R016..."
            },
            "key_mappings": [],
            "statistics": self.get_mapping_statistics()
        }
        
        # 添加关键映射示例
        key_holes = ['C007R001', 'C008R001', 'C006R001', 'C009R001']
        for original_id in key_holes:
            rule = next((r for r in self.mapping_rules if r.original_id == original_id), None)
            if rule:
                sample_data["key_mappings"].append({
                    "original_id": rule.original_id,
                    "target_id": rule.target_id,
                    "label": rule.label,
                    "coordinates": {"x_mm": rule.x_coord, "y_mm": rule.y_coord},
                    "row_index": rule.row_index,
                    "ab_sequence": rule.ab_sequence
                })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 示例映射已导出到: {output_file}")


# 测试和演示
if __name__ == "__main__":
    print("🚀 A/B标签奇偶行编号映射器测试")
    print("=" * 60)
    
    mapper = ABLabelHoleMapper()
    
    try:
        json_file = "assets/dxf/DXF Graph/dongzhong_hole_grid.json"
        mapper.load_training_data(json_file)
        
        # 验证关键映射
        mapper.verify_key_mappings()
        
        # 分析A/B分布
        mapper.analyze_ab_distribution()
        
        # 统计信息
        stats = mapper.get_mapping_statistics()
        print(f"\n📈 映射统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # 导出示例
        mapper.export_sample_mappings("ab_label_mapping.json")
        
    except FileNotFoundError:
        print("⚠️ 数据文件未找到")
    except Exception as e:
        print(f"❌ 测试失败: {e}")