#!/usr/bin/env python3
"""
AIDCIS3-LFS 迁移工具集
提供迁移过程中需要的实用工具和助手函数
"""

import os
import sqlite3
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import hashlib
import zipfile
import tempfile


class MigrationValidator:
    """迁移验证器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.db_path = project_root / "data" / "aidcis3_data.db"
    
    def validate_database_schema(self, expected_version: str) -> Dict[str, Any]:
        """验证数据库模式"""
        result = {
            "valid": False,
            "version": None,
            "missing_tables": [],
            "missing_columns": {},
            "errors": []
        }
        
        try:
            if not self.db_path.exists():
                result["errors"].append("数据库文件不存在")
                return result
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取当前版本
            try:
                cursor.execute("SELECT version FROM migration_history ORDER BY applied_at DESC LIMIT 1")
                current_version = cursor.fetchone()
                result["version"] = current_version[0] if current_version else None
            except sqlite3.OperationalError:
                result["version"] = "unknown"
            
            # 根据期望版本验证表结构
            expected_tables = self._get_expected_tables(expected_version)
            
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            for table_name in expected_tables:
                if table_name not in existing_tables:
                    result["missing_tables"].append(table_name)
                else:
                    # 检查列
                    expected_columns = self._get_expected_columns(expected_version, table_name)
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    existing_columns = {row[1] for row in cursor.fetchall()}
                    
                    missing_columns = set(expected_columns) - existing_columns
                    if missing_columns:
                        result["missing_columns"][table_name] = list(missing_columns)
            
            # 验证通过条件
            result["valid"] = (
                len(result["missing_tables"]) == 0 and
                len(result["missing_columns"]) == 0 and
                result["version"] == expected_version
            )
            
            conn.close()
            
        except Exception as e:
            result["errors"].append(str(e))
        
        return result
    
    def _get_expected_tables(self, version: str) -> List[str]:
        """获取期望的表列表"""
        base_tables = ["workpieces", "holes", "measurements", "endoscope_images"]
        
        if version >= "1.1.0":
            base_tables.extend(["ui_configurations", "view_states", "migration_history"])
        
        if version >= "1.2.0":
            base_tables.extend(["graphics_configurations", "sector_management"])
        
        if version >= "2.0.0":
            base_tables.extend([
                "service_registry", 
                "data_processing_chains", 
                "unified_id_mappings"
            ])
        
        return base_tables
    
    def _get_expected_columns(self, version: str, table_name: str) -> List[str]:
        """获取期望的列列表"""
        column_definitions = {
            "workpieces": ["id", "name", "dxf_file_path", "status", "created_at"],
            "holes": ["id", "workpiece_id", "hole_id", "x", "y", "diameter"],
            "measurements": ["id", "hole_id", "measurement_type", "value"],
            "endoscope_images": ["id", "hole_id", "image_path", "depth"]
        }
        
        # 版本特定的列
        if version >= "1.1.0":
            if table_name == "workpieces":
                column_definitions["workpieces"].extend(["view_model_state", "ui_metadata"])
        
        if version >= "1.2.0":
            if table_name == "holes":
                column_definitions["holes"].extend(["graphics_state", "render_options", "sector_id"])
        
        if version >= "2.0.0":
            if table_name == "workpieces":
                column_definitions["workpieces"].extend([
                    "mvvm_version", "data_service_config", 
                    "processing_chain_id", "unified_id"
                ])
        
        return column_definitions.get(table_name, [])


class BackupManager:
    """备份管理器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backup_root = project_root / "backups"
        self.backup_root.mkdir(exist_ok=True)
    
    def create_full_backup(self, version: str) -> Path:
        """创建完整项目备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"full_backup_v{version}_{timestamp}"
        backup_path = self.backup_root / backup_name
        
        # 创建ZIP备份
        zip_path = backup_path.with_suffix('.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 备份重要目录
            important_dirs = ["src", "config", "data", "tests"]
            
            for dir_name in important_dirs:
                dir_path = self.project_root / dir_name
                if dir_path.exists():
                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file():
                            arcname = file_path.relative_to(self.project_root)
                            zipf.write(file_path, arcname)
            
            # 备份重要文件
            important_files = [
                "pyproject.toml", "pytest.ini", "README.md", 
                "requirements.txt", "LICENSE"
            ]
            
            for file_name in important_files:
                file_path = self.project_root / file_name
                if file_path.exists():
                    zipf.write(file_path, file_name)
        
        return zip_path
    
    def restore_backup(self, backup_path: Path) -> bool:
        """恢复备份"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(self.project_root)
            return True
        except Exception:
            return False
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出可用备份"""
        backups = []
        
        for backup_file in self.backup_root.glob("*.zip"):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.stem,
                "path": backup_file,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime)
            })
        
        return sorted(backups, key=lambda x: x["created"], reverse=True)


class ConfigurationMerger:
    """配置文件合并器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.config_dir = project_root / "config"
    
    def merge_user_settings(self, old_config: Dict[str, Any], 
                           new_config: Dict[str, Any]) -> Dict[str, Any]:
        """合并用户设置"""
        merged = new_config.copy()
        
        # 保留用户自定义设置
        user_keys = [
            "window_geometry", "user_preferences", "theme_settings",
            "custom_shortcuts", "workspace_layout"
        ]
        
        for key in user_keys:
            if key in old_config:
                merged[key] = old_config[key]
        
        return merged
    
    def update_config_version(self, config_file: Path, version: str):
        """更新配置文件版本"""
        if not config_file.exists():
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            config["version"] = version
            config["updated_at"] = datetime.now().isoformat()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
        except Exception:
            pass  # 忽略配置文件错误


class DependencyChecker:
    """依赖检查器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def check_python_version(self) -> Dict[str, Any]:
        """检查Python版本"""
        import sys
        
        current = sys.version_info
        required = (3, 8)
        
        return {
            "current": f"{current.major}.{current.minor}.{current.micro}",
            "required": f"{required[0]}.{required[1]}+",
            "compatible": current >= required
        }
    
    def check_package_dependencies(self, version: str) -> Dict[str, Any]:
        """检查包依赖"""
        result = {
            "missing": [],
            "outdated": [],
            "all_satisfied": True
        }
        
        # 版本特定的依赖
        dependencies = self._get_version_dependencies(version)
        
        for package, min_version in dependencies.items():
            try:
                __import__(package)
                # 这里可以添加版本检查逻辑
            except ImportError:
                result["missing"].append(package)
                result["all_satisfied"] = False
        
        return result
    
    def _get_version_dependencies(self, version: str) -> Dict[str, str]:
        """获取版本特定依赖"""
        base_deps = {
            "PySide6": "6.9.1",
            "numpy": "1.24.0",
            "matplotlib": "3.7.0"
        }
        
        if version >= "1.2.0":
            base_deps.update({
                "pyqtgraph": "0.13.0",
                "scipy": "1.10.0"
            })
        
        if version >= "2.0.0":
            base_deps.update({
                "SQLAlchemy": "2.0.0",
                "pydantic": "2.0.0"
            })
        
        return base_deps


class MigrationReporter:
    """迁移报告生成器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports_dir = project_root / "reports"
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_migration_report(self, migration_data: Dict[str, Any]) -> Path:
        """生成迁移报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_name = f"migration_report_{timestamp}.json"
        report_path = self.reports_dir / report_name
        
        report = {
            "migration_info": migration_data,
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "system_info": self._get_system_info()
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 也生成HTML报告
        html_report = self._generate_html_report(report)
        html_path = report_path.with_suffix('.html')
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        return report_path
    
    def _get_system_info(self) -> Dict[str, str]:
        """获取系统信息"""
        import platform
        import sys
        
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": platform.architecture()[0]
        }
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """生成HTML报告"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AIDCIS3-LFS 迁移报告</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; }}
        .success {{ color: green; }}
        .error {{ color: red; }}
        .warning {{ color: orange; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AIDCIS3-LFS 迁移报告</h1>
        <p>生成时间: {report_data['timestamp']}</p>
        <p>项目路径: {report_data['project_root']}</p>
    </div>
    
    <div class="section">
        <h2>迁移信息</h2>
        <pre>{json.dumps(report_data['migration_info'], indent=2, ensure_ascii=False)}</pre>
    </div>
    
    <div class="section">
        <h2>系统信息</h2>
        <pre>{json.dumps(report_data['system_info'], indent=2, ensure_ascii=False)}</pre>
    </div>
</body>
</html>
        """
        return html


class PerformanceBenchmark:
    """性能基准测试"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def benchmark_database_operations(self) -> Dict[str, float]:
        """基准测试数据库操作"""
        db_path = self.project_root / "data" / "aidcis3_data.db"
        
        if not db_path.exists():
            return {"error": "Database not found"}
        
        results = {}
        
        # 测试连接时间
        start_time = time.time()
        conn = sqlite3.connect(db_path)
        results["connection_time"] = time.time() - start_time
        
        # 测试查询时间
        cursor = conn.cursor()
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM workpieces")
        cursor.fetchone()
        results["simple_query_time"] = time.time() - start_time
        
        # 测试复杂查询时间
        start_time = time.time()
        cursor.execute("""
            SELECT w.name, COUNT(h.id) 
            FROM workpieces w 
            LEFT JOIN holes h ON w.id = h.workpiece_id 
            GROUP BY w.id
        """)
        cursor.fetchall()
        results["complex_query_time"] = time.time() - start_time
        
        conn.close()
        
        return results
    
    def benchmark_file_operations(self) -> Dict[str, float]:
        """基准测试文件操作"""
        results = {}
        
        # 测试文件读取
        test_file = self.project_root / "pyproject.toml"
        if test_file.exists():
            start_time = time.time()
            test_file.read_text()
            results["file_read_time"] = time.time() - start_time
        
        # 测试目录遍历
        start_time = time.time()
        list(self.project_root.rglob("*.py"))
        results["directory_scan_time"] = time.time() - start_time
        
        return results


def create_migration_checklist(version: str) -> List[Dict[str, Any]]:
    """创建迁移检查清单"""
    base_checklist = [
        {
            "task": "备份当前数据",
            "description": "创建数据库和配置文件的完整备份",
            "required": True,
            "completed": False
        },
        {
            "task": "检查依赖",
            "description": "验证所有必需的Python包和版本",
            "required": True,
            "completed": False
        },
        {
            "task": "停止应用程序",
            "description": "确保应用程序完全关闭",
            "required": True,
            "completed": False
        }
    ]
    
    # 版本特定任务
    if version >= "2.0.0":
        base_checklist.extend([
            {
                "task": "验证MVVM架构",
                "description": "确认新的MVVM架构组件正常工作",
                "required": True,
                "completed": False
            },
            {
                "task": "测试服务注册",
                "description": "验证服务注册和依赖注入功能",
                "required": True,
                "completed": False
            }
        ])
    
    return base_checklist


if __name__ == "__main__":
    # 示例用法
    project_root = Path(__file__).parent.parent
    
    # 创建验证器
    validator = MigrationValidator(project_root)
    result = validator.validate_database_schema("2.0.0")
    print(f"验证结果: {result}")
    
    # 创建备份管理器
    backup_manager = BackupManager(project_root)
    backups = backup_manager.list_backups()
    print(f"可用备份: {len(backups)} 个")
    
    # 性能基准测试
    benchmark = PerformanceBenchmark(project_root)
    db_perf = benchmark.benchmark_database_operations()
    print(f"数据库性能: {db_perf}")