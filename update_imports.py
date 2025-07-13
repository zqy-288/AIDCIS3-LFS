"""批量更新main_window导入语句"""
import os
import re
from pathlib import Path

def update_imports_in_file(file_path):
    """更新单个文件中的导入语句"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # 替换导入语句
        patterns = [
            (r'from main_window import MainWindow', 'from main_window.main_window import MainWindow'),
            (r'import main_window\b', 'import main_window.main_window as main_window'),
        ]
        
        for old_pattern, new_pattern in patterns:
            content = re.sub(old_pattern, new_pattern, content)
            
        # 如果内容有变化，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """主函数"""
    root_path = Path("/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS")
    
    # 需要更新的文件列表
    files_to_update = [
        "test_*.py",
        "scripts/**/*.py",
        "tests/**/*.py",
        "run_project.py"
    ]
    
    updated_count = 0
    
    for pattern in files_to_update:
        for file_path in root_path.rglob(pattern):
            if file_path.is_file() and file_path.suffix == '.py':
                # 跳过新的main_window模块目录
                if 'main_window/' in str(file_path):
                    continue
                    
                print(f"Checking: {file_path.relative_to(root_path)}")
                
                if update_imports_in_file(file_path):
                    print(f"  ✓ Updated")
                    updated_count += 1
                    
    print(f"\nTotal files updated: {updated_count}")
    
    # 确认原始文件已被重命名
    original_file = root_path / "src" / "main_window.py"
    if original_file.exists():
        print(f"\n⚠️  Warning: Original main_window.py still exists at {original_file}")
    else:
        print("\n✓ Original main_window.py has been renamed/removed")

if __name__ == "__main__":
    main()