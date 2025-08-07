#!/usr/bin/env python3
"""
CAP1000产品DXF文件关联诊断脚本
检查CAP1000产品记录中的dxf_file_path字段以及相关文件和路径解析功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def check_cap1000_dxf_association():
    """检查CAP1000产品的DXF文件关联"""
    print("=" * 80)
    print("CAP1000产品DXF文件关联诊断报告")
    print("=" * 80)
    print()
    
    try:
        # 1. 检查产品数据库中CAP1000的记录
        print("1. 检查产品数据库中CAP1000记录...")
        print("-" * 50)
        
        from src.shared.models.product_model import ProductModelManager
        product_manager = ProductModelManager()
        
        # 查找CAP1000产品
        cap1000_product = product_manager.get_product_by_name("CAP1000")
        
        if not cap1000_product:
            print("❌ 未找到CAP1000产品记录")
            print("   请检查产品数据库是否已正确初始化")
            return False
        
        print(f"✅ 找到CAP1000产品记录:")
        print(f"   ID: {cap1000_product.id}")
        print(f"   名称: {cap1000_product.model_name}")
        print(f"   代码: {cap1000_product.model_code}")
        print(f"   DXF文件路径: {cap1000_product.dxf_file_path}")
        print(f"   描述: {cap1000_product.description}")
        print(f"   是否启用: {cap1000_product.is_active}")
        print()
        
        # 2. 检查DXF文件路径是否存在
        print("2. 检查DXF文件路径...")
        print("-" * 50)
        
        dxf_path = cap1000_product.dxf_file_path
        if not dxf_path:
            print("❌ CAP1000产品记录中没有设置dxf_file_path")
            return False
        
        print(f"原始路径: {dxf_path}")
        
        # 检查绝对路径
        if os.path.isabs(dxf_path):
            abs_path = dxf_path
            print(f"绝对路径: {abs_path}")
        else:
            # 尝试相对于项目根目录的路径
            abs_path = project_root / dxf_path
            print(f"相对路径转换为绝对路径: {abs_path}")
        
        file_exists = Path(abs_path).exists()
        print(f"文件是否存在: {'✅ 是' if file_exists else '❌ 否'}")
        
        if file_exists:
            file_size = Path(abs_path).stat().st_size
            print(f"文件大小: {file_size} bytes ({file_size/1024:.2f} KB)")
            print(f"文件扩展名: {Path(abs_path).suffix}")
        print()
        
        # 3. 验证路径解析器resolve_dxf_path的工作状态
        print("3. 验证路径解析器resolve_dxf_path...")
        print("-" * 50)
        
        try:
            from src.core.data_path_manager import DataPathManager
            path_manager = DataPathManager()
            
            resolved_path = path_manager.resolve_dxf_path(dxf_path)
            print(f"路径解析器输入: {dxf_path}")  
            print(f"路径解析器输出: {resolved_path}")
            
            resolved_exists = Path(resolved_path).exists()
            print(f"解析后路径是否存在: {'✅ 是' if resolved_exists else '❌ 否'}")
            
            if resolved_path != str(abs_path):
                print(f"⚠️  解析后路径与直接计算的绝对路径不同")
                print(f"   直接计算: {abs_path}")
                print(f"   解析器结果: {resolved_path}")
        
        except Exception as e:
            print(f"❌ 路径解析器出错: {e}")
        
        print()
        
        # 4. 测试parse_dxf_file方法的执行情况
        print("4. 测试parse_dxf_file方法...")
        print("-" * 50)
        
        try:
            from src.shared.services.business_service import get_business_service
            business_service = get_business_service()
            
            # 使用解析后的路径测试DXF解析
            test_path = resolved_path if resolved_exists else abs_path
            print(f"测试解析路径: {test_path}")
            
            if not Path(test_path).exists():
                print("❌ 无法测试parse_dxf_file - 文件不存在")
            else:
                print("🔄 开始解析DXF文件...")
                
                hole_collection = business_service.parse_dxf_file(test_path)
                
                if hole_collection is None:
                    print("❌ parse_dxf_file返回None - 解析失败")
                else:
                    hole_count = len(hole_collection.holes) if hasattr(hole_collection, 'holes') else 0
                    print(f"✅ parse_dxf_file成功解析")
                    print(f"   检测到孔位数量: {hole_count}")
                    print(f"   孔位集合类型: {type(hole_collection)}")
                    
                    # 显示前几个孔位信息
                    if hasattr(hole_collection, 'holes') and hole_collection.holes:
                        print("   前3个孔位信息:")
                        hole_items = list(hole_collection.holes.items())[:3]
                        for i, (hole_id, hole) in enumerate(hole_items):
                            print(f"     孔位{i+1} ({hole_id}): 中心({hole.center_x:.2f}, {hole.center_y:.2f}), 半径: {hole.radius:.2f}")
        
        except Exception as e:
            print(f"❌ parse_dxf_file执行出错: {e}")
            import traceback
            print("详细错误信息:")
            traceback.print_exc()
        
        print()
        
        # 5. 检查DXF解析器是否可用
        print("5. 检查DXF解析器状态...")
        print("-" * 50)
        
        try:
            from src.shared.services.parsers.dxf_parser import DXFParser
            dxf_parser = DXFParser()
            print("✅ DXF解析器成功导入")
            print(f"   解析器类型: {type(dxf_parser)}")
            
            # 检查解析器的关键方法
            methods = ['parse_file', 'parse', 'load_dxf', 'extract_holes']
            available_methods = []
            for method in methods:
                if hasattr(dxf_parser, method):
                    available_methods.append(method)
            
            print(f"   可用方法: {available_methods}")
            
        except Exception as e:
            print(f"❌ DXF解析器导入失败: {e}")
        
        print()
        
        # 6. 总结诊断结果
        print("6. 诊断结果总结")
        print("-" * 50)
        
        issues = []
        suggestions = []
        
        if not file_exists:
            issues.append("DXF文件不存在于指定路径")
            suggestions.append(f"请检查文件是否存在于: {abs_path}")
            suggestions.append("或更新产品记录中的dxf_file_path字段")
        
        if not resolved_exists and resolved_path != str(abs_path):
            issues.append("路径解析器无法正确解析DXF路径")
            suggestions.append("检查DataPathManager.resolve_dxf_path方法的实现")
        
        if issues:
            print("发现的问题:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
            
            print("\n建议的解决方案:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
        else:
            print("✅ 未发现明显问题，CAP1000的DXF文件关联看起来正常")
        
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ 诊断过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("\n" + "=" * 80)


def check_related_files():
    """检查相关的DXF文件"""
    print("\n7. 检查项目中的DXF文件...")
    print("-" * 50)
    
    # 搜索项目中的DXF文件
    dxf_files = []
    search_dirs = [
        project_root / "assets",
        project_root / "Data", 
        project_root / "dxf",
        project_root
    ]
    
    for search_dir in search_dirs:
        if search_dir.exists():
            for dxf_file in search_dir.rglob("*.dxf"):
                dxf_files.append(dxf_file)
    
    if dxf_files:
        print(f"找到 {len(dxf_files)} 个DXF文件:")
        for dxf_file in dxf_files:
            relative_path = dxf_file.relative_to(project_root)
            size = dxf_file.stat().st_size
            print(f"  📄 {relative_path} ({size} bytes)")
    else:
        print("❌ 未找到任何DXF文件")
    
    # 特别检查东重管板.dxf
    dongzhong_file = None
    for dxf_file in dxf_files:
        if "东重管板" in dxf_file.name:
            dongzhong_file = dxf_file
            break
    
    if dongzhong_file:
        print(f"\n✅ 找到东重管板.dxf文件:")
        print(f"   路径: {dongzhong_file}")
        print(f"   相对路径: {dongzhong_file.relative_to(project_root)}")
        print(f"   建议更新CAP1000产品记录中的dxf_file_path为: {dongzhong_file.relative_to(project_root)}")
    else:
        print("\n❌ 未找到东重管板.dxf文件")


if __name__ == "__main__":
    success = check_cap1000_dxf_association()
    check_related_files()
    
    if success:
        print("\n🎉 诊断完成 - CAP1000 DXF关联正常")
        sys.exit(0)
    else:
        print("\n⚠️  诊断完成 - 发现问题需要修复")  
        sys.exit(1)