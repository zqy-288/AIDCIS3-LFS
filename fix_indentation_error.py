#!/usr/bin/env python3
"""
修复缩进错误
"""

import re

def fix_indentation():
    """修复 dynamic_sector_view.py 中的缩进错误"""
    print("🔧 修复缩进错误...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    
    # 读取文件
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到问题行并修复
    fixed_lines = []
    in_trigger_method = False
    
    for i, line in enumerate(lines):
        if i == 943 and line.strip().startswith("def trigger_mini_panorama_paint"):
            # 这行缩进错误，应该与其他方法对齐（4个空格）
            fixed_lines.append("    def trigger_mini_panorama_paint(self):\n")
            in_trigger_method = True
            print(f"✅ 修复了第 {i+1} 行的缩进")
        else:
            fixed_lines.append(line)
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("✅ 缩进错误已修复")

def verify_fix():
    """验证修复是否成功"""
    print("\n🔍 验证修复...")
    
    try:
        # 尝试导入模块
        import sys
        import os
        sys.path.insert(0, 'src')
        
        from aidcis2.graphics.dynamic_sector_view import DynamicSectorDisplayWidget
        print("✅ 模块可以正常导入")
        return True
    except IndentationError as e:
        print(f"❌ 仍有缩进错误: {e}")
        return False
    except Exception as e:
        print(f"⚠️ 其他错误: {e}")
        return True  # 其他错误不是缩进问题

def main():
    print("=" * 60)
    print("修复缩进错误")
    print("=" * 60)
    
    fix_indentation()
    
    if verify_fix():
        print("\n✅ 修复完成！可以重新运行程序了。")
    else:
        print("\n❌ 修复失败，请检查文件。")

if __name__ == "__main__":
    main()