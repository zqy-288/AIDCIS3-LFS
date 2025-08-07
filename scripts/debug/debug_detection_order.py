#!/usr/bin/env python3
"""
调试检测顺序问题
"""

import sys
from pathlib import Path
import logging

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def debug_real_dxf_loading():
    """调试实际的DXF加载和检测顺序"""
    print("\n" + "="*80)
    print("调试实际DXF加载和检测顺序")
    print("="*80)
    
    try:
        # 测试DXF解析
        from src.core_business.dxf_parser import DXFParser
        
        dxf_file = "Data/Products/CAP1000/dxf/CAP1000.dxf"
        
        if Path(dxf_file).exists():
            print(f"✅ 找到DXF文件: {dxf_file}")
            
            parser = DXFParser()
            hole_collection = parser.parse_file(dxf_file)
            
            if hole_collection:
                print(f"✅ 解析成功，共 {len(hole_collection.holes)} 个孔位")
                
                # 检查ID格式
                first_5_ids = list(hole_collection.holes.keys())[:5]
                print(f"\n前5个孔位ID: {first_5_ids}")
                
                # 查找R164行的孔位
                r164_holes = []
                for hole_id, hole in hole_collection.holes.items():
                    if "R164" in hole_id:
                        r164_holes.append((hole_id, hole))
                
                print(f"\nR164行的孔位数: {len(r164_holes)}")
                if r164_holes:
                    # 按列号排序
                    r164_holes.sort(key=lambda x: x[0])
                    print("R164行的前10个孔位:")
                    for hole_id, hole in r164_holes[:10]:
                        print(f"  - {hole_id}: X={hole.center_x:.1f}, Y={hole.center_y:.1f}")
                    
                    # 检查是否有BC098R164和BC102R164
                    bc098r164 = None
                    bc102r164 = None
                    for hole_id, hole in r164_holes:
                        if hole_id == "BC098R164":
                            bc098r164 = hole
                        elif hole_id == "BC102R164":
                            bc102r164 = hole
                    
                    if bc098r164:
                        print(f"\n✅ 找到BC098R164: X={bc098r164.center_x:.1f}, Y={bc098r164.center_y:.1f}")
                    else:
                        print("\n❌ 未找到BC098R164")
                        
                    if bc102r164:
                        print(f"✅ 找到BC102R164: X={bc102r164.center_x:.1f}, Y={bc102r164.center_y:.1f}")
                    else:
                        print("❌ 未找到BC102R164")
                
                # 测试蛇形路径生成
                print("\n" + "-"*60)
                print("测试蛇形路径生成")
                print("-"*60)
                
                from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
                
                renderer = SnakePathRenderer()
                renderer.set_hole_collection(hole_collection)
                
                # 生成检测单元
                detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
                
                if detection_units:
                    print(f"\n生成了 {len(detection_units)} 个检测单元")
                    
                    # 检查前10个检测单元
                    print("\n前10个检测单元:")
                    for i, unit in enumerate(detection_units[:10]):
                        if unit.is_pair and len(unit.holes) >= 2:
                            hole1 = unit.holes[0]
                            hole2 = unit.holes[1]
                            print(f"  {i+1}. {hole1.hole_id} + {hole2.hole_id} (Y1={hole1.center_y:.1f}, Y2={hole2.center_y:.1f})")
                        elif len(unit.holes) == 1:
                            hole = unit.holes[0]
                            print(f"  {i+1}. {hole.hole_id} (单孔, Y={hole.center_y:.1f})")
                    
                    # 分析第一个检测单元
                    first_unit = detection_units[0]
                    if first_unit.holes:
                        first_hole = first_unit.holes[0]
                        print(f"\n第一个检测孔位: {first_hole.hole_id}")
                        print(f"坐标: X={first_hole.center_x:.1f}, Y={first_hole.center_y:.1f}")
                        
                        if "R164" in first_hole.hole_id:
                            print("✅ 检测从R164行开始")
                        else:
                            print("❌ 检测不是从R164开始")
                            
                            # 查找实际的R001行Y坐标
                            r001_holes = [(hid, h) for hid, h in hole_collection.holes.items() if "R001" in hid]
                            if r001_holes:
                                print(f"\nR001行的Y坐标范围:")
                                y_values = [h.center_y for _, h in r001_holes]
                                print(f"  最小Y: {min(y_values):.1f}")
                                print(f"  最大Y: {max(y_values):.1f}")
                                
                            # 查找实际的R164行Y坐标
                            if r164_holes:
                                print(f"\nR164行的Y坐标范围:")
                                y_values = [h.center_y for _, h in r164_holes]
                                print(f"  最小Y: {min(y_values):.1f}")
                                print(f"  最大Y: {max(y_values):.1f}")
                
        else:
            print(f"❌ 未找到DXF文件: {dxf_file}")
            print("使用模拟数据进行测试...")
            
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("🔍 调试检测顺序问题\n")
    
    debug_real_dxf_loading()
    
    print("\n" + "="*80)
    print("调试建议")
    print("="*80)
    
    print("\n1. 检查Y坐标值:")
    print("   - 在Qt坐标系中，Y值越小越在上方")
    print("   - R164应该有最小的Y值（在管板顶部）")
    print("   - R001应该有较大的Y值（在管板底部）")
    
    print("\n2. 检查扇形分配:")
    print("   - sector_1和sector_2是上半部分")
    print("   - 应该使用sorted(holes_by_y.keys())从小到大排序")
    
    print("\n3. 检查ID格式:")
    print("   - 应该是BC098R164格式，不是BC99R001")
    print("   - 注意列号是3位数字（098而不是99）")


if __name__ == "__main__":
    main()