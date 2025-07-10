#!/usr/bin/env python3
"""
数据库迁移脚本
Database Migration Script for Priority 3 Phase 2
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

from modules.models import Base, Workpiece, Hole, DatabaseManager


class DatabaseMigration:
    """数据库迁移类"""
    
    def __init__(self, database_url: str = "sqlite:///detection_system.db"):
        """
        初始化数据库迁移
        
        Args:
            database_url: 数据库连接URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.logger = logging.getLogger(__name__)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
    
    def check_current_schema(self) -> dict:
        """
        检查当前数据库模式
        
        Returns:
            Dict[str, List[str]]: 表名和列名的映射
        """
        inspector = inspect(self.engine)
        schema = {}
        
        for table_name in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            schema[table_name] = columns
            
        return schema
    
    def backup_database(self) -> str:
        """
        备份数据库
        
        Returns:
            str: 备份文件路径
        """
        if "sqlite" in self.database_url:
            # SQLite数据库备份
            db_file = self.database_url.replace("sqlite:///", "")
            if os.path.exists(db_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{db_file}.backup_{timestamp}"
                
                import shutil
                shutil.copy2(db_file, backup_file)
                self.logger.info(f"数据库备份完成: {backup_file}")
                return backup_file
        
        return ""
    
    def migrate_workpieces_table(self) -> bool:
        """
        迁移workpieces表
        
        Returns:
            bool: 迁移是否成功
        """
        try:
            # 检查当前表结构
            inspector = inspect(self.engine)
            
            if 'workpieces' not in inspector.get_table_names():
                self.logger.info("workpieces表不存在，将创建新表")
                return True
            
            # 获取当前列
            current_columns = [col['name'] for col in inspector.get_columns('workpieces')]
            
            # 需要添加的新列
            new_columns = [
                ("dxf_file_path", "VARCHAR(255)"),
                ("project_data_path", "VARCHAR(255)"),
                ("hole_count", "INTEGER DEFAULT 0"),
                ("completed_holes", "INTEGER DEFAULT 0"),
                ("status", "VARCHAR(20) DEFAULT 'active'"),
                ("description", "TEXT"),
                ("version", "VARCHAR(10) DEFAULT '1.0'")
            ]
            
            # 添加缺失的列
            with self.engine.connect() as conn:
                for column_name, column_def in new_columns:
                    if column_name not in current_columns:
                        sql = f"ALTER TABLE workpieces ADD COLUMN {column_name} {column_def}"
                        conn.execute(text(sql))
                        conn.commit()
                        self.logger.info(f"添加列: workpieces.{column_name}")
            
            self.logger.info("workpieces表迁移完成")
            return True
            
        except Exception as e:
            self.logger.error(f"workpieces表迁移失败: {e}")
            return False
    
    def migrate_holes_table(self) -> bool:
        """
        迁移holes表
        
        Returns:
            bool: 迁移是否成功
        """
        try:
            # 检查当前表结构
            inspector = inspect(self.engine)
            
            if 'holes' not in inspector.get_table_names():
                self.logger.info("holes表不存在，将创建新表")
                return True
            
            # 获取当前列
            current_columns = [col['name'] for col in inspector.get_columns('holes')]
            
            # 需要添加的新列
            new_columns = [
                ("depth", "FLOAT"),
                ("file_system_path", "VARCHAR(255)"),
                ("last_measurement_at", "DATETIME"),
                ("measurement_count", "INTEGER DEFAULT 0"),
                ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
            ]
            
            # 添加缺失的列
            with self.engine.connect() as conn:
                for column_name, column_def in new_columns:
                    if column_name not in current_columns:
                        sql = f"ALTER TABLE holes ADD COLUMN {column_name} {column_def}"
                        conn.execute(text(sql))
                        conn.commit()
                        self.logger.info(f"添加列: holes.{column_name}")
                
                # 更新status列的默认值
                if 'status' in current_columns:
                    # SQLite不支持直接修改列默认值，需要更新现有数据
                    conn.execute(text("UPDATE holes SET status = 'pending' WHERE status = 'not_detected'"))
                    conn.commit()
                    self.logger.info("更新holes.status默认值")
            
            self.logger.info("holes表迁移完成")
            return True
            
        except Exception as e:
            self.logger.error(f"holes表迁移失败: {e}")
            return False
    
    def migrate_data_consistency(self) -> bool:
        """
        迁移数据一致性
        
        Returns:
            bool: 迁移是否成功
        """
        try:
            session = self.SessionLocal()
            try:
                # 更新workpieces表的统计信息
                workpieces = session.query(Workpiece).all()
                
                for workpiece in workpieces:
                    # 计算孔位统计
                    total_holes = session.query(Hole).filter_by(workpiece_id=workpiece.id).count()
                    completed_holes = session.query(Hole).filter_by(
                        workpiece_id=workpiece.id, status='completed'
                    ).count()
                    
                    # 更新统计信息
                    workpiece.hole_count = total_holes
                    workpiece.completed_holes = completed_holes
                    
                    # 设置默认值
                    if not workpiece.status:
                        workpiece.status = 'active'
                    if not workpiece.version:
                        workpiece.version = '1.0'
                
                session.commit()
                self.logger.info("数据一致性迁移完成")
                return True
                
            finally:
                session.close()
                
        except Exception as e:
            self.logger.error(f"数据一致性迁移失败: {e}")
            return False
    
    def run_migration(self) -> bool:
        """
        运行完整迁移
        
        Returns:
            bool: 迁移是否成功
        """
        try:
            self.logger.info("开始数据库迁移...")
            
            # 1. 备份数据库
            backup_file = self.backup_database()
            
            # 2. 检查当前模式
            current_schema = self.check_current_schema()
            self.logger.info(f"当前数据库模式: {current_schema}")
            
            # 3. 创建所有表（如果不存在）
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("确保所有表存在")
            
            # 4. 迁移workpieces表
            if not self.migrate_workpieces_table():
                return False
            
            # 5. 迁移holes表
            if not self.migrate_holes_table():
                return False
            
            # 6. 迁移数据一致性
            if not self.migrate_data_consistency():
                return False
            
            # 7. 验证迁移结果
            new_schema = self.check_current_schema()
            self.logger.info(f"迁移后数据库模式: {new_schema}")
            
            self.logger.info("数据库迁移完成！")
            return True
            
        except Exception as e:
            self.logger.error(f"数据库迁移失败: {e}")
            return False
    
    def rollback_migration(self, backup_file: str) -> bool:
        """
        回滚迁移
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            bool: 回滚是否成功
        """
        try:
            if backup_file and os.path.exists(backup_file):
                db_file = self.database_url.replace("sqlite:///", "")
                
                import shutil
                shutil.copy2(backup_file, db_file)
                self.logger.info(f"数据库回滚完成: {backup_file} -> {db_file}")
                return True
            else:
                self.logger.error("备份文件不存在，无法回滚")
                return False
                
        except Exception as e:
            self.logger.error(f"数据库回滚失败: {e}")
            return False


def main():
    """主函数"""
    print("=" * 80)
    print("🔄 优先级3阶段2：数据库迁移")
    print("=" * 80)
    
    # 初始化迁移器
    migration = DatabaseMigration()
    
    try:
        # 运行迁移
        success = migration.run_migration()
        
        if success:
            print("\n✅ 数据库迁移成功完成！")
            print("\n📊 迁移内容:")
            print("   - workpieces表扩展字段")
            print("   - holes表扩展字段")
            print("   - 数据一致性更新")
            print("   - 统计信息计算")
        else:
            print("\n❌ 数据库迁移失败！")
            return False
            
    except Exception as e:
        print(f"\n💥 迁移过程中发生错误: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
