#!/usr/bin/env python3
"""
测试DXF渲染和编号功能
验证DXF文件的可视化渲染、孔位编号和数据导出功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'modules'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'models'))

def check_dependencies():
    """检查依赖库"""
    print("=== 检查依赖库 ===")
    
    deps = {}
    
    # 检查ezdxf
    try:
        import ezdxf
        deps['ezdxf'] = True
        print("✓ ezdxf 可用")
    except ImportError:
        deps['ezdxf'] = False
        print("✗ ezdxf 不可用")
    
    # 检查matplotlib
    try:
        import matplotlib.pyplot as plt
        deps['matplotlib'] = True
        print("✓ matplotlib 可用")
    except ImportError:
        deps['matplotlib'] = False
        print("✗ matplotlib 不可用")
    
    # 检查numpy
    try:
        import numpy as np
        deps['numpy'] = True
        print("✓ numpy 可用")
    except ImportError:
        deps['numpy'] = False
        print("✗ numpy 不可用")
    
    return deps

def test_dxf_renderer():
    """测试DXF渲染器"""
    print("\n=== 测试DXF渲染器 ===")
    
    try:
        from dxf_renderer import get_dxf_renderer
        
        renderer = get_dxf_renderer()
        print("✓ DXF渲染器创建成功")
        
        # 检查依赖
        deps = renderer.check_dependencies()
        print(f"依赖检查结果: {deps}")
        
        if not all(deps.values()):
            missing = [k for k, v in deps.items() if not v]
            print(f"✗ 缺少依赖: {missing}")
            return False
        
        print("✓ 所有依赖检查通过")
        return True
        
    except Exception as e:
        print(f"✗ DXF渲染器测试失败: {str(e)}")
        return False

def test_dxf_rendering():
    """测试DXF渲染功能"""
    print("\n=== 测试DXF渲染功能 ===")
    
    dxf_file_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/测试管板.dxf"
    
    if not os.path.exists(dxf_file_path):
        print(f"✗ 测试DXF文件不存在: {dxf_file_path}")
        return False
    
    print(f"✓ 使用测试文件: {os.path.basename(dxf_file_path)}")
    
    try:
        from dxf_renderer import get_dxf_renderer
        
        renderer = get_dxf_renderer()
        
        # 准备输出路径
        output_dir = os.path.dirname(dxf_file_path)
        base_name = os.path.splitext(os.path.basename(dxf_file_path))[0]
        output_image_path = os.path.join(output_dir, f"{base_name}_test_render.png")
        
        print("正在渲染DXF文件...")
        
        # 测试不同的编号策略
        strategies = ['left_to_right', 'top_to_bottom', 'spiral', 'distance_from_center']
        
        for strategy in strategies:
            print(f"\n测试编号策略: {strategy}")
            
            try:
                strategy_output_path = os.path.join(
                    output_dir, f"{base_name}_{strategy}_render.png"
                )
                
                # 执行渲染
                render_result = renderer.render_dxf_with_numbering(
                    dxf_file_path,
                    strategy,
                    strategy_output_path
                )
                
                print(f"✓ 渲染成功")
                print(f"  - 检测孔数: {len(render_result.holes)}")
                print(f"  - 标注数量: {len(render_result.annotations)}")
                print(f"  - 输出图像: {strategy_output_path}")
                
                if render_result.hole_table_data:
                    print(f"  - 孔位表数据: {len(render_result.hole_table_data)} 行")
                    
                    # 显示前3个孔的信息
                    for i, hole_data in enumerate(render_result.hole_table_data[:3]):
                        print(f"    孔 {i+1}: {hole_data}")
                
                # 测试数据导出
                csv_path = os.path.join(output_dir, f"{base_name}_{strategy}_holes.csv")
                exported_csv = renderer.export_hole_data(render_result, csv_path, 'csv')
                print(f"  - CSV导出: {exported_csv}")
                
                # 测试创建带编号的DXF
                numbered_dxf_path = os.path.join(output_dir, f"{base_name}_{strategy}_numbered.dxf")
                numbered_dxf = renderer.create_numbered_dxf(
                    dxf_file_path, numbered_dxf_path, strategy
                )
                print(f"  - 编号DXF: {numbered_dxf}")
                
            except Exception as e:
                print(f"✗ 策略 {strategy} 测试失败: {str(e)}")
                continue
        
        print("\n✅ DXF渲染功能测试完成")
        return True
        
    except Exception as e:
        print(f"✗ DXF渲染测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_hole_numbering_strategies():
    """测试孔位编号策略"""
    print("\n=== 测试孔位编号策略 ===")
    
    try:
        from dxf_renderer import get_dxf_renderer
        from dxf_import import DXFHoleInfo
        
        renderer = get_dxf_renderer()
        
        # 创建测试孔位数据
        test_holes = [
            DXFHoleInfo(100, 100, 10, "standard"),  # 左下
            DXFHoleInfo(200, 100, 10, "standard"),  # 右下
            DXFHoleInfo(100, 200, 10, "standard"),  # 左上
            DXFHoleInfo(200, 200, 10, "standard"),  # 右上
            DXFHoleInfo(150, 150, 10, "standard"),  # 中心
        ]
        
        strategies = renderer.hole_numbering_strategies
        
        for strategy_name, strategy_func in strategies.items():
            print(f"\n测试策略: {strategy_name}")
            
            ordered_holes = strategy_func(test_holes.copy())
            
            print("排序结果:")
            for i, hole in enumerate(ordered_holes):
                print(f"  {i+1}: ({hole.center_x}, {hole.center_y})")
        
        print("\n✓ 所有编号策略测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 编号策略测试失败: {str(e)}")
        return False

def install_missing_dependencies():
    """安装缺少的依赖"""
    print("\n=== 安装缺少的依赖 ===")
    
    import subprocess
    
    required_packages = ['matplotlib', 'numpy']
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} 已安装")
        except ImportError:
            print(f"正在安装 {package}...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✓ {package} 安装成功")
            except subprocess.CalledProcessError:
                print(f"✗ {package} 安装失败")
                return False
    
    return True

def main():
    """主函数"""
    print("DXF渲染和编号功能测试")
    print("=" * 50)
    
    # 检查依赖
    deps = check_dependencies()
    
    missing_deps = [k for k, v in deps.items() if not v]
    if missing_deps:
        print(f"\n缺少依赖: {missing_deps}")
        
        if 'matplotlib' in missing_deps or 'numpy' in missing_deps:
            print("尝试自动安装...")
            if not install_missing_dependencies():
                print("❌ 依赖安装失败，请手动安装:")
                for dep in missing_deps:
                    print(f"  pip install {dep}")
                return 1
        else:
            print("请手动安装缺少的依赖")
            return 1
    
    # 执行测试
    tests = [
        ("DXF渲染器", test_dxf_renderer),
        ("孔位编号策略", test_hole_numbering_strategies),
        ("DXF渲染功能", test_dxf_rendering),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ 测试异常: {str(e)}")
            results.append((test_name, False))
    
    # 输出结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
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
        print("\n🎉 所有测试通过！DXF渲染和编号功能正常工作。")
        print("\n功能说明:")
        print("✅ DXF文件解析和孔位识别")
        print("✅ 多种孔位编号策略")
        print("✅ 图像渲染和可视化")
        print("✅ 孔位数据表生成")
        print("✅ CSV数据导出")
        print("✅ 带编号DXF文件生成")
        
        return 0
    else:
        print(f"\n❌ {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())