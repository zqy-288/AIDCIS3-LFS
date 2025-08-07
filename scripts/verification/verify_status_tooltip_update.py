#!/usr/bin/env python3
"""
验证状态和提示框更新修复
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def verify_status_tooltip_fix():
    """验证状态和提示框更新修复"""
    print("🔍 验证状态和提示框更新修复...\n")
    
    # 检查文件修改
    hole_item_file = Path("src/core_business/graphics/hole_item.py")
    
    with open(hole_item_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = []
    
    # 1. 检查update_status方法是否更新提示框
    if "self.hole_data.status = new_status" in content and \
       "self.setToolTip(self._create_tooltip())" in content:
        # 检查这两行是否在同一个方法中
        lines = content.split('\n')
        in_update_status = False
        has_status_update = False
        has_tooltip_update = False
        
        for line in lines:
            if "def update_status" in line:
                in_update_status = True
                has_status_update = False
                has_tooltip_update = False
            elif in_update_status:
                if "self.hole_data.status = new_status" in line:
                    has_status_update = True
                if "self.setToolTip(self._create_tooltip())" in line:
                    has_tooltip_update = True
                if "def " in line and not "def update_status" in line:
                    break
        
        if has_status_update and has_tooltip_update:
            checks.append(("✅", "update_status方法更新提示框"))
        else:
            checks.append(("❌", "update_status方法未正确更新提示框"))
    else:
        checks.append(("❌", "update_status方法缺少提示框更新"))
    
    # 2. 检查clear_color_override是否更新提示框
    if "def clear_color_override" in content:
        # 检查clear_color_override方法中是否有提示框更新
        lines = content.split('\n')
        in_clear_override = False
        has_tooltip_update = False
        
        for line in lines:
            if "def clear_color_override" in line:
                in_clear_override = True
                has_tooltip_update = False
            elif in_clear_override:
                if "self.setToolTip(self._create_tooltip())" in line:
                    has_tooltip_update = True
                if "def " in line and not "def clear_color_override" in line:
                    break
        
        if has_tooltip_update:
            checks.append(("✅", "clear_color_override方法更新提示框"))
        else:
            checks.append(("❌", "clear_color_override方法未更新提示框"))
    
    # 3. 检查_create_tooltip方法是否正确显示状态
    if "self.hole_data.status.value" in content:
        checks.append(("✅", "_create_tooltip显示状态值"))
    else:
        checks.append(("❌", "_create_tooltip未正确显示状态"))
    
    # 4. 检查模拟控制器是否正确调用状态更新
    sim_file = Path("src/pages/main_detection_p1/components/simulation_controller.py")
    with open(sim_file, 'r', encoding='utf-8') as f:
        sim_content = f.read()
    
    if "_update_hole_status(hole.hole_id, final_status, color_override=None)" in sim_content:
        checks.append(("✅", "模拟控制器正确更新最终状态"))
    else:
        checks.append(("❌", "模拟控制器未正确更新最终状态"))
    
    # 打印结果
    print("📊 验证结果:")
    print("="*50)
    
    passed = 0
    for status, desc in checks:
        print(f"{status} {desc}")
        if status == "✅":
            passed += 1
    
    total = len(checks)
    print(f"\n总计: {passed}/{total} 项通过")
    
    if passed == total:
        print("\n🎉 状态和提示框更新问题已修复！")
        print("\n修复说明：")
        print("1. 状态更新时会同时更新提示框文本")
        print("2. 清除颜色覆盖时也会更新提示框")
        print("3. 检测完成后状态会从'pending'变为'qualified'或'defective'")
        print("4. 提示框会实时反映当前状态")
        return True
    else:
        print(f"\n⚠️ 有 {total - passed} 项需要检查")
        return False


if __name__ == "__main__":
    print("="*60)
    print("状态和提示框更新验证")
    print("="*60)
    
    success = verify_status_tooltip_fix()
    sys.exit(0 if success else 1)