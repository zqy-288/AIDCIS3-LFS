#!/usr/bin/env python3
"""
修复panorama_view包内的相对导入
"""

import os
import re
from pathlib import Path


def fix_imports_in_file(file_path):
    """修复单个文件中的导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # 修复从src.modules.panorama_view到相对导入的模式
        replacements = [
            # interfaces应该从core导入
            (r'from src\.modules\.panorama_view\.interfaces import', 
             'from ..core.interfaces import'),
            # event_bus应该从core导入
            (r'from src\.modules\.panorama_view\.event_bus import', 
             'from ..core.event_bus import'),
            # 其他组件之间的导入
            (r'from src\.modules\.panorama_view\.(\w+) import', 
             r'from .\1 import'),
            # 修复已有的错误相对导入
            (r'from \.\.components\.(\w+) import',
             r'from .\1 import'),
        ]
        
        # 根据文件位置决定导入方式
        file_str = str(file_path)
        
        if '/components/' in file_str:
            # 在components目录中
            replacements.extend([
                (r'from src\.modules\.panorama_view import', 'from .. import'),
                (r'from src\.modules\.panorama_view\.core import', 'from ..core import'),
                (r'from src\.modules\.panorama_view\.core\.(\w+) import', r'from ..core.\1 import'),
            ])
        elif '/core/' in file_str:
            # 在core目录中  
            replacements.extend([
                (r'from src\.modules\.panorama_view import', 'from .. import'),
                (r'from src\.modules\.panorama_view\.components import', 'from ..components import'),
                (r'from src\.modules\.panorama_view\.components\.(\w+) import', r'from ..components.\1 import'),
            ])
        elif '/adapters/' in file_str:
            # 在adapters目录中
            replacements.extend([
                (r'from src\.modules\.panorama_view import', 'from .. import'),
                (r'from src\.modules\.panorama_view\.core import', 'from ..core import'),
                (r'from src\.modules\.panorama_view\.components import', 'from ..components import'),
            ])
            
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
            
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 修复: {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ 错误处理 {file_path}: {e}")
        return False


def fix_all_imports():
    """修复所有文件的导入"""
    panorama_dir = Path("src/modules/panorama_view")
    fixed_count = 0
    total_count = 0
    
    for py_file in panorama_dir.rglob("*.py"):
        if '__pycache__' in str(py_file):
            continue
            
        total_count += 1
        if fix_imports_in_file(py_file):
            fixed_count += 1
            
    print(f"\n修复完成: {fixed_count}/{total_count} 个文件")


def main():
    """主函数"""
    print("="*60)
    print("修复 panorama_view 包内导入")
    print("="*60)
    
    fix_all_imports()


if __name__ == "__main__":
    main()