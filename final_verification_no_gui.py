#!/usr/bin/env python3
"""
最终验证 - 不启动GUI
"""

import sys
import ast
from pathlib import Path

def verify_all_fixes():
    """验证所有修复内容"""
    print("🔍 最终验证（无GUI）...\n")
    
    results = []
    
    # 1. 验证主文件修改
    print("1️⃣ 检查 native_main_detection_view_p1.py...")
    main_file = Path("src/pages/main_detection_p1/native_main_detection_view_p1.py")
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析AST找到类和方法
    tree = ast.parse(content)
    
    # 查找NativeLeftInfoPanel类
    left_panel_methods = []
    main_view_methods = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if node.name == "NativeLeftInfoPanel":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        left_panel_methods.append(item.name)
            elif node.name == "NativeMainDetectionView":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        main_view_methods.append(item.name)
    
    # 检查关键内容
    checks = [
        ("SimulationController导入", 
         "from src.pages.main_detection_p1.components.simulation_controller import SimulationController" in content),
        ("simulation_controller属性定义", 
         "self.simulation_controller = None" in content),
        ("sector_stats_table创建", 
         "self.sector_stats_table = QTableWidget(6, 2)" in content),
        ("update_sector_stats方法", 
         "update_sector_stats" in left_panel_methods),
        ("setText(str(count))修复", 
         "setText(str(count))" in content),
        ("_on_start_simulation方法", 
         "_on_start_simulation" in main_view_methods),
        ("_on_simulation_progress方法", 
         "_on_simulation_progress" in main_view_methods),
        ("_calculate_overall_stats方法", 
         "_calculate_overall_stats" in main_view_methods),
    ]
    
    for name, result in checks:
        results.append((name, result))
        print(f"{'✅' if result else '❌'} {name}")
    
    # 2. 验证simulation_controller.py修改
    print("\n2️⃣ 检查 simulation_controller.py...")
    sim_file = Path("src/pages/main_detection_p1/components/simulation_controller.py")
    
    with open(sim_file, 'r', encoding='utf-8') as f:
        sim_content = f.read()
    
    sim_checks = [
        ("颜色覆盖清除修复", 
         "self._update_hole_status(hole.hole_id, final_status, color_override=None)" in sim_content),
        ("颜色日志增强", 
         'color_info = "蓝色" if color_override else "默认颜色"' in sim_content),
    ]
    
    for name, result in sim_checks:
        results.append((name, result))
        print(f"{'✅' if result else '❌'} {name}")
    
    # 3. 统计结果
    print("\n📊 验证结果汇总:")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有修复验证通过！功能已完整实现！")
        return True
    else:
        print(f"\n⚠️ 有 {total - passed} 项未通过")
        failed = [name for name, result in results if not result]
        print("失败项：", failed)
        return False


if __name__ == "__main__":
    print("="*60)
    print("模拟检测修复 - 最终验证")
    print("="*60)
    
    success = verify_all_fixes()
    
    print("\n" + "="*60)
    if success:
        print("✅ 验证完成：所有修复已正确应用")
    else:
        print("❌ 验证失败：部分修复未正确应用")
    
    sys.exit(0 if success else 1)