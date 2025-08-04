#!/usr/bin/env python3
"""
更新CAP1000产品的DXF文件路径到新的存储位置
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.models.product_model import ProductModelManager

def update_cap1000_dxf_path():
    """更新CAP1000的DXF文件路径"""
    
    manager = ProductModelManager()
    
    # 查找CAP1000产品
    product = manager.get_product_by_name("CAP1000")
    
    if product:
        print(f"找到产品: {product.model_name}")
        print(f"当前DXF路径: {product.dxf_file_path}")
        
        # 更新路径到正确的Data目录
        new_path = "Data/Products/CAP1000/dxf/CAP1000.dxf"
        
        try:
            manager.update_product(product.id, dxf_file_path=new_path)
            print(f"✅ DXF路径已更新为: {new_path}")
            
            # 验证更新
            updated_product = manager.get_product_by_id(product.id)
            print(f"验证新路径: {updated_product.dxf_file_path}")
            
        except Exception as e:
            print(f"❌ 更新失败: {e}")
    else:
        print("❌ 未找到CAP1000产品")

if __name__ == "__main__":
    update_cap1000_dxf_path()