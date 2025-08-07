#!/usr/bin/env python3
"""
修复DXF路径解析器问题的脚本
当前resolve_dxf_path方法有一个问题：它没有正确解析相对于项目根目录的路径
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def fix_resolve_dxf_path():
    """修复resolve_dxf_path方法"""
    print("=" * 60)
    print("修复DXF路径解析器")
    print("=" * 60)
    
    file_path = project_root / "src/core/data_path_manager.py"
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到resolve_dxf_path方法
    old_method = '''    def resolve_dxf_path(self, dxf_path: str) -> str:
        """
        解析DXF文件路径
        
        Args:
            dxf_path: DXF文件路径（可能是绝对路径或相对路径）
            
        Returns:
            绝对路径
        """
        if not dxf_path:
            return ""
            
        # 如果是绝对路径且存在，直接返回
        if os.path.isabs(dxf_path) and os.path.exists(dxf_path):
            return dxf_path
            
        # 尝试作为相对于data_root的路径
        abs_path = self.data_root / dxf_path
        if abs_path.exists():
            return str(abs_path)
            
        # 如果都不存在，返回原路径
        return dxf_path'''
    
    new_method = '''    def resolve_dxf_path(self, dxf_path: str) -> str:
        """
        解析DXF文件路径
        
        Args:
            dxf_path: DXF文件路径（可能是绝对路径或相对路径）
            
        Returns:
            绝对路径
        """
        if not dxf_path:
            return ""
            
        # 如果是绝对路径且存在，直接返回
        if os.path.isabs(dxf_path) and os.path.exists(dxf_path):
            return dxf_path
            
        # 尝试作为相对于项目根目录的路径
        project_root = self.data_root.parent  # data_root是项目根目录下的Data，所以parent就是项目根目录
        abs_path_from_root = project_root / dxf_path
        if abs_path_from_root.exists():
            return str(abs_path_from_root)
            
        # 尝试作为相对于data_root的路径
        abs_path_from_data = self.data_root / dxf_path
        if abs_path_from_data.exists():
            return str(abs_path_from_data)
            
        # 如果都不存在，返回相对于项目根目录的绝对路径（便于调试）
        return str(abs_path_from_root)'''
    
    if old_method not in content:
        print("❌ 未找到要替换的方法")
        return False
    
    # 替换方法
    new_content = content.replace(old_method, new_method)
    
    # 写回文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 已修复resolve_dxf_path方法")
    print("主要改进:")
    print("  1. 首先尝试相对于项目根目录的路径解析")
    print("  2. 然后尝试相对于data_root的路径解析")
    print("  3. 即使文件不存在也返回完整的绝对路径便于调试")
    
    return True

def test_path_resolution():
    """测试路径解析功能"""
    print("\n" + "=" * 60)
    print("测试路径解析功能")
    print("=" * 60)
    
    try:
        from src.core.data_path_manager import DataPathManager
        path_manager = DataPathManager()
        
        # 测试CAP1000的DXF路径
        test_path = "assets/dxf/DXF Graph/东重管板.dxf"
        resolved = path_manager.resolve_dxf_path(test_path)
        
        print(f"输入路径: {test_path}")
        print(f"解析结果: {resolved}")
        print(f"文件存在: {'✅ 是' if Path(resolved).exists() else '❌ 否'}")
        
        if Path(resolved).exists():
            size = Path(resolved).stat().st_size
            print(f"文件大小: {size} bytes ({size/1024:.2f} KB)")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def update_cap1000_product():
    """更新CAP1000产品记录中的DXF路径（如果需要）"""
    print("\n" + "=" * 60)
    print("检查CAP1000产品记录")
    print("=" * 60)
    
    try:
        from src.shared.models.product_model import ProductModelManager
        product_manager = ProductModelManager()
        
        cap1000_product = product_manager.get_product_by_name("CAP1000")
        if not cap1000_product:
            print("❌ 未找到CAP1000产品")
            return False
        
        current_path = cap1000_product.dxf_file_path
        print(f"当前DXF路径: {current_path}")
        
        # 检查当前路径是否能正确解析
        from src.core.data_path_manager import DataPathManager
        path_manager = DataPathManager()
        resolved = path_manager.resolve_dxf_path(current_path)
        
        if Path(resolved).exists():
            print("✅ 当前路径可以正确解析，无需更新")
            return True
        else:
            print("❌ 当前路径无法解析，需要更新")
            # 这里可以添加自动更新逻辑
            return False
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

if __name__ == "__main__":
    print("开始修复DXF路径解析器...")
    
    # 1. 修复路径解析方法
    if not fix_resolve_dxf_path():
        print("❌ 修复失败")
        sys.exit(1)
    
    # 2. 测试修复后的功能
    if not test_path_resolution():
        print("❌ 测试失败")
        sys.exit(1)
    
    # 3. 检查产品记录
    update_cap1000_product()
    
    print("\n🎉 DXF路径解析器修复完成！")