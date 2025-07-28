#!/usr/bin/env python3
"""
孔位ID格式迁移脚本
将系统中所有旧格式的孔位ID统一迁移为AC/BC格式
"""

import os
import sys
import json
import shutil
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.hole_id_converter import HoleIDConverter, convert_hole_id


class HoleIDMigrator:
    """孔位ID迁移器"""
    
    def __init__(self, project_root: Path, dry_run: bool = True):
        """
        初始化迁移器
        
        Args:
            project_root: 项目根目录
            dry_run: 是否为模拟运行（不实际修改文件）
        """
        self.project_root = project_root
        self.dry_run = dry_run
        self.converter = HoleIDConverter()
        self.migration_log = []
        self.error_log = []
        
        # 创建备份目录
        self.backup_dir = project_root / "backup" / f"hole_id_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.migration_log.append(log_entry)
        print(log_entry)
    
    def error(self, message: str):
        """记录错误"""
        self.error_log.append(message)
        self.log(message, "ERROR")
    
    def backup_file(self, file_path: Path) -> Path:
        """备份文件"""
        if self.dry_run:
            return file_path
        
        relative_path = file_path.relative_to(self.project_root)
        backup_path = self.backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def migrate_database(self, db_path: Path) -> int:
        """
        迁移数据库中的孔位ID
        
        Returns:
            更新的记录数
        """
        self.log(f"开始迁移数据库: {db_path}")
        
        if not db_path.exists():
            self.error(f"数据库文件不存在: {db_path}")
            return 0
        
        # 备份数据库
        if not self.dry_run:
            self.backup_file(db_path)
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查找所有包含hole_id的表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            total_updated = 0
            
            for table_name, in tables:
                # 检查表是否有hole_id列
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                has_hole_id = any(col[1] == 'hole_id' for col in columns)
                
                if has_hole_id:
                    # 获取所有需要更新的记录
                    cursor.execute(f"SELECT DISTINCT hole_id FROM {table_name} WHERE hole_id IS NOT NULL")
                    hole_ids = cursor.fetchall()
                    
                    for old_id, in hole_ids:
                        try:
                            new_id = self.converter.convert(old_id)
                            if old_id != new_id:
                                if not self.dry_run:
                                    cursor.execute(
                                        f"UPDATE {table_name} SET hole_id = ? WHERE hole_id = ?",
                                        (new_id, old_id)
                                    )
                                    updated = cursor.rowcount
                                else:
                                    # 模拟运行时只计数
                                    cursor.execute(
                                        f"SELECT COUNT(*) FROM {table_name} WHERE hole_id = ?",
                                        (old_id,)
                                    )
                                    updated = cursor.fetchone()[0]
                                
                                total_updated += updated
                                self.log(f"  表 {table_name}: {old_id} -> {new_id} (更新 {updated} 条记录)")
                        except ValueError as e:
                            self.error(f"  无法转换ID {old_id}: {e}")
            
            if not self.dry_run:
                conn.commit()
            conn.close()
            
            self.log(f"数据库迁移完成，共更新 {total_updated} 条记录")
            return total_updated
            
        except Exception as e:
            self.error(f"数据库迁移失败: {e}")
            return 0
    
    def migrate_directories(self, data_dir: Path) -> int:
        """
        迁移文件系统中的目录名
        
        Returns:
            重命名的目录数
        """
        self.log(f"开始迁移目录: {data_dir}")
        
        if not data_dir.exists():
            self.error(f"数据目录不存在: {data_dir}")
            return 0
        
        renamed_count = 0
        
        # 遍历所有子目录
        for dir_path in data_dir.iterdir():
            if dir_path.is_dir():
                old_name = dir_path.name
                
                try:
                    # 尝试转换目录名
                    new_name = self.converter.convert(old_name)
                    
                    if old_name != new_name:
                        new_path = dir_path.parent / new_name
                        
                        if new_path.exists():
                            self.error(f"  目标目录已存在: {new_path}")
                            continue
                        
                        if not self.dry_run:
                            dir_path.rename(new_path)
                        
                        renamed_count += 1
                        self.log(f"  重命名目录: {old_name} -> {new_name}")
                        
                except ValueError:
                    # 不是孔位ID格式的目录，跳过
                    pass
        
        self.log(f"目录迁移完成，共重命名 {renamed_count} 个目录")
        return renamed_count
    
    def migrate_json_file(self, file_path: Path) -> int:
        """
        迁移JSON文件中的孔位ID
        
        Returns:
            更新的ID数量
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 备份文件
            if not self.dry_run:
                self.backup_file(file_path)
            
            updated_count = 0
            
            def update_dict(obj):
                nonlocal updated_count
                if isinstance(obj, dict):
                    # 检查是否有hole_id键
                    if 'hole_id' in obj:
                        old_id = obj['hole_id']
                        try:
                            new_id = self.converter.convert(old_id)
                            if old_id != new_id:
                                obj['hole_id'] = new_id
                                updated_count += 1
                                self.log(f"    {old_id} -> {new_id}")
                        except ValueError:
                            pass
                    
                    # 递归处理所有值
                    for key, value in obj.items():
                        if isinstance(value, (dict, list)):
                            update_dict(value)
                            
                elif isinstance(obj, list):
                    for item in obj:
                        update_dict(item)
            
            update_dict(data)
            
            if updated_count > 0 and not self.dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            return updated_count
            
        except Exception as e:
            self.error(f"处理JSON文件失败 {file_path}: {e}")
            return 0
    
    def migrate_json_files(self, directory: Path) -> int:
        """
        迁移目录中所有JSON文件
        
        Returns:
            更新的文件数
        """
        self.log(f"开始迁移JSON文件: {directory}")
        
        total_files = 0
        total_updates = 0
        
        for json_file in directory.rglob("*.json"):
            updates = self.migrate_json_file(json_file)
            if updates > 0:
                total_files += 1
                total_updates += updates
                self.log(f"  更新文件: {json_file.relative_to(self.project_root)} ({updates} 个ID)")
        
        self.log(f"JSON文件迁移完成，共更新 {total_files} 个文件，{total_updates} 个ID")
        return total_files
    
    def migrate_python_tests(self) -> int:
        """
        迁移测试文件中的孔位ID
        
        Returns:
            更新的文件数
        """
        self.log("开始迁移测试文件中的孔位ID")
        
        test_dir = self.project_root / "tests"
        if not test_dir.exists():
            self.error("测试目录不存在")
            return 0
        
        updated_files = 0
        
        # 需要替换的ID映射
        replacements = {
            'H001': 'AC001R001',
            'H002': 'AC001R002',
            'H003': 'AC001R003',
            'H004': 'AC001R004',
            'H005': 'AC001R005',
            'H006': 'AC001R006',
            'H007': 'AC001R007',
            'H008': 'AC001R008',
            'C001R001': 'AC001R001',
            'C001R002': 'AC001R002',
            'R001C001': 'AC001R001',
            'R001C002': 'AC001R002',
        }
        
        for py_file in test_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # 替换所有已知的旧格式ID
                for old_id, new_id in replacements.items():
                    # 替换字符串中的ID（包括引号）
                    content = content.replace(f'"{old_id}"', f'"{new_id}"')
                    content = content.replace(f"'{old_id}'", f"'{new_id}'")
                    content = content.replace(f'`{old_id}`', f'`{new_id}`')
                
                if content != original_content:
                    if not self.dry_run:
                        self.backup_file(py_file)
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                    
                    updated_files += 1
                    self.log(f"  更新文件: {py_file.relative_to(self.project_root)}")
                    
            except Exception as e:
                self.error(f"处理Python文件失败 {py_file}: {e}")
        
        self.log(f"测试文件迁移完成，共更新 {updated_files} 个文件")
        return updated_files
    
    def save_migration_report(self):
        """保存迁移报告"""
        report_path = self.project_root / f"hole_id_migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("孔位ID格式迁移报告\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("迁移日志:\n")
            f.write("-" * 30 + "\n")
            for log_entry in self.migration_log:
                f.write(log_entry + "\n")
            
            if self.error_log:
                f.write("\n错误日志:\n")
                f.write("-" * 30 + "\n")
                for error in self.error_log:
                    f.write(error + "\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write(f"模拟运行: {'是' if self.dry_run else '否'}\n")
            if not self.dry_run:
                f.write(f"备份目录: {self.backup_dir}\n")
        
        self.log(f"迁移报告已保存: {report_path}")
    
    def run(self):
        """执行迁移"""
        self.log("开始孔位ID格式迁移")
        self.log(f"项目根目录: {self.project_root}")
        self.log(f"模拟运行: {'是' if self.dry_run else '否'}")
        
        # 1. 迁移数据库
        db_path = self.project_root / "detection_system.db"
        self.migrate_database(db_path)
        
        # 2. 迁移文件系统目录
        data_dir = self.project_root / "Data" / "CAP1000"
        self.migrate_directories(data_dir)
        
        # 3. 迁移JSON配置文件
        self.migrate_json_files(self.project_root / "assets")
        self.migrate_json_files(self.project_root / "config")
        self.migrate_json_files(self.project_root / "Data")
        
        # 4. 迁移测试文件
        self.migrate_python_tests()
        
        # 5. 保存迁移报告
        self.save_migration_report()
        
        if self.dry_run:
            self.log("\n⚠️  这是模拟运行，没有实际修改任何文件")
            self.log("如果要执行实际迁移，请使用 --execute 参数")
        else:
            self.log("\n✅ 迁移完成！")
            self.log(f"备份已保存在: {self.backup_dir}")


def main():
    parser = argparse.ArgumentParser(description="孔位ID格式迁移工具")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="执行实际迁移（默认为模拟运行）"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="项目根目录路径"
    )
    
    args = parser.parse_args()
    
    migrator = HoleIDMigrator(
        project_root=args.project_root,
        dry_run=not args.execute
    )
    
    try:
        migrator.run()
    except KeyboardInterrupt:
        print("\n\n迁移被用户中断")
    except Exception as e:
        print(f"\n\n迁移失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()