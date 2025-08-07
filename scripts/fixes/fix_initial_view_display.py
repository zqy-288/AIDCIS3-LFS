#!/usr/bin/env python3
"""
修复初始视图显示问题
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def fix_initial_view_display():
    """修复初始加载时显示整个管板的问题"""
    print("🔧 修复初始视图显示问题\n")
    
    # 1. 修改 _show_sector_in_view 方法，确保适配完成后才恢复标志
    native_view_file = "src/pages/main_detection_p1/native_main_detection_view_p1.py"
    
    print("1. 检查 _show_sector_in_view 方法...")
    with open(native_view_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找关键代码
    if "graphics_view._fitted_to_sector = True" in content:
        print("   ✅ 找到扇形适配标志设置")
        
        # 检查是否在适配后立即恢复了 disable_auto_fit
        import re
        pattern = r'graphics_view\.fitInView.*?\n.*?graphics_view\._fitted_to_sector = True'
        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            print("   ✅ fitInView 和标志设置顺序正确")
    
    # 2. 检查 graphics_view.py 中的保护机制
    graphics_view_file = "src/core_business/graphics/graphics_view.py"
    
    print("\n2. 检查 graphics_view.py 保护机制...")
    with open(graphics_view_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ("load_holes中的微观视图检查", "if hasattr(self, 'current_view_mode') and self.current_view_mode == 'micro':" in content),
        ("fit_to_window_width的保护", "if getattr(self, 'disable_auto_fit', False):" in content),
        ("fit_in_view_with_margin的缩放锁", "if getattr(self, '_is_fitting', False):" in content),
    ]
    
    for name, result in checks:
        print(f"   {'✅' if result else '❌'} {name}")
    
    # 3. 提供修复建议
    print("\n3. 修复建议：")
    print("   a) 在 _show_sector_in_view 完成适配后，添加延迟恢复：")
    print("      QTimer.singleShot(100, lambda: setattr(graphics_view, 'disable_auto_fit', False))")
    print("   b) 确保 setup_initial_display 在加载数据后立即显示扇形")
    print("   c) 在 load_holes 方法开始时就检查并跳过自动适配")
    
    return True


def add_debug_logging():
    """添加调试日志来追踪问题"""
    print("\n4. 建议添加的调试日志：")
    
    debug_points = [
        ("load_holes方法开始", "self.logger.debug(f'load_holes called, view_mode={self.current_view_mode}, disable_auto_fit={getattr(self, \"disable_auto_fit\", False)}')"),
        ("fit_to_window_width调用前", "self.logger.debug('About to call fit_to_window_width')"),
        ("_show_sector_in_view完成后", "self.logger.debug(f'Sector {sector} displayed, view fitted')"),
    ]
    
    for location, code in debug_points:
        print(f"   - {location}:")
        print(f"     {code}")


def main():
    """主函数"""
    fix_initial_view_display()
    add_debug_logging()
    
    print("\n" + "="*60)
    print("总结")
    print("="*60)
    
    print("\n问题原因：")
    print("1. 加载数据时触发了 fit_to_window_width，显示了整个管板")
    print("2. disable_auto_fit 标志管理不当")
    print("3. 微观视图模式设置时机不对")
    
    print("\n解决方案：")
    print("1. 确保加载数据前就设置好微观视图模式和禁用自动适配")
    print("2. 在扇形显示完成后才恢复 disable_auto_fit")
    print("3. 添加更多的保护检查，防止意外的全视图适配")


if __name__ == "__main__":
    main()