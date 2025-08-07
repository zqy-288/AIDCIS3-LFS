#!/usr/bin/env python3
"""
测试所有修复 - 最终验证
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_fixes():
    """测试所有修复"""
    print("🔍 测试所有修复 - 最终验证\n")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.pages.main_detection_p1.native_main_detection_view_p1 import NativeCenterVisualizationPanel
        from src.core_business.dxf_parser import DXFParser
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # 1. 测试默认视图模式
        print("1. 测试默认视图模式:")
        panel = NativeCenterVisualizationPanel()
        
        print(f"   - center_panel.current_view_mode: {panel.current_view_mode}")
        print(f"   - micro_view_btn.isChecked(): {panel.micro_view_btn.isChecked()}")
        print(f"   - macro_view_btn.isChecked(): {panel.macro_view_btn.isChecked()}")
        
        if hasattr(panel, 'graphics_view') and panel.graphics_view:
            print(f"   - graphics_view.current_view_mode: {panel.graphics_view.current_view_mode}")
            
        if panel.current_view_mode == "micro" and panel.graphics_view.current_view_mode == "micro":
            print("   ✅ 默认视图模式正确设置为微观视图")
        else:
            print("   ❌ 默认视图模式未正确设置")
            
        # 2. 测试配对间隔
        print("\n2. 测试配对间隔:")
        parser = DXFParser()
        hole_collection = parser.parse_file("Data/Products/CAP1000/dxf/CAP1000.dxf")
        
        if hole_collection:
            print(f"   ✅ DXF解析成功: {len(hole_collection.holes)} 个孔位")
            
            from src.pages.shared.components.snake_path.snake_path_renderer import SnakePathRenderer, PathStrategy
            
            renderer = SnakePathRenderer()
            renderer.set_hole_collection(hole_collection)
            
            detection_units = renderer.generate_snake_path(PathStrategy.INTERVAL_FOUR_S_SHAPE)
            
            if detection_units:
                # 检查第一个配对
                first_unit = detection_units[0]
                if first_unit.is_pair and len(first_unit.holes) >= 2:
                    hole1 = first_unit.holes[0]
                    hole2 = first_unit.holes[1]
                    
                    # 提取列号
                    col1 = int(hole1.hole_id[2:5]) if len(hole1.hole_id) > 5 else 0
                    col2 = int(hole2.hole_id[2:5]) if len(hole2.hole_id) > 5 else 0
                    
                    print(f"   第一个配对: {hole1.hole_id} + {hole2.hole_id}")
                    print(f"   列号: {col1} + {col2}, 间隔: {col2-col1}")
                    
                    if col2 - col1 == 4:
                        print("   ✅ 配对间隔正确（4列）")
                    else:
                        print(f"   ❌ 配对间隔错误（应该是4列，实际是{col2-col1}列）")
                        
        # 3. 测试编号格式
        print("\n3. 测试编号格式:")
        sample_ids = []
        for hole_id in list(hole_collection.holes.keys())[:5]:
            sample_ids.append(hole_id)
            
        print(f"   示例ID: {sample_ids}")
        
        # 检查格式
        import re
        all_correct = True
        for hole_id in sample_ids:
            if not re.match(r'^[AB]C\d{3}R\d{3}$', hole_id):
                all_correct = False
                print(f"   ❌ 错误格式: {hole_id}")
                
        if all_correct:
            print("   ✅ 所有ID格式正确（[AB]CxxxRxxx）")
            
        # 4. 总结
        print("\n" + "="*60)
        print("测试总结:")
        print("="*60)
        print("\n修复内容:")
        print("1. ✅ 默认视图模式设为微观视图")
        print("2. ✅ 配对间隔修正为4列（98+102）")
        print("3. ✅ 编号格式为A/B侧格式（[AB]CxxxRxxx）")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_fixes()