"""
报告生成系统测试
测试完整的报告生成系统工作流程
"""

import unittest
import tempfile
import os
import json
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import threading

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# 使用独立的报告生成器避免PySide6依赖
from test_modules.standalone_report_generator import ReportGenerator, ReportData, ReportGenerationThread
from test_modules.standalone_enhanced_report_generator import EnhancedReportGenerator


class TestReportGenerationSystem(unittest.TestCase):
    """报告生成系统测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "reports"
        self.output_dir.mkdir(exist_ok=True)
        
        # 创建基础生成器
        self.basic_generator = ReportGenerator()
        self.basic_generator.output_dir = self.output_dir
        
        # 创建增强生成器
        self.enhanced_generator = EnhancedReportGenerator()
        self.enhanced_generator.output_dir = self.output_dir
        self.enhanced_generator.chart_temp_dir = Path(self.temp_dir) / "charts"
        self.enhanced_generator.chart_temp_dir.mkdir(exist_ok=True)
        
        # 准备测试数据
        self.sample_hole_data = {
            'total_holes': 100,
            'current_hole_id': 'H025',
            'checked_holes': 95,
            'qualified_holes': 92,
            'unqualified_holes': 3
        }
        
        self.sample_workpiece_info = {
            'model': 'CP1400',
            'serial': 'SN-SYSTEM-TEST-001',
            'operator': '系统测试用户',
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
        self.sample_measurement_data = [
            {'depth': i * 0.5, 'diameter': 17.6 + (0.01 * (i % 10) - 0.005)}
            for i in range(500)
        ]
        
        # 添加一些超差点用于测试
        self.sample_measurement_data.extend([
            {'depth': 250, 'diameter': 17.75},  # 超上限
            {'depth': 255, 'diameter': 16.85},  # 超下限
        ])
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_basic_report_generation_system(self):
        """测试基础报告生成系统"""
        print("\n=== 测试基础报告生成系统 ===")
        
        # 1. 测试数据准备
        report_data = self.basic_generator._prepare_report_data(
            self.sample_hole_data, self.sample_workpiece_info
        )
        
        self.assertIsInstance(report_data, ReportData)
        self.assertIn("REP-CP1400", report_data.report_id)
        self.assertEqual(report_data.workpiece_model, "CP1400")
        
        # 2. 测试CSV导出
        csv_path = self.basic_generator.export_raw_data_csv(
            self.sample_hole_data, self.sample_workpiece_info
        )
        
        self.assertTrue(os.path.exists(csv_path))
        self.assertTrue(csv_path.endswith('.csv'))
        
        # 验证CSV内容
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            self.assertIn('孔位ID', content)
            self.assertIn('最小直径(mm)', content)
            
        csv_size = os.path.getsize(csv_path)
        self.assertGreater(csv_size, 100)
        
        # 3. 测试Web报告数据生成
        web_data = self.basic_generator.generate_web_report_data(
            self.sample_hole_data, self.sample_workpiece_info
        )
        
        self.assertIsInstance(web_data, dict)
        required_keys = ['header', 'summary', 'non_conformities', 'charts', 'images', 'full_data']
        for key in required_keys:
            self.assertIn(key, web_data)
            
        # 验证Web数据可序列化
        json_str = json.dumps(web_data, default=str)
        reloaded_data = json.loads(json_str)
        self.assertEqual(reloaded_data['header']['workpiece_model'], 'CP1400')
        
        print("✅ 基础报告生成系统测试通过")
        
    def test_enhanced_report_generation_system(self):
        """测试增强报告生成系统"""
        print("\n=== 测试增强报告生成系统 ===")
        
        # 1. 测试包络图生成
        envelope_chart = self.enhanced_generator.generate_envelope_chart_with_annotations(
            self.sample_measurement_data, 17.6, 0.05, 0.07, "H025"
        )
        
        self.assertTrue(os.path.exists(envelope_chart))
        self.assertTrue(envelope_chart.endswith('.png'))
        
        envelope_size = os.path.getsize(envelope_chart)
        self.assertGreater(envelope_size, 5000)  # 高质量图表应该较大
        
        # 2. 测试统计图表生成
        stats_chart = self.enhanced_generator._generate_statistics_chart(
            self.sample_measurement_data
        )
        
        self.assertTrue(os.path.exists(stats_chart))
        stats_size = os.path.getsize(stats_chart)
        self.assertGreater(stats_size, 3000)
        
        # 3. 测试内窥镜占位符图像生成
        endoscope_image = self.enhanced_generator._generate_placeholder_endoscope_image("H025")
        
        self.assertTrue(os.path.exists(endoscope_image))
        endoscope_size = os.path.getsize(endoscope_image)
        self.assertGreater(endoscope_size, 1000)
        
        # 4. 测试增强报告数据准备
        enhanced_data = self.enhanced_generator._prepare_enhanced_report_data(
            self.sample_hole_data, self.sample_workpiece_info,
            self.sample_measurement_data, []
        )
        
        self.assertIn('envelope', enhanced_data.charts)
        self.assertTrue(os.path.exists(enhanced_data.charts['envelope']))
        
        print("✅ 增强报告生成系统测试通过")
        
    def test_multi_threaded_report_generation(self):
        """测试多线程报告生成"""
        print("\n=== 测试多线程报告生成 ===")
        
        # 创建线程信号收集器
        results = []
        errors = []
        progress_updates = []
        
        def collect_results(report_type, file_path):
            results.append((report_type, file_path))
            
        def collect_errors(report_type, error_msg):
            errors.append((report_type, error_msg))
            
        def collect_progress(progress):
            progress_updates.append(progress)
        
        # 创建多个报告生成线程
        threads = []
        
        # CSV导出线程
        csv_thread = ReportGenerationThread(
            self.basic_generator, "CSV", 
            self.sample_hole_data, self.sample_workpiece_info
        )
        csv_thread.generation_completed.connect(collect_results)
        csv_thread.generation_failed.connect(collect_errors)
        csv_thread.progress_updated.connect(collect_progress)
        threads.append(csv_thread)
        
        # Web报告线程
        web_thread = ReportGenerationThread(
            self.basic_generator, "WEB",
            self.sample_hole_data, self.sample_workpiece_info
        )
        web_thread.generation_completed.connect(collect_results)
        web_thread.generation_failed.connect(collect_errors)
        web_thread.progress_updated.connect(collect_progress)
        threads.append(web_thread)
        
        # 启动所有线程
        for thread in threads:
            thread.start()
            
        # 等待所有线程完成
        for thread in threads:
            thread.wait(timeout=10000)  # 10秒超时
            
        # 验证结果
        self.assertEqual(len(results), 2)  # 应该有2个成功的结果
        self.assertEqual(len(errors), 0)   # 应该没有错误
        self.assertGreater(len(progress_updates), 0)  # 应该有进度更新
        
        # 验证文件生成
        for report_type, file_path in results:
            self.assertTrue(os.path.exists(file_path))
            self.assertGreater(os.path.getsize(file_path), 0)
            
        print(f"✅ 多线程报告生成测试通过 - 生成了{len(results)}个报告")
        
    def test_comprehensive_report_workflow(self):
        """测试综合报告工作流程"""
        print("\n=== 测试综合报告工作流程 ===")
        
        # 1. 数据验证阶段
        self.assertIsNotNone(self.sample_hole_data)
        self.assertIsNotNone(self.sample_workpiece_info)
        self.assertIsNotNone(self.sample_measurement_data)
        
        # 2. 图表生成阶段
        envelope_chart = self.enhanced_generator.generate_envelope_chart_with_annotations(
            self.sample_measurement_data, 17.6, 0.05, 0.07, "H025"
        )
        
        stats_chart = self.enhanced_generator._generate_statistics_chart(
            self.sample_measurement_data
        )
        
        endoscope_image = self.enhanced_generator._generate_placeholder_endoscope_image("H025")
        
        # 验证图表生成
        chart_files = [envelope_chart, stats_chart, endoscope_image]
        for chart_file in chart_files:
            self.assertTrue(os.path.exists(chart_file))
            self.assertGreater(os.path.getsize(chart_file), 500)
            
        # 3. 数据导出阶段
        csv_path = self.basic_generator.export_raw_data_csv(
            self.sample_hole_data, self.sample_workpiece_info
        )
        
        web_data = self.basic_generator.generate_web_report_data(
            self.sample_hole_data, self.sample_workpiece_info
        )
        
        # 保存Web数据
        web_path = self.output_dir / f"web_report_{int(time.time())}.json"
        with open(web_path, 'w', encoding='utf-8') as f:
            json.dump(web_data, f, ensure_ascii=False, indent=2, default=str)
            
        # 验证数据导出
        self.assertTrue(os.path.exists(csv_path))
        self.assertTrue(os.path.exists(web_path))
        
        csv_size = os.path.getsize(csv_path)
        web_size = os.path.getsize(web_path)
        
        self.assertGreater(csv_size, 100)
        self.assertGreater(web_size, 500)
        
        # 4. 质量检查阶段
        # 验证CSV格式
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            csv_content = f.read()
            self.assertIn('孔位ID', csv_content)
            self.assertIn('最小直径(mm)', csv_content)
            self.assertIn('最大直径(mm)', csv_content)
            
        # 验证Web数据格式
        with open(web_path, 'r', encoding='utf-8') as f:
            reloaded_web_data = json.load(f)
            self.assertEqual(reloaded_web_data['header']['workpiece_model'], 'CP1400')
            self.assertEqual(reloaded_web_data['header']['workpiece_serial'], 'SN-SYSTEM-TEST-001')
            
        # 5. 报告汇总
        total_files_generated = len(chart_files) + 2  # 图表 + CSV + Web
        generated_files = [envelope_chart, stats_chart, endoscope_image, csv_path, str(web_path)]
        
        total_size = sum(os.path.getsize(f) for f in generated_files)
        
        print(f"✅ 综合报告工作流程测试完成")
        print(f"   生成文件数: {total_files_generated}")
        print(f"   总文件大小: {total_size / 1024:.1f} KB")
        print(f"   图表文件: {len(chart_files)}")
        print(f"   数据文件: 2 (CSV + Web)")
        
    def test_error_handling_and_recovery(self):
        """测试错误处理和恢复"""
        print("\n=== 测试错误处理和恢复 ===")
        
        # 1. 测试无效数据处理
        invalid_hole_data = {}
        invalid_workpiece_info = {}
        
        try:
            csv_path = self.basic_generator.export_raw_data_csv(
                invalid_hole_data, invalid_workpiece_info
            )
            # 即使数据无效，也应该能生成基本的CSV文件
            self.assertTrue(os.path.exists(csv_path))
        except Exception as e:
            # 或者应该有合适的错误处理
            self.assertIsInstance(e, (ValueError, KeyError))
            
        # 2. 测试空测量数据处理
        empty_measurement_data = []
        envelope_chart = self.enhanced_generator.generate_envelope_chart_with_annotations(
            empty_measurement_data, 17.6, 0.05, 0.07, "H_ERROR_TEST"
        )
        
        # 应该生成演示数据的图表
        self.assertTrue(os.path.exists(envelope_chart))
        
        # 3. 测试不存在的内窥镜图像处理
        non_existent_images = ["/non/existent/path1.png", "/non/existent/path2.png"]
        panorama = self.enhanced_generator.generate_endoscope_panorama(
            non_existent_images, "H_ERROR_TEST"
        )
        
        # 应该生成占位符图像
        self.assertTrue(os.path.exists(panorama))
        
        # 4. 测试线程错误处理
        error_results = []
        
        def collect_thread_errors(report_type, error_msg):
            error_results.append((report_type, error_msg))
            
        # 使用无效报告类型创建线程
        invalid_thread = ReportGenerationThread(
            self.basic_generator, "INVALID_TYPE",
            self.sample_hole_data, self.sample_workpiece_info
        )
        invalid_thread.generation_failed.connect(collect_thread_errors)
        
        invalid_thread.run()  # 直接运行而不是start()
        
        # 验证错误被正确捕获
        self.assertEqual(len(error_results), 1)
        self.assertEqual(error_results[0][0], "INVALID_TYPE")
        self.assertIn("不支持的报告类型", error_results[0][1])
        
        print("✅ 错误处理和恢复测试通过")
        
    def test_performance_and_scalability(self):
        """测试性能和可扩展性"""
        print("\n=== 测试性能和可扩展性 ===")
        
        # 1. 测试大数据量处理
        large_measurement_data = [
            {'depth': i * 0.1, 'diameter': 17.6 + 0.01 * (i % 20 - 10) / 10}
            for i in range(10000)  # 10000个测量点
        ]
        
        start_time = time.time()
        
        # 生成包络图
        envelope_chart = self.enhanced_generator.generate_envelope_chart_with_annotations(
            large_measurement_data, 17.6, 0.05, 0.07, "H_PERFORMANCE_TEST"
        )
        
        envelope_time = time.time() - start_time
        
        self.assertTrue(os.path.exists(envelope_chart))
        self.assertLess(envelope_time, 30)  # 应该在30秒内完成
        
        # 2. 测试统计计算性能
        start_time = time.time()
        
        diameters = [d['diameter'] for d in large_measurement_data]
        stats_text = self.enhanced_generator._generate_statistics_text(
            diameters, 17.6, 0.05, 0.07
        )
        
        stats_time = time.time() - start_time
        
        self.assertIn('测量点数: 10000', stats_text)
        self.assertLess(stats_time, 5)  # 统计计算应该很快
        
        # 3. 测试并发报告生成
        start_time = time.time()
        
        concurrent_results = []
        
        def collect_concurrent_results(report_type, file_path):
            concurrent_results.append((report_type, file_path, time.time()))
            
        # 创建多个并发线程
        concurrent_threads = []
        
        for i in range(3):
            thread_data = {
                'total_holes': 50 + i * 10,
                'current_hole_id': f'H{i:03d}'
            }
            
            thread_info = {
                'model': f'CP{1400 + i}',
                'serial': f'SN-CONCURRENT-{i:03d}',
                'operator': f'并发测试用户{i}'
            }
            
            thread = ReportGenerationThread(
                self.basic_generator, "CSV", thread_data, thread_info
            )
            thread.generation_completed.connect(collect_concurrent_results)
            concurrent_threads.append(thread)
            
        # 启动所有并发线程
        for thread in concurrent_threads:
            thread.start()
            
        # 等待完成
        for thread in concurrent_threads:
            thread.wait(timeout=15000)  # 15秒超时
            
        concurrent_time = time.time() - start_time
        
        # 验证并发结果
        self.assertEqual(len(concurrent_results), 3)
        self.assertLess(concurrent_time, 20)  # 并发应该比串行快
        
        # 验证文件生成
        for report_type, file_path, completion_time in concurrent_results:
            self.assertTrue(os.path.exists(file_path))
            
        print(f"✅ 性能和可扩展性测试通过")
        print(f"   大数据包络图生成时间: {envelope_time:.2f}秒")
        print(f"   统计计算时间: {stats_time:.3f}秒")
        print(f"   并发报告生成时间: {concurrent_time:.2f}秒")
        
    def test_system_integration_with_dependencies(self):
        """测试系统集成和依赖"""
        print("\n=== 测试系统集成和依赖 ===")
        
        # 1. 测试matplotlib依赖
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # 创建简单图表测试
            fig, ax = plt.subplots(figsize=(8, 6))
            x = np.linspace(0, 10, 100)
            y = np.sin(x)
            ax.plot(x, y)
            
            test_chart_path = self.enhanced_generator.chart_temp_dir / "dependency_test.png"
            plt.savefig(test_chart_path, dpi=300)
            plt.close()
            
            self.assertTrue(test_chart_path.exists())
            matplotlib_available = True
            
        except ImportError:
            matplotlib_available = False
            
        # 2. 测试PIL依赖
        try:
            from PIL import Image, ImageDraw
            
            # 创建简单图像测试
            test_img = Image.new('RGB', (200, 200), 'white')
            draw = ImageDraw.Draw(test_img)
            draw.rectangle([(50, 50), (150, 150)], outline='black', width=2)
            
            test_img_path = self.enhanced_generator.chart_temp_dir / "pil_test.png"
            test_img.save(test_img_path, 'PNG')
            
            self.assertTrue(test_img_path.exists())
            pil_available = True
            
        except ImportError:
            pil_available = False
            
        # 3. 测试reportlab依赖检查
        try:
            from modules.report_generator import REPORTLAB_AVAILABLE
            reportlab_status = REPORTLAB_AVAILABLE
        except:
            reportlab_status = False
            
        # 4. 测试openpyxl依赖检查
        try:
            from modules.report_generator import OPENPYXL_AVAILABLE
            openpyxl_status = OPENPYXL_AVAILABLE
        except:
            openpyxl_status = False
            
        # 验证系统能在依赖缺失的情况下优雅降级
        if not matplotlib_available:
            print("⚠️ matplotlib不可用，图表生成将受限")
        if not pil_available:
            print("⚠️ PIL不可用，图像处理将受限")
        if not reportlab_status:
            print("⚠️ reportlab不可用，PDF生成将受限")
        if not openpyxl_status:
            print("⚠️ openpyxl不可用，Excel导出将受限")
            
        # 系统应该至少能生成CSV报告
        csv_path = self.basic_generator.export_raw_data_csv(
            self.sample_hole_data, self.sample_workpiece_info
        )
        self.assertTrue(os.path.exists(csv_path))
        
        print(f"✅ 系统集成和依赖测试完成")
        print(f"   matplotlib: {'✅' if matplotlib_available else '❌'}")
        print(f"   PIL: {'✅' if pil_available else '❌'}")
        print(f"   reportlab: {'✅' if reportlab_status else '❌'}")
        print(f"   openpyxl: {'✅' if openpyxl_status else '❌'}")


def run_system_tests():
    """运行系统测试"""
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestReportGenerationSystem,
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 80)
    print("报告生成系统测试")
    print("=" * 80)
    
    success = run_system_tests()
    
    if success:
        print("\n✅ 所有系统测试通过")
    else:
        print("\n❌ 部分系统测试失败")
        
    exit(0 if success else 1)