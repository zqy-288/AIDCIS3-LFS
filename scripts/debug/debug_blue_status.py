#!/usr/bin/env python3
"""
调试蓝色状态更新问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def analyze_update_chain():
    """分析更新链路"""
    print("=== 蓝色状态更新链路分析 ===\n")
    
    print("1. SimulationController 更新链路:")
    print("   SimulationController._update_hole_status()")
    print("   ├─> graphics_view.update_hole_status()")
    print("   │   └─> hole_item.clear_color_override()")
    print("   └─> panorama_widget.update_hole_status()")
    print("       └─> ???")
    
    print("\n2. 检查各组件的 update_hole_status 实现:")
    
    # 检查 graphics_view.py
    print("\n   a) graphics_view.py:")
    with open('src/core_business/graphics/graphics_view.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'clear_color_override()' in content:
            print("      ✅ 正确调用 clear_color_override()")
        else:
            print("      ❌ 未调用 clear_color_override()")
    
    # 检查 complete_panorama_widget.py
    print("\n   b) complete_panorama_widget.py:")
    with open('src/pages/main_detection_p1/components/graphics/complete_panorama_widget.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'clear_color_override()' in content:
            print("      ✅ 正确调用 clear_color_override()")
        else:
            print("      ❌ 未调用 clear_color_override()")
            
        if '_should_update_immediately' in content and 'return True' in content:
            print("      ✅ 设置为立即更新")
        else:
            print("      ❌ 可能使用批量更新导致延迟")
    
    # 检查 hole_item.py
    print("\n   c) hole_item.py:")
    with open('src/core_business/graphics/hole_item.py', 'r', encoding='utf-8') as f:
        content = f.read()
        if 'prepareGeometryChange()' in content and 'scene().update(' in content:
            print("      ✅ 包含强制重绘机制")
        else:
            print("      ❌ 缺少强制重绘机制")
    
    print("\n3. 可能的问题原因:")
    print("   - 左侧全景图的 hole_items 可能不是 HoleGraphicsItem 实例")
    print("   - 左侧全景图可能使用了不同的更新机制")
    print("   - 批量更新延迟导致视觉更新滞后")
    print("   - Qt的绘制优化可能跳过了某些更新")
    
    print("\n4. 建议的额外修复:")
    print("   - 在 CompletePanoramaWidget 中确保 panorama_view.hole_items 使用相同的 HoleGraphicsItem")
    print("   - 添加更多强制刷新机制")
    print("   - 考虑使用 QApplication.processEvents() 强制处理事件")

if __name__ == "__main__":
    analyze_update_chain()