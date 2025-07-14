#!/usr/bin/env python3
"""
修复HoleStatus枚举不匹配问题
"""

import re

def fix_hole_item_status_colors():
    """修复hole_item.py中的状态颜色映射"""
    print("🔧 修复状态枚举映射...")
    
    filepath = "src/aidcis2/graphics/hole_item.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换STATUS_COLORS定义，使用正确的枚举值
    pattern = r'STATUS_COLORS = \{[^}]+\}'
    replacement = '''STATUS_COLORS = {
        HoleStatus.PENDING: QColor(200, 200, 200),          # 灰色 - 待检
        HoleStatus.PROCESSING: QColor(100, 150, 255),       # 蓝色 - 检测中
        HoleStatus.QUALIFIED: QColor(50, 200, 50),          # 绿色 - 合格
        HoleStatus.DEFECTIVE: QColor(255, 50, 50),          # 红色 - 异常
        HoleStatus.BLIND: QColor(255, 200, 50),             # 黄色 - 盲孔
        HoleStatus.TIE_ROD: QColor(100, 255, 100),         # 亮绿色 - 拉杆孔
    }'''
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # 同时修复所有使用了错误枚举名的地方
    replacements = [
        (r'HoleStatus\.NOT_DETECTED', 'HoleStatus.PENDING'),
        (r'HoleStatus\.DETECTING', 'HoleStatus.PROCESSING'),
        (r'HoleStatus\.UNQUALIFIED', 'HoleStatus.DEFECTIVE'),
        (r'HoleStatus\.UNCERTAIN', 'HoleStatus.BLIND'),
        (r'HoleStatus\.ERROR', 'HoleStatus.DEFECTIVE'),
        (r'HoleStatus\.REAL_DATA', 'HoleStatus.TIE_ROD'),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ hole_item.py 状态枚举修复完成")

def fix_main_window_status_mapping():
    """修复main_window.py中的状态映射"""
    print("\n🔧 修复主窗口状态映射...")
    
    filepath = "src/main_window.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复_get_simulation_status方法中的状态列表
    pattern = r'status_options = \[[^\]]+\]'
    replacement = '''status_options = [
            HoleStatus.QUALIFIED,     # 合格
            HoleStatus.DEFECTIVE,     # 异常
            HoleStatus.QUALIFIED,     # 合格（更高概率）
            HoleStatus.QUALIFIED,     # 合格（更高概率）
            HoleStatus.BLIND,         # 盲孔
        ]'''
    
    content = re.sub(pattern, replacement, content)
    
    # 修复update_hole_status中的状态映射
    replacements = [
        (r"'not_detected'", "'pending'"),
        (r"'detecting'", "'processing'"),
        (r"'qualified'", "'qualified'"),
        (r"'unqualified'", "'defective'"),
        (r"'uncertain'", "'blind'"),
        (r"'error'", "'defective'"),
        (r"'real_data'", "'tie_rod'"),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content, flags=re.IGNORECASE)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ main_window.py 状态映射修复完成")

def fix_dynamic_sector_view_status():
    """修复dynamic_sector_view.py中的状态引用"""
    print("\n🔧 修复动态扇形视图状态引用...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复状态引用
    replacements = [
        (r'HoleStatus\.NOT_DETECTED', 'HoleStatus.PENDING'),
        (r'HoleStatus\.DETECTING', 'HoleStatus.PROCESSING'),
        (r'HoleStatus\.UNQUALIFIED', 'HoleStatus.DEFECTIVE'),
        (r'HoleStatus\.QUALIFIED', 'HoleStatus.QUALIFIED'),
        (r"'not_detected'", "'pending'"),
        (r"'detecting'", "'processing'"),
        (r"'unqualified'", "'defective'"),
        (r"'qualified'", "'qualified'"),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content, flags=re.IGNORECASE)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ dynamic_sector_view.py 状态引用修复完成")

def fix_graphics_view_status():
    """修复graphics_view.py中的状态引用"""
    print("\n🔧 修复图形视图状态引用...")
    
    filepath = "src/aidcis2/graphics/graphics_view.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修复状态统计中的key
    replacements = [
        (r"'not_detected'", "'pending'"),
        (r"'detecting'", "'processing'"),
        (r"'unqualified'", "'defective'"),
        (r"'qualified'", "'qualified'"),
        (r"'real_data'", "'tie_rod'"),
    ]
    
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ graphics_view.py 状态引用修复完成")

def main():
    print("=" * 60)
    print("修复HoleStatus枚举不匹配问题")
    print("=" * 60)
    
    fix_hole_item_status_colors()
    fix_main_window_status_mapping()
    fix_dynamic_sector_view_status()
    fix_graphics_view_status()
    
    print("\n✅ 所有状态枚举修复完成！")
    print("\n现在再次运行测试...")
    
    # 验证语法
    import subprocess
    import sys
    
    print("\n🔍 验证修复后的语法...")
    files = [
        "src/aidcis2/graphics/hole_item.py",
        "src/main_window.py",
        "src/aidcis2/graphics/dynamic_sector_view.py",
        "src/aidcis2/graphics/graphics_view.py"
    ]
    
    all_good = True
    for filepath in files:
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', filepath],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {filepath}")
        else:
            print(f"❌ {filepath}")
            print(result.stderr)
            all_good = False
    
    return all_good

if __name__ == "__main__":
    main()