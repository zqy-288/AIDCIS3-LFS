#!/usr/bin/env python3
"""
侧边栏全景图测试套件运行器
运行所有相关的单元测试、集成测试和系统测试
"""

import sys
import os
import unittest
from pathlib import Path

def setup_environment():
    """设置测试环境"""
    # 添加项目根目录到路径
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # 设置环境变量
    os.environ['PYTHONPATH'] = str(src_path)

def discover_and_run_tests():
    """发现并运行所有侧边栏全景图相关测试"""
    
    print("🧪 侧边栏全景图测试套件")
    print("=" * 60)
    
    # 设置测试发现器
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 测试文件路径
    test_files = [
        'tests/unit/test_sidebar_panorama_layout.py',
        'tests/integration/test_sidebar_panorama_integration.py', 
        'tests/system/test_sidebar_panorama_system.py'
    ]
    
    # 加载测试
    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        if test_path.exists():
            print(f"📁 发现测试文件: {test_file}")
            
            # 导入测试模块
            module_name = test_file.replace('/', '.').replace('.py', '')
            try:
                spec = unittest.util.spec_from_file_location(module_name, test_path)
                module = unittest.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 添加测试到套件
                module_tests = loader.loadTestsFromModule(module)
                suite.addTests(module_tests)
                
            except Exception as e:
                print(f"❌ 加载测试文件 {test_file} 失败: {e}")
        else:
            print(f"⚠️ 测试文件不存在: {test_file}")
    
    # 运行测试
    print("\\n🏃 开始运行测试...")
    print("-" * 60)
    
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        buffer=False
    )
    
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print("\\n" + "=" * 60)
    print("📊 测试结果摘要")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    successful = total_tests - failures - errors - skipped
    
    print(f"总测试数: {total_tests}")
    print(f"✅ 成功: {successful}")
    print(f"❌ 失败: {failures}")
    print(f"🔥 错误: {errors}")
    print(f"⏭️ 跳过: {skipped}")
    
    success_rate = (successful / total_tests * 100) if total_tests > 0 else 0
    print(f"\\n📈 成功率: {success_rate:.1f}%")
    
    # 详细失败信息
    if failures:
        print("\\n❌ 失败测试详情:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.splitlines()[-1] if traceback else 'Unknown failure'}")
    
    if errors:
        print("\\n🔥 错误测试详情:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.splitlines()[-1] if traceback else 'Unknown error'}")
    
    # 返回是否所有测试都通过
    return failures == 0 and errors == 0

def run_specific_test_category(category):
    """运行特定类别的测试"""
    test_mapping = {
        'unit': 'tests/unit/test_sidebar_panorama_layout.py',
        'integration': 'tests/integration/test_sidebar_panorama_integration.py',
        'system': 'tests/system/test_sidebar_panorama_system.py'
    }
    
    if category not in test_mapping:
        print(f"❌ 未知的测试类别: {category}")
        print(f"可用类别: {', '.join(test_mapping.keys())}")
        return False
    
    test_file = test_mapping[category]
    test_path = Path(__file__).parent / test_file
    
    if not test_path.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    print(f"🧪 运行 {category} 测试: {test_file}")
    print("=" * 60)
    
    # 使用unittest的发现和运行机制
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    try:
        # 导入并加载测试
        module_name = test_file.replace('/', '.').replace('.py', '')
        spec = unittest.util.spec_from_file_location(module_name, test_path)
        module = unittest.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        module_tests = loader.loadTestsFromModule(module)
        suite.addTests(module_tests)
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return len(result.failures) == 0 and len(result.errors) == 0
        
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")
        return False

def run_quick_verification():
    """运行快速验证测试"""
    print("🚀 运行扇形专注显示快速验证")
    print("=" * 60)
    
    verification_script = Path(__file__).parent / "test_sector_focused_display.py"
    if not verification_script.exists():
        print("❌ 快速验证脚本不存在")
        return False
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, str(verification_script)], 
                              capture_output=True, text=True, timeout=60)
        
        # 输出结果
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ 快速验证超时")
        return False
    except Exception as e:
        print(f"❌ 运行快速验证失败: {e}")
        return False

def main():
    """主函数"""
    setup_environment()
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == "quick" or arg == "verify":
            # 运行快速验证
            success = run_quick_verification()
        else:
            # 运行特定类别的测试
            success = run_specific_test_category(arg)
    else:
        # 先运行快速验证，再运行完整测试
        print("🔍 首先运行快速验证...")
        quick_success = run_quick_verification()
        
        if quick_success:
            print("\\n✅ 快速验证通过，继续运行完整测试套件...")
            success = discover_and_run_tests()
        else:
            print("\\n❌ 快速验证失败，跳过完整测试")
            success = False
    
    # 根据测试结果退出
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()