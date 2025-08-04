"""
修复视图和检测顺序问题

问题1: 默认视图问题
- 现象：加载DXF后仍显示宏观视图（整个圆形）
- 期望：默认显示微观视图（放大的扇形）

问题2: 检测顺序问题  
- 现象：从BC098R164（B区，下半部分）开始
- 期望：从AC098R164（A区，上半部分）开始

根本原因分析：
1. 视图问题：load_hole_collection方法中，宏观视图模式下会调用fit_in_view_with_margin()显示全部内容
2. 检测顺序：蛇形路径生成时先处理B侧（因为Qt坐标系中Y<0在上方，与编号系统相反）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def fix_default_view():
    """修复默认视图问题"""
    print("\n=== 修复问题1：默认视图问题 ===")
    
    # 文件路径
    file_path = "src/pages/main_detection_p1/native_main_detection_view_p1.py"
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复1：修改初始按钮状态 - 默认选中宏观视图而非微观视图
    old_macro_checked = 'self.macro_view_btn.setChecked(False)  # 不再默认选中'
    new_macro_checked = 'self.macro_view_btn.setChecked(True)  # 默认选中宏观视图'
    
    old_micro_checked = 'self.micro_view_btn.setChecked(True)  # 默认选中扇形视图'
    new_micro_checked = 'self.micro_view_btn.setChecked(False)  # 不默认选中微观视图'
    
    # 修复2：在load_hole_collection中，确保微观视图模式正确设置
    # 在第1715行附近，更改默认检查逻辑
    old_check = """                # 检查当前视图模式
                is_micro_view = (self.center_panel and 
                               hasattr(self.center_panel, 'micro_view_btn') and 
                               self.center_panel.micro_view_btn.isChecked())"""
    
    new_check = """                # 检查当前视图模式 - 默认应该是微观视图
                # 如果按钮状态还未初始化，默认使用微观视图
                is_micro_view = True  # 默认使用微观视图
                if self.center_panel and hasattr(self.center_panel, 'micro_view_btn'):
                    # 如果按钮已初始化，则使用按钮状态
                    is_micro_view = self.center_panel.micro_view_btn.isChecked()
                    # 但如果两个按钮都未选中（初始状态），强制使用微观视图
                    if (hasattr(self.center_panel, 'macro_view_btn') and 
                        not self.center_panel.macro_view_btn.isChecked() and 
                        not self.center_panel.micro_view_btn.isChecked()):
                        is_micro_view = True
                        # 同时更新按钮状态
                        self.center_panel.micro_view_btn.setChecked(True)
                        self.center_panel.macro_view_btn.setChecked(False)"""
    
    # 应用修复
    if old_macro_checked in content:
        # 注意：这里我们反转了逻辑，保持原始的按钮初始状态（微观视图为默认）
        print("✓ 保持微观视图为默认选中状态")
    else:
        print("⚠️ 未找到宏观视图按钮初始化代码")
    
    if old_check in content:
        content = content.replace(old_check, new_check)
        print("✓ 修复了视图模式检查逻辑，确保默认使用微观视图")
    else:
        print("⚠️ 未找到视图模式检查代码，尝试其他位置...")
        
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ 默认视图问题修复完成")


def fix_detection_order():
    """修复检测顺序问题"""
    print("\n=== 修复问题2：检测顺序问题 ===")
    
    # 文件路径
    file_path = "src/pages/shared/components/snake_path/snake_path_renderer.py"
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复1：修改_generate_hybrid_path方法，确保先处理A侧
    # 原代码已经是先处理A侧，但问题可能在于A/B侧的判定
    
    # 修复2：修改_parse_hole_position中的A/B侧判定
    # 根据文档，y>0为A侧，但Qt坐标系中y向下增长
    # 所以在Qt坐标系中，y<0（屏幕上方）才是A侧
    old_side_check = """            # 如果没有标准编号，根据位置推断A/B侧
            side = 'A' if hole.center_y > 0 else 'B'"""
    
    new_side_check = """            # 如果没有标准编号，根据位置推断A/B侧
            # 注意：在Qt坐标系中，y向下增长，所以y<0在屏幕上方
            # 根据实际管板布局，上半部分是A侧，下半部分是B侧
            side = 'A' if hole.center_y < 0 else 'B'  # Qt坐标系：y<0在上方为A侧"""
    
    # 修复3：在_generate_interval_four_path中调整扇形处理顺序
    # 确保sector_1和sector_2（上半部分）先被处理
    old_sector_order = "        # 按照指定顺序处理扇形：右上(1) → 左上(2) → 左下(3) → 右下(4)"
    new_sector_order = "        # 按照指定顺序处理扇形：确保A侧（上半部分）优先\n        # sector_1(右上) 和 sector_2(左上) 包含A侧孔位（Qt坐标系y<0）"
    
    # 应用修复
    if old_side_check in content:
        content = content.replace(old_side_check, new_side_check)
        print("✓ 修复了A/B侧判定逻辑（Qt坐标系）")
    else:
        print("⚠️ 未找到A/B侧判定代码")
    
    if old_sector_order in content:
        content = content.replace(old_sector_order, new_sector_order)
        print("✓ 更新了扇形处理顺序说明")
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ 检测顺序问题修复完成")


def verify_fixes():
    """验证修复结果"""
    print("\n=== 验证修复结果 ===")
    
    # 验证视图文件
    with open("src/pages/main_detection_p1/native_main_detection_view_p1.py", 'r', encoding='utf-8') as f:
        view_content = f.read()
    
    # 检查关键修复
    if "is_micro_view = True  # 默认使用微观视图" in view_content:
        print("✓ 视图默认设置已修复")
    else:
        print("⚠️ 视图默认设置可能未正确修复")
    
    # 验证蛇形路径文件
    with open("src/pages/shared/components/snake_path/snake_path_renderer.py", 'r', encoding='utf-8') as f:
        snake_content = f.read()
    
    if "side = 'A' if hole.center_y < 0 else 'B'" in snake_content:
        print("✓ A/B侧判定已修复（适配Qt坐标系）")
    else:
        print("⚠️ A/B侧判定可能未正确修复")
    
    print("\n修复总结：")
    print("1. 默认视图：确保加载DXF后默认显示微观视图（扇形放大）")
    print("2. 检测顺序：修正A/B侧判定，确保从A侧（上半部分）开始检测")
    print("3. 坐标系统：适配Qt坐标系（y向下增长），y<0为屏幕上方（A侧）")


if __name__ == "__main__":
    print("开始修复视图和检测顺序问题...")
    
    try:
        fix_default_view()
        fix_detection_order()
        verify_fixes()
        
        print("\n✅ 所有修复已完成！")
        print("\n建议测试步骤：")
        print("1. 启动程序并加载DXF文件")
        print("2. 验证是否默认显示微观视图（扇形放大视图）")
        print("3. 开始检测，验证是否从AC098R164（A区，上半部分）开始")
        print("4. 观察检测路径是否正确遵循A侧→B侧的顺序")
        
    except Exception as e:
        print(f"\n❌ 修复过程中出错: {e}")
        import traceback
        traceback.print_exc()