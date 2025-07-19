"""
初始化数据库，创建所有表
"""

import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from models.product_model import Base, ProductModel


def init_database():
    """初始化数据库"""
    
    # 获取数据库路径
    db_path = Path(__file__).parent.parent.parent / "detection_system.db"
    print(f"数据库路径: {db_path}")
    
    # 创建数据库引擎
    engine = create_engine(f'sqlite:///{db_path}')
    
    try:
        # 创建所有表
        print("正在创建数据库表...")
        Base.metadata.create_all(engine)
        print("✅ 数据库表创建成功")
        
        # 列出创建的表
        print("\n已创建的表:")
        for table in Base.metadata.tables:
            print(f"  - {table}")
            
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise


if __name__ == "__main__":
    init_database()