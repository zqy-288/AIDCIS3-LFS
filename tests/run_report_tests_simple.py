#!/usr/bin/env python3
"""
简化的报告生成系统测试运行器
跳过需要PySide6的UI组件测试，专注于核心功能测试
"""

import sys
import os
import time
import unittest
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(Path(__file__).parent))

def run_dependency_check():
    """运行依赖检查"""
    print("🔍 检查依赖...")
    
    dependencies = {
        'numpy': False,
        'matplotlib': False,
        'PIL': False,
        'reportlab': False,
        'openpyxl': False
    }
    
    # 检查numpy
    try:
        import numpy
        dependencies['numpy'] = True
    except ImportError:
        pass
        
    # 检查matplotlib
    try:
        import matplotlib
        dependencies['matplotlib'] = True
    except ImportError:
        pass
        
    # 检查PIL
    try:
        from PIL import Image
        dependencies['PIL'] = True
    except ImportError:
        pass
        
    # 检查reportlab
    try:
        import reportlab
        dependencies['reportlab'] = True
    except ImportError:
        pass
        
    # 检查openpyxl
    try:
        import openpyxl
        dependencies['openpyxl'] = True
    except ImportError:
        pass
        
    print("依赖状态:")
    for dep, available in dependencies.items():
        status = "✅" if available else "❌"
        print(f"  {status} {dep}")
        
    return dependencies

def run_basic_unit_tests():
    """运行基础报告生成器单元测试"""
    print("\n📋 运行基础报告生成器单元测试...")
    
    try:
        from unit.test_report_generator import run_unit_tests
        return run_unit_tests()
    except Exception as e:
        print(f"❌ 基础单元测试失败: {e}")
        return False

def run_enhanced_unit_tests():
    """运行增强报告生成器单元测试"""
    print("\n🎨 运行增强报告生成器单元测试...")
    
    try:
        from unit.test_enhanced_report_generator import run_enhanced_tests
        return run_enhanced_tests()
    except Exception as e:
        print(f"❌ 增强单元测试失败: {e}")
        return False

def run_system_tests():
    """运行系统测试"""
    print("\n🔧 运行系统测试...")
    
    try:
        from system.test_report_generation_system import run_system_tests
        return run_system_tests()
    except Exception as e:
        print(f"❌ 系统测试失败: {e}")
        return False

def run_e2e_tests():
    """运行端到端测试"""
    print("\n🎯 运行端到端测试...")
    
    try:
        from e2e.test_report_generation_e2e import run_e2e_tests
        return run_e2e_tests()
    except Exception as e:
        print(f"❌ 端到端测试失败: {e}")
        return False

def run_test_data_generation():
    """运行测试数据生成"""
    print("\n🔄 生成测试数据...")
    
    try:
        from test_data.sample_data_generator import generate_test_data
        manifest = generate_test_data()
        print("✅ 测试数据生成完成")
        return True
    except Exception as e:
        print(f"❌ 测试数据生成失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("报告生成系统简化测试套件")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    
    # 1. 依赖检查
    dependencies = run_dependency_check()
    
    # 2. 测试数据生成
    data_gen_success = run_test_data_generation()
    if not data_gen_success:
        print("⚠️ 测试数据生成失败，但继续运行测试...")
    
    # 3. 运行核心测试
    start_time = time.time()
    
    results = {
        "基础单元测试": run_basic_unit_tests(),
        "增强单元测试": run_enhanced_unit_tests(), 
        "系统测试": run_system_tests(),
        "端到端测试": run_e2e_tests()
    }
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # 4. 结果汇总
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    passed_tests = sum(1 for success in results.values() if success)
    total_tests = len(results)
    
    print(f"总体状态: {'✅ 全部通过' if passed_tests == total_tests else '❌ 部分失败'}")
    print(f"总耗时: {total_duration:.2f}秒")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n📊 详细结果:")
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")
        
    print(f"\n📈 统计信息:")
    print(f"  总测试组: {total_tests}")
    print(f"  通过: {passed_tests}")
    print(f"  失败: {total_tests - passed_tests}")
    print(f"  成功率: {passed_tests/total_tests*100:.1f}%")
    
    # 跳过的测试说明
    print(f"\n⏭️ 跳过的测试:")
    print(f"  ⚠️ 报告管理器UI组件测试 (需要PySide6)")
    
    # 保存测试报告
    report_dir = Path(__file__).parent / "test_reports"
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"simple_test_results_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("报告生成系统简化测试结果\n")
        f.write("=" * 50 + "\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总体状态: {'成功' if passed_tests == total_tests else '失败'}\n")
        f.write(f"总耗时: {total_duration:.2f}秒\n\n")
        
        f.write("详细结果:\n")
        f.write("-" * 30 + "\n")
        for test_name, success in results.items():
            status = "通过" if success else "失败"
            f.write(f"{test_name}: {status}\n")
            
        f.write("\n跳过的测试:\n")
        f.write("报告管理器UI组件测试 (需要PySide6)\n")
        
    print(f"\n📄 测试报告已保存到: {report_file}")
    
    # 返回结果
    if passed_tests == total_tests:
        print("\n🎉 所有核心测试通过！报告生成系统核心功能正常。")
        return 0
    else:
        print("\n💥 部分测试失败！请检查上述错误信息。")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)