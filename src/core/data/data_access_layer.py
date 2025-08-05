"""
数据访问层
提供统一的数据访问接口
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager

from .config_manager import get_config


class DataAccessLayer:
    """数据访问层"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        
        # 获取数据库路径
        if db_path is None:
            db_path = get_config('database.url', 'sqlite:///Data/Databases/detection_system.db')
            # 移除 sqlite:/// 前缀
            if db_path.startswith('sqlite:///'):
                db_path = db_path[10:]
        
        self.db_path = Path(db_path)
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """确保数据库文件存在"""
        try:
            # 创建数据库目录
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 如果数据库不存在，创建基本表结构
            if not self.db_path.exists():
                self._create_tables()
                self.logger.info(f"数据库创建成功: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
    
    def _create_tables(self):
        """创建基本表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建工件表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workpieces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建孔位表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS holes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workpiece_id INTEGER,
                    hole_id TEXT NOT NULL,
                    x REAL NOT NULL,
                    y REAL NOT NULL,
                    diameter REAL,
                    status TEXT DEFAULT 'unknown',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workpiece_id) REFERENCES workpieces (id)
                )
            ''')
            
            # 创建测量表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hole_id INTEGER,
                    measurement_type TEXT NOT NULL,
                    value REAL,
                    unit TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hole_id) REFERENCES holes (id)
                )
            ''')
            
            # 创建检测批次表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inspection_batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_name TEXT NOT NULL,
                    workpiece_id INTEGER,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    status TEXT DEFAULT 'in_progress',
                    total_holes INTEGER DEFAULT 0,
                    completed_holes INTEGER DEFAULT 0,
                    FOREIGN KEY (workpiece_id) REFERENCES workpieces (id)
                )
            ''')
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """执行查询并返回结果"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # 将结果转换为字典列表
                columns = [description[0] for description in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results
        except Exception as e:
            self.logger.error(f"查询执行失败: {e}")
            return []
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """执行非查询语句（INSERT, UPDATE, DELETE）"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            self.logger.error(f"非查询语句执行失败: {e}")
            return 0
    
    def execute_scalar(self, query: str, params: Optional[tuple] = None) -> Any:
        """执行查询并返回单个值"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            self.logger.error(f"标量查询执行失败: {e}")
            return None
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表结构信息"""
        query = f"PRAGMA table_info({table_name})"
        return self.execute_query(query)
    
    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute_scalar(query, (table_name,))
        return result is not None
    
    def get_all_tables(self) -> List[str]:
        """获取所有表名"""
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        results = self.execute_query(query)
        return [row['name'] for row in results]
    
    def backup_database(self, backup_path: str) -> bool:
        """备份数据库"""
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self.get_connection() as source_conn:
                with sqlite3.connect(str(backup_path)) as backup_conn:
                    source_conn.backup(backup_conn)
            
            self.logger.info(f"数据库备份成功: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"数据库备份失败: {e}")
            return False
    
    def get_database_size(self) -> int:
        """获取数据库文件大小（字节）"""
        try:
            return self.db_path.stat().st_size
        except Exception:
            return 0
    
    def vacuum_database(self) -> bool:
        """压缩数据库"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
            self.logger.info("数据库压缩完成")
            return True
        except Exception as e:
            self.logger.error(f"数据库压缩失败: {e}")
            return False
    
    def get_repository(self, repository_name: str):
        """获取Repository实例"""
        try:
            # 动态导入和创建Repository实例
            if repository_name == "WorkpieceRepository":
                from .repositories import WorkpieceRepository
                return WorkpieceRepository()
            elif repository_name == "HoleRepository":
                from .repositories import HoleRepository
                return HoleRepository()
            elif repository_name == "MeasurementRepository":
                from .repositories import MeasurementRepository
                return MeasurementRepository()
            else:
                self.logger.warning(f"未知的Repository类型: {repository_name}")
                return None
        except Exception as e:
            self.logger.error(f"创建Repository失败: {repository_name}, 错误: {e}")
            return None


# 创建全局数据访问层实例
data_access_layer = DataAccessLayer()
