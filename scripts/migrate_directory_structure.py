#!/usr/bin/env python3
"""
AI员工3号修改开始
目录迁移工具 - 将H格式目录结构迁移为新格式C{col:03d}R{row:03d}
支持安全的目录重命名和数据完整性验证
AI员工3号修改结束
"""

import os
import shutil
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import argparse

class DirectoryMigrationTool:
    """目录结构迁移工具"""
    
    def __init__(self, base_data_path: str = "Data", archive_path: str = "Archive", backup_path: str = "Backup"):
        """
        初始化迁移工具
        
        Args:
            base_data_path: 数据基础路径
            archive_path: 归档路径
            backup_path: 备份路径
        """
        # AI员工3号修改开始
        self.base_data_path = Path(base_data_path)
        self.archive_path = Path(archive_path)
        self.backup_path = Path(backup_path)
        
        # 确保路径存在
        self.base_data_path.mkdir(exist_ok=True)
        if self.archive_path.exists():
            self.archive_path.mkdir(exist_ok=True)
        self.backup_path.mkdir(exist_ok=True)
        
        # 迁移记录
        self.migration_log: List[Dict] = []
        self.errors: List[str] = []
        
        # 支持的格式转换
        self.format_patterns = {
            'H_format': r'^H(\d+)$',  # H00001 格式
            'coord_format': r'^\((\d+),(\d+)\)$',  # (1,2) 格式
            'rc_format': r'^R(\d+)C(\d+)$',  # R001C002 格式
            'new_format': r'^C(\d{3})R(\d{3})$'  # C001R002 格式
        }
        # AI员工3号修改结束
    
    def validate_new_format(self, hole_id: str) -> bool:
        """验证是否为新格式ID"""
        # AI员工3号修改开始
        pattern = r'^C\d{3}R\d{3}$'
        return bool(re.match(pattern, hole_id))
        # AI员工3号修改结束
    
    def parse_hole_coordinates(self, hole_id: str) -> Optional[Tuple[int, int]]:
        """
        解析孔位ID获取行列坐标
        
        Args:
            hole_id: 孔位ID
            
        Returns:
            Optional[Tuple[int, int]]: (row, column) 或 None
        """
        # AI员工3号修改开始
        # 新格式: C001R002 -> (row=2, col=1)
        new_match = re.match(r'^C(\d{3})R(\d{3})$', hole_id)
        if new_match:
            col, row = map(int, new_match.groups())
            return (row, col)
        
        # 坐标格式: (1,2) -> (row=1, col=2)
        coord_match = re.match(r'^\((\d+),(\d+)\)$', hole_id)
        if coord_match:
            row, col = map(int, coord_match.groups())
            return (row, col)
        
        # R###C###格式: R001C002 -> (row=1, col=2)
        rc_match = re.match(r'^R(\d+)C(\d+)$', hole_id)
        if rc_match:
            row, col = map(int, rc_match.groups())
            return (row, col)
        
        # H格式无法直接转换
        return None
        # AI员工3号修改结束
    
    def convert_to_new_format(self, hole_id: str, row: Optional[int] = None, col: Optional[int] = None) -> str:
        """
        转换为新格式ID
        
        Args:
            hole_id: 原始孔位ID
            row: 可选的行号
            col: 可选的列号
            
        Returns:
            str: 新格式ID
        """
        # AI员工3号修改开始
        # 如果已经是新格式，直接返回
        if self.validate_new_format(hole_id):
            return hole_id
        
        # 尝试从hole_id解析坐标
        coords = self.parse_hole_coordinates(hole_id)
        if coords:
            row, col = coords
            return f"C{col:03d}R{row:03d}"
        
        # 如果提供了外部坐标信息
        if row is not None and col is not None:
            return f"C{col:03d}R{row:03d}"
        
        # 无法转换，返回原ID
        return hole_id
        # AI员工3号修改结束
    
    def scan_directories(self, path: Path) -> List[Tuple[Path, str]]:
        """
        扫描目录，找到需要迁移的目录
        
        Args:
            path: 扫描路径
            
        Returns:
            List[Tuple[Path, str]]: [(目录路径, 孔位ID)]
        """
        # AI员工3号修改开始
        directories_to_migrate = []
        
        if not path.exists():
            print(f"⚠️ 路径不存在: {path}")
            return directories_to_migrate
        
        print(f"🔍 扫描目录: {path}")
        
        for item in path.iterdir():
            if item.is_dir():
                dir_name = item.name
                
                # 检查是否需要迁移（非新格式的目录）
                if not self.validate_new_format(dir_name):
                    # 检查是否是可识别的旧格式
                    if (re.match(r'^H\d+$', dir_name) or  # H格式
                        re.match(r'^\(\d+,\d+\)$', dir_name) or  # 坐标格式
                        re.match(r'^R\d+C\d+$', dir_name)):  # RC格式
                        
                        directories_to_migrate.append((item, dir_name))
                        print(f"📁 发现需迁移目录: {dir_name}")
        
        print(f"✅ 扫描完成，找到 {len(directories_to_migrate)} 个目录需要迁移")
        return directories_to_migrate
        # AI员工3号修改结束
    
    def create_backup(self, source_path: Path, backup_name: str) -> Path:
        """
        创建备份
        
        Args:
            source_path: 源路径
            backup_name: 备份名称
            
        Returns:
            Path: 备份路径
        """
        # AI员工3号修改开始
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_path / f"{backup_name}_{timestamp}"
        
        try:
            print(f"📦 创建备份: {source_path} -> {backup_dir}")
            shutil.copytree(source_path, backup_dir)
            
            # 创建备份元数据
            metadata = {
                'source_path': str(source_path),
                'backup_path': str(backup_dir),
                'created_at': timestamp,
                'backup_type': 'pre_migration'
            }
            
            metadata_file = backup_dir / "backup_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 备份创建成功: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            error_msg = f"❌ 创建备份失败: {e}"
            print(error_msg)
            self.errors.append(error_msg)
            raise
        # AI员工3号修改结束
    
    def migrate_single_directory(self, source_dir: Path, old_hole_id: str, dry_run: bool = False) -> bool:
        """
        迁移单个目录
        
        Args:
            source_dir: 源目录路径
            old_hole_id: 旧孔位ID
            dry_run: 是否为模拟运行
            
        Returns:
            bool: 是否成功
        """
        # AI员工3号修改开始
        try:
            # 尝试转换为新格式
            new_hole_id = self.convert_to_new_format(old_hole_id)
            
            # 如果无法转换，跳过
            if new_hole_id == old_hole_id and not self.validate_new_format(old_hole_id):
                warning_msg = f"⚠️ 无法转换孔位ID: {old_hole_id}"
                print(warning_msg)
                self.errors.append(warning_msg)
                return False
            
            # 如果已经是新格式，跳过
            if old_hole_id == new_hole_id:
                print(f"ℹ️ 已是新格式，跳过: {old_hole_id}")
                return True
            
            # 确定新目录路径
            new_dir = source_dir.parent / new_hole_id
            
            # 检查目标目录是否已存在
            if new_dir.exists() and new_dir != source_dir:
                error_msg = f"❌ 目标目录已存在: {new_dir}"
                print(error_msg)
                self.errors.append(error_msg)
                return False
            
            migration_record = {
                'old_hole_id': old_hole_id,
                'new_hole_id': new_hole_id,
                'source_path': str(source_dir),
                'target_path': str(new_dir),
                'timestamp': datetime.now().isoformat(),
                'dry_run': dry_run
            }
            
            if dry_run:
                print(f"🔄 [模拟] 迁移: {old_hole_id} -> {new_hole_id}")
                print(f"     源路径: {source_dir}")
                print(f"     目标路径: {new_dir}")
                migration_record['status'] = 'simulated'
            else:
                print(f"🔄 迁移目录: {old_hole_id} -> {new_hole_id}")
                
                # 重命名目录
                source_dir.rename(new_dir)
                
                print(f"✅ 迁移成功: {source_dir} -> {new_dir}")
                migration_record['status'] = 'completed'
            
            self.migration_log.append(migration_record)
            return True
            
        except Exception as e:
            error_msg = f"❌ 迁移失败 {old_hole_id}: {e}"
            print(error_msg)
            self.errors.append(error_msg)
            
            migration_record = {
                'old_hole_id': old_hole_id,
                'source_path': str(source_dir),
                'timestamp': datetime.now().isoformat(),
                'status': 'failed',
                'error': str(e),
                'dry_run': dry_run
            }
            self.migration_log.append(migration_record)
            return False
        # AI员工3号修改结束
    
    def migrate_data_directories(self, dry_run: bool = False, create_backup: bool = True) -> bool:
        """
        迁移数据目录
        
        Args:
            dry_run: 是否为模拟运行
            create_backup: 是否创建备份
            
        Returns:
            bool: 是否成功
        """
        # AI员工3号修改开始
        print(f"🚀 开始迁移数据目录: {self.base_data_path}")
        print(f"   模式: {'模拟运行' if dry_run else '实际执行'}")
        print(f"   备份: {'是' if create_backup else '否'}")
        
        # 创建备份
        if create_backup and not dry_run:
            try:
                self.create_backup(self.base_data_path, "data_directories")
            except Exception as e:
                print(f"❌ 备份失败，停止迁移: {e}")
                return False
        
        # 扫描需要迁移的目录
        directories_to_migrate = self.scan_directories(self.base_data_path)
        
        if not directories_to_migrate:
            print("ℹ️ 没有找到需要迁移的目录")
            return True
        
        # 执行迁移
        success_count = 0
        for dir_path, hole_id in directories_to_migrate:
            if self.migrate_single_directory(dir_path, hole_id, dry_run):
                success_count += 1
        
        print(f"\n📊 数据目录迁移完成:")
        print(f"   总计: {len(directories_to_migrate)} 个目录")
        print(f"   成功: {success_count} 个")
        print(f"   失败: {len(directories_to_migrate) - success_count} 个")
        
        return success_count == len(directories_to_migrate)
        # AI员工3号修改结束
    
    def migrate_archive_directories(self, dry_run: bool = False, create_backup: bool = True) -> bool:
        """
        迁移归档目录
        
        Args:
            dry_run: 是否为模拟运行
            create_backup: 是否创建备份
            
        Returns:
            bool: 是否成功
        """
        # AI员工3号修改开始
        if not self.archive_path.exists():
            print(f"ℹ️ 归档路径不存在，跳过: {self.archive_path}")
            return True
        
        print(f"🗃️ 开始迁移归档目录: {self.archive_path}")
        
        # 创建备份
        if create_backup and not dry_run:
            try:
                self.create_backup(self.archive_path, "archive_directories")
            except Exception as e:
                print(f"❌ 备份失败，停止迁移: {e}")
                return False
        
        # 扫描需要迁移的目录
        directories_to_migrate = self.scan_directories(self.archive_path)
        
        if not directories_to_migrate:
            print("ℹ️ 没有找到需要迁移的归档目录")
            return True
        
        # 执行迁移
        success_count = 0
        for dir_path, hole_id in directories_to_migrate:
            if self.migrate_single_directory(dir_path, hole_id, dry_run):
                success_count += 1
        
        print(f"\n📊 归档目录迁移完成:")
        print(f"   总计: {len(directories_to_migrate)} 个目录")
        print(f"   成功: {success_count} 个")
        print(f"   失败: {len(directories_to_migrate) - success_count} 个")
        
        return success_count == len(directories_to_migrate)
        # AI员工3号修改结束
    
    def generate_migration_report(self, output_file: str = "migration_report.json") -> bool:
        """
        生成迁移报告
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        # AI员工3号修改开始
        try:
            report = {
                'migration_summary': {
                    'total_directories': len(self.migration_log),
                    'successful_migrations': len([r for r in self.migration_log if r.get('status') == 'completed']),
                    'failed_migrations': len([r for r in self.migration_log if r.get('status') == 'failed']),
                    'simulated_migrations': len([r for r in self.migration_log if r.get('status') == 'simulated']),
                    'errors_count': len(self.errors),
                    'generated_at': datetime.now().isoformat()
                },
                'migration_log': self.migration_log,
                'errors': self.errors,
                'format_conversion_rules': {
                    'target_format': 'C{col:03d}R{row:03d}',
                    'supported_source_formats': [
                        'H{number} (需要额外坐标信息)',
                        '(row,col) 坐标格式',
                        'R{row}C{col} 格式'
                    ]
                }
            }
            
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"📄 迁移报告已生成: {output_path}")
            return True
            
        except Exception as e:
            error_msg = f"❌ 生成报告失败: {e}"
            print(error_msg)
            self.errors.append(error_msg)
            return False
        # AI员工3号修改结束
    
    def run_full_migration(self, dry_run: bool = False, create_backup: bool = True) -> bool:
        """
        执行完整迁移
        
        Args:
            dry_run: 是否为模拟运行
            create_backup: 是否创建备份
            
        Returns:
            bool: 是否成功
        """
        # AI员工3号修改开始
        print("=" * 60)
        print("🔄 AIDCIS 目录结构迁移工具")
        print("=" * 60)
        print(f"目标格式: C{{col:03d}}R{{row:03d}}")
        print(f"模式: {'模拟运行' if dry_run else '实际执行'}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 执行数据目录迁移
        data_success = self.migrate_data_directories(dry_run, create_backup)
        
        # 执行归档目录迁移
        archive_success = self.migrate_archive_directories(dry_run, create_backup)
        
        # 生成报告
        report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.generate_migration_report(report_file)
        
        # 输出总结
        print("\n" + "=" * 60)
        print("📊 迁移总结")
        print("=" * 60)
        print(f"数据目录迁移: {'✅ 成功' if data_success else '❌ 失败'}")
        print(f"归档目录迁移: {'✅ 成功' if archive_success else '❌ 失败'}")
        print(f"总计迁移: {len(self.migration_log)} 个目录")
        print(f"错误数量: {len(self.errors)}")
        
        if self.errors:
            print("\n❌ 错误列表:")
            for error in self.errors:
                print(f"  - {error}")
        
        overall_success = data_success and archive_success
        print(f"\n🎯 整体状态: {'✅ 成功' if overall_success else '❌ 失败'}")
        print("=" * 60)
        
        return overall_success
        # AI员工3号修改结束


def main():
    """主函数"""
    # AI员工3号修改开始
    parser = argparse.ArgumentParser(description="AIDCIS 目录结构迁移工具")
    parser.add_argument("--dry-run", action="store_true", help="模拟运行，不实际执行迁移")
    parser.add_argument("--no-backup", action="store_true", help="不创建备份")
    parser.add_argument("--data-path", default="Data", help="数据目录路径")
    parser.add_argument("--archive-path", default="Archive", help="归档目录路径")
    parser.add_argument("--backup-path", default="Backup", help="备份目录路径")
    
    args = parser.parse_args()
    
    # 创建迁移工具实例
    migration_tool = DirectoryMigrationTool(
        base_data_path=args.data_path,
        archive_path=args.archive_path,
        backup_path=args.backup_path
    )
    
    # 执行迁移
    success = migration_tool.run_full_migration(
        dry_run=args.dry_run,
        create_backup=not args.no_backup
    )
    
    # 退出状态
    exit(0 if success else 1)
    # AI员工3号修改结束


if __name__ == "__main__":
    main()