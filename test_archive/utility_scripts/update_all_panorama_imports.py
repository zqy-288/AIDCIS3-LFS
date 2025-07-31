#!/usr/bin/env python3
"""
更新所有文件中的panorama导入路径
"""

import os
import re
from pathlib import Path


def update_file(file_path):
    """更新单个文件中的导入路径"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # 定义替换规则
        replacements = [
            # 导入语句
            (r'from src\.core_business\.graphics\.panorama', 
             'from src.modules.panorama_view'),
            (r'import src\.core_business\.graphics\.panorama', 
             'import src.modules.panorama_view'),
            # 字符串中的引用
            (r'src\.core_business\.graphics\.panorama', 
             'src.modules.panorama_view'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
            
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 更新: {file_path}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ 错误处理 {file_path}: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("更新所有panorama导入路径")
    print("="*60)
    
    # 要排除的目录
    exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', '.pytest_cache'}
    
    # 要排除的文件
    exclude_files = {
        'update_panorama_imports.py',
        'update_all_panorama_imports.py',
        'test_panorama_migration.py',
        'simple_panorama_test.py'
    }
    
    updated_count = 0
    total_count = 0
    
    # 遍历所有Python文件
    for root, dirs, files in os.walk('.'):
        # 过滤掉不需要的目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py') and file not in exclude_files:
                file_path = os.path.join(root, file)
                total_count += 1
                
                if update_file(file_path):
                    updated_count += 1
    
    print(f"\n更新完成: {updated_count}/{total_count} 个文件")
    
    # 特别检查一些关键文件
    print("\n检查关键文件...")
    key_files = [
        'src/modules/panorama_controller.py',
        'src/services/graphics_service.py',
        'src/core_business/graphics/dynamic_sector_view.py',
    ]
    
    for file in key_files:
        if os.path.exists(file):
            print(f"检查 {file}...")
            update_file(file)


if __name__ == "__main__":
    main()