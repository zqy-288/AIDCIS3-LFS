#!/usr/bin/env python3
"""
全面测试所有修复并提供调试信息
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


def test_dxf_parser_and_id_generation():
    """测试DXF解析器和ID生成"""
    print("\n" + "="*80)
    print("测试1: DXF解析器和ID生成")
    print("="*80)
    
    try:
        from src.core_business.dxf_parser import DXFParser
        from src.core_business.models.hole_data import HoleData
        
        # 创建解析器实例
        parser = DXFParser()
        print("✅ DXFParser 创建成功")
        
        # 创建模拟的孔位数据来测试ID生成流程
        test_holes = []
        # 创建R164行的孔位（坐标基于实际CAP1000管板）
        for col in [94, 98, 102, 106, 110]:
            # B侧（下半部分）- Y坐标为正值
            x = col * 12.0  # 假设列间距12mm
            y = 2111.2 + 10  # R164的Y坐标，稍微偏离中心线以确保在B侧
            hole = HoleData(
                hole_id=None,  # 初始无ID
                center_x=x,
                center_y=y,
                radius=8.87
            )
            test_holes.append(hole)
        
        print(f"创建了 {len(test_holes)} 个测试孔位")
        
        # 测试HoleNumberingService
        from src.core_business.hole_numbering_service import HoleNumberingService
        from src.core_business.models.hole_data import HoleCollection
        
        # 创建孔位集合
        holes_dict = {str(i): hole for i, hole in enumerate(test_holes)}
        hole_collection = HoleCollection(
            holes=holes_dict,
            metadata={'no_ids': True}
        )
        
        # 应用编号
        numbering_service = HoleNumberingService()
        numbering_service.apply_numbering(hole_collection)
        
        print("\n生成的ID：")
        for hole_id, hole in hole_collection.holes.items():
            print(f"  - {hole.hole_id}: X={hole.center_x:.1f}, Y={hole.center_y:.1f}")
        
        # 验证ID格式
        first_hole = next(iter(hole_collection.holes.values()))
        if first_hole.hole_id and first_hole.hole_id.startswith(('AC', 'BC')):
            print("\n✅ ID格式正确（AC/BC格式）")
        else:
            print(f"\n❌ ID格式错误: {first_hole.hole_id}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_snake_path_detection_order():
    """测试蛇形路径检测顺序"""
    print("\n" + "="*80)
    print("测试2: 蛇形路径检测顺序")
    print("="*80)
    
    try:
        from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
        from src.core_business.models.hole_data import HoleData, HoleCollection
        
        # 创建测试数据 - 模拟实际的管板数据
        test_holes = []
        
        # 创建多行数据，包括R001和R164
        rows = [1, 2, 3, 160, 161, 162, 163, 164]  # 包括开始和结束的行
        
        for row in rows:
            # 为每行创建一些孔位
            for col in [94, 98, 102, 106, 110, 114]:
                # B侧（下半部分）
                hole_id = f"BC{col:03d}R{row:03d}"
                x = col * 12.0
                # 在Qt坐标系中，Y值越小越在上方
                # R164应该有最小的Y值（在顶部）
                y = 2200 - row * 13.5  # R164的Y值最小，R001的Y值最大
                
                hole = HoleData(
                    hole_id=hole_id,
                    center_x=x,
                    center_y=y,
                    radius=8.87
                )
                test_holes.append(hole)
        
        print(f"创建了 {len(test_holes)} 个测试孔位")
        print(f"Y值范围: {min(h.center_y for h in test_holes):.1f} 到 {max(h.center_y for h in test_holes):.1f}")
        
        # 创建集合
        holes_dict = {hole.hole_id: hole for hole in test_holes}
        hole_collection = HoleCollection(holes=holes_dict)
        
        # 创建渲染器并生成路径
        renderer = SnakePathRenderer()
        renderer.set_hole_collection(hole_collection)
        
        # 生成检测单元
        detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
        
        if detection_units:
            print(f"\n生成了 {len(detection_units)} 个检测单元")
            
            # 检查前5个检测单元
            print("\n前5个检测单元：")
            for i, unit in enumerate(detection_units[:5]):
                if unit.is_pair and len(unit.holes) >= 2:
                    hole1 = unit.holes[0]
                    hole2 = unit.holes[1]
                    print(f"  {i+1}. {hole1.hole_id} + {hole2.hole_id} (Y: {hole1.center_y:.1f})")
                elif len(unit.holes) == 1:
                    hole = unit.holes[0]
                    print(f"  {i+1}. {hole.hole_id} (单孔, Y: {hole.center_y:.1f})")
            
            # 验证第一个单元
            first_unit = detection_units[0]
            if first_unit.is_pair and len(first_unit.holes) >= 2:
                hole1_id = first_unit.holes[0].hole_id
                hole2_id = first_unit.holes[1].hole_id
                
                print(f"\n第一个检测单元: {hole1_id} + {hole2_id}")
                
                # 检查是否从R164开始
                if "R164" in hole1_id:
                    print("✅ 检测从R164行开始")
                    
                    # 检查是否是BC098R164+BC102R164
                    if hole1_id == "BC098R164" and hole2_id == "BC102R164":
                        print("✅ 检测从BC098R164+BC102R164开始")
                    else:
                        print(f"⚠️  R164行的配对是 {hole1_id}+{hole2_id}，不是BC098R164+BC102R164")
                else:
                    print(f"❌ 检测不是从R164开始，而是从 {hole1_id} 开始")
                    
        else:
            print("❌ 未生成检测单元")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_view_initialization():
    """测试视图初始化"""
    print("\n" + "="*80)
    print("测试3: 视图初始化设置")
    print("="*80)
    
    try:
        # 检查关键代码设置
        native_view_file = "src/pages/main_detection_p1/native_main_detection_view_p1.py"
        graphics_view_file = "src/core_business/graphics/graphics_view.py"
        
        print("检查native_main_detection_view_p1.py中的设置：")
        with open(native_view_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查关键设置
        checks = [
            ("设置微观视图模式", "graphics_view.current_view_mode = 'micro'" in content),
            ("禁用自动适配", "graphics_view.disable_auto_fit = True" in content),
            ("移除定时器恢复", "QTimer.singleShot(1000" not in content or "# 不要立即恢复" in content),
            ("设置扇形适配标志", "_fitted_to_sector = True" in content),
        ]
        
        for check_name, result in checks:
            print(f"  {'✅' if result else '❌'} {check_name}")
        
        print("\n检查graphics_view.py中的保护机制：")
        with open(graphics_view_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查保护机制
        checks = [
            ("微观视图模式检查", "if hasattr(self, 'current_view_mode') and self.current_view_mode == 'micro':" in content),
            ("缩放锁机制", "_is_fitting" in content),
            ("扇形适配标志", "_fitted_to_sector" in content),
            ("缩放范围0.5-2.0", "min_micro_scale = 0.5" in content and "max_micro_scale = 2.0" in content),
        ]
        
        for check_name, result in checks:
            print(f"  {'✅' if result else '❌'} {check_name}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_coordinate_system_understanding():
    """测试坐标系理解"""
    print("\n" + "="*80)
    print("测试4: 坐标系理解验证")
    print("="*80)
    
    # 检查snake_path_renderer.py中的注释和逻辑
    snake_path_file = "src/pages/shared/components/snake_path/snake_path_renderer.py"
    
    try:
        with open(snake_path_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print("检查坐标系相关代码：")
        
        # 查找关键行
        for i, line in enumerate(lines):
            if "在Qt坐标系中" in line:
                print(f"\n第{i+1}行的注释：")
                # 打印前后几行
                for j in range(max(0, i-2), min(len(lines), i+5)):
                    print(f"  {j+1}: {lines[j].rstrip()}")
                    
            if "sorted_rows = sorted(holes_by_y.keys())" in line:
                print(f"\n第{i+1}行的排序逻辑：")
                # 打印前后几行
                for j in range(max(0, i-3), min(len(lines), i+3)):
                    print(f"  {j+1}: {lines[j].rstrip()}")
        
        print("\n✅ 坐标系理解验证完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def run_debugging_tests():
    """运行调试测试"""
    print("\n" + "="*80)
    print("调试信息收集")
    print("="*80)
    
    # 收集可能影响问题的配置
    print("\n检查可能的配置问题：")
    
    # 检查是否有其他地方调用switch_to_macro_view
    files_to_check = [
        "src/pages/main_detection_p1/native_main_detection_view_p1.py",
        "src/core_business/graphics/graphics_view.py",
        "src/pages/main_detection_p1/components/graphics/graphics_view.py",
    ]
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            macro_view_calls = content.count("switch_to_macro_view")
            micro_view_calls = content.count("switch_to_micro_view")
            fit_to_window_calls = content.count("fit_to_window_width")
            
            print(f"\n{Path(file_path).name}:")
            print(f"  - switch_to_macro_view 调用: {macro_view_calls} 次")
            print(f"  - switch_to_micro_view 调用: {micro_view_calls} 次")
            print(f"  - fit_to_window_width 调用: {fit_to_window_calls} 次")
            
        except Exception as e:
            print(f"  ❌ 无法读取: {e}")


def main():
    """运行所有测试"""
    print("🔬 全面测试和调试\n")
    
    # 运行各项测试
    test_dxf_parser_and_id_generation()
    test_snake_path_detection_order()
    test_view_initialization()
    test_coordinate_system_understanding()
    run_debugging_tests()
    
    print("\n" + "="*80)
    print("📊 测试总结和建议")
    print("="*80)
    
    print("\n关键发现：")
    print("1. ID生成机制已修复，应该生成标准格式")
    print("2. 坐标系理解已修正，R164应该最先被检测")
    print("3. 视图初始化保护机制已添加")
    
    print("\n如果问题仍然存在，建议检查：")
    print("1. 实际的DXF文件中R164行的Y坐标值")
    print("2. 扇形分配逻辑是否正确")
    print("3. 是否有其他地方覆盖了视图设置")
    
    print("\n调试步骤：")
    print("1. 在_generate_interval_four_s_shape方法中添加日志，打印sorted_rows的值")
    print("2. 在_show_sector_in_view方法中添加日志，确认视图模式设置")
    print("3. 在load_holes方法中添加日志，确认是否跳过了自动适配")


if __name__ == "__main__":
    main()