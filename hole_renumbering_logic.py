#!/usr/bin/env python3
"""
孔位编号重新映射逻辑
将C001R165 -> C001R001, C001R167 -> C001R003 等规律进行重新编号
"""

import json
import re
from typing import Dict, List, Tuple

class HoleRenumberingLogic:
    """孔位重新编号逻辑类"""
    
    def __init__(self):
        self.original_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/dongzhong_hole_grid.json"
        self.output_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/dongzhong_hole_grid_renumbered.json"
        self.mapping_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/hole_id_mapping.json"
        
    def analyze_current_numbering(self, data: Dict) -> Dict:
        """分析当前编号系统"""
        holes = data.get('holes', [])
        
        # 提取所有行号
        row_numbers = set()
        col_numbers = set()
        
        for hole in holes:
            hole_id = hole.get('hole_id', '')
            match = re.match(r'C(\d+)R(\d+)', hole_id)
            if match:
                col_num = int(match.group(1))
                row_num = int(match.group(2))
                col_numbers.add(col_num)
                row_numbers.add(row_num)
        
        return {
            'total_holes': len(holes),
            'row_range': (min(row_numbers), max(row_numbers)),
            'col_range': (min(col_numbers), max(col_numbers)),
            'unique_rows': sorted(row_numbers),
            'unique_cols': sorted(col_numbers),
            'row_count': len(row_numbers),
            'col_count': len(col_numbers)
        }
    
    def create_renumbering_strategy_1(self, analysis: Dict) -> Dict[int, int]:
        """
        策略1: 紧密编号 - 移除空隙
        将现有的行号重新映射为连续的1,2,3...序列
        """
        unique_rows = analysis['unique_rows']
        mapping = {}
        
        for new_row, old_row in enumerate(unique_rows, 1):
            mapping[old_row] = new_row
            
        return mapping
    
    def create_renumbering_strategy_2(self, analysis: Dict, start_from: int = 165) -> Dict[int, int]:
        """
        策略2: 指定起点重新编号
        从指定行号开始，重新编号为从1开始的序列
        """
        unique_rows = analysis['unique_rows']
        
        # 找到起始行的索引
        try:
            start_index = unique_rows.index(start_from)
        except ValueError:
            # 如果指定行不存在，从最接近的行开始
            start_index = 0
            for i, row in enumerate(unique_rows):
                if row >= start_from:
                    start_index = i
                    break
        
        mapping = {}
        
        # 从指定行开始重新编号
        for i, old_row in enumerate(unique_rows[start_index:], 1):
            mapping[old_row] = i
            
        # 处理指定行之前的行（如果有）
        if start_index > 0:
            remaining_rows = unique_rows[:start_index]
            next_number = len(unique_rows) - start_index + 1
            for old_row in remaining_rows:
                mapping[old_row] = next_number
                next_number += 1
                
        return mapping
    
    def create_renumbering_strategy_3(self, analysis: Dict) -> Dict[int, int]:
        """
        策略3: 基于您的示例模式
        C001R165 -> C001R001, C001R167 -> C001R003
        即每隔一个编号，从165开始映射到1开始
        """
        unique_rows = analysis['unique_rows']
        mapping = {}
        
        # 寻找R165的位置
        try:
            start_index = unique_rows.index(165)
        except ValueError:
            print("警告: 未找到R165，使用第一个行作为起点")
            start_index = 0
        
        # 按照您的示例：165->1, 167->3 的模式
        # 这意味着每隔一个行号，重新编号
        new_row = 1
        for i in range(start_index, len(unique_rows), 2):  # 每隔一个
            if i < len(unique_rows):
                mapping[unique_rows[i]] = new_row
                new_row += 2  # 奇数编号：1, 3, 5, 7...
        
        # 处理偶数位置的行（如果需要）
        new_row = 2
        for i in range(start_index + 1, len(unique_rows), 2):  # 偶数位置
            if i < len(unique_rows):
                mapping[unique_rows[i]] = new_row
                new_row += 2  # 偶数编号：2, 4, 6, 8...
        
        return mapping
    
    def apply_renumbering(self, data: Dict, row_mapping: Dict[int, int]) -> Tuple[Dict, Dict[str, str]]:
        """应用重新编号逻辑"""
        holes = data.get('holes', [])
        id_mapping = {}  # 记录ID变化
        
        for hole in holes:
            old_hole_id = hole.get('hole_id', '')
            match = re.match(r'C(\d+)R(\d+)', old_hole_id)
            
            if match:
                col_num = int(match.group(1))
                old_row_num = int(match.group(2))
                
                if old_row_num in row_mapping:
                    new_row_num = row_mapping[old_row_num]
                    new_hole_id = f"C{col_num:03d}R{new_row_num:03d}"
                    
                    # 更新孔位ID
                    hole['hole_id'] = new_hole_id
                    id_mapping[old_hole_id] = new_hole_id
        
        return data, id_mapping
    
    def generate_mapping_report(self, analysis: Dict, strategies: Dict[str, Dict[int, int]]) -> str:
        """生成映射报告"""
        report = []
        report.append("# 孔位编号重新映射分析报告")
        report.append("=" * 50)
        report.append("")
        
        # 当前状态分析
        report.append("## 当前编号系统分析")
        report.append(f"- 总孔位数: {analysis['total_holes']}")
        report.append(f"- 行范围: R{analysis['row_range'][0]:03d} - R{analysis['row_range'][1]:03d}")
        report.append(f"- 列范围: C{analysis['col_range'][0]:03d} - C{analysis['col_range'][1]:03d}")
        report.append(f"- 唯一行数: {analysis['row_count']}")
        report.append(f"- 唯一列数: {analysis['col_count']}")
        report.append("")
        
        # 显示当前行分布（前20个和后20个）
        unique_rows = analysis['unique_rows']
        report.append("## 当前行号分布")
        report.append("前20个行号:")
        report.append(", ".join([f"R{r:03d}" for r in unique_rows[:20]]))
        if len(unique_rows) > 40:
            report.append("...")
            report.append("后20个行号:")
            report.append(", ".join([f"R{r:03d}" for r in unique_rows[-20:]]))
        report.append("")
        
        # 各种策略的映射结果
        for strategy_name, mapping in strategies.items():
            report.append(f"## {strategy_name}")
            report.append("映射规则示例 (前10个):")
            
            sorted_mapping = sorted(mapping.items())[:10]
            for old_row, new_row in sorted_mapping:
                report.append(f"  R{old_row:03d} -> R{new_row:03d}")
            
            if len(mapping) > 10:
                report.append("  ...")
                report.append(f"  (共{len(mapping)}个映射)")
            report.append("")
        
        return "\n".join(report)
    
    def execute_renumbering(self, strategy: str = "strategy_1"):
        """执行重新编号"""
        print("正在读取原始数据...")
        
        try:
            with open(self.original_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"错误: 找不到文件 {self.original_file}")
            return False
        except json.JSONDecodeError:
            print(f"错误: JSON格式错误 {self.original_file}")
            return False
        
        print("分析当前编号系统...")
        analysis = self.analyze_current_numbering(data)
        
        # 创建不同的重新编号策略
        strategies = {
            "策略1: 紧密编号": self.create_renumbering_strategy_1(analysis),
            "策略2: 从R165开始重新编号": self.create_renumbering_strategy_2(analysis, 165),
            "策略3: 按您的示例模式 (165->1, 167->3)": self.create_renumbering_strategy_3(analysis)
        }
        
        # 生成报告
        report = self.generate_mapping_report(analysis, strategies)
        
        # 保存报告
        report_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/renumbering_analysis_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"分析报告已保存到: {report_file}")
        
        # 选择策略并应用
        if strategy == "strategy_1":
            chosen_mapping = strategies["策略1: 紧密编号"]
            strategy_name = "策略1"
        elif strategy == "strategy_2":
            chosen_mapping = strategies["策略2: 从R165开始重新编号"]
            strategy_name = "策略2"
        elif strategy == "strategy_3":
            chosen_mapping = strategies["策略3: 按您的示例模式 (165->1, 167->3)"]
            strategy_name = "策略3"
        else:
            print(f"未知策略: {strategy}")
            return False
        
        print(f"应用{strategy_name}...")
        new_data, id_mapping = self.apply_renumbering(data.copy(), chosen_mapping)
        
        # 保存重新编号后的数据
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
        
        # 保存ID映射表
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            json.dump(id_mapping, f, indent=2, ensure_ascii=False)
        
        print(f"重新编号完成!")
        print(f"新数据文件: {self.output_file}")
        print(f"ID映射表: {self.mapping_file}")
        print(f"分析报告: {report_file}")
        
        # 显示一些示例映射
        print("\n示例映射:")
        example_mappings = list(id_mapping.items())[:5]
        for old_id, new_id in example_mappings:
            print(f"  {old_id} -> {new_id}")
        
        if len(id_mapping) > 5:
            print(f"  ... (共{len(id_mapping)}个映射)")
        
        return True

def main():
    """主函数"""
    renumberer = HoleRenumberingLogic()
    
    print("孔位编号重新映射工具")
    print("=" * 30)
    print("可用策略:")
    print("1. strategy_1: 紧密编号 (移除所有间隙)")
    print("2. strategy_2: 从R165开始重新编号为R001开始")
    print("3. strategy_3: 按您的示例模式 (165->1, 167->3, 即隔行编号)")
    print()
    
    # 首先生成分析报告
    print("正在生成分析报告...")
    renumberer.execute_renumbering("strategy_1")  # 生成报告
    
    print("\n请查看生成的分析报告，然后选择适合的策略:")
    print("报告文件: /Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/renumbering_analysis_report.txt")

if __name__ == "__main__":
    main()