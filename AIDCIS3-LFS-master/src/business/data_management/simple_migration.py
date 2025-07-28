#!/usr/bin/env python3
"""
简化数据库迁移（无Qt依赖）
Simple Database Migration (without Qt dependencies)
"""

import os
import sqlite3
import logging
from datetime import datetime
from pathlib import Path


class SimpleDatabaseMigration:
    """简化数据库迁移类（无Qt依赖）"""
    
    def __init__(self, database_path: str = "detection_system.db"):
        """
        初始化简化数据库迁移
        
        Args:
            database_path: 数据库文件路径
        """
        self.database_path = database_path
        self.logger = logging.getLogger(__name__)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
    
    def check_current_schema(self) -> dict:
        """
        检查当前数据库模式
        
        Returns:
            dict: 表名和列名的映射
        """
        schema = {}
        
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                # 获取表的列信息
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                schema[table_name] = [col[1] for col in columns]  # col[1] 是列名
            
            conn.close()
            
        except Exception as e:
            self.logger.error(f"检查数据库模式失败: {e}")
        
        return schema
    
    def create_tables(self) -> bool:
        """
        创建基础表结构
        
        Returns:
            bool: 创建是否成功
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 创建workpieces表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workpieces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workpiece_id VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    material VARCHAR(50),
                    dxf_file_path VARCHAR(255),
                    project_data_path VARCHAR(255),
                    hole_count INTEGER DEFAULT 0,
                    completed_holes INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'active',
                    description TEXT,
                    version VARCHAR(10) DEFAULT '1.0',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建holes表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS holes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hole_id VARCHAR(50) NOT NULL,
                    workpiece_id INTEGER NOT NULL,
                    position_x FLOAT,
                    position_y FLOAT,
                    target_diameter FLOAT NOT NULL,
                    tolerance FLOAT NOT NULL,
                    depth FLOAT,
                    file_system_path VARCHAR(255),
                    status VARCHAR(20) DEFAULT 'pending',
                    last_measurement_at DATETIME,
                    measurement_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workpiece_id) REFERENCES workpieces (id)
                )
            ''')
            
            # 创建measurements表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hole_id INTEGER NOT NULL,
                    depth FLOAT NOT NULL,
                    diameter FLOAT NOT NULL,
                    operator VARCHAR(50),
                    is_qualified BOOLEAN,
                    deviation FLOAT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hole_id) REFERENCES holes (id)
                )
            ''')
            
            # 创建endoscope_images表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS endoscope_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hole_id INTEGER NOT NULL,
                    image_path VARCHAR(255) NOT NULL,
                    depth FLOAT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hole_id) REFERENCES holes (id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("数据库表创建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"创建数据库表失败: {e}")
            return False
    
    def add_missing_columns(self) -> bool:
        """
        添加缺失的列
        
        Returns:
            bool: 添加是否成功
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 检查当前表结构
            schema = self.check_current_schema()
            
            # workpieces表需要添加的列
            workpieces_new_columns = [
                ("dxf_file_path", "VARCHAR(255)"),
                ("project_data_path", "VARCHAR(255)"),
                ("hole_count", "INTEGER DEFAULT 0"),
                ("completed_holes", "INTEGER DEFAULT 0"),
                ("status", "VARCHAR(20) DEFAULT 'active'"),
                ("description", "TEXT"),
                ("version", "VARCHAR(10) DEFAULT '1.0'")
            ]
            
            if 'workpieces' in schema:
                workpieces_columns = schema['workpieces']
                for column_name, column_def in workpieces_new_columns:
                    if column_name not in workpieces_columns:
                        try:
                            cursor.execute(f"ALTER TABLE workpieces ADD COLUMN {column_name} {column_def}")
                            self.logger.info(f"添加列: workpieces.{column_name}")
                        except Exception as e:
                            self.logger.warning(f"添加列失败 workpieces.{column_name}: {e}")
            
            # holes表需要添加的列
            holes_new_columns = [
                ("depth", "FLOAT"),
                ("file_system_path", "VARCHAR(255)"),
                ("last_measurement_at", "DATETIME"),
                ("measurement_count", "INTEGER DEFAULT 0"),
                ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
            ]
            
            if 'holes' in schema:
                holes_columns = schema['holes']
                for column_name, column_def in holes_new_columns:
                    if column_name not in holes_columns:
                        try:
                            cursor.execute(f"ALTER TABLE holes ADD COLUMN {column_name} {column_def}")
                            self.logger.info(f"添加列: holes.{column_name}")
                        except Exception as e:
                            self.logger.warning(f"添加列失败 holes.{column_name}: {e}")
                
                # 更新holes表的status默认值
                if 'status' in holes_columns:
                    try:
                        cursor.execute("UPDATE holes SET status = 'pending' WHERE status = 'not_detected' OR status IS NULL")
                        self.logger.info("更新holes.status默认值")
                    except Exception as e:
                        self.logger.warning(f"更新status默认值失败: {e}")
            
            conn.commit()
            conn.close()
            
            self.logger.info("缺失列添加完成")
            return True
            
        except Exception as e:
            self.logger.error(f"添加缺失列失败: {e}")
            return False
    
    def run_migration(self) -> bool:
        """
        运行完整迁移
        
        Returns:
            bool: 迁移是否成功
        """
        try:
            self.logger.info("开始简化数据库迁移...")
            
            # 1. 创建基础表结构
            if not self.create_tables():
                return False
            
            # 2. 添加缺失的列
            if not self.add_missing_columns():
                return False
            
            # 3. 验证迁移结果
            schema = self.check_current_schema()
            self.logger.info(f"迁移后数据库模式: {schema}")
            
            # 验证必需的表存在
            required_tables = ['workpieces', 'holes', 'measurements', 'endoscope_images']
            for table in required_tables:
                if table not in schema:
                    self.logger.error(f"缺少必需的表: {table}")
                    return False
            
            # 验证workpieces表的关键字段
            workpieces_required_fields = [
                'id', 'workpiece_id', 'name', 'type', 'dxf_file_path',
                'project_data_path', 'hole_count', 'status'
            ]
            workpieces_columns = schema.get('workpieces', [])
            for field in workpieces_required_fields:
                if field not in workpieces_columns:
                    self.logger.error(f"workpieces表缺少字段: {field}")
                    return False
            
            # 验证holes表的关键字段
            holes_required_fields = [
                'id', 'hole_id', 'workpiece_id', 'target_diameter',
                'tolerance', 'depth', 'file_system_path', 'status'
            ]
            holes_columns = schema.get('holes', [])
            for field in holes_required_fields:
                if field not in holes_columns:
                    self.logger.error(f"holes表缺少字段: {field}")
                    return False
            
            self.logger.info("简化数据库迁移完成！")
            return True
            
        except Exception as e:
            self.logger.error(f"简化数据库迁移失败: {e}")
            return False
    
    def test_basic_operations(self) -> bool:
        """
        测试基础数据库操作
        
        Returns:
            bool: 测试是否成功
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # 测试插入workpiece
            cursor.execute('''
                INSERT INTO workpieces (workpiece_id, name, type, hole_count, status)
                VALUES (?, ?, ?, ?, ?)
            ''', ('test_workpiece_001', '测试工件', 'DXF导入', 5, 'active'))
            
            workpiece_id = cursor.lastrowid
            
            # 测试插入hole
            cursor.execute('''
                INSERT INTO holes (hole_id, workpiece_id, position_x, position_y, 
                                 target_diameter, tolerance, depth, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('C001R001', workpiece_id, 10.0, 20.0, 8.865, 0.1, 900.0, 'pending'))
            
            hole_id = cursor.lastrowid
            
            # 测试插入measurement
            cursor.execute('''
                INSERT INTO measurements (hole_id, depth, diameter, operator, is_qualified)
                VALUES (?, ?, ?, ?, ?)
            ''', (hole_id, 0.0, 8.865, '测试操作员', True))
            
            # 测试查询
            cursor.execute('''
                SELECT w.name, h.hole_id, m.diameter
                FROM workpieces w
                JOIN holes h ON w.id = h.workpiece_id
                JOIN measurements m ON h.id = m.hole_id
                WHERE w.workpiece_id = ?
            ''', ('test_workpiece_001',))
            
            result = cursor.fetchone()
            if not result:
                raise Exception("查询测试失败")
            
            conn.commit()
            conn.close()
            
            self.logger.info("基础数据库操作测试成功")
            return True
            
        except Exception as e:
            self.logger.error(f"基础数据库操作测试失败: {e}")
            return False


def main():
    """主函数"""
    print("=" * 80)
    print("🔄 简化数据库迁移测试")
    print("=" * 80)
    
    # 创建临时数据库进行测试
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="simple_migration_test_")
    test_db = os.path.join(temp_dir, "test.db")
    
    try:
        migration = SimpleDatabaseMigration(test_db)
        
        # 运行迁移
        print("\n执行数据库迁移...")
        success = migration.run_migration()
        
        if success:
            print("✅ 数据库迁移成功")
            
            # 测试基础操作
            print("\n测试基础数据库操作...")
            test_success = migration.test_basic_operations()
            
            if test_success:
                print("✅ 基础操作测试成功")
                
                # 显示最终表结构
                schema = migration.check_current_schema()
                print(f"\n📊 最终表结构:")
                for table, columns in schema.items():
                    print(f"   {table}: {len(columns)} 列")
                    for col in columns:
                        print(f"      - {col}")
                
                print(f"\n🎉 简化数据库迁移测试完全成功！")
                return True
            else:
                print("❌ 基础操作测试失败")
                return False
        else:
            print("❌ 数据库迁移失败")
            return False
            
    except Exception as e:
        print(f"💥 测试过程中发生错误: {e}")
        return False
    
    finally:
        # 清理临时文件
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
