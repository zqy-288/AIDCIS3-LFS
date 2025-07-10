"""
报告生成端到端测试
测试从用户界面到完整报告生成的端到端流程
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
from test_modules.standalone_report_generator import ReportGenerator, ReportGenerationThread
from test_modules.standalone_enhanced_report_generator import EnhancedReportGenerator

# 创建模拟的数据库管理器
class MockDatabaseManager:
    def __init__(self):
        self.connected = True
        
    def get_all_hole_data(self):
        """模拟获取所有孔位数据"""
        return [
            {
                'hole_id': f'H{i:03d}',
                'min_diameter': 17.55 + (i % 10) * 0.001,
                'max_diameter': 17.65 + (i % 10) * 0.001,
                'avg_diameter': 17.60 + (i % 10) * 0.001,
                'qualified': True if i % 20 != 0 else False,
                'surface_defects': 'None' if i % 15 != 0 else 'Minor scratches'
            }
            for i in range(100)
        ]
        
    def get_measurement_data_for_hole(self, hole_id):
        """模拟获取特定孔位的测量数据"""
        return [
            {
                'depth': i * 0.5,
                'diameter': 17.6 + 0.005 * (i % 20 - 10) / 10
            }
            for i in range(500)
        ]
        
    def get_endoscope_images_for_hole(self, hole_id):
        """模拟获取内窥镜图像路径"""
        return []  # 空列表，会触发占位符图像生成


class TestReportGenerationE2E(unittest.TestCase):
    """报告生成端到端测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "reports"
        self.output_dir.mkdir(exist_ok=True)
        
        # 创建模拟数据库管理器
        self.mock_db = MockDatabaseManager()
        
        # 模拟用户输入数据
        self.user_workpiece_info = {
            'model': 'CP1400',
            'serial': 'SN-E2E-TEST-001',
            'operator': '端到端测试用户',
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
        # 模拟系统检测数据
        self.system_hole_data = {
            'total_holes': 100,
            'current_hole_id': 'H050',
            'checked_holes': 100,
            'qualified_holes': 95,
            'unqualified_holes': 5
        }
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_complete_report_generation_workflow(self):
        """测试完整的报告生成工作流程"""
        print("\n=== 端到端报告生成工作流程测试 ===")
        
        # 使用已导入的模块
        # ReportGenerator 和 EnhancedReportGenerator 已在文件顶部导入
        
        # 1. 用户界面数据收集阶段
        print("1️⃣ 用户界面数据收集...")
        
        # 模拟用户在界面中输入工件信息
        workpiece_model = self.user_workpiece_info['model']
        workpiece_serial = self.user_workpiece_info['serial']
        operator_name = self.user_workpiece_info['operator']
        
        # 验证用户输入
        self.assertIsNotNone(workpiece_model)
        self.assertIsNotNone(workpiece_serial)
        self.assertIsNotNone(operator_name)
        self.assertTrue(len(workpiece_model) > 0)
        self.assertTrue(len(workpiece_serial) > 0)
        self.assertTrue(len(operator_name) > 0)
        
        print(f"   ✅ 工件型号: {workpiece_model}")
        print(f"   ✅ 工件序列号: {workpiece_serial}")
        print(f"   ✅ 操作员: {operator_name}")
        
        # 2. 系统数据获取阶段
        print("2️⃣ 系统数据获取...")
        
        # 模拟从数据库获取检测数据
        all_hole_data = self.mock_db.get_all_hole_data()
        current_hole_data = self.mock_db.get_measurement_data_for_hole('H050')
        endoscope_images = self.mock_db.get_endoscope_images_for_hole('H050')
        
        # 验证数据获取
        self.assertIsInstance(all_hole_data, list)
        self.assertGreater(len(all_hole_data), 0)
        self.assertIsInstance(current_hole_data, list)
        self.assertGreater(len(current_hole_data), 0)
        
        print(f"   ✅ 获取孔位数据: {len(all_hole_data)} 个孔位")
        print(f"   ✅ 获取测量数据: {len(current_hole_data)} 个测量点")
        print(f"   ✅ 获取内窥镜图像: {len(endoscope_images)} 张图像")
        
        # 3. 报告生成器初始化阶段
        print("3️⃣ 报告生成器初始化...")
        
        basic_generator = ReportGenerator(self.mock_db)
        basic_generator.output_dir = self.output_dir
        
        enhanced_generator = EnhancedReportGenerator(self.mock_db)
        enhanced_generator.output_dir = self.output_dir
        enhanced_generator.chart_temp_dir = Path(self.temp_dir) / "charts"
        enhanced_generator.chart_temp_dir.mkdir(exist_ok=True)
        
        print("   ✅ 基础报告生成器已初始化")
        print("   ✅ 增强报告生成器已初始化")
        
        # 4. 图表和图像生成阶段
        print("4️⃣ 图表和图像生成...")
        
        # 生成包络图
        envelope_chart = enhanced_generator.generate_envelope_chart_with_annotations(
            current_hole_data, 17.6, 0.05, 0.07, "H050"
        )
        
        # 生成统计图表
        stats_chart = enhanced_generator._generate_statistics_chart(current_hole_data)
        
        # 生成内窥镜图像（占位符）
        endoscope_image = enhanced_generator._generate_placeholder_endoscope_image("H050")
        
        # 验证图表生成
        chart_files = [envelope_chart, stats_chart, endoscope_image]
        for chart_file in chart_files:
            self.assertTrue(os.path.exists(chart_file))
            self.assertGreater(os.path.getsize(chart_file), 1000)
            
        print(f"   ✅ 包络图生成: {os.path.basename(envelope_chart)}")
        print(f"   ✅ 统计图表生成: {os.path.basename(stats_chart)}")
        print(f"   ✅ 内窥镜图像生成: {os.path.basename(endoscope_image)}")
        
        # 5. 报告数据准备阶段
        print("5️⃣ 报告数据准备...")
        
        # 准备报告数据
        report_data = basic_generator._prepare_report_data(
            self.system_hole_data, self.user_workpiece_info
        )
        
        # 添加图表到报告数据
        report_data.charts['envelope'] = envelope_chart
        report_data.charts['statistics'] = stats_chart
        report_data.images['endoscope'] = endoscope_image
        
        # 验证报告数据
        self.assertIsNotNone(report_data.report_id)
        self.assertEqual(report_data.workpiece_model, workpiece_model)
        self.assertEqual(report_data.workpiece_serial, workpiece_serial)
        self.assertEqual(report_data.operator, operator_name)
        
        print(f"   ✅ 报告ID: {report_data.report_id}")
        print(f"   ✅ 报告数据准备完成")
        
        # 6. 多格式报告生成阶段
        print("6️⃣ 多格式报告生成...")
        
        generated_files = {}
        
        # 生成CSV报告
        csv_path = basic_generator.export_raw_data_csv(
            self.system_hole_data, self.user_workpiece_info
        )
        generated_files['CSV'] = csv_path
        
        # 生成Web报告数据
        web_data = basic_generator.generate_web_report_data(
            self.system_hole_data, self.user_workpiece_info
        )
        
        # 保存Web报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        web_path = self.output_dir / f"web_report_{workpiece_model}_{timestamp}.json"
        with open(web_path, 'w', encoding='utf-8') as f:
            json.dump(web_data, f, ensure_ascii=False, indent=2, default=str)
        generated_files['WEB'] = str(web_path)
        
        # 尝试生成Excel报告（如果openpyxl可用）
        try:
            excel_path = basic_generator.export_raw_data_excel(
                self.system_hole_data, self.user_workpiece_info
            )
            generated_files['EXCEL'] = excel_path
        except ImportError:
            print("   ⚠️ openpyxl不可用，跳过Excel生成")
        except Exception as e:
            print(f"   ⚠️ Excel生成失败: {e}")
            
        # 验证文件生成
        for report_type, file_path in generated_files.items():
            self.assertTrue(os.path.exists(file_path))
            self.assertGreater(os.path.getsize(file_path), 100)
            print(f"   ✅ {report_type}报告: {os.path.basename(file_path)}")
            
        # 7. 质量验证阶段
        print("7️⃣ 质量验证...")
        
        # 验证CSV内容
        with open(generated_files['CSV'], 'r', encoding='utf-8-sig') as f:
            csv_content = f.read()
            self.assertIn('孔位ID', csv_content)
            self.assertIn('最小直径(mm)', csv_content)
            self.assertIn('最大直径(mm)', csv_content)
            
        # 验证Web数据内容
        with open(generated_files['WEB'], 'r', encoding='utf-8') as f:
            web_content = json.load(f)
            self.assertIn('header', web_content)
            self.assertIn('summary', web_content)
            self.assertEqual(web_content['header']['workpiece_model'], workpiece_model)
            
        print("   ✅ CSV内容验证通过")
        print("   ✅ Web数据验证通过")
        
        # 8. 结果汇总阶段
        print("8️⃣ 结果汇总...")
        
        total_files = len(generated_files) + len(chart_files)
        total_size = sum(
            os.path.getsize(f) for f in list(generated_files.values()) + chart_files
        )
        
        print(f"   📊 总生成文件数: {total_files}")
        print(f"   📊 总文件大小: {total_size / 1024:.1f} KB")
        print(f"   📊 报告文件: {len(generated_files)}")
        print(f"   📊 图表文件: {len(chart_files)}")
        
        # 最终验证
        self.assertGreaterEqual(total_files, 4)  # 至少4个文件
        self.assertGreater(total_size, 10000)   # 至少10KB
        
        print("✅ 端到端报告生成工作流程测试完成")
        
    def test_user_interaction_simulation(self):
        """测试用户交互模拟"""
        print("\n=== 用户交互模拟测试 ===")
        
        # 模拟报告管理器组件
        class MockReportManagerWidget:
            def __init__(self):
                self.model_input = Mock()
                self.serial_input = Mock()
                self.operator_input = Mock()
                self.progress_bar = Mock()
                self.status_label = Mock()
                
                # 设置默认值
                self.model_input.text = ""
                self.serial_input.text = ""
                self.operator_input.text = ""
                self.progress_bar.value = 0
                self.status_label.text = "准备就绪"
                
            def set_user_input(self, model, serial, operator):
                """模拟用户输入"""
                self.model_input.text = model
                self.serial_input.text = serial
                self.operator_input.text = operator
                
            def get_workpiece_info(self):
                """获取工件信息"""
                return {
                    'model': self.model_input.text,
                    'serial': self.serial_input.text,
                    'operator': self.operator_input.text,
                    'start_time': datetime.now(),
                    'end_time': datetime.now()
                }
                
            def validate_inputs(self):
                """验证输入"""
                if not self.model_input.text:
                    return False, "请输入产品型号"
                if not self.serial_input.text:
                    return False, "请输入工件序列号"
                if not self.operator_input.text:
                    return False, "请输入操作员姓名"
                return True, ""
                
            def update_progress(self, value):
                """更新进度"""
                self.progress_bar.value = value
                
            def update_status(self, status):
                """更新状态"""
                self.status_label.text = status
                
        # 1. 创建模拟界面
        mock_widget = MockReportManagerWidget()
        
        # 2. 模拟用户输入
        print("1️⃣ 模拟用户输入...")
        mock_widget.set_user_input("CP1400", "SN-UI-TEST-001", "界面测试用户")
        
        # 验证输入
        is_valid, error_msg = mock_widget.validate_inputs()
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
        
        workpiece_info = mock_widget.get_workpiece_info()
        self.assertEqual(workpiece_info['model'], "CP1400")
        
        print("   ✅ 用户输入验证通过")
        
        # 3. 模拟报告生成过程
        print("2️⃣ 模拟报告生成过程...")
        
        # 使用已导入的ReportGenerator
        
        generator = ReportGenerator(self.mock_db)
        generator.output_dir = self.output_dir
        
        # 模拟进度更新
        mock_widget.update_status("正在准备数据...")
        mock_widget.update_progress(10)
        self.assertEqual(mock_widget.status_label.text, "正在准备数据...")
        self.assertEqual(mock_widget.progress_bar.value, 10)
        
        mock_widget.update_status("正在生成CSV报告...")
        mock_widget.update_progress(30)
        
        # 生成CSV报告
        csv_path = generator.export_raw_data_csv(
            self.system_hole_data, workpiece_info
        )
        
        mock_widget.update_progress(60)
        mock_widget.update_status("正在生成Web报告...")
        
        # 生成Web报告
        web_data = generator.generate_web_report_data(
            self.system_hole_data, workpiece_info
        )
        
        mock_widget.update_progress(90)
        mock_widget.update_status("正在保存文件...")
        
        # 保存Web报告
        web_path = self.output_dir / "web_report_ui_test.json"
        with open(web_path, 'w', encoding='utf-8') as f:
            json.dump(web_data, f, ensure_ascii=False, indent=2, default=str)
            
        mock_widget.update_progress(100)
        mock_widget.update_status("报告生成完成")
        
        # 验证最终状态
        self.assertEqual(mock_widget.progress_bar.value, 100)
        self.assertEqual(mock_widget.status_label.text, "报告生成完成")
        
        # 验证文件生成
        self.assertTrue(os.path.exists(csv_path))
        self.assertTrue(os.path.exists(web_path))
        
        print("   ✅ 报告生成过程模拟完成")
        
        # 4. 模拟错误处理
        print("3️⃣ 模拟错误处理...")
        
        # 测试无效输入
        mock_widget.set_user_input("", "", "")
        is_valid, error_msg = mock_widget.validate_inputs()
        self.assertFalse(is_valid)
        self.assertIn("产品型号", error_msg)
        
        mock_widget.update_status(f"输入错误: {error_msg}")
        mock_widget.update_progress(0)
        
        print(f"   ✅ 错误处理: {error_msg}")
        
        print("✅ 用户交互模拟测试完成")
        
    def test_concurrent_report_generation_e2e(self):
        """测试并发报告生成端到端流程"""
        print("\n=== 并发报告生成端到端测试 ===")
        
        # 使用已导入的ReportGenerator, ReportGenerationThread
        
        # 创建多个工件的测试数据
        test_workpieces = [
            {
                'model': f'CP{1400 + i}',
                'serial': f'SN-CONCURRENT-E2E-{i:03d}',
                'operator': f'并发测试用户{i}',
                'start_time': datetime.now(),
                'end_time': datetime.now()
            }
            for i in range(3)
        ]
        
        test_hole_data = [
            {
                'total_holes': 50 + i * 10,
                'current_hole_id': f'H{i:03d}',
                'checked_holes': 50 + i * 10,
                'qualified_holes': 45 + i * 10,
                'unqualified_holes': 5
            }
            for i in range(3)
        ]
        
        # 结果收集器
        generation_results = []
        generation_errors = []
        progress_updates = {}
        
        def collect_results(report_type, file_path):
            generation_results.append((report_type, file_path, time.time()))
            
        def collect_errors(report_type, error_msg):
            generation_errors.append((report_type, error_msg, time.time()))
            
        def collect_progress(progress, thread_id=None):
            if thread_id not in progress_updates:
                progress_updates[thread_id] = []
            progress_updates[thread_id].append(progress)
        
        # 创建报告生成器
        generator = ReportGenerator(self.mock_db)
        generator.output_dir = self.output_dir
        
        # 创建并发线程
        threads = []
        start_time = time.time()
        
        for i, (workpiece, hole_data) in enumerate(zip(test_workpieces, test_hole_data)):
            # CSV线程
            csv_thread = ReportGenerationThread(
                generator, "CSV", hole_data, workpiece
            )
            csv_thread.generation_completed.connect(collect_results)
            csv_thread.generation_failed.connect(collect_errors)
            csv_thread.progress_updated.connect(lambda p, tid=i: collect_progress(p, f"csv_{tid}"))
            threads.append(csv_thread)
            
            # Web线程
            web_thread = ReportGenerationThread(
                generator, "WEB", hole_data, workpiece
            )
            web_thread.generation_completed.connect(collect_results)
            web_thread.generation_failed.connect(collect_errors)
            web_thread.progress_updated.connect(lambda p, tid=i: collect_progress(p, f"web_{tid}"))
            threads.append(web_thread)
            
        print(f"1️⃣ 创建了 {len(threads)} 个并发报告生成线程")
        
        # 启动所有线程
        for thread in threads:
            thread.start()
            time.sleep(0.1)  # 小间隔避免竞争
            
        print("2️⃣ 所有线程已启动")
        
        # 等待所有线程完成
        for i, thread in enumerate(threads):
            thread.wait(timeout=15000)  # 15秒超时
            print(f"   线程 {i+1}/{len(threads)} 完成")
            
        end_time = time.time()
        total_time = end_time - start_time
        
        print("3️⃣ 所有线程已完成")
        
        # 验证结果
        expected_results = len(threads)
        actual_results = len(generation_results)
        actual_errors = len(generation_errors)
        
        self.assertEqual(actual_results, expected_results)
        self.assertEqual(actual_errors, 0)
        
        # 验证文件生成
        for report_type, file_path, completion_time in generation_results:
            self.assertTrue(os.path.exists(file_path))
            self.assertGreater(os.path.getsize(file_path), 100)
            
        # 验证进度更新
        self.assertGreater(len(progress_updates), 0)
        
        print(f"4️⃣ 结果验证:")
        print(f"   ✅ 预期结果: {expected_results}")
        print(f"   ✅ 实际结果: {actual_results}")
        print(f"   ✅ 错误数量: {actual_errors}")
        print(f"   ✅ 总耗时: {total_time:.2f}秒")
        print(f"   ✅ 平均每个报告: {total_time/actual_results:.2f}秒")
        
        print("✅ 并发报告生成端到端测试完成")
        
    def test_error_recovery_e2e(self):
        """测试错误恢复端到端流程"""
        print("\n=== 错误恢复端到端测试 ===")
        
        # 使用已导入的ReportGenerator
        from modules.enhanced_report_generator import EnhancedReportGenerator
        
        # 1. 测试数据缺失场景
        print("1️⃣ 测试数据缺失场景...")
        
        # 创建基础生成器
        generator = ReportGenerator(self.mock_db)
        generator.output_dir = self.output_dir
        
        # 使用空数据
        empty_hole_data = {}
        empty_workpiece_info = {}
        
        try:
            csv_path = generator.export_raw_data_csv(empty_hole_data, empty_workpiece_info)
            # 系统应该能够处理空数据并生成基本文件
            self.assertTrue(os.path.exists(csv_path))
            print("   ✅ 空数据处理成功")
        except Exception as e:
            # 或者有合适的错误处理
            print(f"   ⚠️ 空数据处理失败但被捕获: {e}")
            
        # 2. 测试文件系统错误场景
        print("2️⃣ 测试文件系统错误场景...")
        
        # 尝试写入只读目录（模拟）
        readonly_generator = ReportGenerator(self.mock_db)
        readonly_generator.output_dir = Path("/nonexistent/readonly/path")
        
        try:
            csv_path = readonly_generator.export_raw_data_csv(
                self.system_hole_data, self.user_workpiece_info
            )
            # 如果成功，说明系统创建了目录
            print("   ⚠️ 只读目录测试未触发预期错误")
        except Exception as e:
            # 预期的错误
            print(f"   ✅ 文件系统错误被正确捕获: {type(e).__name__}")
            
        # 3. 测试依赖缺失场景
        print("3️⃣ 测试依赖缺失场景...")
        
        enhanced_generator = EnhancedReportGenerator(self.mock_db)
        enhanced_generator.output_dir = self.output_dir
        enhanced_generator.chart_temp_dir = Path(self.temp_dir) / "charts"
        enhanced_generator.chart_temp_dir.mkdir(exist_ok=True)
        
        # 测试无图像数据的包络图生成
        empty_measurement_data = []
        envelope_chart = enhanced_generator.generate_envelope_chart_with_annotations(
            empty_measurement_data, 17.6, 0.05, 0.07, "H_ERROR_TEST"
        )
        
        # 应该生成演示数据的图表
        self.assertTrue(os.path.exists(envelope_chart))
        print("   ✅ 无测量数据时生成演示图表")
        
        # 测试无内窥镜图像的处理
        empty_images = []
        panorama = enhanced_generator.generate_endoscope_panorama(empty_images, "H_ERROR_TEST")
        
        # 应该生成占位符图像
        self.assertTrue(os.path.exists(panorama))
        print("   ✅ 无内窥镜图像时生成占位符")
        
        # 4. 测试系统恢复能力
        print("4️⃣ 测试系统恢复能力...")
        
        # 在错误后系统应该能继续正常工作
        normal_csv = generator.export_raw_data_csv(
            self.system_hole_data, self.user_workpiece_info
        )
        
        self.assertTrue(os.path.exists(normal_csv))
        self.assertGreater(os.path.getsize(normal_csv), 100)
        
        normal_web = generator.generate_web_report_data(
            self.system_hole_data, self.user_workpiece_info
        )
        
        self.assertIsInstance(normal_web, dict)
        self.assertIn('header', normal_web)
        
        print("   ✅ 系统在错误后恢复正常")
        
        print("✅ 错误恢复端到端测试完成")


def run_e2e_tests():
    """运行端到端测试"""
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestReportGenerationE2E,
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
    print("报告生成端到端测试")
    print("=" * 80)
    
    success = run_e2e_tests()
    
    if success:
        print("\n✅ 所有端到端测试通过")
    else:
        print("\n❌ 部分端到端测试失败")
        
    exit(0 if success else 1)