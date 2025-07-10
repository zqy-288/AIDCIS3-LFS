#!/usr/bin/env python3
"""
核心功能测试运行器
只测试报告生成的核心功能，避免复杂的模拟和依赖问题
"""

import sys
import os
import tempfile
import time
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(Path(__file__).parent))

def test_standalone_report_generator():
    """测试独立报告生成器的核心功能"""
    print("🔧 测试独立报告生成器...")
    
    try:
        from test_modules.standalone_report_generator import ReportGenerator
        
        # 创建生成器
        generator = ReportGenerator()
        
        # 测试数据
        hole_data = {
            'total_holes': 50,
            'checked_holes': 48,
            'qualified_holes': 45,
            'unqualified_holes': 3
        }
        
        workpiece_info = {
            'model': 'CP1400',
            'serial': 'SN-CORE-TEST-001',
            'operator': '核心测试用户',
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
        print("  📄 测试CSV导出...")
        csv_path = generator.export_raw_data_csv(hole_data, workpiece_info)
        if os.path.exists(csv_path) and os.path.getsize(csv_path) > 100:
            print(f"    ✅ CSV导出成功: {os.path.basename(csv_path)}")
        else:
            print(f"    ❌ CSV导出失败")
            return False
            
        print("  🌐 测试Web数据生成...")
        web_data = generator.generate_web_report_data(hole_data, workpiece_info)
        if isinstance(web_data, dict) and 'header' in web_data and 'summary' in web_data:
            print(f"    ✅ Web数据生成成功: {len(web_data)} 个字段")
        else:
            print(f"    ❌ Web数据生成失败")
            return False
            
        print("  📊 测试包络图生成...")
        measurement_data = [
            {'depth': i * 0.5, 'diameter': 17.6 + (i % 10) * 0.001}
            for i in range(100)
        ]
        chart_path = generator.generate_envelope_chart(measurement_data, 17.6, 0.05, 0.07)
        if os.path.exists(chart_path) and os.path.getsize(chart_path) > 1000:
            print(f"    ✅ 包络图生成成功: {os.path.basename(chart_path)}")
        else:
            print(f"    ❌ 包络图生成失败")
            return False
            
        print("  💾 测试Excel导出...")
        try:
            excel_path = generator.export_raw_data_excel(hole_data, workpiece_info)
            if os.path.exists(excel_path) and os.path.getsize(excel_path) > 100:
                print(f"    ✅ Excel导出成功: {os.path.basename(excel_path)}")
            else:
                print(f"    ❌ Excel导出失败")
                return False
        except ImportError:
            print(f"    ⚠️ Excel导出跳过 (openpyxl不可用)")
            
        return True
        
    except Exception as e:
        print(f"    ❌ 独立报告生成器测试失败: {e}")
        return False

def test_enhanced_report_generator():
    """测试增强报告生成器的核心功能"""
    print("🎨 测试增强报告生成器...")
    
    try:
        from test_modules.standalone_enhanced_report_generator import EnhancedReportGenerator
        
        # 创建生成器
        generator = EnhancedReportGenerator()
        
        # 测试数据
        measurement_data = [
            {'depth': i * 0.5, 'diameter': 17.6 + (i % 20 - 10) * 0.01 / 10}
            for i in range(500)
        ]
        
        print("  📈 测试包络图生成...")
        envelope_chart = generator.generate_envelope_chart_with_annotations(
            measurement_data, 17.6, 0.05, 0.07, "H001"
        )
        if os.path.exists(envelope_chart) and os.path.getsize(envelope_chart) > 5000:
            print(f"    ✅ 包络图生成成功: {os.path.basename(envelope_chart)}")
        else:
            print(f"    ❌ 包络图生成失败")
            return False
            
        print("  📊 测试统计图表生成...")
        stats_chart = generator._generate_statistics_chart(measurement_data)
        if os.path.exists(stats_chart) and os.path.getsize(stats_chart) > 3000:
            print(f"    ✅ 统计图表生成成功: {os.path.basename(stats_chart)}")
        else:
            print(f"    ❌ 统计图表生成失败")
            return False
            
        print("  🔍 测试占位符内窥镜图像...")
        placeholder = generator._generate_placeholder_endoscope_image("H001")
        if os.path.exists(placeholder) and os.path.getsize(placeholder) > 1000:
            print(f"    ✅ 占位符图像生成成功: {os.path.basename(placeholder)}")
        else:
            print(f"    ❌ 占位符图像生成失败")
            return False
            
        print("  📝 测试统计文本生成...")
        diameters = [d['diameter'] for d in measurement_data]
        stats_text = generator._generate_statistics_text(diameters, 17.6, 0.05, 0.07)
        if '平均直径' in stats_text and '标准偏差' in stats_text:
            print(f"    ✅ 统计文本生成成功")
        else:
            print(f"    ❌ 统计文本生成失败")
            return False
            
        return True
        
    except Exception as e:
        print(f"    ❌ 增强报告生成器测试失败: {e}")
        return False

def test_multi_threading():
    """测试多线程报告生成"""
    print("🧵 测试多线程报告生成...")
    
    try:
        from test_modules.standalone_report_generator import ReportGenerator, ReportGenerationThread
        
        # 创建生成器
        generator = ReportGenerator()
        
        # 测试数据
        hole_data = {'total_holes': 20, 'checked_holes': 20}
        workpiece_info = {
            'model': 'CP1400',
            'serial': 'SN-THREAD-TEST',
            'operator': '线程测试用户'
        }
        
        # 结果收集器
        results = []
        errors = []
        
        def collect_result(report_type, file_path):
            results.append((report_type, file_path))
            
        def collect_error(report_type, error_msg):
            errors.append((report_type, error_msg))
            
        print("  🔄 创建CSV生成线程...")
        csv_thread = ReportGenerationThread(generator, "CSV", hole_data, workpiece_info)
        csv_thread.generation_completed.connect(collect_result)
        csv_thread.generation_failed.connect(collect_error)
        
        print("  🌐 创建Web生成线程...")
        web_thread = ReportGenerationThread(generator, "WEB", hole_data, workpiece_info)
        web_thread.generation_completed.connect(collect_result)
        web_thread.generation_failed.connect(collect_error)
        
        # 启动线程
        csv_thread.start()
        web_thread.start()
        
        # 等待完成
        csv_success = csv_thread.wait(5000)
        web_success = web_thread.wait(5000)
        
        if csv_success and web_success and len(results) == 2 and len(errors) == 0:
            print(f"    ✅ 多线程生成成功: {len(results)} 个报告")
            return True
        else:
            print(f"    ❌ 多线程生成失败: {len(results)} 个成功, {len(errors)} 个错误")
            return False
            
    except Exception as e:
        print(f"    ❌ 多线程测试失败: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    print("🛡️ 测试错误处理...")
    
    try:
        from test_modules.standalone_report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        print("  📄 测试空数据处理...")
        try:
            csv_path = generator.export_raw_data_csv({}, {})
            if os.path.exists(csv_path):
                print(f"    ✅ 空数据处理成功")
            else:
                print(f"    ❌ 空数据处理失败")
                return False
        except Exception as e:
            print(f"    ⚠️ 空数据抛出异常但被捕获: {type(e).__name__}")
            
        print("  📊 测试空测量数据包络图...")
        chart_path = generator.generate_envelope_chart([], 17.6, 0.05, 0.07)
        if os.path.exists(chart_path):
            print(f"    ✅ 空测量数据处理成功")
        else:
            print(f"    ❌ 空测量数据处理失败")
            return False
            
        return True
        
    except Exception as e:
        print(f"    ❌ 错误处理测试失败: {e}")
        return False

def run_dependency_check():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    deps = {}
    
    try:
        import numpy
        deps['numpy'] = True
        print("  ✅ numpy")
    except ImportError:
        deps['numpy'] = False
        print("  ❌ numpy")
        
    try:
        import matplotlib
        deps['matplotlib'] = True
        print("  ✅ matplotlib")
    except ImportError:
        deps['matplotlib'] = False
        print("  ❌ matplotlib")
        
    try:
        from PIL import Image
        deps['PIL'] = True
        print("  ✅ PIL")
    except ImportError:
        deps['PIL'] = False
        print("  ❌ PIL")
        
    try:
        import reportlab
        deps['reportlab'] = True
        print("  ✅ reportlab")
    except ImportError:
        deps['reportlab'] = False
        print("  ❌ reportlab")
        
    try:
        import openpyxl
        deps['openpyxl'] = True
        print("  ✅ openpyxl")
    except ImportError:
        deps['openpyxl'] = False
        print("  ❌ openpyxl")
        
    return deps

def main():
    """主函数"""
    print("=" * 80)
    print("报告生成系统核心功能测试")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    
    # 检查依赖
    deps = run_dependency_check()
    
    # 运行核心测试
    tests = [
        ("独立报告生成器", test_standalone_report_generator),
        ("增强报告生成器", test_enhanced_report_generator),
        ("多线程功能", test_multi_threading),
        ("错误处理", test_error_handling)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        results[test_name] = test_func()
        
    end_time = time.time()
    total_duration = end_time - start_time
    
    # 汇总结果
    print(f"\n{'='*80}")
    print("测试结果汇总")
    print("="*80)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"总体状态: {'✅ 全部通过' if passed == total else '❌ 部分失败'}")
    print(f"总耗时: {total_duration:.2f}秒")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n📊 详细结果:")
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {test_name}")
        
    print(f"\n📈 统计信息:")
    print(f"  总测试: {total}")
    print(f"  通过: {passed}")
    print(f"  失败: {total - passed}")
    print(f"  成功率: {passed/total*100:.1f}%")
    
    # 保存报告
    report_dir = Path(__file__).parent / "test_reports"
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"core_test_results_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("报告生成系统核心功能测试结果\n")
        f.write("=" * 50 + "\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总体状态: {'成功' if passed == total else '失败'}\n")
        f.write(f"总耗时: {total_duration:.2f}秒\n\n")
        
        f.write("详细结果:\n")
        f.write("-" * 30 + "\n")
        for test_name, success in results.items():
            status = "通过" if success else "失败"
            f.write(f"{test_name}: {status}\n")
            
    print(f"\n📄 测试报告已保存到: {report_file}")
    
    if passed == total:
        print("\n🎉 所有核心功能测试通过！")
        return 0
    else:
        print(f"\n💥 {total - passed} 个测试失败！")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)