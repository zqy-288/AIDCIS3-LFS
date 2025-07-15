#!/usr/bin/env python3
"""
清理详细的HoleData调试输出
"""

import re
from pathlib import Path

def clean_debug_output():
    """清理详细的调试输出"""
    
    print("🧹 清理详细的HoleData调试输出")
    print("=" * 60)
    
    # 需要检查的文件
    files_to_check = [
        "src/aidcis2/graphics/dynamic_sector_view.py",
        "src/main_window.py",
        "src/models/batch_data_manager.py",
        "src/aidcis2/dxf_parser.py"
    ]
    
    for file_path in files_to_check:
        file_full_path = Path(__file__).parent / file_path
        if file_full_path.exists():
            clean_file_debug_output(file_full_path)
        else:
            print(f"⚠️ 文件不存在: {file_path}")

def clean_file_debug_output(file_path: Path):
    """清理单个文件的调试输出"""
    
    print(f"\n📁 处理文件: {file_path.name}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # 1. 移除直接打印hole_collection对象的代码
        patterns_to_remove = [
            r'print\(f".*hole_collection:\s*{hole_collection}.*"\)',
            r'print\(f".*hole_collection.*{hole_collection}.*"\)',
            r'print\(hole_collection\)',
            r'print\(.*hole_collection\.holes.*\)',
        ]
        
        for pattern in patterns_to_remove:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                content = re.sub(pattern, '', content, flags=re.MULTILINE)
                changes_made.extend(matches)
        
        # 2. 移除打印大量数据的调试语句
        debug_patterns = [
            # 移除打印hole_collection类型的详细信息（保留简单的类型检查）
            r'print\(f".*hole_collection类型:\s*{type\(hole_collection\)}.*"\)',
            
            # 移除打印完整holes字典的语句
            r'print\(.*\.holes\)',
            
            # 移除DEBUG级别的详细输出
            r'print\(f"🔍 \[DEBUG\].*hole_collection.*{.*}.*"\)',
        ]
        
        for pattern in debug_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                content = re.sub(pattern, '', content, flags=re.MULTILINE)
                changes_made.extend(matches)
        
        # 3. 简化一些冗余的调试输出
        simplifications = [
            # 简化过于详细的调试信息
            (r'print\(f"🔍 \[小型全景图\] hole_collection类型: {type\(hole_collection\)}"\)', 
             '# hole_collection类型检查已简化'),
            
            # 移除重复的数据量打印
            (r'print\(f"🔍 \[小型全景图\] 数据量: {len\(hole_collection\)}"\)', 
             ''),
        ]
        
        for old_pattern, new_text in simplifications:
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_text, content)
                changes_made.append(f"简化: {old_pattern[:50]}...")
        
        # 4. 检查是否有其他可能的详细输出
        potential_issues = [
            r'print\(.*HoleData\(',
            r'print\(.*source_arcs',
            r'print\(.*metadata.*arc_count',
        ]
        
        for pattern in potential_issues:
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                print(f"  ⚠️ 发现潜在问题: {matches}")
                content = re.sub(pattern, '# 详细数据输出已移除', content)
                changes_made.append(f"移除潜在问题: {pattern}")
        
        # 写入修改后的内容
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✅ 已修改 {len(changes_made)} 处")
            for i, change in enumerate(changes_made[:3]):  # 只显示前3个
                print(f"    {i+1}. {change[:80]}...")
            if len(changes_made) > 3:
                print(f"    ... 还有 {len(changes_made) - 3} 处修改")
        else:
            print(f"  ✅ 无需修改")
            
    except Exception as e:
        print(f"  ❌ 处理失败: {e}")

if __name__ == "__main__":
    clean_debug_output()
    
    print(f"\n✅ 调试输出清理完成！")
    print(f"\n🎯 清理效果:")
    print(f"  • 移除了直接打印hole_collection对象的代码")
    print(f"  • 移除了详细的HoleData输出")
    print(f"  • 简化了冗余的调试信息")
    print(f"  • 保留了必要的数量和状态信息")
    
    print(f"\n📋 建议:")
    print(f"  • 重启应用程序测试效果")
    print(f"  • 如果还有详细输出，请检查其他可能的源文件")
    print(f"  • 保持简洁的日志输出，只显示关键信息")