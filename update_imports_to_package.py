#!/usr/bin/env python3
"""
更新项目中的导入语句以使用新的包结构
"""
import os
import re
from pathlib import Path


def find_python_files(directory, exclude_dirs=None):
    """查找所有Python文件"""
    if exclude_dirs is None:
        exclude_dirs = {'.git', '__pycache__', 'venv', 'env', '.venv'}
    
    python_files = []
    
    for root, dirs, files in os.walk(directory):
        # 排除特定目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
                
    return python_files


def check_imports(file_path):
    """检查文件中的导入语句"""
    imports_to_update = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找旧的导入模式
        patterns = [
            r'from\s+modules\.realtime_chart\s+import\s+RealTimeChart',
            r'from\s+modules\.realtime_chart\s+import\s+RealtimeChart',
            r'import\s+modules\.realtime_chart',
            r'from\s+\.modules\.realtime_chart\s+import',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            if matches:
                imports_to_update.extend(matches)
                
        return imports_to_update
        
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return []


def update_imports(file_path, dry_run=True):
    """更新文件中的导入语句"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # 定义替换规则
        replacements = [
            # 旧导入 -> 新导入
            (r'from\s+modules\.realtime_chart\s+import\s+RealTimeChart',
             'from src.modules.realtime_chart_package import RealTimeChart'),
            
            (r'from\s+modules\.realtime_chart\s+import\s+RealtimeChart',
             'from src.modules.realtime_chart_package import RealtimeChart'),
            
            (r'import\s+modules\.realtime_chart\s+as\s+(\w+)',
             r'import src.modules.realtime_chart_package as \1'),
            
            (r'import\s+modules\.realtime_chart',
             'import src.modules.realtime_chart_package'),
        ]
        
        # 执行替换
        for old_pattern, new_pattern in replacements:
            content = re.sub(old_pattern, new_pattern, content)
            
        # 检查是否有变化
        if content != original_content:
            if dry_run:
                print(f"[DRY RUN] 将更新: {file_path}")
                # 显示变化
                lines1 = original_content.splitlines()
                lines2 = content.splitlines()
                for i, (line1, line2) in enumerate(zip(lines1, lines2)):
                    if line1 != line2:
                        print(f"  行 {i+1}:")
                        print(f"    - {line1}")
                        print(f"    + {line2}")
            else:
                # 备份原文件
                backup_path = f"{file_path}.backup"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                    
                # 写入更新后的内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                print(f"✅ 已更新: {file_path}")
                print(f"   备份保存在: {backup_path}")
                
            return True
            
    except Exception as e:
        print(f"❌ 更新失败 {file_path}: {e}")
        
    return False


def main():
    """主函数"""
    print("🔍 扫描项目中的导入语句...")
    print("=" * 60)
    
    # 项目根目录
    project_root = Path(__file__).parent
    
    # 查找所有Python文件
    python_files = find_python_files(project_root)
    
    # 排除特定文件
    exclude_files = {
        'update_imports_to_package.py',
        'test_package_import.py',
        'example_main_with_package.py'
    }
    
    files_to_update = []
    
    print(f"\n找到 {len(python_files)} 个Python文件")
    print("\n检查导入语句...")
    
    for file_path in python_files:
        # 排除特定文件
        if os.path.basename(file_path) in exclude_files:
            continue
            
        # 排除包自身的文件
        if 'realtime_chart_package' in file_path:
            continue
            
        imports = check_imports(file_path)
        if imports:
            files_to_update.append(file_path)
            print(f"\n📄 {file_path}")
            for imp in imports:
                print(f"   - {imp}")
                
    if not files_to_update:
        print("\n✅ 没有找到需要更新的导入语句")
        return
        
    print(f"\n\n找到 {len(files_to_update)} 个文件需要更新")
    print("-" * 60)
    
    # 询问用户
    print("\n选项:")
    print("1. 预览更改 (dry run)")
    print("2. 执行更新 (创建备份)")
    print("3. 取消")
    
    choice = input("\n请选择 (1-3): ").strip()
    
    if choice == '1':
        print("\n预览模式...")
        for file_path in files_to_update:
            update_imports(file_path, dry_run=True)
            
    elif choice == '2':
        print("\n执行更新...")
        confirm = input("确认更新这些文件？(y/n): ").strip().lower()
        
        if confirm == 'y':
            updated_count = 0
            for file_path in files_to_update:
                if update_imports(file_path, dry_run=False):
                    updated_count += 1
                    
            print(f"\n✅ 更新完成！共更新 {updated_count} 个文件")
        else:
            print("\n已取消")
            
    else:
        print("\n已取消")


if __name__ == '__main__':
    main()