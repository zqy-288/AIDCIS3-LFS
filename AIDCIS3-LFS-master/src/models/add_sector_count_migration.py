"""
数据库迁移脚本：添加sector_count字段到product_models表
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from models.product_model import Base, ProductModel


def add_sector_count_column():
    """添加sector_count列到product_models表"""
    
    # 获取数据库路径
    db_path = Path(__file__).parent.parent.parent / "detection_system.db"
    engine = create_engine(f'sqlite:///{db_path}')
    
    try:
        # 检查表是否存在
        with engine.connect() as conn:
            # 检查列是否已存在
            result = conn.execute(text("PRAGMA table_info(product_models)"))
            columns = [row[1] for row in result]
            
            if 'sector_count' in columns:
                print("sector_count列已存在，无需迁移")
                return
            
            # 添加新列
            print("正在添加sector_count列...")
            conn.execute(text("""
                ALTER TABLE product_models 
                ADD COLUMN sector_count INTEGER DEFAULT 4 
                CHECK (sector_count >= 2 AND sector_count <= 12)
            """))
            conn.commit()
            
            print("✅ sector_count列添加成功")
            
            # 更新现有记录的默认值
            conn.execute(text("""
                UPDATE product_models 
                SET sector_count = 4 
                WHERE sector_count IS NULL
            """))
            conn.commit()
            
            print("✅ 现有记录已更新默认值")
            
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        raise


if __name__ == "__main__":
    add_sector_count_column()