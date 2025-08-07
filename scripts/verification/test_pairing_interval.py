#!/usr/bin/env python3
"""
测试配对间隔修复
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_pairing_logic():
    """测试配对逻辑"""
    print("🔍 测试配对间隔逻辑\n")
    
    # 模拟列号序列
    sorted_cols = [98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
    
    print("列号序列:", sorted_cols)
    print("\n间隔4列的配对（在排序列表中跳过4个位置）：")
    
    for i, col in enumerate(sorted_cols):
        target_index = i + 4
        if target_index < len(sorted_cols):
            target_col = sorted_cols[target_index]
            print(f"  列{col} -> 列{target_col} (索引{i} -> 索引{target_index})")
        else:
            print(f"  列{col} -> 无配对（超出范围）")
    
    print("\n✅ 按照新逻辑：")
    print("   - 列98配对列102（98->99->100->101->102）")
    print("   - 列99配对列103")
    print("   - 列100配对列104")
    print("   - 以此类推...")


def test_real_dxf_pairing():
    """测试实际DXF文件的配对"""
    print("\n" + "="*60)
    print("测试实际DXF文件的配对")
    print("="*60)
    
    try:
        from src.core_business.dxf_parser import DXFParser
        from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
        
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
                
                detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
                
                if detection_units:
                    print(f"\n生成了 {len(detection_units)} 个检测单元")
                    
                    # 查看前5个检测单元
                    print("\n前5个检测单元（新配对逻辑）：")
                    for i, unit in enumerate(detection_units[:5]):
                        if unit.is_pair and len(unit.holes) >= 2:
                            hole1 = unit.holes[0]
                            hole2 = unit.holes[1]
                            # 提取列号
                            col1 = int(hole1.hole_id[2:5]) if len(hole1.hole_id) > 5 else 0
                            col2 = int(hole2.hole_id[2:5]) if len(hole2.hole_id) > 5 else 0
                            print(f"  {i+1}. {hole1.hole_id} + {hole2.hole_id} (列间隔: {col2-col1})")
                        elif len(unit.holes) == 1:
                            hole = unit.holes[0]
                            print(f"  {i+1}. {hole.hole_id} (单孔)")
                            
                    # 特别检查第一个单元
                    first_unit = detection_units[0]
                    if first_unit.is_pair and len(first_unit.holes) >= 2:
                        if first_unit.holes[0].hole_id == "BC098R164" and first_unit.holes[1].hole_id == "BC102R164":
                            print("\n✅ 成功！第一个配对是 BC098R164 + BC102R164")
                        else:
                            print(f"\n⚠️  第一个配对是 {first_unit.holes[0].hole_id} + {first_unit.holes[1].hole_id}")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    test_pairing_logic()
    test_real_dxf_pairing()
    
    print("\n" + "="*60)
    print("配对间隔修复总结")
    print("="*60)
    
    print("\n修复内容：")
    print("1. 将简单的 target_col = current_col + 4 改为基于索引的配对")
    print("2. 间隔4列现在表示在排序列表中跳过4个位置")
    print("3. 例如：列98（索引0）配对列102（索引4）")
    
    print("\n预期效果：")
    print("- BC098R164 + BC102R164（而不是BC098R164 + BC106R164）")
    print("- 真正实现间隔4列的配对")


if __name__ == "__main__":
    main()