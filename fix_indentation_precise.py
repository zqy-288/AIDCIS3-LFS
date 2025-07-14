#!/usr/bin/env python3
"""
精确修复缩进错误
"""

def fix_indentation():
    """修复 dynamic_sector_view.py 中的缩进错误"""
    print("🔧 精确修复缩进错误...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    
    # 读取文件
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找有问题的方法定义
    # 第944行的方法定义缩进不正确
    lines = content.split('\n')
    
    # 检查第943行（索引942）
    if len(lines) > 943:
        line_943 = lines[943]
        if "def trigger_mini_panorama_paint(self):" in line_943:
            # 计算正确的缩进（应该是4个空格）
            correct_indent = "    "
            lines[943] = correct_indent + "def trigger_mini_panorama_paint(self):"
            print(f"✅ 修复了第 944 行（索引943）的缩进")
            
            # 重新组合内容
            content = '\n'.join(lines)
            
            # 写回文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ 文件已保存")
        else:
            print(f"❌ 第944行内容不匹配: {line_943[:50]}...")
    else:
        print("❌ 文件行数不足")

def check_all_method_indentations():
    """检查所有方法定义的缩进"""
    print("\n🔍 检查所有方法定义的缩进...")
    
    filepath = "src/aidcis2/graphics/dynamic_sector_view.py"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    problems = []
    for i, line in enumerate(lines):
        if line.strip().startswith("def ") and line.strip().endswith("):"):
            # 计算缩进级别
            indent = len(line) - len(line.lstrip())
            # 在类中的方法应该是4个空格
            if indent != 4 and indent != 0:  # 0是顶级函数
                problems.append((i + 1, line.strip(), indent))
    
    if problems:
        print("发现缩进问题：")
        for line_num, content, indent in problems:
            print(f"  第 {line_num} 行: 缩进 {indent} 个空格 - {content[:50]}...")
    else:
        print("✅ 所有方法定义的缩进都正确")
    
    return problems

def main():
    print("=" * 60)
    print("精确修复缩进错误")
    print("=" * 60)
    
    # 先检查问题
    problems = check_all_method_indentations()
    
    if problems:
        fix_indentation()
        
        # 再次检查
        print("\n重新检查...")
        problems = check_all_method_indentations()
        
        if not problems:
            print("\n✅ 所有缩进问题已修复！")
        else:
            print("\n❌ 仍有缩进问题需要修复")
    else:
        print("\n✅ 没有发现缩进问题")

if __name__ == "__main__":
    main()