#!/usr/bin/env python3
"""
简单的DXF导入功能测试（无GUI）
验证DXF文件解析和产品型号创建功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'modules'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'models'))

def test_imports():
    """测试基本导入"""
    print("=== 测试基本导入 ===")
    
    try:
        # 测试产品模型导入
        from product_model import get_product_manager, ProductModel
        print("✓ 产品模型导入成功")
        
        # 测试产品管理器
        manager = get_product_manager()
        print("✓ 产品管理器创建成功")
        
        # 测试基本查询
        products = manager.get_all_products()
        print(f"✓ 获取产品列表成功，共{len(products)}个产品")
        
        return True
        
    except Exception as e:
        print(f"✗ 基本导入测试失败: {str(e)}")
        return False

def test_dxf_importer():
    """测试DXF导入器"""
    print("\n=== 测试DXF导入器 ===")
    
    try:
        # 检查ezdxf可用性
        try:
            import ezdxf
            print("✓ ezdxf库可用")
        except ImportError:
            print("✗ ezdxf库不可用，请安装: pip install ezdxf")
            return False
        
        # 导入DXF导入器
        from dxf_import import get_dxf_importer, DXFImporter
        print("✓ DXF导入器导入成功")
        
        # 创建导入器实例
        importer = get_dxf_importer()
        print("✓ DXF导入器实例创建成功")
        
        # 检查ezdxf可用性
        if importer.check_ezdxf_availability():
            print("✓ ezdxf可用性检查通过")
        else:
            print("✗ ezdxf可用性检查失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ DXF导入器测试失败: {str(e)}")
        return False

def test_dxf_analysis():
    """测试DXF文件分析"""
    print("\n=== 测试DXF文件分析 ===")
    
    # DXF文件路径
    dxf_file_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/测试管板.dxf"
    
    if not os.path.exists(dxf_file_path):
        print(f"✗ DXF文件不存在: {dxf_file_path}")
        return False
    
    print(f"✓ DXF文件存在: {os.path.basename(dxf_file_path)}")
    
    try:
        from dxf_import import get_dxf_importer
        
        # 获取导入器
        importer = get_dxf_importer()
        
        # 获取预览信息
        print("正在分析DXF文件...")
        preview_info = importer.get_import_preview(dxf_file_path)
        
        if 'error' in preview_info:
            print(f"✗ DXF分析失败: {preview_info['error']}")
            return False
        
        # 显示分析结果
        print("✓ DXF文件分析成功")
        print(f"  - 文件路径: {preview_info.get('file_path', 'N/A')}")
        print(f"  - 建议产品型号: {preview_info.get('suggested_model_name', 'N/A')}")
        print(f"  - 检测孔数量: {preview_info.get('total_holes', 0)}")
        print(f"  - 标准直径: {preview_info.get('standard_diameter', 0):.2f} mm")
        print(f"  - 建议公差: ±{preview_info.get('tolerance_estimate', 0):.3f} mm")
        print(f"  - 图层数量: {preview_info.get('layer_count', 0)}")
        
        # 显示详细统计
        if 'diameter_stats' in preview_info:
            stats = preview_info['diameter_stats']
            print(f"  - 直径统计:")
            print(f"    最小: {stats.get('min', 0):.3f} mm")
            print(f"    最大: {stats.get('max', 0):.3f} mm")
            print(f"    平均: {stats.get('mean', 0):.3f} mm")
            print(f"    数量: {stats.get('count', 0)}")
        
        # 边界信息
        if 'boundary_info' in preview_info:
            boundary = preview_info['boundary_info']
            print(f"  - 边界信息: {boundary}")
        
        return True
        
    except Exception as e:
        print(f"✗ DXF分析测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_product_creation():
    """测试产品创建"""
    print("\n=== 测试产品创建 ===")
    
    try:
        from product_model import get_product_manager
        from dxf_import import get_dxf_importer
        
        # DXF文件路径
        dxf_file_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/测试管板.dxf"
        
        if not os.path.exists(dxf_file_path):
            print(f"✗ DXF文件不存在: {dxf_file_path}")
            return False
        
        # 获取导入器和管理器
        importer = get_dxf_importer()
        manager = get_product_manager()
        
        # 分析DXF文件
        analysis_result = importer.import_from_dxf(dxf_file_path)
        if not analysis_result:
            print("✗ DXF分析失败")
            return False
        
        print("✓ DXF分析成功")
        
        # 创建测试产品
        test_model_name = f"TEST_{analysis_result.suggested_model_name}"
        
        # 检查是否已存在
        existing = manager.get_product_by_name(test_model_name)
        if existing:
            print(f"产品 '{test_model_name}' 已存在，跳过创建")
            return True
        
        # 创建产品
        success = importer.create_product_from_dxf(
            analysis_result,
            dxf_file_path,
            model_name=test_model_name,
            model_code="TEST001",
            description="测试用DXF导入产品"
        )
        
        if success:
            print(f"✓ 产品创建成功: {test_model_name}")
            
            # 验证产品是否存在
            created_product = manager.get_product_by_name(test_model_name)
            if created_product:
                print(f"✓ 产品验证成功")
                print(f"  - 产品ID: {created_product.id}")
                print(f"  - 型号名称: {created_product.model_name}")
                print(f"  - 标准直径: {created_product.standard_diameter:.2f} mm")
                print(f"  - 公差范围: {created_product.tolerance_range}")
                print(f"  - DXF文件路径: {created_product.dxf_file_path}")
                return True
            else:
                print("✗ 产品验证失败")
                return False
        else:
            print("✗ 产品创建失败")
            return False
            
    except Exception as e:
        print(f"✗ 产品创建测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("启动DXF导入功能测试...")
    print("=" * 50)
    
    results = []
    
    # 运行测试
    results.append(("基本导入测试", test_imports()))
    results.append(("DXF导入器测试", test_dxf_importer()))
    results.append(("DXF文件分析测试", test_dxf_analysis()))
    results.append(("产品创建测试", test_product_creation()))
    
    # 输出结果
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！DXF导入功能正常工作。")
        return 0
    else:
        print("❌ 部分测试失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())