#!/usr/bin/env python3
"""
快速验证脚本 - 不启动GUI
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def validate_fixes():
    """验证修复内容"""
    print("🔍 快速验证修复内容...\n")
    
    results = []
    
    # 1. 检查文件修改
    print("1️⃣ 检查文件修改...")
    file_path = project_root / "src/pages/main_detection_p1/native_main_detection_view_p1.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # 检查是否导入了SimulationController
        if "from src.pages.main_detection_p1.components.simulation_controller import SimulationController" in content:
            results.append("✅ SimulationController导入正确")
        else:
            results.append("❌ SimulationController导入缺失")
            
        # 检查是否有simulation_controller属性
        if "self.simulation_controller = None" in content:
            results.append("✅ simulation_controller属性已定义")
        else:
            results.append("❌ simulation_controller属性未定义")
            
        # 检查模拟方法
        simulation_methods = [
            "_on_start_simulation",
            "_on_pause_simulation", 
            "_on_stop_simulation",
            "_on_simulation_progress",
            "_on_hole_status_updated",
            "_on_simulation_completed"
        ]
        
        for method in simulation_methods:
            if f"def {method}(self" in content:
                results.append(f"✅ {method}方法存在")
            else:
                results.append(f"❌ {method}方法缺失")
                
        # 检查表格数值格式修复
        if 'setText(str(count))' in content:
            results.append("✅ 表格数值格式已修复（纯数字）")
        else:
            results.append("❌ 表格数值格式未修复")
    
    # 2. 检查simulation_controller.py修复
    print("\n2️⃣ 检查simulation_controller.py修复...")
    sim_file = project_root / "src/pages/main_detection_p1/components/simulation_controller.py"
    
    with open(sim_file, 'r', encoding='utf-8') as f:
        sim_content = f.read()
        
        # 检查颜色覆盖清除
        if "self._update_hole_status(hole.hole_id, final_status, color_override=None)" in sim_content:
            results.append("✅ 颜色覆盖清除修复已应用")
        else:
            results.append("❌ 颜色覆盖清除修复未应用")
            
        # 检查日志改进
        if '蓝色" if color_override else "默认颜色"' in sim_content:
            results.append("✅ 颜色日志改进已应用")
        else:
            results.append("❌ 颜色日志改进未应用")
    
    # 打印结果
    print("\n📊 验证结果汇总:")
    print("="*40)
    
    success_count = 0
    for result in results:
        print(result)
        if result.startswith("✅"):
            success_count += 1
    
    total_count = len(results)
    print(f"\n总计: {success_count}/{total_count} 项通过")
    
    if success_count == total_count:
        print("\n🎉 所有修复验证通过！")
        return True
    else:
        print(f"\n⚠️ 有 {total_count - success_count} 项未通过")
        return False


if __name__ == "__main__":
    print("="*60)
    print("模拟检测修复 - 快速验证")
    print("="*60)
    
    success = validate_fixes()
    sys.exit(0 if success else 1)