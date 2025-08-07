#!/usr/bin/env python3
"""
修复默认视图和检测顺序的最终方案
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def fix_default_view_and_order():
    """修复默认视图和检测顺序"""
    print("=" * 80)
    print("修复默认视图和检测顺序")
    print("=" * 80)
    
    # 1. 检查并修复坐标系统一性
    print("\n1. 检查坐标系统一性...")
    
    # 检查snake_path_renderer.py
    snake_path_file = "src/pages/shared/components/snake_path/snake_path_renderer.py"
    with open(snake_path_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否使用了正确的Qt坐标系
    if "# Qt坐标系：Y轴向下" in content and "if x_sign >= 0 and dy <= 0:" in content:
        print("   ✅ snake_path_renderer使用Qt坐标系")
    else:
        print("   ❌ snake_path_renderer坐标系不正确")
    
    # 2. 增强默认微观视图逻辑
    print("\n2. 增强默认微观视图逻辑...")
    
    # 修改方案
    print("\n建议的修改方案：")
    print("1. 在load_hole_collection中，确保is_micro_view默认为True")
    print("2. 在_load_default_sector1中，增加更多日志")
    print("3. 在coordinator初始化后立即设置默认扇形")
    
    # 3. 检查可能的问题点
    print("\n3. 检查可能的问题点...")
    
    issues = []
    
    # 检查是否有其他文件设置宏观视图
    if "visualization_panel_component" in content:
        issues.append("visualization_panel_component可能设置了宏观视图")
    
    # 检查是否有异步操作
    if "QTimer.singleShot" in content and "_load_default_sector1" in content:
        issues.append("有延迟加载可能导致时序问题")
    
    # 检查coordinator初始化
    if "self.coordinator.current_sector = None" in content:
        issues.append("coordinator的current_sector初始化为None")
    
    if issues:
        print("   发现以下潜在问题：")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("   ✅ 未发现明显问题")
    
    # 4. 提供修复建议
    print("\n4. 修复建议：")
    print("   a) 在coordinator初始化后立即设置默认扇形：")
    print("      self.coordinator.current_sector = SectorQuadrant.SECTOR_1")
    print("   b) 在load_hole_collection开始时强制设置微观视图：")
    print("      if self.center_panel:")
    print("          self.center_panel.micro_view_btn.setChecked(True)")
    print("          self.center_panel.current_view_mode = 'micro'")
    print("   c) 增加调试日志确认各步骤执行：")
    print("      - 数据加载完成")
    print("      - 视图模式设置")
    print("      - 扇形选择")
    print("      - 视图更新")


if __name__ == "__main__":
    fix_default_view_and_order()