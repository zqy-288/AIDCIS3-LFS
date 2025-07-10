#!/usr/bin/env python3
"""
报告生成系统完整测试套件运行器
运行所有报告生成相关的单元测试、系统测试和端到端测试
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

# 导入测试模块
from unit.test_report_generator import run_unit_tests as run_basic_unit_tests
from unit.test_enhanced_report_generator import run_enhanced_tests
from unit.test_report_manager_widget import run_report_manager_tests
from system.test_report_generation_system import run_system_tests
from e2e.test_report_generation_e2e import run_e2e_tests


class ReportTestSuite:
    """报告生成系统测试套件"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.results = {}
        
    def print_header(self, title: str, char: str = "=", width: int = 80):
        """打印测试标题"""
        print(char * width)
        print(f"{title:^{width}}")
        print(char * width)
        
    def print_section(self, title: str, char: str = "-", width: int = 60):
        """打印测试部分标题"""
        print(f"\n{char * width}")
        print(f" {title}")
        print(char * width)
        
    def run_test_group(self, group_name: str, test_function, description: str = ""):
        """运行测试组"""
        self.print_section(f"{group_name} - {description}" if description else group_name)
        
        start_time = time.time()
        
        try:
            success = test_function()
            end_time = time.time()
            duration = end_time - start_time
            
            self.results[group_name] = {
                'success': success,
                'duration': duration,
                'error': None
            }
            
            status = "✅ 通过" if success else "❌ 失败"
            print(f"\n{group_name}: {status} (耗时: {duration:.2f}秒)")
            
            return success
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            self.results[group_name] = {
                'success': False,
                'duration': duration,
                'error': str(e)
            }
            
            print(f"\n{group_name}: ❌ 异常 - {e} (耗时: {duration:.2f}秒)")
            return False
            
    def run_all_tests(self):
        """运行所有测试"""
        self.start_time = time.time()
        
        self.print_header("报告生成系统完整测试套件")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Python版本: {sys.version}")
        print(f"工作目录: {os.getcwd()}")
        
        # 1. 单元测试
        self.print_section("第一阶段：单元测试", "=")
        
        unit_success = all([
            self.run_test_group(
                "基础报告生成器单元测试", 
                run_basic_unit_tests,
                "测试ReportGenerator核心功能"
            ),
            self.run_test_group(
                "增强报告生成器单元测试", 
                run_enhanced_tests,
                "测试包络图和内窥镜图像功能"
            ),
            self.run_test_group(
                "报告管理器组件单元测试", 
                run_report_manager_tests,
                "测试UI组件功能"
            )
        ])
        
        # 2. 系统测试
        self.print_section("第二阶段：系统测试", "=")
        
        system_success = self.run_test_group(
            "报告生成系统测试", 
            run_system_tests,
            "测试完整报告生成流程"
        )
        
        # 3. 端到端测试
        self.print_section("第三阶段：端到端测试", "=")
        
        e2e_success = self.run_test_group(
            "端到端测试", 
            run_e2e_tests,
            "测试用户界面到报告生成的完整流程"
        )
        
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        # 4. 生成测试报告
        self.generate_test_report(unit_success, system_success, e2e_success, total_duration)
        
        # 返回总体成功状态
        return unit_success and system_success and e2e_success
        
    def generate_test_report(self, unit_success: bool, system_success: bool, 
                           e2e_success: bool, total_duration: float):
        """生成测试报告"""
        self.print_header("测试结果汇总", "=")
        
        # 总体状态
        overall_success = unit_success and system_success and e2e_success
        overall_status = "✅ 全部通过" if overall_success else "❌ 部分失败"
        
        print(f"总体状态: {overall_status}")
        print(f"总耗时: {total_duration:.2f}秒")
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 各阶段结果
        print("\n📊 各阶段结果:")
        stages = [
            ("单元测试", unit_success),
            ("系统测试", system_success),
            ("端到端测试", e2e_success)
        ]
        
        for stage_name, success in stages:
            status = "✅" if success else "❌"
            print(f"  {status} {stage_name}")
            
        # 详细结果
        print("\n📋 详细测试结果:")
        for test_name, result in self.results.items():
            status = "✅" if result['success'] else "❌"
            duration = result['duration']
            print(f"  {status} {test_name:<35} {duration:>6.2f}s")
            if result['error']:
                print(f"     错误: {result['error']}")
                
        # 统计信息
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 统计信息:")
        print(f"  总测试组: {total_tests}")
        print(f"  通过: {passed_tests}")
        print(f"  失败: {failed_tests}")
        print(f"  成功率: {passed_tests/total_tests*100:.1f}%")
        
        # 性能分析
        if self.results:
            durations = [r['duration'] for r in self.results.values()]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            
            print(f"\n⏱️ 性能分析:")
            print(f"  平均耗时: {avg_duration:.2f}s")
            print(f"  最长耗时: {max_duration:.2f}s")
            print(f"  最短耗时: {min_duration:.2f}s")
            
        # 保存测试报告到文件
        self.save_test_report_to_file(overall_success, total_duration)
        
    def save_test_report_to_file(self, overall_success: bool, total_duration: float):
        """保存测试报告到文件"""
        report_dir = Path(__file__).parent / "test_reports"
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"report_test_results_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("报告生成系统测试结果\n")
            f.write("=" * 50 + "\n")
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总体状态: {'成功' if overall_success else '失败'}\n")
            f.write(f"总耗时: {total_duration:.2f}秒\n\n")
            
            f.write("详细结果:\n")
            f.write("-" * 30 + "\n")
            for test_name, result in self.results.items():
                status = "通过" if result['success'] else "失败"
                f.write(f"{test_name}: {status} ({result['duration']:.2f}s)\n")
                if result['error']:
                    f.write(f"  错误: {result['error']}\n")
                    
        print(f"\n📄 测试报告已保存到: {report_file}")


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
        
    missing_deps = [dep for dep, available in dependencies.items() if not available]
    if missing_deps:
        print(f"\n⚠️ 缺失依赖: {', '.join(missing_deps)}")
        print("某些测试可能会失败或跳过")
    else:
        print("\n✅ 所有依赖都已安装")
        
    return dependencies


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
    print("启动报告生成系统完整测试套件...")
    
    # 1. 依赖检查
    dependencies = run_dependency_check()
    
    # 2. 测试数据生成
    data_gen_success = run_test_data_generation()
    if not data_gen_success:
        print("⚠️ 测试数据生成失败，但继续运行测试...")
        
    # 3. 运行测试套件
    test_suite = ReportTestSuite()
    success = test_suite.run_all_tests()
    
    # 4. 输出最终结果
    if success:
        print("\n🎉 所有测试通过！报告生成系统工作正常。")
        exit_code = 0
    else:
        print("\n💥 部分测试失败！请检查上述错误信息。")
        exit_code = 1
        
    return exit_code


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)