#!/usr/bin/env python3
"""
批量更新panorama包的导入路径
"""

import os
import re
from pathlib import Path

def update_imports_in_file(file_path, dry_run=True):
    """更新单个文件中的导入路径"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # 更新从core_business到modules的导入
        patterns = [
            # from导入模式
            (r'from\s+src\.core_business\.graphics\.panorama', 
             'from src.modules.panorama_view'),
            # import导入模式
            (r'import\s+src\.core_business\.graphics\.panorama', 
             'import src.modules.panorama_view'),
        ]
        
        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                changes.append(f"{pattern} -> {replacement}")
                content = new_content
        
        # 特殊处理：更新包内部结构导入
        if 'panorama_view' in str(file_path):
            # 更新到新的包结构
            content = re.sub(
                r'from\s+src\.modules\.panorama_view\s+import',
                'from src.modules.panorama_view.core import',
                content
            )
            
            # 更新组件导入
            content = re.sub(
                r'from\s+\.(?!\.)',  # 单点相对导入
                'from ..components.',
                content
            ) if '/core/' in str(file_path) or '/adapters/' in str(file_path) else content
        
        if content != original_content:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ 更新: {file_path}")
                for change in changes:
                    print(f"   - {change}")
            else:
                print(f"🔍 需要更新: {file_path}")
                for change in changes:
                    print(f"   - {change}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ 错误处理 {file_path}: {e}")
        return False

def find_and_update_imports(root_dir, dry_run=True):
    """查找并更新所有Python文件中的导入"""
    updated_files = 0
    total_files = 0
    
    # 定义需要更新的目录
    directories_to_update = [
        'src/modules/panorama_view',  # 新位置的文件
        'src/modules',  # 其他模块
        'src/pages',    # 页面
        'src/services', # 服务
        'src/core_business/graphics',  # 图形组件
    ]
    
    for directory in directories_to_update:
        dir_path = Path(root_dir) / directory
        if not dir_path.exists():
            continue
            
        for py_file in dir_path.rglob('*.py'):
            # 跳过__pycache__目录
            if '__pycache__' in str(py_file):
                continue
                
            total_files += 1
            if update_imports_in_file(py_file, dry_run):
                updated_files += 1
    
    print(f"\n{'🔍 分析' if dry_run else '✅ 更新'}完成: {updated_files}/{total_files} 个文件需要更新")
    return updated_files, total_files

def main():
    """主函数"""
    import sys
    
    # 获取项目根目录
    root_dir = Path(__file__).parent
    
    print("="*60)
    print("Panorama包导入路径更新工具")
    print("="*60)
    
    # 首先进行dry run
    print("\n1. 分析需要更新的文件...")
    updated, total = find_and_update_imports(root_dir, dry_run=True)
    
    if updated == 0:
        print("\n✅ 没有需要更新的文件")
        return
    
    # 询问是否执行更新
    if len(sys.argv) > 1 and sys.argv[1] == '--execute':
        execute = True
    else:
        response = input(f"\n是否执行更新？({updated} 个文件将被修改) [y/N]: ")
        execute = response.lower() == 'y'
    
    if execute:
        print("\n2. 执行更新...")
        find_and_update_imports(root_dir, dry_run=False)
        print("\n✅ 更新完成！")
        
        # 更新特定文件的导入
        print("\n3. 更新关键文件的特定导入...")
        update_specific_imports()
    else:
        print("\n❌ 更新已取消")

def update_specific_imports():
    """更新特定文件的导入"""
    specific_updates = {
        'src/modules/panorama_view/__init__.py': {
            'old': 'from src.core_business.graphics.panorama',
            'new': 'from src.modules.panorama_view.core'
        },
        'src/modules/panorama_controller.py': {
            'old': 'from src.core_business.graphics.panorama import PanoramaDIContainer',
            'new': 'from src.modules.panorama_view.core import PanoramaDIContainer'
        }
    }
    
    for file_path, update in specific_updates.items():
        if Path(file_path).exists():
            update_imports_in_file(file_path, dry_run=False)

if __name__ == "__main__":
    main()