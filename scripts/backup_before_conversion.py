#!/usr/bin/env python3
"""
孔位ID格式转换前的数据备份脚本
AI员工1号创建 - 2025-01-14

功能：
- 备份所有可能包含孔位ID的关键文件
- 创建时间戳目录保存备份
- 生成备份清单和验证文件
"""

import os
import shutil
import json
import hashlib
import datetime
from pathlib import Path
from typing import List, Dict, Any


class BackupManager:
    """备份管理器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.project_root / "backups" / f"hole_id_conversion_backup_{self.timestamp}"
        self.backup_manifest = {
            "backup_time": datetime.datetime.now().isoformat(),
            "backup_purpose": "Hole ID format conversion preparation",
            "project_root": str(self.project_root),
            "files": [],
            "directories": [],
            "checksums": {}
        }
    
    def create_backup_structure(self):
        """创建备份目录结构"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建备份目录: {self.backup_dir}")
    
    def calculate_checksum(self, file_path: Path) -> str:
        """计算文件的MD5校验和"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"⚠️ 无法计算校验和 {file_path}: {e}")
            return ""
    
    def backup_file(self, source_path: Path, relative_path: str):
        """备份单个文件"""
        if not source_path.exists():
            print(f"⚠️ 文件不存在: {source_path}")
            return
        
        backup_file_path = self.backup_dir / relative_path
        backup_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(source_path, backup_file_path)
            checksum = self.calculate_checksum(source_path)
            
            self.backup_manifest["files"].append({
                "original_path": str(source_path),
                "backup_path": str(backup_file_path),
                "relative_path": relative_path,
                "size": source_path.stat().st_size,
                "modified_time": datetime.datetime.fromtimestamp(source_path.stat().st_mtime).isoformat()
            })
            
            if checksum:
                self.backup_manifest["checksums"][str(source_path)] = checksum
            
            print(f"✅ 备份文件: {relative_path}")
            
        except Exception as e:
            print(f"❌ 备份失败 {source_path}: {e}")
    
    def backup_directory(self, source_path: Path, relative_path: str):
        """备份整个目录"""
        if not source_path.exists() or not source_path.is_dir():
            print(f"⚠️ 目录不存在: {source_path}")
            return
        
        backup_dir_path = self.backup_dir / relative_path
        
        try:
            shutil.copytree(source_path, backup_dir_path, dirs_exist_ok=True)
            
            self.backup_manifest["directories"].append({
                "original_path": str(source_path),
                "backup_path": str(backup_dir_path),
                "relative_path": relative_path
            })
            
            print(f"✅ 备份目录: {relative_path}")
            
        except Exception as e:
            print(f"❌ 备份目录失败 {source_path}: {e}")
    
    def backup_core_files(self):
        """备份核心代码文件"""
        print("\n📁 备份核心代码文件...")
        
        core_files = [
            # 核心数据模型
            "src/aidcis2/models/hole_data.py",
            "src/aidcis2/dxf_parser.py",
            "src/models/batch_data_manager.py",
            
            # 主要数据文件
            "assets/dxf/DXF Graph/dongzhong_hole_grid.json",
            "reports/test_report_WP-2025-001.json",
            
            # 业务逻辑层
            "src/modules/report_output_interface.py",
            "src/modules/realtime_chart.py",
            "src/main_window.py",
            "src/modules/archive_manager.py",
            
            # UI显示层
            "src/aidcis2/graphics/hole_item.py",
            "src/aidcis2/graphics/dynamic_sector_view.py",
            "src/aidcis2/graphics/graphics_view.py",
            "src/aidcis2/graphics/sector_view.py",
            
            # 工具脚本
            "parse_dongzhong_dxf.py"
        ]
        
        for file_path in core_files:
            source_path = self.project_root / file_path
            self.backup_file(source_path, file_path)
    
    def backup_data_directories(self):
        """备份数据目录"""
        print("\n📁 备份数据目录...")
        
        data_dirs = [
            "Data/C001R001",
            "Data/C002R001", 
            "Data/C003R001",
            "assets/archive/Archive/C001R001",
            "src/data"
        ]
        
        for dir_path in data_dirs:
            source_path = self.project_root / dir_path
            if source_path.exists():
                self.backup_directory(source_path, dir_path)
    
    def backup_batch_data_files(self):
        """备份批处理数据文件"""
        print("\n📁 备份批处理数据文件...")
        
        src_data_dir = self.project_root / "src" / "data"
        if src_data_dir.exists():
            for file_path in src_data_dir.glob("batch_*.json"):
                relative_path = f"src/data/{file_path.name}"
                self.backup_file(file_path, relative_path)
    
    def save_manifest(self):
        """保存备份清单"""
        manifest_path = self.backup_dir / "backup_manifest.json"
        
        # 添加统计信息
        self.backup_manifest["statistics"] = {
            "total_files": len(self.backup_manifest["files"]),
            "total_directories": len(self.backup_manifest["directories"]),
            "total_checksums": len(self.backup_manifest["checksums"])
        }
        
        try:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(self.backup_manifest, f, indent=2, ensure_ascii=False)
            print(f"✅ 保存备份清单: {manifest_path}")
        except Exception as e:
            print(f"❌ 保存备份清单失败: {e}")
    
    def create_restore_script(self):
        """创建恢复脚本"""
        restore_script_path = self.backup_dir / "restore_backup.py"
        
        restore_script_content = f'''#!/usr/bin/env python3
"""
孔位ID格式转换备份恢复脚本
生成时间: {datetime.datetime.now().isoformat()}
"""

import os
import shutil
import json
from pathlib import Path

def restore_backup():
    """恢复备份"""
    backup_dir = Path(__file__).parent
    project_root = Path("{self.project_root}")
    
    print("⚠️ 警告: 此操作将覆盖现有文件!")
    confirm = input("是否继续恢复备份? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ 恢复操作已取消")
        return
    
    # 读取备份清单
    manifest_path = backup_dir / "backup_manifest.json"
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    # 恢复文件
    for file_info in manifest["files"]:
        backup_path = Path(file_info["backup_path"])
        original_path = Path(file_info["original_path"])
        
        if backup_path.exists():
            original_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, original_path)
            print(f"✅ 恢复文件: {{original_path}}")
        else:
            print(f"⚠️ 备份文件不存在: {{backup_path}}")
    
    # 恢复目录
    for dir_info in manifest["directories"]:
        backup_path = Path(dir_info["backup_path"])
        original_path = Path(dir_info["original_path"])
        
        if backup_path.exists():
            if original_path.exists():
                shutil.rmtree(original_path)
            shutil.copytree(backup_path, original_path)
            print(f"✅ 恢复目录: {{original_path}}")
        else:
            print(f"⚠️ 备份目录不存在: {{backup_path}}")
    
    print("✅ 备份恢复完成!")

if __name__ == "__main__":
    restore_backup()
'''
        
        try:
            with open(restore_script_path, 'w', encoding='utf-8') as f:
                f.write(restore_script_content)
            
            # 设置执行权限
            os.chmod(restore_script_path, 0o755)
            print(f"✅ 创建恢复脚本: {restore_script_path}")
        except Exception as e:
            print(f"❌ 创建恢复脚本失败: {e}")
    
    def run_backup(self):
        """执行完整备份"""
        print(f"🚀 开始孔位ID格式转换前备份...")
        print(f"📅 备份时间: {self.backup_manifest['backup_time']}")
        print(f"📁 备份目录: {self.backup_dir}")
        
        self.create_backup_structure()
        self.backup_core_files()
        self.backup_data_directories()
        self.backup_batch_data_files()
        self.save_manifest()
        self.create_restore_script()
        
        print(f"\n✅ 备份完成!")
        print(f"📊 统计信息:")
        print(f"   - 文件数量: {len(self.backup_manifest['files'])}")
        print(f"   - 目录数量: {len(self.backup_manifest['directories'])}")
        print(f"   - 校验和数量: {len(self.backup_manifest['checksums'])}")
        print(f"📁 备份位置: {self.backup_dir}")
        print(f"📄 清单文件: {self.backup_dir}/backup_manifest.json")
        print(f"🔧 恢复脚本: {self.backup_dir}/restore_backup.py")


def main():
    """主函数"""
    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print("🛡️ 孔位ID格式转换前数据备份工具")
    print("=" * 50)
    
    backup_manager = BackupManager(str(project_root))
    backup_manager.run_backup()


if __name__ == "__main__":
    main()