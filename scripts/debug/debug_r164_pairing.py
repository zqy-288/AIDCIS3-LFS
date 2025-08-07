#!/usr/bin/env python3
"""
调试R164行的配对问题
"""

import sys
from pathlib import Path
import logging

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def debug_r164_pairing():
    """调试R164行的配对"""
    print("🔍 调试R164行配对问题\n")
    
    try:
        from src.core_business.dxf_parser import DXFParser
        from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
        
        dxf_file = "Data/Products/CAP1000/dxf/CAP1000.dxf"
        
        if Path(dxf_file).exists():
            print(f"加载DXF文件: {dxf_file}")
            
            parser = DXFParser()
            hole_collection = parser.parse_file(dxf_file)
            
            if hole_collection:
                print(f"✅ 解析成功，共 {len(hole_collection.holes)} 个孔位\n")
                
                # 手动查找R164行的所有孔位
                r164_holes = []
                for hole_id, hole in hole_collection.holes.items():
                    if "R164" in hole_id and hole_id.startswith("BC"):
                        r164_holes.append((hole_id, hole))
                
                # 按列号排序
                r164_holes.sort(key=lambda x: int(x[0][2:5]))  # 提取列号部分
                
                print(f"R164行B侧孔位数: {len(r164_holes)}")
                print("\n前20个孔位:")
                for i, (hole_id, hole) in enumerate(r164_holes[:20]):
                    col_num = int(hole_id[2:5])
                    print(f"  {i+1:2d}. {hole_id} (列号: {col_num})")
                
                # 分析列号间隔
                if len(r164_holes) > 1:
                    col_nums = [int(h[0][2:5]) for h in r164_holes]
                    print("\n列号序列:", col_nums[:20])
                    
                    intervals = []
                    for i in range(min(10, len(col_nums)-1)):
                        intervals.append(col_nums[i+1] - col_nums[i])
                    print("相邻列号间隔:", intervals)
                    
                    # 检查特定列号
                    print(f"\n列98存在: {'BC098R164' in [h[0] for h in r164_holes]}")
                    print(f"列102存在: {'BC102R164' in [h[0] for h in r164_holes]}")
                    print(f"列106存在: {'BC106R164' in [h[0] for h in r164_holes]}")
                
                # 生成蛇形路径查看实际配对
                print("\n" + "="*60)
                print("生成蛇形路径")
                print("="*60)
                
                renderer = SnakePathRenderer()
                renderer.set_hole_collection(hole_collection)
                
                detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
                
                # 找出第一个R164的配对
                for i, unit in enumerate(detection_units[:50]):
                    if unit.is_pair and len(unit.holes) >= 2:
                        if "R164" in unit.holes[0].hole_id:
                            hole1 = unit.holes[0]
                            hole2 = unit.holes[1]
                            col1 = int(hole1.hole_id[2:5])
                            col2 = int(hole2.hole_id[2:5])
                            print(f"\n找到R164配对: {hole1.hole_id} + {hole2.hole_id}")
                            print(f"列号: {col1} + {col2}, 间隔: {col2-col1}")
                            break
                            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    debug_r164_pairing()


if __name__ == "__main__":
    main()