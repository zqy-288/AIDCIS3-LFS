#!/usr/bin/env python3
"""
精确的孔位重新编号脚本
专门用于将C001R165->C001R001, C001R167->C001R003的模式应用到所有孔位
"""

import json
import re
from typing import Dict, List, Tuple

class PreciseHoleRenumbering:
    """精确的孔位重新编号类"""
    
    def __init__(self):
        self.original_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/dongzhong_hole_grid.json"
        self.output_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/dongzhong_hole_grid_precise_renumbered.json"
        self.mapping_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/precise_hole_id_mapping.json"
        
    def understand_user_pattern(self) -> Tuple[int, int, int]:
        """
        理解用户的编号模式
        从用户示例: C001R165->C001R001, C001R167->C001R003
        
        返回: (起始旧行号, 起始新行号, 步长)
        """
        # 分析模式:
        # 旧编号 165 -> 新编号 1  (差值: 164)
        # 旧编号 167 -> 新编号 3  (差值: 164)
        # 步长: 167-165 = 2, 3-1 = 2 (保持一致)
        
        old_start = 165  # 起始的旧行号
        new_start = 1    # 起始的新行号
        step = 2         # 步长，从示例看是每隔一个
        
        return old_start, new_start, step
    
    def create_comprehensive_mapping(self, data: Dict) -> Dict[str, str]:
        """
        创建全面的重新编号映射
        基于用户的模式，但应用到所有孔位
        """
        holes = data.get('holes', [])
        
        # 收集所有唯一的行号，按列分组
        rows_by_column = {}
        
        for hole in holes:
            hole_id = hole.get('hole_id', '')
            match = re.match(r'C(\d+)R(\d+)', hole_id)
            if match:
                col_num = int(match.group(1))
                row_num = int(match.group(2))
                
                if col_num not in rows_by_column:
                    rows_by_column[col_num] = set()
                rows_by_column[col_num].add(row_num)
        
        # 为每一列创建行号映射
        mapping = {}
        
        for col_num in sorted(rows_by_column.keys()):
            rows = sorted(rows_by_column[col_num])
            
            # 应用重新编号逻辑
            # 方案1: 连续重新编号 (从1开始)
            for new_row, old_row in enumerate(rows, 1):
                old_id = f"C{col_num:03d}R{old_row:03d}"
                new_id = f"C{col_num:03d}R{new_row:03d}"
                mapping[old_id] = new_id
                
        return mapping
    
    def create_pattern_based_mapping(self, data: Dict) -> Dict[str, str]:
        """
        基于用户具体模式的映射 (165->1, 167->3)
        这个模式似乎是选择性重新编号，只针对特定的行
        """
        holes = data.get('holes', [])
        
        # 定义用户的映射模式
        user_pattern = {
            165: 1,   # C001R165 -> C001R001
            167: 3,   # C001R167 -> C001R003
            # 可以扩展更多模式...
        }
        
        # 收集所有唯一的行号
        all_rows = set()
        for hole in holes:
            hole_id = hole.get('hole_id', '')
            match = re.match(r'C(\d+)R(\d+)', hole_id)
            if match:
                row_num = int(match.group(2))
                all_rows.add(row_num)
        
        # 扩展模式到所有行
        # 假设模式是: 从165开始，每隔一个行映射到奇数编号
        sorted_rows = sorted(all_rows)
        extended_pattern = {}
        
        # 找到165的位置
        if 165 in sorted_rows:
            start_index = sorted_rows.index(165)
            
            # 从165开始，每隔一个行号，映射到1,3,5,7...
            new_odd = 1
            for i in range(start_index, len(sorted_rows), 2):
                extended_pattern[sorted_rows[i]] = new_odd
                new_odd += 2
            
            # 处理165之前的行号，映射到偶数或剩余编号
            new_even = 2
            for i in range(start_index + 1, len(sorted_rows), 2):
                extended_pattern[sorted_rows[i]] = new_even
                new_even += 2
        
        # 创建完整的ID映射
        mapping = {}
        for hole in holes:
            hole_id = hole.get('hole_id', '')
            match = re.match(r'C(\d+)R(\d+)', hole_id)
            if match:
                col_num = int(match.group(1))
                old_row = int(match.group(2))
                
                if old_row in extended_pattern:
                    new_row = extended_pattern[old_row]
                    new_id = f"C{col_num:03d}R{new_row:03d}"
                    mapping[hole_id] = new_id
                else:
                    # 保持原有编号
                    mapping[hole_id] = hole_id
        
        return mapping
    
    def apply_mapping(self, data: Dict, mapping: Dict[str, str]) -> Dict:
        """应用映射到数据"""
        holes = data.get('holes', [])
        
        for hole in holes:
            old_id = hole.get('hole_id', '')
            if old_id in mapping:
                hole['hole_id'] = mapping[old_id]
        
        return data
    
    def generate_mapping_preview(self, mapping: Dict[str, str], limit: int = 20) -> str:
        """生成映射预览"""
        lines = []
        lines.append("编号映射预览:")
        lines.append("=" * 40)
        
        # 显示用户关心的具体示例
        examples = ['C001R165', 'C001R167', 'C001R169', 'C002R165', 'C002R167']
        
        lines.append("用户示例映射:")
        for example in examples:
            if example in mapping:
                lines.append(f"  {example} -> {mapping[example]}")
        
        lines.append("")
        lines.append(f"所有映射预览 (前{limit}个):")
        
        sorted_mappings = sorted(mapping.items())[:limit]
        for old_id, new_id in sorted_mappings:
            if old_id != new_id:  # 只显示有变化的
                lines.append(f"  {old_id} -> {new_id}")
        
        lines.append(f"...")
        lines.append(f"总共 {len(mapping)} 个孔位，其中 {sum(1 for k, v in mapping.items() if k != v)} 个有变化")
        
        return "\n".join(lines)
    
    def execute_renumbering(self, method: str = "comprehensive"):
        """执行重新编号"""
        print("正在读取原始数据...")
        
        try:
            with open(self.original_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"错误: 找不到文件 {self.original_file}")
            return False
        
        print("创建重新编号映射...")
        
        if method == "comprehensive":
            # 全面重新编号：每列从R001开始连续编号
            mapping = self.create_comprehensive_mapping(data)
            method_desc = "全面重新编号 (每列从R001开始)"
        elif method == "pattern":
            # 基于用户模式的选择性重新编号
            mapping = self.create_pattern_based_mapping(data)
            method_desc = "基于用户模式的选择性重新编号"
        else:
            print(f"未知方法: {method}")
            return False
        
        print(f"使用方法: {method_desc}")
        
        # 显示映射预览
        preview = self.generate_mapping_preview(mapping)
        print("\n" + preview)
        
        # 应用映射
        print("\n应用重新编号...")
        new_data = self.apply_mapping(data.copy(), mapping)
        
        # 保存结果
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
        
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        
        print(f"\n重新编号完成!")
        print(f"输出文件: {self.output_file}")
        print(f"映射文件: {self.mapping_file}")
        
        return True

def main():
    """主函数"""
    renumberer = PreciseHoleRenumbering()
    
    print("精确孔位重新编号工具")
    print("=" * 30)
    print("基于您的示例: C001R165->C001R001, C001R167->C001R003")
    print()
    print("可用方法:")
    print("1. comprehensive: 全面重新编号 (推荐)")
    print("   - 每列的行号从R001开始连续编号")
    print("   - C001R165变成C001R001, C001R166变成C001R002, 等等")
    print()
    print("2. pattern: 基于模式的选择性重新编号")
    print("   - 严格按照165->1, 167->3的隔行模式")
    print("   - 保持您示例中的跳跃编号特征")
    print()
    
    # 默认使用全面重新编号
    print("正在执行全面重新编号...")
    success = renumberer.execute_renumbering("comprehensive")
    
    if success:
        print("\n如果需要使用模式编号，请修改main()中的方法参数为'pattern'")

if __name__ == "__main__":
    main()