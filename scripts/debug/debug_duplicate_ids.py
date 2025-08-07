#!/usr/bin/env python3
"""
调试重复ID问题
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core_business.dxf_parser import DXFParser

def debug_duplicate_ids():
    """调试重复ID"""
    print("🔍 调试孔位ID问题\n")
    
    try:
        parser = DXFParser()
        hole_collection = parser.parse_file("Data/Products/CAP1000/dxf/CAP1000.dxf")
        
        print(f"总孔位数: {len(hole_collection.holes)}")
        
        # 查找包含C098R164的所有ID
        c098r164_ids = []
        for hole_id in hole_collection.holes.keys():
            if "C098R164" in hole_id:
                c098r164_ids.append(hole_id)
        
        print(f"\n包含'C098R164'的所有ID:")
        for id in c098r164_ids:
            hole = hole_collection.holes[id]
            print(f"  - {id} (坐标: {hole.center_x:.1f}, {hole.center_y:.1f})")
        
        # 检查特定坐标的孔位
        print(f"\n查找特定坐标附近的孔位:")
        target_x = None
        for hole_id, hole in hole_collection.holes.items():
            if "C098R164" in hole_id:
                target_x = hole.center_x
                target_y = hole.center_y
                break
        
        if target_x:
            print(f"目标坐标: ({target_x:.1f}, {target_y:.1f})")
            nearby_holes = []
            for hole_id, hole in hole_collection.holes.items():
                if abs(hole.center_x - target_x) < 1 and abs(hole.center_y - target_y) < 1:
                    nearby_holes.append((hole_id, hole))
            
            print(f"\n该坐标处的所有孔位:")
            for hole_id, hole in nearby_holes:
                print(f"  - {hole_id}")
                
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_duplicate_ids()