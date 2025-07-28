#!/usr/bin/env python3
"""
分析项目中需要重构的文件
"""
import os
import re
from pathlib import Path
from collections import defaultdict

def count_file_metrics(file_path):
    """统计文件的度量信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.splitlines()
            
        # 统计类和函数
        classes = len(re.findall(r'^class\s+\w+', content, re.MULTILINE))
        functions = len(re.findall(r'^def\s+\w+', content, re.MULTILINE))
        methods = len(re.findall(r'^\s+def\s+\w+', content, re.MULTILINE))
        imports = len([l for l in lines if l.strip().startswith(('import ', 'from '))])
        
        # 统计代码复杂度指标
        if_statements = len(re.findall(r'\bif\b', content))
        for_loops = len(re.findall(r'\bfor\b', content))
        while_loops = len(re.findall(r'\bwhile\b', content))
        try_blocks = len(re.findall(r'\btry\b:', content))
        
        complexity = if_statements + for_loops + while_loops
        
        return {
            'lines': len(lines),
            'classes': classes,
            'functions': functions,
            'methods': methods,
            'imports': imports,
            'complexity': complexity,
            'try_blocks': try_blocks
        }
    except Exception as e:
        return None

def analyze_directory(directory):
    """分析目录中的Python文件"""
    results = []
    
    for root, dirs, files in os.walk(directory):
        # 排除特定目录
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'venv', '.venv'}]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                metrics = count_file_metrics(file_path)
                
                if metrics and metrics['lines'] > 300:  # 只关注较大的文件
                    # 计算复杂度分数
                    complexity_score = (
                        metrics['lines'] / 100 +
                        metrics['classes'] * 5 +
                        metrics['complexity'] / 10
                    )
                    
                    results.append({
                        'path': file_path,
                        'file': file,
                        'metrics': metrics,
                        'complexity_score': complexity_score
                    })
    
    return results

def find_duplicate_functionality():
    """查找可能的重复功能"""
    src_dir = '/Users/vsiyo/Desktop/AIDCIS3-LFS/src'
    
    # 按功能分组文件
    groups = defaultdict(list)
    
    patterns = {
        'plugin': r'plugin',
        'error': r'error|exception',
        'ui': r'ui_|widget|view|panel',
        'graphics': r'graphics|render|draw',
        'data': r'data_|model|manager',
        'report': r'report',
        'history': r'history',
        'config': r'config|settings',
        'test': r'test_',
    }
    
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'venv'}]
        
        for file in files:
            if file.endswith('.py'):
                file_lower = file.lower()
                file_path = os.path.join(root, file)
                
                # 分类文件
                for group, pattern in patterns.items():
                    if re.search(pattern, file_lower):
                        groups[group].append(file_path)
                        break
    
    return groups

def main():
    """主函数"""
    print("🔍 分析项目重构需求")
    print("=" * 70)
    
    # 分析src目录
    src_dir = '/Users/vsiyo/Desktop/AIDCIS3-LFS/src'
    results = analyze_directory(src_dir)
    
    # 按复杂度排序
    results.sort(key=lambda x: x['complexity_score'], reverse=True)
    
    print("\n📊 需要重构的大文件（按复杂度排序）：")
    print("-" * 70)
    
    for i, result in enumerate(results[:20]):
        metrics = result['metrics']
        rel_path = os.path.relpath(result['path'], src_dir)
        
        print(f"\n{i+1}. {rel_path}")
        print(f"   行数: {metrics['lines']}")
        print(f"   类: {metrics['classes']}, 函数: {metrics['functions']}, 方法: {metrics['methods']}")
        print(f"   导入: {metrics['imports']}, 复杂度: {metrics['complexity']}")
        print(f"   复杂度分数: {result['complexity_score']:.1f}")
    
    # 查找重复功能
    print("\n\n🔄 可能存在重复功能的文件组：")
    print("-" * 70)
    
    groups = find_duplicate_functionality()
    
    for group, files in groups.items():
        if len(files) > 1:
            print(f"\n{group.upper()} 相关文件 ({len(files)}个):")
            for file in files[:10]:  # 只显示前10个
                rel_path = os.path.relpath(file, src_dir)
                size = os.path.getsize(file)
                print(f"   - {rel_path} ({size:,} 字节)")
    
    # 特别关注的问题
    print("\n\n⚠️ 特别需要关注的问题：")
    print("-" * 70)
    
    # 检查main_window.py
    main_window_path = os.path.join(src_dir, 'main_window.py')
    if os.path.exists(main_window_path):
        metrics = count_file_metrics(main_window_path)
        if metrics:
            print(f"\n1. main_window.py - 超大单文件")
            print(f"   - {metrics['lines']} 行 (建议: < 1000行)")
            print(f"   - {metrics['classes']} 个类 (建议: 1-3个)")
            print(f"   - {metrics['methods']} 个方法 (建议: < 50个)")
    
    # 检查插件系统
    plugin_files = [f for f in groups['plugin'] if 'plugin_system' not in f]
    if len(plugin_files) > 5:
        print(f"\n2. 插件系统 - 过度设计")
        print(f"   - {len(plugin_files)} 个插件相关文件")
        print(f"   - 建议合并为3-4个核心模块")
    
    # 检查错误处理
    error_files = groups['error']
    if len(error_files) > 3:
        print(f"\n3. 错误处理 - 分散的实现")
        print(f"   - {len(error_files)} 个错误处理文件")
        print(f"   - 建议统一错误处理机制")
    
    # 检查UI组件
    ui_files = [f for f in groups['ui'] if 'realtime_chart_package' not in f]
    large_ui_files = [f for f in ui_files if os.path.getsize(f) > 30000]
    if large_ui_files:
        print(f"\n4. UI组件 - 大型单体文件")
        print(f"   - {len(large_ui_files)} 个超大UI文件")
        for f in large_ui_files[:5]:
            print(f"   - {os.path.basename(f)} ({os.path.getsize(f):,} 字节)")

if __name__ == '__main__':
    main()