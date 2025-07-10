#!/usr/bin/env python3
"""
修复数据库模式
Fix Database Schema - Add missing columns
"""

import os
import sys
import sqlite3
from pathlib import Path

def fix_database_schema():
    """修复数据库模式，添加缺失的字段"""
    
    print("🔧 修复数据库模式")
    print("=" * 50)
    
    # 数据库文件路径
    db_path = "detection_system.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"📁 连接数据库: {db_path}")
        
        # 检查workpieces表的当前结构
        cursor.execute("PRAGMA table_info(workpieces)")
        columns = cursor.fetchall()
        
        print("📋 当前workpieces表结构:")
        existing_columns = []
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            existing_columns.append(col_name)
            print(f"   {col_name}: {col_type}")
        
        # 需要添加的字段
        new_columns = [
            ("dxf_file_path", "VARCHAR(255)"),
            ("project_data_path", "VARCHAR(255)"),
            ("hole_count", "INTEGER DEFAULT 0"),
            ("completed_holes", "INTEGER DEFAULT 0"),
            ("status", "VARCHAR(20) DEFAULT 'active'"),
            ("description", "TEXT"),
            ("version", "VARCHAR(10) DEFAULT '1.0'")
        ]
        
        print("\n🔧 添加缺失的字段:")
        
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                try:
                    sql = f"ALTER TABLE workpieces ADD COLUMN {col_name} {col_type}"
                    cursor.execute(sql)
                    print(f"   ✅ 添加字段: {col_name} {col_type}")
                except sqlite3.Error as e:
                    print(f"   ❌ 添加字段失败 {col_name}: {e}")
            else:
                print(f"   ⏭️ 字段已存在: {col_name}")
        
        # 提交更改
        conn.commit()
        
        # 验证修复结果
        print("\n📋 修复后的workpieces表结构:")
        cursor.execute("PRAGMA table_info(workpieces)")
        columns = cursor.fetchall()
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            print(f"   {col_name}: {col_type}")
        
        # 更新现有记录的默认值
        print("\n🔄 更新现有记录的默认值:")
        
        # 设置默认值
        update_queries = [
            "UPDATE workpieces SET hole_count = 0 WHERE hole_count IS NULL",
            "UPDATE workpieces SET completed_holes = 0 WHERE completed_holes IS NULL",
            "UPDATE workpieces SET status = 'active' WHERE status IS NULL",
            "UPDATE workpieces SET version = '1.0' WHERE version IS NULL"
        ]
        
        for query in update_queries:
            try:
                cursor.execute(query)
                affected_rows = cursor.rowcount
                print(f"   ✅ 更新记录: {affected_rows} 行")
            except sqlite3.Error as e:
                print(f"   ❌ 更新失败: {e}")
        
        # 提交更改
        conn.commit()
        
        print("\n🎉 数据库模式修复完成！")
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 数据库操作失败: {e}")
        return False
    
    finally:
        if conn:
            conn.close()

def test_database_access():
    """测试数据库访问"""
    
    print("\n" + "=" * 50)
    print("🧪 测试数据库访问")
    print("=" * 50)
    
    try:
        # 使用SQLAlchemy测试
        from modules.models import db_manager
        
        # 尝试创建示例数据
        print("📝 尝试创建示例数据...")
        db_manager.create_sample_data()
        print("✅ 示例数据创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库访问测试失败: {e}")
        return False

def main():
    """主函数"""
    try:
        # 修复数据库模式
        schema_fixed = fix_database_schema()
        
        if schema_fixed:
            # 测试数据库访问
            access_ok = test_database_access()
            
            if access_ok:
                print("\n🎉 数据库问题已完全修复！")
                print("✅ 缺失字段已添加")
                print("✅ 数据库访问正常")
                print("✅ 示例数据创建成功")
            else:
                print("\n⚠️ 数据库模式已修复，但访问仍有问题")
        else:
            print("\n❌ 数据库模式修复失败")
        
        return schema_fixed and access_ok if schema_fixed else False
        
    except Exception as e:
        print(f"\n❌ 修复过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
