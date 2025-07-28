#!/usr/bin/env python3
"""
AIDCIS3-LFS 版本迁移脚本
提供完整的版本升级和迁移功能，包括数据库迁移、配置更新、文件迁移等
"""

import os
import sys
import sqlite3
import shutil
import json
import argparse
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

# 添加项目路径到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

class Color:
    """控制台颜色常量"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class VersionManager:
    """版本管理器"""
    
    SUPPORTED_VERSIONS = {
        "1.0.0": "Initial release",
        "1.1.0": "Basic MVVM refactoring",
        "1.2.0": "Enhanced graphics components",
        "2.0.0": "Complete MVVM architecture with 96.6% code reduction"
    }
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.migration_log = []
        self.current_version = None
        self.target_version = None
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.project_root / 'migration.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        print(f"{Color.CYAN}🔄 AIDCIS3-LFS 版本迁移工具{Color.END}")
        print(f"📁 项目根目录: {self.project_root}")
    
    def print_section(self, title: str):
        """打印章节标题"""
        print(f"\n{Color.BOLD}{Color.BLUE}{'='*60}{Color.END}")
        print(f"{Color.BOLD}{Color.BLUE}🚀 {title}{Color.END}")
        print(f"{Color.BOLD}{Color.BLUE}{'='*60}{Color.END}")
    
    def print_success(self, message: str):
        """打印成功消息"""
        print(f"{Color.GREEN}✅ {message}{Color.END}")
        self.logger.info(message)
    
    def print_error(self, message: str):
        """打印错误消息"""
        print(f"{Color.RED}❌ {message}{Color.END}")
        self.logger.error(message)
    
    def print_warning(self, message: str):
        """打印警告消息"""
        print(f"{Color.YELLOW}⚠️  {message}{Color.END}")
        self.logger.warning(message)
    
    def print_info(self, message: str):
        """打印信息消息"""
        print(f"{Color.CYAN}ℹ️  {message}{Color.END}")
        self.logger.info(message)


class DatabaseMigrator:
    """数据库迁移器"""
    
    def __init__(self, version_manager: VersionManager):
        self.vm = version_manager
        self.db_path = self.vm.project_root / "data" / "aidcis3_data.db"
        
    def backup_database(self, version: str) -> Path:
        """备份数据库"""
        self.vm.print_info(f"备份数据库到版本 {version}")
        
        if not self.db_path.exists():
            self.vm.print_warning("数据库文件不存在，跳过备份")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"aidcis3_data_v{version}_{timestamp}.db"
        backup_path = self.vm.project_root / "backups" / backup_name
        
        # 创建备份目录
        backup_path.parent.mkdir(exist_ok=True)
        
        # 复制数据库文件
        shutil.copy2(self.db_path, backup_path)
        
        self.vm.print_success(f"数据库已备份到: {backup_path}")
        return backup_path
    
    def get_database_version(self) -> Optional[str]:
        """获取当前数据库版本"""
        if not self.db_path.exists():
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查版本表是否存在
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='migration_history'
            """)
            
            if not cursor.fetchone():
                # 如果没有版本表，检查表结构来推断版本
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                if 'workpieces' in tables and 'holes' in tables:
                    return "1.0.0"  # 基础版本
                else:
                    return None
            
            # 获取最新的迁移版本
            cursor.execute("""
                SELECT version FROM migration_history 
                ORDER BY applied_at DESC LIMIT 1
            """)
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            self.vm.print_error(f"获取数据库版本失败: {e}")
            return None
    
    def create_migration_table(self):
        """创建迁移历史表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_migration(self, version: str, description: str):
        """记录迁移历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO migration_history (version, description)
            VALUES (?, ?)
        """, (version, description))
        
        conn.commit()
        conn.close()
    
    def migrate_to_1_1_0(self):
        """迁移到版本 1.1.0 - 基础MVVM重构"""
        self.vm.print_info("执行 1.1.0 迁移: 基础MVVM重构")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 添加UI配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ui_configurations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT UNIQUE NOT NULL,
                    window_geometry TEXT,
                    splitter_states TEXT,
                    user_preferences TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 添加视图状态表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS view_states (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    view_name TEXT NOT NULL,
                    state_data TEXT,
                    workpiece_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workpiece_id) REFERENCES workpieces (id)
                )
            """)
            
            # 为现有表添加MVVM相关字段
            cursor.execute("PRAGMA table_info(workpieces)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'view_model_state' not in columns:
                cursor.execute("""
                    ALTER TABLE workpieces 
                    ADD COLUMN view_model_state TEXT DEFAULT '{}'
                """)
            
            if 'ui_metadata' not in columns:
                cursor.execute("""
                    ALTER TABLE workpieces 
                    ADD COLUMN ui_metadata TEXT DEFAULT '{}'
                """)
            
            conn.commit()
            self.record_migration("1.1.0", "基础MVVM重构 - 添加UI配置和视图状态表")
            self.vm.print_success("1.1.0 迁移完成")
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"1.1.0 迁移失败: {e}")
        finally:
            conn.close()
    
    def migrate_to_1_2_0(self):
        """迁移到版本 1.2.0 - 增强图形组件"""
        self.vm.print_info("执行 1.2.0 迁移: 增强图形组件")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 添加图形渲染配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS graphics_configurations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_type TEXT NOT NULL,
                    config_data TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 添加扇区管理表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sector_management (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workpiece_id INTEGER NOT NULL,
                    sector_count INTEGER DEFAULT 4 CHECK (sector_count >= 2 AND sector_count <= 12),
                    sector_config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workpiece_id) REFERENCES workpieces (id)
                )
            """)
            
            # 为holes表添加图形相关字段
            cursor.execute("PRAGMA table_info(holes)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'graphics_state' not in columns:
                cursor.execute("""
                    ALTER TABLE holes 
                    ADD COLUMN graphics_state TEXT DEFAULT '{}'
                """)
            
            if 'render_options' not in columns:
                cursor.execute("""
                    ALTER TABLE holes 
                    ADD COLUMN render_options TEXT DEFAULT '{}'
                """)
            
            if 'sector_id' not in columns:
                cursor.execute("""
                    ALTER TABLE holes 
                    ADD COLUMN sector_id INTEGER
                """)
            
            conn.commit()
            self.record_migration("1.2.0", "增强图形组件 - 添加图形配置和扇区管理")
            self.vm.print_success("1.2.0 迁移完成")
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"1.2.0 迁移失败: {e}")
        finally:
            conn.close()
    
    def migrate_to_2_0_0(self):
        """迁移到版本 2.0.0 - 完整MVVM架构"""
        self.vm.print_info("执行 2.0.0 迁移: 完整MVVM架构")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 添加服务注册表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS service_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_name TEXT UNIQUE NOT NULL,
                    service_type TEXT NOT NULL,
                    config_data TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 添加数据处理链表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_processing_chains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chain_name TEXT UNIQUE NOT NULL,
                    chain_config TEXT NOT NULL,
                    processing_order INTEGER DEFAULT 0,
                    is_enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 添加统一ID管理表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unified_id_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_table TEXT NOT NULL,
                    source_id INTEGER NOT NULL,
                    unified_id TEXT UNIQUE NOT NULL,
                    mapping_type TEXT DEFAULT 'auto',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_table, source_id)
                )
            """)
            
            # 更新workpieces表结构
            cursor.execute("PRAGMA table_info(workpieces)")
            columns = [column[1] for column in cursor.fetchall()]
            
            new_columns = {
                'mvvm_version': 'TEXT DEFAULT "2.0.0"',
                'data_service_config': 'TEXT DEFAULT "{}"',
                'processing_chain_id': 'INTEGER',
                'unified_id': 'TEXT UNIQUE'
            }
            
            for column_name, column_def in new_columns.items():
                if column_name not in columns:
                    cursor.execute(f"""
                        ALTER TABLE workpieces 
                        ADD COLUMN {column_name} {column_def}
                    """)
            
            # 生成统一ID
            cursor.execute("SELECT id FROM workpieces WHERE unified_id IS NULL")
            workpieces = cursor.fetchall()
            
            for (workpiece_id,) in workpieces:
                unified_id = f"WP_{workpiece_id:06d}"
                cursor.execute("""
                    UPDATE workpieces 
                    SET unified_id = ? 
                    WHERE id = ?
                """, (unified_id, workpiece_id))
                
                cursor.execute("""
                    INSERT OR REPLACE INTO unified_id_mappings 
                    (source_table, source_id, unified_id)
                    VALUES (?, ?, ?)
                """, ("workpieces", workpiece_id, unified_id))
            
            # 插入默认服务配置
            default_services = [
                ("DataService", "core", '{"auto_load": true, "cache_enabled": true}'),
                ("GraphicsService", "ui", '{"render_mode": "optimized", "quality": "high"}'),
                ("ProcessingService", "business", '{"parallel_processing": true, "workers": 4}')
            ]
            
            for service_name, service_type, config in default_services:
                cursor.execute("""
                    INSERT OR REPLACE INTO service_registry 
                    (service_name, service_type, config_data)
                    VALUES (?, ?, ?)
                """, (service_name, service_type, config))
            
            conn.commit()
            self.record_migration("2.0.0", "完整MVVM架构 - 服务注册、数据处理链、统一ID管理")
            self.vm.print_success("2.0.0 迁移完成")
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"2.0.0 迁移失败: {e}")
        finally:
            conn.close()


class ConfigurationMigrator:
    """配置文件迁移器"""
    
    def __init__(self, version_manager: VersionManager):
        self.vm = version_manager
        self.config_dir = self.vm.project_root / "config"
    
    def backup_configurations(self, version: str):
        """备份配置文件"""
        self.vm.print_info(f"备份配置文件到版本 {version}")
        
        if not self.config_dir.exists():
            self.vm.print_warning("配置目录不存在，跳过备份")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.vm.project_root / "backups" / f"config_v{version}_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制所有配置文件
        for config_file in self.config_dir.rglob("*"):
            if config_file.is_file():
                relative_path = config_file.relative_to(self.config_dir)
                backup_file = backup_dir / relative_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(config_file, backup_file)
        
        self.vm.print_success(f"配置文件已备份到: {backup_dir}")
    
    def migrate_config_to_2_0_0(self):
        """迁移配置到 2.0.0"""
        self.vm.print_info("迁移配置文件到 2.0.0")
        
        # 创建新的服务配置文件
        services_config = {
            "services": {
                "data_service": {
                    "enabled": True,
                    "auto_start": True,
                    "config": {
                        "cache_size": 1000,
                        "auto_save": True,
                        "backup_interval": 300
                    }
                },
                "graphics_service": {
                    "enabled": True,
                    "auto_start": True,
                    "config": {
                        "render_quality": "high",
                        "animation_enabled": True,
                        "hardware_acceleration": True
                    }
                },
                "processing_service": {
                    "enabled": True,
                    "auto_start": True,
                    "config": {
                        "max_workers": 4,
                        "timeout": 30,
                        "retry_count": 3
                    }
                }
            }
        }
        
        services_config_path = self.config_dir / "services.json"
        with open(services_config_path, 'w', encoding='utf-8') as f:
            json.dump(services_config, f, indent=2, ensure_ascii=False)
        
        # 创建MVVM配置文件
        mvvm_config = {
            "architecture": {
                "version": "2.0.0",
                "pattern": "MVVM",
                "view_model_binding": "auto",
                "dependency_injection": True
            },
            "views": {
                "main_window": {
                    "layout": "adaptive",
                    "theme": "default",
                    "responsive": True
                },
                "graphics_view": {
                    "rendering": "opengl",
                    "anti_aliasing": True,
                    "background_color": "#f0f0f0"
                }
            },
            "models": {
                "auto_load": True,
                "validation": True,
                "serialization": "json"
            }
        }
        
        mvvm_config_path = self.config_dir / "mvvm.json"
        with open(mvvm_config_path, 'w', encoding='utf-8') as f:
            json.dump(mvvm_config, f, indent=2, ensure_ascii=False)
        
        self.vm.print_success("配置文件迁移完成")


class FileMigrator:
    """文件结构迁移器"""
    
    def __init__(self, version_manager: VersionManager):
        self.vm = version_manager
    
    def migrate_file_structure_to_2_0_0(self):
        """迁移文件结构到 2.0.0"""
        self.vm.print_info("迁移文件结构到 2.0.0")
        
        # 创建新的目录结构
        new_dirs = [
            "src/core",
            "src/ui/views",
            "src/ui/view_models", 
            "src/ui/controls",
            "src/business/services",
            "src/business/models",
            "config/services",
            "data/migrations",
            "logs/migrations"
        ]
        
        for dir_path in new_dirs:
            full_path = self.vm.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
        
        # 创建新的__init__.py文件
        init_files = [
            "src/core/__init__.py",
            "src/ui/__init__.py",
            "src/ui/views/__init__.py",
            "src/ui/view_models/__init__.py",
            "src/business/__init__.py",
            "src/business/services/__init__.py"
        ]
        
        for init_file in init_files:
            init_path = self.vm.project_root / init_file
            if not init_path.exists():
                init_path.write_text('"""Module initialization"""')
        
        self.vm.print_success("文件结构迁移完成")


class VersionMigrationManager:
    """版本迁移管理器"""
    
    def __init__(self, project_root: Path = None):
        self.vm = VersionManager(project_root)
        self.db_migrator = DatabaseMigrator(self.vm)
        self.config_migrator = ConfigurationMigrator(self.vm)
        self.file_migrator = FileMigrator(self.vm)
    
    def check_current_version(self) -> str:
        """检查当前版本"""
        self.vm.print_section("检查当前版本")
        
        # 检查数据库版本
        db_version = self.db_migrator.get_database_version()
        
        # 检查文件版本
        version_file = self.vm.project_root / "src" / "version.py"
        file_version = None
        
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '__version__' in content:
                        # 提取版本号
                        import re
                        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
                        if match:
                            file_version = match.group(1)
            except Exception as e:
                self.vm.print_warning(f"读取版本文件失败: {e}")
        
        # 确定当前版本
        if db_version and file_version:
            if db_version == file_version:
                current_version = db_version
                self.vm.print_success(f"当前版本: {current_version}")
            else:
                self.vm.print_warning(f"版本不一致 - 数据库: {db_version}, 文件: {file_version}")
                current_version = max(db_version, file_version, key=lambda v: [int(x) for x in v.split('.')])
        elif db_version:
            current_version = db_version
            self.vm.print_info(f"从数据库获取版本: {current_version}")
        elif file_version:
            current_version = file_version
            self.vm.print_info(f"从文件获取版本: {current_version}")
        else:
            current_version = "1.0.0"
            self.vm.print_warning("未找到版本信息，假设为 1.0.0")
        
        self.vm.current_version = current_version
        return current_version
    
    def list_available_versions(self):
        """列出可用版本"""
        self.vm.print_section("可用版本")
        
        for version, description in self.vm.SUPPORTED_VERSIONS.items():
            status = "✅ 当前" if version == self.vm.current_version else "⬆️  可升级"
            print(f"{status} {version}: {description}")
    
    def migrate_to_version(self, target_version: str, force: bool = False) -> bool:
        """迁移到指定版本"""
        self.vm.print_section(f"迁移到版本 {target_version}")
        
        if target_version not in self.vm.SUPPORTED_VERSIONS:
            self.vm.print_error(f"不支持的版本: {target_version}")
            return False
        
        current_version = self.vm.current_version or self.check_current_version()
        
        if current_version == target_version and not force:
            self.vm.print_warning(f"已经是目标版本 {target_version}")
            return True
        
        # 确定迁移路径
        migration_path = self._get_migration_path(current_version, target_version)
        
        if not migration_path:
            self.vm.print_error(f"无法从 {current_version} 迁移到 {target_version}")
            return False
        
        self.vm.print_info(f"迁移路径: {' → '.join(migration_path)}")
        
        try:
            # 创建迁移历史表
            self.db_migrator.create_migration_table()
            
            # 执行每个版本的迁移
            for i in range(len(migration_path) - 1):
                from_version = migration_path[i]
                to_version = migration_path[i + 1]
                
                self.vm.print_info(f"从 {from_version} 迁移到 {to_version}")
                
                # 备份
                self.db_migrator.backup_database(to_version)
                self.config_migrator.backup_configurations(to_version)
                
                # 执行迁移
                if not self._execute_migration(to_version):
                    self.vm.print_error(f"迁移到 {to_version} 失败")
                    return False
                
                self.vm.print_success(f"成功迁移到 {to_version}")
            
            # 更新版本文件
            self._update_version_file(target_version)
            
            self.vm.target_version = target_version
            self.vm.print_success(f"🎉 成功迁移到版本 {target_version}")
            
            return True
            
        except Exception as e:
            self.vm.print_error(f"迁移失败: {e}")
            return False
    
    def _get_migration_path(self, from_version: str, to_version: str) -> List[str]:
        """获取迁移路径"""
        versions = list(self.vm.SUPPORTED_VERSIONS.keys())
        
        try:
            from_idx = versions.index(from_version)
            to_idx = versions.index(to_version)
            
            if from_idx > to_idx:
                self.vm.print_error("不支持版本降级")
                return None
            
            return versions[from_idx:to_idx + 1]
            
        except ValueError:
            return None
    
    def _execute_migration(self, version: str) -> bool:
        """执行指定版本的迁移"""
        try:
            if version == "1.1.0":
                self.db_migrator.migrate_to_1_1_0()
            elif version == "1.2.0":
                self.db_migrator.migrate_to_1_2_0()
            elif version == "2.0.0":
                self.db_migrator.migrate_to_2_0_0()
                self.config_migrator.migrate_config_to_2_0_0()
                self.file_migrator.migrate_file_structure_to_2_0_0()
            
            return True
            
        except Exception as e:
            self.vm.print_error(f"执行迁移失败: {e}")
            return False
    
    def _update_version_file(self, version: str):
        """更新版本文件"""
        version_file = self.vm.project_root / "src" / "version.py"
        version_content = f'__version__ = "{version}"\n'
        
        version_file.write_text(version_content, encoding='utf-8')
        self.vm.print_success(f"版本文件已更新: {version}")
    
    def validate_migration(self) -> bool:
        """验证迁移结果"""
        self.vm.print_section("验证迁移结果")
        
        try:
            # 验证数据库
            db_version = self.db_migrator.get_database_version()
            if db_version != self.vm.target_version:
                self.vm.print_error(f"数据库版本验证失败: {db_version} != {self.vm.target_version}")
                return False
            
            # 验证文件结构
            if self.vm.target_version == "2.0.0":
                required_dirs = [
                    "src/core",
                    "src/ui/views",
                    "src/business/services"
                ]
                
                for dir_path in required_dirs:
                    if not (self.vm.project_root / dir_path).exists():
                        self.vm.print_error(f"缺少目录: {dir_path}")
                        return False
            
            self.vm.print_success("迁移验证通过")
            return True
            
        except Exception as e:
            self.vm.print_error(f"验证失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AIDCIS3-LFS 版本迁移工具')
    parser.add_argument('--version', '-v', help='目标版本')
    parser.add_argument('--list', '-l', action='store_true', help='列出可用版本')
    parser.add_argument('--current', '-c', action='store_true', help='显示当前版本')
    parser.add_argument('--force', '-f', action='store_true', help='强制迁移')
    parser.add_argument('--validate', action='store_true', help='验证迁移结果')
    parser.add_argument('--project-root', type=str, help='项目根目录路径')
    
    args = parser.parse_args()
    
    # 设置项目根目录
    project_root = Path(args.project_root) if args.project_root else None
    
    # 创建迁移管理器
    migrator = VersionMigrationManager(project_root)
    
    try:
        if args.current:
            migrator.check_current_version()
            return 0
        
        if args.list:
            migrator.check_current_version()
            migrator.list_available_versions()
            return 0
        
        if args.validate:
            if migrator.validate_migration():
                return 0
            else:
                return 1
        
        if args.version:
            migrator.check_current_version()
            if migrator.migrate_to_version(args.version, args.force):
                if migrator.validate_migration():
                    return 0
                else:
                    return 1
            else:
                return 1
        
        # 默认显示当前版本和可用版本
        migrator.check_current_version()
        migrator.list_available_versions()
        return 0
        
    except KeyboardInterrupt:
        print(f"\n{Color.YELLOW}⚠️  迁移被用户中断{Color.END}")
        return 1
    
    except Exception as e:
        print(f"\n{Color.RED}💥 迁移异常: {e}{Color.END}")
        return 1


if __name__ == '__main__':
    sys.exit(main())