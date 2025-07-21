#!/usr/bin/env python3
"""
交互式孔位重新编号工具
根据用户需求提供多种编号策略
"""

import json
import re
from typing import Dict, List, Tuple, Optional

class InteractiveHoleRenumbering:
    """交互式孔位重新编号类"""
    
    def __init__(self):
        self.original_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/dongzhong_hole_grid.json"
        self.output_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/dongzhong_hole_grid_final.json"
        self.mapping_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/final_hole_id_mapping.json"
        
    def parse_hole_id(self, hole_id: str) -> Tuple[int, int]:
        """解析孔位ID，返回(列号, 行号)"""
        match = re.match(r'C(\d+)R(\d+)', hole_id)
        if match:
            return int(match.group(1)), int(match.group(2))
        return 0, 0
    
    def analyze_data_structure(self, data: Dict) -> Dict:
        """分析数据结构"""
        holes = data.get('holes', [])
        
        cols = set()
        rows = set()
        col_row_pairs = set()
        
        for hole in holes:
            col, row = self.parse_hole_id(hole.get('hole_id', ''))
            if col > 0 and row > 0:
                cols.add(col)
                rows.add(row)
                col_row_pairs.add((col, row))
        
        return {
            'total_holes': len(holes),
            'columns': sorted(cols),
            'rows': sorted(rows),
            'col_count': len(cols),
            'row_count': len(rows),
            'col_range': (min(cols), max(cols)),
            'row_range': (min(rows), max(rows)),
            'density': len(col_row_pairs) / (len(cols) * len(rows)) if cols and rows else 0
        }
    
    def strategy_1_sequential(self, data: Dict) -> Dict[str, str]:
        """策略1: 连续序列编号 (00001, 00002, ...)"""
        holes = data.get('holes', [])
        mapping = {}
        
        # 按原有顺序重新编号
        for i, hole in enumerate(holes, 1):
            old_id = hole.get('hole_id', '')
            new_id = f"{i:05d}"
            mapping[old_id] = new_id
        
        return mapping
    
    def strategy_2_offset_rows(self, data: Dict, offset: int = 164) -> Dict[str, str]:
        """策略2: 行号偏移 (R165->R001, 即减去164)"""
        holes = data.get('holes', [])
        mapping = {}
        
        for hole in holes:
            old_id = hole.get('hole_id', '')
            col, row = self.parse_hole_id(old_id)
            
            if col > 0 and row > 0:
                new_row = row - offset
                if new_row > 0:  # 只保留正数行号
                    new_id = f"C{col:03d}R{new_row:03d}"
                    mapping[old_id] = new_id
                else:
                    # 对于负数行号，可以选择保持原样或其他处理
                    mapping[old_id] = old_id
            else:
                mapping[old_id] = old_id
        
        return mapping
    
    def strategy_3_compact_grid(self, data: Dict) -> Dict[str, str]:
        """策略3: 紧凑网格 (移除空行空列，重新编号)"""
        holes = data.get('holes', [])
        
        # 收集所有存在的行列号
        existing_cols = set()
        existing_rows = set()
        
        for hole in holes:
            col, row = self.parse_hole_id(hole.get('hole_id', ''))
            if col > 0 and row > 0:
                existing_cols.add(col)
                existing_rows.add(row)
        
        # 创建紧凑映射
        col_mapping = {old_col: new_col for new_col, old_col in enumerate(sorted(existing_cols), 1)}
        row_mapping = {old_row: new_row for new_row, old_row in enumerate(sorted(existing_rows), 1)}
        
        mapping = {}
        for hole in holes:
            old_id = hole.get('hole_id', '')
            col, row = self.parse_hole_id(old_id)
            
            if col in col_mapping and row in row_mapping:
                new_col = col_mapping[col]
                new_row = row_mapping[row]
                new_id = f"C{new_col:03d}R{new_row:03d}"
                mapping[old_id] = new_id
            else:
                mapping[old_id] = old_id
        
        return mapping
    
    def strategy_4_custom_range(self, data: Dict, start_row: int = 165, target_start: int = 1) -> Dict[str, str]:
        """策略4: 自定义范围重新编号"""
        holes = data.get('holes', [])
        mapping = {}
        
        offset = start_row - target_start  # 计算偏移量
        
        for hole in holes:
            old_id = hole.get('hole_id', '')
            col, row = self.parse_hole_id(old_id)
            
            if col > 0 and row > 0:
                if row >= start_row:  # 只处理指定行及以后
                    new_row = row - offset
                    new_id = f"C{col:03d}R{new_row:03d}"
                    mapping[old_id] = new_id
                else:
                    mapping[old_id] = old_id  # 保持原编号
            else:
                mapping[old_id] = old_id
        
        return mapping
    
    def preview_mapping(self, mapping: Dict[str, str], limit: int = 10) -> str:
        """预览映射结果"""
        lines = []
        lines.append("映射预览:")
        lines.append("-" * 40)
        
        # 找出有变化的映射
        changed = [(k, v) for k, v in mapping.items() if k != v]
        unchanged = len(mapping) - len(changed)
        
        lines.append(f"总计: {len(mapping)} 个孔位")
        lines.append(f"有变化: {len(changed)} 个")
        lines.append(f"无变化: {unchanged} 个")
        lines.append("")
        
        if changed:
            lines.append(f"变化示例 (前{min(limit, len(changed))}个):")
            for old_id, new_id in changed[:limit]:
                lines.append(f"  {old_id} -> {new_id}")
            
            if len(changed) > limit:
                lines.append(f"  ... 还有 {len(changed) - limit} 个变化")
        
        return "\n".join(lines)
    
    def apply_mapping(self, data: Dict, mapping: Dict[str, str]) -> Dict:
        """应用映射"""
        new_data = data.copy()
        holes = new_data.get('holes', [])
        
        for hole in holes:
            old_id = hole.get('hole_id', '')
            if old_id in mapping:
                hole['hole_id'] = mapping[old_id]
        
        return new_data
    
    def save_results(self, data: Dict, mapping: Dict[str, str], strategy_name: str):
        """保存结果"""
        # 保存重新编号后的数据
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 保存映射表
        mapping_with_info = {
            'strategy': strategy_name,
            'total_mappings': len(mapping),
            'changed_mappings': len([k for k, v in mapping.items() if k != v]),
            'mappings': mapping
        }
        
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mapping_with_info, f, indent=2, ensure_ascii=False)
        
        print(f"\n结果已保存:")
        print(f"数据文件: {self.output_file}")
        print(f"映射文件: {self.mapping_file}")
    
    def run_interactive(self):
        """运行交互式重新编号"""
        print("=" * 50)
        print("🔧 交互式孔位重新编号工具")
        print("=" * 50)
        
        # 读取数据
        try:
            with open(self.original_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 成功读取数据文件: {self.original_file}")
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return
        
        # 分析数据结构
        analysis = self.analyze_data_structure(data)
        print(f"\n📊 数据结构分析:")
        print(f"   总孔位数: {analysis['total_holes']}")
        print(f"   列范围: C{analysis['col_range'][0]:03d} - C{analysis['col_range'][1]:03d} (共{analysis['col_count']}列)")
        print(f"   行范围: R{analysis['row_range'][0]:03d} - R{analysis['row_range'][1]:03d} (共{analysis['row_count']}行)")
        print(f"   网格密度: {analysis['density']:.2%}")
        
        # 显示策略选项
        print(f"\n🎯 可用的重新编号策略:")
        print("1. 连续序列编号 (00001, 00002, 00003, ...)")
        print("2. 行号偏移编号 (R165->R001, R166->R002, ...)")
        print("3. 紧凑网格编号 (移除空行空列)")
        print("4. 自定义范围编号 (指定起始行)")
        print("5. 分析模式后退出")
        
        while True:
            try:
                choice = input(f"\n请选择策略 (1-5): ").strip()
                
                if choice == "1":
                    mapping = self.strategy_1_sequential(data)
                    strategy_name = "连续序列编号"
                    break
                    
                elif choice == "2":
                    offset = input("请输入偏移量 (默认164，即R165->R001): ").strip()
                    offset = int(offset) if offset.isdigit() else 164
                    mapping = self.strategy_2_offset_rows(data, offset)
                    strategy_name = f"行号偏移编号 (偏移-{offset})"
                    break
                    
                elif choice == "3":
                    mapping = self.strategy_3_compact_grid(data)
                    strategy_name = "紧凑网格编号"
                    break
                    
                elif choice == "4":
                    start_row = input("请输入起始行号 (默认165): ").strip()
                    start_row = int(start_row) if start_row.isdigit() else 165
                    target_start = input("请输入目标起始行号 (默认1): ").strip()
                    target_start = int(target_start) if target_start.isdigit() else 1
                    mapping = self.strategy_4_custom_range(data, start_row, target_start)
                    strategy_name = f"自定义范围编号 (R{start_row}->R{target_start})"
                    break
                    
                elif choice == "5":
                    print("分析完成，退出程序。")
                    return
                    
                else:
                    print("❌ 无效选择，请输入1-5之间的数字")
                    
            except KeyboardInterrupt:
                print("\n\n👋 用户取消操作")
                return
            except Exception as e:
                print(f"❌ 输入错误: {e}")
        
        # 预览映射
        preview = self.preview_mapping(mapping)
        print(f"\n📋 {strategy_name} - {preview}")
        
        # 确认执行
        confirm = input(f"\n是否执行此重新编号策略？(y/N): ").strip().lower()
        if confirm in ['y', 'yes']:
            print("🔄 正在应用重新编号...")
            new_data = self.apply_mapping(data, mapping)
            self.save_results(new_data, mapping, strategy_name)
            print("✅ 重新编号完成!")
        else:
            print("❌ 操作已取消")

def main():
    """主函数"""
    renumberer = InteractiveHoleRenumbering()
    renumberer.run_interactive()

if __name__ == "__main__":
    main()