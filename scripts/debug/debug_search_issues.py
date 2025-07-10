#!/usr/bin/env python3
"""
孔位搜索功能调试和修复
优先级2：孔位搜索功能调试和修复
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def diagnose_search_issues():
    """诊断搜索功能问题"""
    
    print("=" * 80)
    print("🔧 优先级2：孔位搜索功能调试和修复")
    print("=" * 80)
    
    print("\n📋 问题诊断阶段")
    print("-" * 50)
    
    # 读取主窗口文件
    main_window_file = "aidcis2/ui/main_window.py"
    
    try:
        with open(main_window_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("🔍 检查搜索功能组件：")
        
        # 检查各个组件
        issues = []
        
        # 1. 检查导入
        if "QCompleter" not in content:
            issues.append("❌ QCompleter未导入")
        else:
            print("   ✅ QCompleter已导入")
            
        if "QStringListModel" not in content:
            issues.append("❌ QStringListModel未导入")
        else:
            print("   ✅ QStringListModel已导入")
        
        # 2. 检查UI组件
        if "search_btn" not in content:
            issues.append("❌ 搜索按钮未创建")
        else:
            print("   ✅ 搜索按钮已创建")
            
        if "self.completer" not in content:
            issues.append("❌ 自动补全器未创建")
        else:
            print("   ✅ 自动补全器已创建")
        
        # 3. 检查方法
        if "def perform_search" not in content:
            issues.append("❌ perform_search方法缺失")
        else:
            print("   ✅ perform_search方法存在")
            
        if "def update_completer_data" not in content:
            issues.append("❌ update_completer_data方法缺失")
        else:
            print("   ✅ update_completer_data方法存在")
        
        # 4. 检查信号连接
        if "search_btn.clicked.connect" not in content:
            issues.append("❌ 搜索按钮信号连接缺失")
        else:
            print("   ✅ 搜索按钮信号连接存在")
        
        # 5. 检查高亮功能
        if "highlight_holes" not in content:
            issues.append("❌ 高亮功能调用缺失")
        else:
            print("   ✅ 高亮功能调用存在")
        
        # 汇总问题
        if issues:
            print(f"\n❌ 发现 {len(issues)} 个问题：")
            for issue in issues:
                print(f"   {issue}")
        else:
            print("\n✅ 所有组件检查通过")
        
        return issues
        
    except FileNotFoundError:
        print(f"❌ 文件不存在: {main_window_file}")
        return ["文件不存在"]
    except Exception as e:
        print(f"❌ 检查文件时出错: {e}")
        return [f"检查错误: {e}"]


def create_fix_plan(issues):
    """创建修复计划"""
    
    print("\n📋 修复计划")
    print("-" * 50)
    
    if not issues:
        print("✅ 无需修复，所有功能正常")
        return []
    
    fix_steps = []
    
    # 根据问题创建修复步骤
    if any("QCompleter" in issue for issue in issues):
        fix_steps.append({
            "step": 1,
            "title": "修复QCompleter导入",
            "description": "添加QCompleter到导入语句",
            "code": "from PySide6.QtWidgets import QCompleter"
        })
    
    if any("QStringListModel" in issue for issue in issues):
        fix_steps.append({
            "step": 2,
            "title": "修复QStringListModel导入", 
            "description": "添加QStringListModel到导入语句",
            "code": "from PySide6.QtCore import QStringListModel"
        })
    
    if any("搜索按钮" in issue for issue in issues):
        fix_steps.append({
            "step": 3,
            "title": "创建搜索按钮",
            "description": "在工具栏中添加搜索按钮",
            "code": "self.search_btn = QPushButton('搜索')"
        })
    
    if any("自动补全器" in issue for issue in issues):
        fix_steps.append({
            "step": 4,
            "title": "创建自动补全器",
            "description": "配置QCompleter和数据模型",
            "code": "self.completer = QCompleter()"
        })
    
    if any("perform_search" in issue for issue in issues):
        fix_steps.append({
            "step": 5,
            "title": "实现perform_search方法",
            "description": "创建搜索逻辑和高亮功能",
            "code": "def perform_search(self): ..."
        })
    
    if any("update_completer_data" in issue for issue in issues):
        fix_steps.append({
            "step": 6,
            "title": "实现update_completer_data方法",
            "description": "更新自动补全数据源",
            "code": "def update_completer_data(self): ..."
        })
    
    if any("信号连接" in issue for issue in issues):
        fix_steps.append({
            "step": 7,
            "title": "修复信号连接",
            "description": "连接搜索按钮到搜索方法",
            "code": "self.search_btn.clicked.connect(self.perform_search)"
        })
    
    if any("高亮功能" in issue for issue in issues):
        fix_steps.append({
            "step": 8,
            "title": "修复高亮功能",
            "description": "确保搜索结果正确高亮显示",
            "code": "self.graphics_view.highlight_holes(...)"
        })
    
    print(f"🔧 需要执行 {len(fix_steps)} 个修复步骤：")
    for step in fix_steps:
        print(f"   {step['step']}. {step['title']}")
        print(f"      {step['description']}")
        print(f"      代码: {step['code']}")
        print()
    
    return fix_steps


def show_current_search_method():
    """显示当前搜索方法的内容"""
    
    print("\n📋 当前搜索方法分析")
    print("-" * 50)
    
    try:
        with open("aidcis2/ui/main_window.py", 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 找到search_holes方法
        in_search_method = False
        method_lines = []
        
        for i, line in enumerate(lines):
            if "def search_holes" in line:
                in_search_method = True
                method_lines.append(f"{i+1:3d}: {line.rstrip()}")
            elif in_search_method:
                if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    # 方法结束
                    break
                method_lines.append(f"{i+1:3d}: {line.rstrip()}")
        
        if method_lines:
            print("🔍 当前search_holes方法：")
            for line in method_lines:
                print(f"   {line}")
            
            # 分析问题
            method_content = '\n'.join(method_lines)
            problems = []
            
            if "highlight_holes" not in method_content:
                problems.append("❌ 缺少高亮功能调用")
            
            if "search_highlight=True" not in method_content:
                problems.append("❌ 缺少搜索高亮参数")
            
            if "模糊搜索" not in method_content and "fuzzy" not in method_content.lower():
                problems.append("❌ 缺少模糊搜索实现")
            
            if problems:
                print(f"\n❌ 发现 {len(problems)} 个问题：")
                for problem in problems:
                    print(f"   {problem}")
            else:
                print("\n✅ 搜索方法看起来正常")
        else:
            print("❌ 未找到search_holes方法")
            
    except Exception as e:
        print(f"❌ 分析搜索方法时出错: {e}")


def main():
    """主函数"""
    
    # 1. 诊断问题
    issues = diagnose_search_issues()
    
    # 2. 显示当前搜索方法
    show_current_search_method()
    
    # 3. 创建修复计划
    fix_steps = create_fix_plan(issues)
    
    print("\n" + "=" * 80)
    print("📊 调试总结")
    print("=" * 80)
    
    if issues:
        print(f"❌ 发现 {len(issues)} 个问题需要修复")
        print(f"🔧 制定了 {len(fix_steps)} 个修复步骤")
        print("\n下一步：执行修复计划")
    else:
        print("✅ 搜索功能组件完整")
        print("🔍 需要进一步测试功能是否正常工作")
    
    print("=" * 80)
    
    return len(issues) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
