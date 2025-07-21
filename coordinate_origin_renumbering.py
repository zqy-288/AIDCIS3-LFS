#!/usr/bin/env python3
"""
方案B: 重新定义坐标原点
以指定位置为新的(1,1)点重新编号孔位
"""

import json
import re
from typing import Dict, List, Tuple, Optional

class CoordinateOriginRenumbering:
    """坐标原点重新定义类"""
    
    def __init__(self):
        self.original_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/dongzhong_hole_grid.json"
        self.output_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/dongzhong_reorigin_renumbered.json"
        self.mapping_file = "/Users/vsiyo/Desktop/AIDCIS3-LFS/assets/dxf/DXF Graph/reorigin_mapping.json"
        
    def parse_hole_id(self, hole_id: str) -> Tuple[int, int]:
        """解析孔位ID，返回(列号, 行号)"""
        match = re.match(r'C(\d+)R(\d+)', hole_id)
        if match:
            return int(match.group(1)), int(match.group(2))
        return 0, 0
    
    def analyze_data_around_origin(self, data: Dict, origin_col: int, origin_row: int) -> Dict:
        """分析指定原点周围的数据分布"""
        holes = data.get('holes', [])
        
        origin_exists = False
        nearby_holes = []
        all_positions = []
        
        for hole in holes:
            col, row = self.parse_hole_id(hole.get('hole_id', ''))
            if col > 0 and row > 0:
                all_positions.append((col, row))
                
                # 检查原点是否存在
                if col == origin_col and row == origin_row:
                    origin_exists = True
                
                # 收集原点周围的孔位（±5范围内）
                if abs(col - origin_col) <= 5 and abs(row - origin_row) <= 5:
                    nearby_holes.append({
                        'hole_id': hole.get('hole_id'),
                        'col': col,
                        'row': row,
                        'relative_col': col - origin_col,
                        'relative_row': row - origin_row
                    })
        
        # 计算在新坐标系中有效的孔位数量
        valid_holes = 0
        for col, row in all_positions:
            new_col = col - origin_col + 1
            new_row = row - origin_row + 1
            if new_col > 0 and new_row > 0:
                valid_holes += 1
        
        return {
            'origin_exists': origin_exists,
            'total_holes': len(holes),
            'valid_holes_after_reorigin': valid_holes,
            'invalid_holes': len(holes) - valid_holes,
            'nearby_holes': sorted(nearby_holes, key=lambda x: (x['relative_row'], x['relative_col'])),
            'coverage_ratio': valid_holes / len(holes) if holes else 0
        }
    
    def redefine_coordinate_origin(self, data: Dict, origin_col: int = 1, origin_row: int = 165) -> Dict[str, str]:
        """
        以指定位置为新的(1,1)点重新编号
        
        Args:
            data: 原始数据
            origin_col: 新原点的列号
            origin_row: 新原点的行号
        
        Returns:
            映射字典 {old_id: new_id}
        """
        holes = data.get('holes', [])
        mapping = {}
        
        for hole in holes:
            old_id = hole.get('hole_id', '')
            old_col, old_row = self.parse_hole_id(old_id)
            
            if old_col > 0 and old_row > 0:
                # 计算新坐标
                new_col = old_col - origin_col + 1
                new_row = old_row - origin_row + 1
                
                if new_col > 0 and new_row > 0:  # 只保留正坐标
                    new_id = f"C{new_col:03d}R{new_row:03d}"
                    mapping[old_id] = new_id
                else:
                    # 负坐标的孔位将被排除（不在新坐标系中）
                    mapping[old_id] = None  # 标记为排除
            else:
                mapping[old_id] = old_id  # 无效ID保持不变
        
        return mapping
    
    def preview_coordinate_change(self, mapping: Dict[str, str], origin_col: int, origin_row: int) -> str:
        """预览坐标变化"""
        lines = []
        lines.append("🎯 坐标原点重新定义预览")
        lines.append("=" * 50)
        lines.append(f"新原点: C{origin_col:03d}R{origin_row:03d} → C001R001")
        lines.append("")
        
        # 统计
        valid_mappings = {k: v for k, v in mapping.items() if v is not None and v != k}
        excluded_mappings = {k: v for k, v in mapping.items() if v is None}
        unchanged_mappings = {k: v for k, v in mapping.items() if v == k}
        
        lines.append("📊 映射统计:")
        lines.append(f"   有效重新编号: {len(valid_mappings)} 个")
        lines.append(f"   排除的孔位: {len(excluded_mappings)} 个 (负坐标)")
        lines.append(f"   保持不变: {len(unchanged_mappings)} 个")
        lines.append(f"   总计: {len(mapping)} 个")
        lines.append("")
        
        # 显示关键映射示例
        lines.append("🔍 关键映射示例:")
        
        # 原点映射
        origin_old_id = f"C{origin_col:03d}R{origin_row:03d}"
        if origin_old_id in mapping:
            lines.append(f"   原点: {origin_old_id} → {mapping[origin_old_id]}")
        
        # 其他示例
        example_count = 0
        for old_id, new_id in valid_mappings.items():
            if example_count < 8 and old_id != origin_old_id:
                lines.append(f"   {old_id} → {new_id}")
                example_count += 1
        
        if len(valid_mappings) > 8:
            lines.append(f"   ... 还有 {len(valid_mappings) - 8} 个映射")
        
        # 显示被排除的示例
        if excluded_mappings:
            lines.append("")
            lines.append("⚠️  被排除的孔位示例 (负坐标):")
            for i, (old_id, _) in enumerate(list(excluded_mappings.items())[:5]):
                old_col, old_row = self.parse_hole_id(old_id)
                new_col = old_col - origin_col + 1
                new_row = old_row - origin_row + 1
                lines.append(f"   {old_id} → (C{new_col:+04d}R{new_row:+04d}) - 排除")
            
            if len(excluded_mappings) > 5:
                lines.append(f"   ... 还有 {len(excluded_mappings) - 5} 个被排除")
        
        return "\n".join(lines)
    
    def apply_mapping_with_exclusion(self, data: Dict, mapping: Dict[str, str]) -> Dict:
        """应用映射，排除负坐标的孔位"""
        new_data = data.copy()
        original_holes = new_data.get('holes', [])
        valid_holes = []
        
        for hole in original_holes:
            old_id = hole.get('hole_id', '')
            if old_id in mapping and mapping[old_id] is not None:
                new_hole = hole.copy()
                new_hole['hole_id'] = mapping[old_id]
                valid_holes.append(new_hole)
        
        new_data['holes'] = valid_holes
        return new_data
    
    def save_results(self, data: Dict, mapping: Dict[str, str], origin_col: int, origin_row: int):
        """保存结果"""
        # 保存重新编号后的数据
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 准备映射信息
        valid_mappings = {k: v for k, v in mapping.items() if v is not None}
        excluded_mappings = [k for k, v in mapping.items() if v is None]
        
        mapping_info = {
            'strategy': 'coordinate_origin_redefinition',
            'new_origin': f"C{origin_col:03d}R{origin_row:03d}",
            'original_hole_count': len(mapping),
            'valid_hole_count': len(valid_mappings),
            'excluded_hole_count': len(excluded_mappings),
            'excluded_holes': excluded_mappings,
            'mappings': valid_mappings
        }
        
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            json.dump(mapping_info, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 结果已保存:")
        print(f"   数据文件: {self.output_file}")
        print(f"   映射文件: {self.mapping_file}")
    
    def run_coordinate_renumbering(self):
        """运行坐标原点重新定义"""
        print("🎯 方案B: 重新定义坐标原点")
        print("=" * 50)
        
        # 读取数据
        try:
            with open(self.original_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 成功读取数据文件")
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return
        
        print(f"📊 原始数据: {len(data.get('holes', []))} 个孔位")
        
        # 使用您示例中的参数：C001R165→C001R001
        print(f"\n🎯 使用您示例中的坐标原点:")
        print(f"   C001R165 → C001R001")
        print(f"   即以 C001R165 为新的原点(1,1)")
        
        origin_col = 1
        origin_row = 165
        
        print(f"✅ 设置新原点: C{origin_col:03d}R{origin_row:03d}")
        
        # 分析原点周围数据
        print(f"\n🔍 分析新原点 C{origin_col:03d}R{origin_row:03d} 周围的数据...")
        analysis = self.analyze_data_around_origin(data, origin_col, origin_row)
        
        print(f"   原点位置存在孔位: {'是' if analysis['origin_exists'] else '否'}")
        print(f"   重新编号后有效孔位: {analysis['valid_holes_after_reorigin']}")
        print(f"   将被排除的孔位: {analysis['invalid_holes']}")
        print(f"   数据覆盖率: {analysis['coverage_ratio']:.1%}")
        
        if analysis['coverage_ratio'] < 0.5:
            print(f"⚠️  警告: 数据覆盖率较低({analysis['coverage_ratio']:.1%})，大量孔位将被排除")
            print(f"💡 这是正常的，因为新原点设在中间位置，前面的孔位会被排除")
        
        # 执行重新编号
        print(f"\n🔄 执行坐标原点重新定义...")
        mapping = self.redefine_coordinate_origin(data, origin_col, origin_row)
        
        # 预览结果
        preview = self.preview_coordinate_change(mapping, origin_col, origin_row)
        print(f"\n{preview}")
        
        # 直接执行保存
        print("💾 正在保存结果...")
        new_data = self.apply_mapping_with_exclusion(data, mapping)
        self.save_results(new_data, mapping, origin_col, origin_row)
        print("✅ 坐标原点重新定义完成!")
        
        # 显示最终统计
        print(f"\n📈 最终结果:")
        print(f"   原始孔位: {len(data.get('holes', []))}")
        print(f"   新坐标系孔位: {len(new_data.get('holes', []))}")
        print(f"   新原点: C{origin_col:03d}R{origin_row:03d} → C001R001")

def main():
    """主函数"""
    renumberer = CoordinateOriginRenumbering()
    renumberer.run_coordinate_renumbering()

if __name__ == "__main__":
    main()