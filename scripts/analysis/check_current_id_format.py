#!/usr/bin/env python3
"""
检查当前ID格式
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core_business.dxf_parser import DXFParser
from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy

def check_id_format():
    """检查ID格式"""
    print("🔍 检查当前孔位ID格式\n")
    
    try:
        dxf_file = "Data/Products/CAP1000/dxf/CAP1000.dxf"
        
        print(f"1. 从DXF解析器获取的ID格式：")
        parser = DXFParser()
        hole_collection = parser.parse_file(dxf_file)
        
        # 查找R164的孔位
        r164_holes = []
        for hole_id, hole in hole_collection.holes.items():
            if "R164" in hole_id:
                r164_holes.append(hole_id)
                if len(r164_holes) >= 5:
                    break
        
        print(f"   R164行的孔位ID示例：")
        for hole_id in r164_holes:
            print(f"   - {hole_id}")
        
        # 生成蛇形路径检查
        print(f"\n2. 蛇形路径渲染器中的ID格式：")
        renderer = SnakePathRenderer()
        renderer.set_hole_collection(hole_collection)
        
        detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
        
        print(f"   前5个检测单元：")
        for i, unit in enumerate(detection_units[:5]):
            if unit.is_pair and len(unit.holes) >= 2:
                hole1_id = unit.holes[0].hole_id
                hole2_id = unit.holes[1].hole_id
                print(f"   {i+1}. {hole1_id} + {hole2_id}")
            else:
                hole_id = unit.holes[0].hole_id
                print(f"   {i+1}. {hole_id} (单孔)")
        
        # 检查特定的孔位
        print(f"\n3. 查找特定孔位：")
        test_ids = ["BC098R164", "AC098R164", "BC102R164", "AC102R164"]
        for test_id in test_ids:
            exists = test_id in hole_collection.holes
            print(f"   {test_id}: {'✓ 存在' if exists else '✗ 不存在'}")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_id_format()