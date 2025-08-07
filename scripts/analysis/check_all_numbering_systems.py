#!/usr/bin/env python3
"""
检查系统中所有的编号方式
"""

import sys
import re
from pathlib import Path
from collections import defaultdict

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core_business.dxf_parser import DXFParser
from src.core_business.models.hole_data import HoleData


def analyze_numbering_systems():
    """分析所有编号系统"""
    print("🔍 分析系统中的所有编号方式\n")
    
    try:
        # 1. 从DXF文件加载数据
        parser = DXFParser()
        hole_collection = parser.parse_file("Data/Products/CAP1000/dxf/CAP1000.dxf")
        
        print(f"总孔位数: {len(hole_collection.holes)}\n")
        
        # 2. 分析编号模式
        patterns = defaultdict(list)
        
        for hole_id in hole_collection.holes.keys():
            # 尝试匹配不同的编号模式
            
            # 模式1: ACxxxRxxx 或 BCxxxRxxx (A/B侧编号)
            if match := re.match(r'^([AB])C(\d{3})R(\d{3})$', hole_id):
                side = match.group(1)
                col = int(match.group(2))
                row = int(match.group(3))
                patterns['A/B侧编号'].append({
                    'id': hole_id,
                    'side': side,
                    'col': col,
                    'row': row
                })
            
            # 模式2: CxxxRxxx (无侧标记)
            elif match := re.match(r'^C(\d{3})R(\d{3})$', hole_id):
                col = int(match.group(1))
                row = int(match.group(2))
                patterns['无侧标记编号'].append({
                    'id': hole_id,
                    'col': col,
                    'row': row
                })
            
            # 模式3: 其他格式
            else:
                patterns['其他格式'].append(hole_id)
        
        # 3. 显示统计结果
        print("编号系统统计:")
        print("=" * 60)
        
        for pattern_name, items in patterns.items():
            print(f"\n{pattern_name}: {len(items)} 个")
            
            if pattern_name == 'A/B侧编号':
                # 统计A侧和B侧
                a_count = sum(1 for item in items if item['side'] == 'A')
                b_count = sum(1 for item in items if item['side'] == 'B')
                print(f"  - A侧 (ACxxxRxxx): {a_count} 个")
                print(f"  - B侧 (BCxxxRxxx): {b_count} 个")
                
                # 显示示例
                print(f"  示例:")
                for item in items[:5]:
                    print(f"    {item['id']}")
                    
            elif pattern_name == '无侧标记编号':
                print(f"  示例:")
                for item in items[:5]:
                    print(f"    {item['id']}")
                    
            elif pattern_name == '其他格式' and items:
                print(f"  示例:")
                for item in items[:5]:
                    print(f"    {item}")
        
        # 4. 检查特定孔位的所有属性
        print("\n\n检查特定孔位的属性:")
        print("=" * 60)
        
        # 查找一个示例孔位
        sample_hole_id = None
        sample_hole = None
        for hole_id, hole in hole_collection.holes.items():
            if "C098R164" in hole_id:
                sample_hole_id = hole_id
                sample_hole = hole
                break
        
        if sample_hole:
            print(f"\n示例孔位: {sample_hole_id}")
            print(f"属性:")
            
            # 检查所有属性
            attrs = dir(sample_hole)
            for attr in attrs:
                if not attr.startswith('_'):
                    try:
                        value = getattr(sample_hole, attr)
                        if not callable(value):
                            print(f"  - {attr}: {value}")
                    except:
                        pass
            
            # 特别检查是否有多个ID属性
            if hasattr(sample_hole, 'standard_id'):
                print(f"\n标准ID: {sample_hole.standard_id}")
            if hasattr(sample_hole, 'original_id'):
                print(f"原始ID: {sample_hole.original_id}")
            if hasattr(sample_hole, 'display_id'):
                print(f"显示ID: {sample_hole.display_id}")
                
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    analyze_numbering_systems()