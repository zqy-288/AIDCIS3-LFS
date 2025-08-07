#!/usr/bin/env python3
"""
详细调试配对逻辑
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def debug_pairing_logic():
    """调试配对逻辑"""
    print("🔍 详细调试配对逻辑\n")
    
    # 模拟实际的列号数据
    sorted_cols = [86, 88, 90, 92, 94, 96, 98, 100, 102, 104, 106, 108, 110]
    print(f"列号序列: {sorted_cols}")
    print(f"列号总数: {len(sorted_cols)}")
    
    # 查找98和102的索引
    idx_98 = sorted_cols.index(98) if 98 in sorted_cols else -1
    idx_102 = sorted_cols.index(102) if 102 in sorted_cols else -1
    
    print(f"\n列98的索引: {idx_98}")
    print(f"列102的索引: {idx_102}")
    print(f"索引差: {idx_102 - idx_98}")
    
    # 模拟新的配对逻辑
    print("\n使用 target_index = i + 2 的配对结果:")
    for i in range(min(5, len(sorted_cols))):
        current_col = sorted_cols[i]
        target_index = i + 2
        if target_index < len(sorted_cols):
            target_col = sorted_cols[target_index]
            print(f"  索引{i}: 列{current_col} -> 索引{target_index}: 列{target_col}")
        else:
            print(f"  索引{i}: 列{current_col} -> 无配对")
    
    # 检查第一个检测单元
    print("\n检查为什么第一个检测单元仍然是 BC098R164 + BC106R164:")
    print("1. 是否有特殊处理覆盖了正常配对？")
    print("2. 检测单元的顺序是否被重新排序？")
    print("3. 是否在其他地方修改了配对逻辑？")


def check_actual_file():
    """检查实际文件的配对"""
    print("\n" + "="*60)
    print("检查实际DXF文件的配对逻辑")
    print("="*60)
    
    try:
        from src.core_business.dxf_parser import DXFParser
        from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
        
        # 启用详细日志
        import logging
        logging.getLogger('SnakePathRenderer').setLevel(logging.DEBUG)
        
        dxf_file = "Data/Products/CAP1000/dxf/CAP1000.dxf"
        
        if Path(dxf_file).exists():
            print(f"加载DXF文件: {dxf_file}")
            
            parser = DXFParser()
            hole_collection = parser.parse_file(dxf_file)
            
            if hole_collection:
                print(f"✅ 解析成功，共 {len(hole_collection.holes)} 个孔位")
                
                # 生成蛇形路径
                renderer = SnakePathRenderer()
                renderer.set_hole_collection(hole_collection)
                
                # 获取检测单元
                detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
                
                # 查看前10个检测单元
                print("\n前10个检测单元:")
                for i, unit in enumerate(detection_units[:10]):
                    if unit.is_pair and len(unit.holes) >= 2:
                        hole1 = unit.holes[0]
                        hole2 = unit.holes[1]
                        col1 = int(hole1.hole_id[2:5]) if len(hole1.hole_id) > 5 else 0
                        col2 = int(hole2.hole_id[2:5]) if len(hole2.hole_id) > 5 else 0
                        print(f"  {i+1:2d}. {hole1.hole_id} + {hole2.hole_id} (列{col1} + 列{col2}, 间隔: {col2-col1})")
                    else:
                        hole = unit.holes[0]
                        print(f"  {i+1:2d}. {hole.hole_id} (单孔)")
                
                # 专门查找BC098R164的配对
                print("\n查找BC098R164的配对:")
                found_98 = False
                for i, unit in enumerate(detection_units[:50]):
                    if unit.is_pair and len(unit.holes) >= 2:
                        for hole in unit.holes:
                            if hole.hole_id == "BC098R164":
                                found_98 = True
                                hole1 = unit.holes[0]
                                hole2 = unit.holes[1]
                                print(f"  在第{i+1}个单元找到: {hole1.hole_id} + {hole2.hole_id}")
                                break
                    if found_98:
                        break
                        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    debug_pairing_logic()
    check_actual_file()


if __name__ == "__main__":
    main()