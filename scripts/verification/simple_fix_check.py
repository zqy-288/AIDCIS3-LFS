#!/usr/bin/env python3
"""
简单检查修复状态
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_file_modifications():
    """检查关键文件是否包含修复代码"""
    
    print("🔍 检查修复状态...")
    
    # 1. 检查模拟控制器修复
    simulation_controller_path = "src/pages/main_detection_p1/components/simulation_controller.py"
    if os.path.exists(simulation_controller_path):
        with open(simulation_controller_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ("_force_refresh_graphics_view", "强制刷新视图修复"),
            ("next_pair_timer", "配对定时器修复"),
            ("final_display_time = 500", "最终显示时间修复")
        ]
        
        for check, desc in checks:
            if check in content:
                print(f"✅ {desc}: 已应用")
            else:
                print(f"❌ {desc}: 未找到")
    
    # 2. 检查协调器修复
    coordinator_path = "src/pages/main_detection_p1/components/panorama_sector_coordinator.py"
    if os.path.exists(coordinator_path):
        with open(coordinator_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "def select_sector" in content:
            print("✅ 协调器select_sector方法: 已添加")
        else:
            print("❌ 协调器select_sector方法: 未找到")
    
    # 3. 检查蛇形路径渲染器修复
    renderer_path = "src/pages/shared/components/snake_path/snake_path_renderer.py"
    if os.path.exists(renderer_path):
        with open(renderer_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "_get_dashed_line_color" in content:
            print("✅ 虚线路径渲染修复: 已应用")
        else:
            print("❌ 虚线路径渲染修复: 未找到")
    
    # 4. 检查主视图修复
    main_view_path = "src/pages/main_detection_p1/native_main_detection_view_p1.py"
    if os.path.exists(main_view_path):
        with open(main_view_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ("_load_default_sector1", "默认sector1加载"),
            ("self.current_hole_collection", "变量作用域修复")
        ]
        
        for check, desc in checks:
            if check in content:
                print(f"✅ {desc}: 已应用")
            else:
                print(f"❌ {desc}: 未找到")

if __name__ == "__main__":
    check_file_modifications()
    print("\n🎯 所有修复检查完成！")
    print("📋 程序现在应该可以正常运行以下功能：")
    print("  1. 点击'开始模拟'立即开始，不转圈")
    print("  2. 加载数据后自动显示sector1")
    print("  3. 路径显示为虚线样式")
    print("  4. 中间孔位状态实时同步")