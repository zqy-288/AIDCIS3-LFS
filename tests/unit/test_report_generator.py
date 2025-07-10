"""
报告生成器单元测试
测试报告生成器的核心功能
"""

import unittest
import tempfile
import os
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# 使用独立的报告生成器避免PySide6依赖
from test_modules.standalone_report_generator import ReportGenerator, ReportData, ReportGenerationThread


class TestReportData(unittest.TestCase):
    """测试ReportData类"""
    
    def setUp(self):
        """测试前准备"""
        self.report_data = ReportData()
        
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.report_data.report_id, "")
        self.assertEqual(self.report_data.total_holes, 0)
        self.assertEqual(len(self.report_data.non_conformities), 0)
        self.assertEqual(len(self.report_data.all_data), 0)
        
    def test_add_non_conformity(self):
        """测试添加不合格项"""
        nc = {
            'hole_id': 'H001',
            'problem_type': '孔径超差',
            'measurement_result': '16.95mm',
            'evidence': {'chart': 'test.png'},
            'review_record': {'reviewer': '张工'}
        }
        
        self.report_data.add_non_conformity(**nc)
        
        self.assertEqual(len(self.report_data.non_conformities), 1)
        added_nc = self.report_data.non_conformities[0]
        self.assertEqual(added_nc['hole_id'], 'H001')
        self.assertEqual(added_nc['problem_type'], '孔径超差')
        
    def test_calculate_summary(self):
        """测试摘要计算"""
        # 添加测试数据
        self.report_data.all_data = [
            {'hole_id': 'H001', 'qualified': True},
            {'hole_id': 'H002', 'qualified': True},
            {'hole_id': 'H003', 'qualified': False},
        ]
        
        self.report_data.add_non_conformity(
            'H003', '孔径超差', '16.95mm', {}, {}
        )
        
        self.report_data.calculate_summary()
        
        self.assertEqual(self.report_data.checked_holes, 3)
        self.assertEqual(self.report_data.qualified_holes, 2)
        self.assertEqual(self.report_data.unqualified_holes, 1)
        self.assertAlmostEqual(self.report_data.qualification_rate, 66.67, places=1)
        self.assertEqual(self.report_data.overall_result, "不合格")


class TestReportGenerator(unittest.TestCase):
    """测试ReportGenerator类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = ReportGenerator()
        self.generator.output_dir = Path(self.temp_dir)
        
        # 模拟数据
        self.hole_data = {
            'total_holes': 100,
            'current_hole_id': 'H001'
        }
        
        self.workpiece_info = {
            'model': 'CP1400',
            'serial': 'SN-TEST-001',
            'operator': '测试用户',
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.generator.temp_dir)
        self.assertIsNotNone(self.generator.output_dir)
        self.assertEqual(self.generator.company_name, "数字化检测系统")
        
    def test_prepare_report_data(self):
        """测试报告数据准备"""
        report_data = self.generator._prepare_report_data(
            self.hole_data, self.workpiece_info
        )
        
        self.assertIsInstance(report_data, ReportData)
        self.assertIn("REP-CP1400", report_data.report_id)
        self.assertEqual(report_data.workpiece_model, "CP1400")
        self.assertEqual(report_data.workpiece_serial, "SN-TEST-001")
        self.assertEqual(report_data.operator, "测试用户")
        self.assertEqual(report_data.total_holes, 100)
        
    def test_generate_web_report_data(self):
        """测试Web报告数据生成"""
        web_data = self.generator.generate_web_report_data(
            self.hole_data, self.workpiece_info
        )
        
        self.assertIsInstance(web_data, dict)
        self.assertIn('header', web_data)
        self.assertIn('summary', web_data)
        self.assertIn('non_conformities', web_data)
        self.assertIn('charts', web_data)
        self.assertIn('images', web_data)
        self.assertIn('full_data', web_data)
        
        # 检查header内容
        header = web_data['header']
        self.assertEqual(header['workpiece_model'], 'CP1400')
        self.assertEqual(header['workpiece_serial'], 'SN-TEST-001')
        
    def test_export_raw_data_csv(self):
        """测试CSV数据导出"""
        csv_path = self.generator.export_raw_data_csv(
            self.hole_data, self.workpiece_info
        )
        
        self.assertTrue(os.path.exists(csv_path))
        self.assertTrue(csv_path.endswith('.csv'))
        
        # 检查CSV内容
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            self.assertIn('孔位ID', content)
            self.assertIn('最小直径(mm)', content)
            self.assertIn('最大直径(mm)', content)
            
    @patch('test_modules.standalone_report_generator.OPENPYXL_AVAILABLE', True)
    @patch('openpyxl.Workbook')
    def test_export_raw_data_excel_success(self, mock_workbook):
        """测试Excel数据导出成功情况"""
        # 模拟openpyxl工作簿
        mock_wb = Mock()
        mock_ws = Mock()
        mock_wb.active = mock_ws
        mock_wb.create_sheet.return_value = mock_ws
        mock_workbook.return_value = mock_wb
        
        excel_path = self.generator.export_raw_data_excel(
            self.hole_data, self.workpiece_info
        )
        
        self.assertIsNotNone(excel_path)
        self.assertTrue(excel_path.endswith('.xlsx'))
        mock_wb.save.assert_called_once()
        
    @patch('test_modules.standalone_report_generator.OPENPYXL_AVAILABLE', False)
    def test_export_raw_data_excel_no_library(self):
        """测试Excel导出库不可用情况"""
        with self.assertRaises(ImportError):
            self.generator.export_raw_data_excel(
                self.hole_data, self.workpiece_info
            )
            
    def test_generate_envelope_chart(self):
        """测试包络图生成"""
        measurement_data = [
            {'depth': i, 'diameter': 17.6 + (i % 10) * 0.001}
            for i in range(100)
        ]
        
        chart_path = self.generator.generate_envelope_chart(
            measurement_data, 17.6, 0.05, 0.07
        )
        
        self.assertTrue(os.path.exists(chart_path))
        self.assertTrue(chart_path.endswith('.png'))
        
        # 检查文件大小（应该大于0）
        file_size = os.path.getsize(chart_path)
        self.assertGreater(file_size, 1000)  # 至少1KB
        
    def test_generate_envelope_chart_with_outliers(self):
        """测试包络图生成（包含超差点）"""
        measurement_data = [
            {'depth': 10, 'diameter': 17.7},  # 超上限
            {'depth': 20, 'diameter': 16.9},  # 超下限
            {'depth': 30, 'diameter': 17.6},  # 正常
        ]
        
        chart_path = self.generator.generate_envelope_chart(
            measurement_data, 17.6, 0.05, 0.07
        )
        
        self.assertTrue(os.path.exists(chart_path))


class TestReportGenerationThread(unittest.TestCase):
    """测试报告生成线程"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = ReportGenerator()
        self.generator.output_dir = Path(self.temp_dir)
        
        self.hole_data = {'total_holes': 10}
        self.workpiece_info = {
            'model': 'TEST',
            'serial': 'SN-001',
            'operator': '测试用户'
        }
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_thread_init(self):
        """测试线程初始化"""
        thread = ReportGenerationThread(
            self.generator, "CSV", self.hole_data, self.workpiece_info
        )
        
        self.assertEqual(thread.generator, self.generator)
        self.assertEqual(thread.report_type, "CSV")
        self.assertEqual(thread.hole_data, self.hole_data)
        self.assertEqual(thread.workpiece_info, self.workpiece_info)
        
    def test_run_csv_generation(self):
        """测试CSV报告生成运行"""
        thread = ReportGenerationThread(
            self.generator, "CSV", self.hole_data, self.workpiece_info
        )
        
        # 模拟信号
        progress_signals = []
        status_signals = []
        completion_signals = []
        error_signals = []
        
        thread.progress_updated.connect(lambda x: progress_signals.append(x))
        thread.status_updated.connect(lambda x: status_signals.append(x))
        thread.generation_completed.connect(
            lambda t, p: completion_signals.append((t, p))
        )
        thread.generation_failed.connect(
            lambda t, e: error_signals.append((t, e))
        )
        
        # 运行线程
        thread.run()
        
        # 检查信号
        self.assertGreater(len(progress_signals), 0)
        self.assertGreater(len(status_signals), 0)
        self.assertEqual(len(completion_signals), 1)
        self.assertEqual(len(error_signals), 0)
        
        # 检查完成信号
        report_type, file_path = completion_signals[0]
        self.assertEqual(report_type, "CSV")
        self.assertTrue(os.path.exists(file_path))
        
    def test_run_invalid_report_type(self):
        """测试无效报告类型"""
        thread = ReportGenerationThread(
            self.generator, "INVALID", self.hole_data, self.workpiece_info
        )
        
        error_signals = []
        thread.generation_failed.connect(
            lambda t, e: error_signals.append((t, e))
        )
        
        thread.run()
        
        self.assertEqual(len(error_signals), 1)
        report_type, error_msg = error_signals[0]
        self.assertEqual(report_type, "INVALID")
        self.assertIn("不支持的报告类型", error_msg)


class TestReportGeneratorIntegration(unittest.TestCase):
    """报告生成器集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = ReportGenerator()
        self.generator.output_dir = Path(self.temp_dir)
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_full_csv_workflow(self):
        """测试完整的CSV工作流程"""
        hole_data = {
            'total_holes': 50,
            'current_hole_id': 'H025'
        }
        
        workpiece_info = {
            'model': 'CP1400',
            'serial': 'SN-INTEGRATION-001',
            'operator': '集成测试用户',
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
        # 生成CSV报告
        csv_path = self.generator.export_raw_data_csv(hole_data, workpiece_info)
        
        # 验证文件存在
        self.assertTrue(os.path.exists(csv_path))
        
        # 验证文件内容
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            
        # 检查表头
        header_line = lines[0].strip()
        expected_headers = ['孔位ID', '最小直径(mm)', '最大直径(mm)', '平均直径(mm)']
        for header in expected_headers:
            self.assertIn(header, header_line)
            
        # 检查数据行数（表头 + 数据行）
        self.assertGreater(len(lines), 1)
        
    def test_web_report_workflow(self):
        """测试Web报告工作流程"""
        hole_data = {'total_holes': 30}
        workpiece_info = {
            'model': 'TEST-WEB',
            'serial': 'SN-WEB-001',
            'operator': 'Web测试用户'
        }
        
        web_data = self.generator.generate_web_report_data(hole_data, workpiece_info)
        
        # 验证数据结构
        required_keys = ['header', 'summary', 'non_conformities', 'charts', 'images', 'full_data']
        for key in required_keys:
            self.assertIn(key, web_data)
            
        # 验证header内容
        header = web_data['header']
        self.assertEqual(header['workpiece_model'], 'TEST-WEB')
        self.assertEqual(header['workpiece_serial'], 'SN-WEB-001')
        
        # 验证summary内容
        summary = web_data['summary']
        self.assertEqual(summary['total_holes'], 30)
        self.assertIsInstance(summary['qualification_rate'], (int, float))
        
        # 验证数据可序列化（JSON兼容）
        json_str = json.dumps(web_data, default=str)
        reloaded_data = json.loads(json_str)
        self.assertEqual(reloaded_data['header']['workpiece_model'], 'TEST-WEB')


def run_unit_tests():
    """运行所有单元测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestReportData,
        TestReportGenerator,
        TestReportGenerationThread,
        TestReportGeneratorIntegration,
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 60)
    print("报告生成器单元测试")
    print("=" * 60)
    
    success = run_unit_tests()
    
    if success:
        print("\n✅ 所有单元测试通过")
    else:
        print("\n❌ 部分单元测试失败")
        
    exit(0 if success else 1)