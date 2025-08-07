#!/usr/bin/env python3
"""
测试最终修复效果
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_final_fixes():
    """测试最终修复"""
    print("=" * 80)
    print("测试最终修复效果")
    print("=" * 80)
    
    # 1. 测试检测配对逻辑
    print("\n1. 测试检测配对逻辑...")
    
    from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer
    from src.core_business.models.hole_data import HoleData, HoleCollection
    
    # 创建测试数据 - 模拟R164行
    test_holes = []
    
    # 创建多个列的孔位，包括98和102列
    for col in [94, 98, 102, 106, 110]:
        # A侧（上半部分，Qt坐标系y<0）
        hole_id = f"AC{col:03d}R164"
        x = col * 12.0  # 假设列间距12mm
        y = -2111.2  # R164行的Y坐标（负值表示在上方）
        test_holes.append(HoleData(hole_id=hole_id, center_x=x, center_y=y, radius=8.87))
        
        # B侧（下半部分，Qt坐标系y>0）
        hole_id = f"BC{col:03d}R164"
        y = 2111.2  # R164行的Y坐标（正值表示在下方）
        test_holes.append(HoleData(hole_id=hole_id, center_x=x, center_y=y, radius=8.87))
    
    # 创建集合
    holes_dict = {hole.hole_id: hole for hole in test_holes}
    hole_collection = HoleCollection(holes=holes_dict)
    
    # 创建渲染器并生成路径
    renderer = SnakePathRenderer()
    renderer.set_hole_collection(hole_collection)
    
    # 生成检测单元
    from src.pages.shared.components.snake_path.snake_path_renderer import PathStrategy
    detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
    
    if detection_units:
        print(f"   生成了 {len(detection_units)} 个检测单元")
        
        # 检查第一个检测单元
        first_unit = detection_units[0]
        if first_unit.is_pair and len(first_unit.holes) >= 2:
            hole1_id = first_unit.holes[0].hole_id
            hole2_id = first_unit.holes[1].hole_id
            print(f"   第一个检测单元: {hole1_id} + {hole2_id}")
            
            # 验证是否是BC098R164+BC102R164
            if hole1_id == "BC098R164" and hole2_id == "BC102R164":
                print("   ✅ 检测从BC098R164+BC102R164开始")
            else:
                print("   ❌ 检测起始配对不正确")
        else:
            print(f"   第一个检测单元: {first_unit.holes[0].hole_id} (单孔)")
    
    # 2. 测试视图模式设置
    print("\n2. 测试视图模式设置...")
    
    # 检查关键代码修改
    graphics_view_file = "src/core_business/graphics/graphics_view.py"
    with open(graphics_view_file, 'r', encoding='utf-8') as f:
        gv_content = f.read()
    
    checks = [
        ("load_holes跳过微观视图适配", "微观视图模式，跳过load_holes时的自动适配" in gv_content),
        ("添加缩放锁", "_is_fitting" in gv_content),
        ("简化centerOn调用", gv_content.count("QTimer.singleShot") < 10)  # 减少了延迟调用
    ]
    
    for name, result in checks:
        status = "✅" if result else "❌"
        print(f"   {status} {name}")
    
    # 3. 测试disable_auto_fit标志
    print("\n3. 测试disable_auto_fit标志恢复...")
    
    native_view_file = "src/pages/main_detection_p1/native_main_detection_view_p1.py"
    with open(native_view_file, 'r', encoding='utf-8') as f:
        nv_content = f.read()
    
    if "QTimer.singleShot(1000, lambda: setattr(graphics_view, 'disable_auto_fit', False))" in nv_content:
        print("   ✅ disable_auto_fit标志会在1秒后恢复")
    else:
        print("   ❌ 缺少disable_auto_fit标志恢复逻辑")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_final_fixes()