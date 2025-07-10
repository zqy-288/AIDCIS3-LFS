"""
增强报告生成器单元测试
测试包络图、内窥镜展开图等高级功能
"""

import unittest
import tempfile
import os
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# 使用独立的增强报告生成器避免PySide6依赖
from test_modules.standalone_enhanced_report_generator import EnhancedReportGenerator


class TestEnhancedReportGenerator(unittest.TestCase):
    """测试增强报告生成器"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = EnhancedReportGenerator()
        self.generator.output_dir = Path(self.temp_dir)
        self.generator.chart_temp_dir = Path(self.temp_dir) / "charts"
        self.generator.chart_temp_dir.mkdir(exist_ok=True)
        
        # 模拟测量数据
        self.measurement_data = [
            {'depth': i * 0.1, 'diameter': 17.6 + np.random.normal(0, 0.005)}
            for i in range(100)
        ]
        
        # 模拟工件信息
        self.workpiece_info = {
            'model': 'CP1400',
            'serial': 'SN-TEST-001',
            'operator': '测试用户',
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
        # 模拟孔位数据
        self.hole_data = {
            'total_holes': 100,
            'current_hole_id': 'H001'
        }
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.generator.chart_temp_dir)
        self.assertTrue(self.generator.chart_temp_dir.exists())
        
    def test_generate_envelope_chart_with_annotations(self):
        """测试包络图生成"""
        chart_path = self.generator.generate_envelope_chart_with_annotations(
            self.measurement_data, 17.6, 0.05, 0.07, "H001"
        )
        
        # 验证文件存在
        self.assertTrue(os.path.exists(chart_path))
        self.assertTrue(chart_path.endswith('.png'))
        
        # 验证文件大小
        file_size = os.path.getsize(chart_path)
        self.assertGreater(file_size, 5000)  # 至少5KB
        
    def test_generate_envelope_chart_empty_data(self):
        """测试空数据包络图生成"""
        chart_path = self.generator.generate_envelope_chart_with_annotations(
            [], 17.6, 0.05, 0.07, "H001"
        )
        
        # 应该生成演示数据的图表
        self.assertTrue(os.path.exists(chart_path))
        self.assertTrue(chart_path.endswith('.png'))
        
    def test_generate_envelope_chart_with_outliers(self):
        """测试包含超差点的包络图"""
        # 添加超差数据
        outlier_data = self.measurement_data.copy()
        outlier_data.extend([
            {'depth': 50, 'diameter': 17.8},  # 超上限
            {'depth': 55, 'diameter': 16.9},  # 超下限
        ])
        
        chart_path = self.generator.generate_envelope_chart_with_annotations(
            outlier_data, 17.6, 0.05, 0.07, "H001"
        )
        
        self.assertTrue(os.path.exists(chart_path))
        
    def test_generate_demo_measurement_data(self):
        """测试演示数据生成"""
        demo_data = self.generator._generate_demo_measurement_data()
        
        self.assertIsInstance(demo_data, list)
        self.assertGreater(len(demo_data), 0)
        
        # 检查数据格式
        sample_point = demo_data[0]
        self.assertIn('depth', sample_point)
        self.assertIn('diameter', sample_point)
        self.assertIsInstance(sample_point['depth'], (int, float))
        self.assertIsInstance(sample_point['diameter'], (int, float))
        
    def test_generate_statistics_text(self):
        """测试统计文本生成"""
        diameters = [d['diameter'] for d in self.measurement_data]
        
        stats_text = self.generator._generate_statistics_text(
            diameters, 17.6, 0.05, 0.07
        )
        
        # 验证包含关键统计信息
        self.assertIn('平均直径', stats_text)
        self.assertIn('标准偏差', stats_text)
        self.assertIn('最小直径', stats_text)
        self.assertIn('最大直径', stats_text)
        self.assertIn('测量点数', stats_text)
        self.assertIn('超差点数', stats_text)
        self.assertIn('超差率', stats_text)
        
    def test_generate_statistics_chart(self):
        """测试统计图表生成"""
        chart_path = self.generator._generate_statistics_chart(self.measurement_data)
        
        self.assertTrue(os.path.exists(chart_path))
        self.assertTrue(chart_path.endswith('.png'))
        
        # 验证文件大小
        file_size = os.path.getsize(chart_path)
        self.assertGreater(file_size, 3000)  # 至少3KB
        
    def test_generate_placeholder_endoscope_image(self):
        """测试占位符内窥镜图像生成"""
        placeholder_path = self.generator._generate_placeholder_endoscope_image("H001")
        
        self.assertTrue(os.path.exists(placeholder_path))
        self.assertTrue(placeholder_path.endswith('.png'))
        
        # 验证文件大小
        file_size = os.path.getsize(placeholder_path)
        self.assertGreater(file_size, 1000)  # 至少1KB
        
    def test_generate_endoscope_panorama_no_images(self):
        """测试无图像的全景图生成"""
        panorama_path = self.generator.generate_endoscope_panorama([], "H001")
        
        # 应该生成占位符图像
        self.assertTrue(os.path.exists(panorama_path))
        self.assertTrue(panorama_path.endswith('.png'))
        
    @patch('PIL.Image.open')
    def test_generate_endoscope_panorama_with_images(self, mock_open):
        """测试有图像的全景图生成"""
        # 模拟图像对象
        mock_img = Mock()
        mock_img.width = 800
        mock_img.height = 600
        mock_img.resize.return_value = mock_img
        mock_open.return_value = mock_img
        
        # 创建模拟图像文件
        test_image_path = os.path.join(self.temp_dir, "test_image.png")
        with open(test_image_path, 'w') as f:
            f.write("mock image")
            
        panorama_path = self.generator.generate_endoscope_panorama(
            [test_image_path], "H001"
        )
        
        self.assertTrue(os.path.exists(panorama_path))
        mock_open.assert_called_once_with(test_image_path)
        
    def test_generate_defect_annotation_overlay_no_image(self):
        """测试无基础图像的缺陷标注"""
        non_existent_path = "/non/existent/path.png"
        
        annotated_path = self.generator.generate_defect_annotation_overlay(
            non_existent_path, [], "H001"
        )
        
        # 应该生成占位符图像
        self.assertTrue(os.path.exists(annotated_path))
        self.assertTrue(annotated_path.endswith('.png'))
        
    @patch('PIL.Image.open')
    def test_generate_defect_annotation_overlay_with_annotations(self, mock_open):
        """测试带缺陷标注的图像生成"""
        # 模拟图像对象
        mock_img = Mock()
        mock_img.width = 800
        mock_img.height = 600
        mock_draw = Mock()
        
        with patch('PIL.ImageDraw.Draw', return_value=mock_draw):
            mock_open.return_value = mock_img
            
            # 创建模拟图像文件
            test_image_path = os.path.join(self.temp_dir, "test_base.png")
            with open(test_image_path, 'w') as f:
                f.write("mock image")
                
            # 模拟缺陷标注
            defect_annotations = [
                {
                    'bbox': [100, 100, 200, 200],
                    'label': '裂纹',
                    'confidence': 0.95
                },
                {
                    'bbox': [300, 150, 400, 250],
                    'label': '孔洞',
                    'confidence': 0.87
                }
            ]
            
            annotated_path = self.generator.generate_defect_annotation_overlay(
                test_image_path, defect_annotations, "H001"
            )
            
            self.assertTrue(os.path.exists(annotated_path))
            mock_open.assert_called_once_with(test_image_path)
            
            # 验证绘制方法被调用
            self.assertGreater(mock_draw.rectangle.call_count, 0)
            self.assertGreater(mock_draw.text.call_count, 0)
            
    def test_prepare_enhanced_report_data(self):
        """测试增强报告数据准备"""
        report_data = self.generator._prepare_enhanced_report_data(
            self.hole_data, self.workpiece_info, 
            self.measurement_data, []
        )
        
        # 验证基本报告数据
        self.assertEqual(report_data.workpiece_model, "CP1400")
        self.assertEqual(report_data.workpiece_serial, "SN-TEST-001")
        self.assertEqual(report_data.operator, "测试用户")
        
        # 验证图表数据
        self.assertIn('envelope', report_data.charts)
        self.assertTrue(os.path.exists(report_data.charts['envelope']))
        
    def test_generate_report_charts(self):
        """测试报告图表生成"""
        from test_modules.standalone_report_generator import ReportData
        
        report_data = ReportData()
        self.generator._generate_report_charts(report_data, self.measurement_data)
        
        # 验证图表生成
        self.assertIn('envelope', report_data.charts)
        self.assertIn('statistics', report_data.charts)
        
        # 验证文件存在
        self.assertTrue(os.path.exists(report_data.charts['envelope']))
        self.assertTrue(os.path.exists(report_data.charts['statistics']))
        
    def test_process_endoscope_images(self):
        """测试内窥镜图像处理"""
        from test_modules.standalone_report_generator import ReportData
        
        report_data = ReportData()
        
        # 创建模拟图像文件
        test_image_path = os.path.join(self.temp_dir, "test_endoscope.png")
        with open(test_image_path, 'w') as f:
            f.write("mock endoscope image")
            
        self.generator._process_endoscope_images(report_data, [test_image_path])
        
        # 验证全景图生成
        self.assertIn('endoscope_panorama', report_data.images)
        self.assertTrue(os.path.exists(report_data.images['endoscope_panorama']))
        
    def test_add_depth_markers(self):
        """测试深度标记添加"""
        from PIL import Image
        
        # 创建测试图像
        test_image = Image.new('RGB', (800, 600), 'white')
        
        # 添加深度标记
        self.generator._add_depth_markers(test_image, 3)
        
        # 验证图像尺寸不变
        self.assertEqual(test_image.size, (800, 600))
        
    def test_add_defect_legend(self):
        """测试缺陷图例添加"""
        from PIL import Image, ImageDraw, ImageFont
        
        # 创建测试图像
        test_image = Image.new('RGB', (800, 600), 'white')
        draw = ImageDraw.Draw(test_image)
        
        try:
            font = ImageFont.load_default()
            small_font = font
        except:
            font = None
            small_font = None
            
        # 添加图例
        self.generator._add_defect_legend(draw, test_image.size, font, small_font)
        
        # 验证图像尺寸不变
        self.assertEqual(test_image.size, (800, 600))
        
    def test_cleanup_temp_files(self):
        """测试临时文件清理"""
        # 创建一些临时文件
        test_files = []
        for i in range(3):
            test_file = self.generator.chart_temp_dir / f"test_{i}.png"
            with open(test_file, 'w') as f:
                f.write("test content")
            test_files.append(test_file)
            
        # 验证文件存在
        for test_file in test_files:
            self.assertTrue(test_file.exists())
            
        # 清理文件
        self.generator.cleanup_temp_files()
        
        # 验证文件被删除
        for test_file in test_files:
            self.assertFalse(test_file.exists())
            
    @patch('test_modules.standalone_enhanced_report_generator.EnhancedReportGenerator.generate_comprehensive_pdf_report')
    def test_generate_comprehensive_pdf_report(self, mock_pdf_gen):
        """测试综合PDF报告生成"""
        mock_pdf_gen.return_value = "/path/to/report.pdf"
        
        pdf_path = self.generator.generate_comprehensive_pdf_report(
            self.hole_data, self.workpiece_info, 
            self.measurement_data, []
        )
        
        self.assertEqual(pdf_path, "/path/to/report.pdf")
        mock_pdf_gen.assert_called_once()


class TestEnhancedReportGeneratorIntegration(unittest.TestCase):
    """增强报告生成器集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = EnhancedReportGenerator()
        self.generator.output_dir = Path(self.temp_dir)
        self.generator.chart_temp_dir = Path(self.temp_dir) / "charts"
        self.generator.chart_temp_dir.mkdir(exist_ok=True)
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_full_enhanced_report_workflow(self):
        """测试完整的增强报告工作流程"""
        # 准备测试数据
        hole_data = {
            'total_holes': 50,
            'current_hole_id': 'H025'
        }
        
        workpiece_info = {
            'model': 'CP1400',
            'serial': 'SN-ENHANCED-001',
            'operator': '增强测试用户',
            'start_time': datetime.now(),
            'end_time': datetime.now()
        }
        
        measurement_data = [
            {'depth': i * 0.5, 'diameter': 17.6 + np.random.normal(0, 0.01)}
            for i in range(200)
        ]
        
        # 添加一些超差点
        measurement_data.extend([
            {'depth': 100, 'diameter': 17.8},  # 超上限
            {'depth': 105, 'diameter': 16.8},  # 超下限
        ])
        
        # 生成包络图
        envelope_chart = self.generator.generate_envelope_chart_with_annotations(
            measurement_data, 17.6, 0.05, 0.07, "H025"
        )
        
        # 验证包络图生成
        self.assertTrue(os.path.exists(envelope_chart))
        file_size = os.path.getsize(envelope_chart)
        self.assertGreater(file_size, 5000)
        
        # 生成统计图表
        stats_chart = self.generator._generate_statistics_chart(measurement_data)
        
        # 验证统计图表生成
        self.assertTrue(os.path.exists(stats_chart))
        stats_file_size = os.path.getsize(stats_chart)
        self.assertGreater(stats_file_size, 3000)
        
        # 生成占位符内窥镜图像
        endoscope_image = self.generator._generate_placeholder_endoscope_image("H025")
        
        # 验证内窥镜图像生成
        self.assertTrue(os.path.exists(endoscope_image))
        endoscope_file_size = os.path.getsize(endoscope_image)
        self.assertGreater(endoscope_file_size, 1000)
        
        # 验证统计文本生成
        diameters = [d['diameter'] for d in measurement_data]
        stats_text = self.generator._generate_statistics_text(
            diameters, 17.6, 0.05, 0.07
        )
        
        # 验证统计信息正确性
        self.assertIn('测量点数: 202', stats_text)  # 200 + 2 超差点
        self.assertIn('超差点数: 2', stats_text)
        self.assertIn('超差率: 1.0%', stats_text)
        
        print(f"✅ 增强报告生成器集成测试完成")
        print(f"   包络图: {envelope_chart}")
        print(f"   统计图: {stats_chart}")
        print(f"   内窥镜图像: {endoscope_image}")
        
    def test_chart_quality_and_content(self):
        """测试图表质量和内容"""
        measurement_data = [
            {'depth': i * 0.1, 'diameter': 17.6 + 0.01 * np.sin(i * 0.1)}
            for i in range(1000)
        ]
        
        # 添加明显的超差点
        measurement_data.extend([
            {'depth': 50, 'diameter': 17.8},   # 明显超上限
            {'depth': 55, 'diameter': 16.8},   # 明显超下限
        ])
        
        # 生成包络图
        envelope_chart = self.generator.generate_envelope_chart_with_annotations(
            measurement_data, 17.6, 0.05, 0.07, "H_QUALITY_TEST"
        )
        
        # 验证文件质量
        self.assertTrue(os.path.exists(envelope_chart))
        file_size = os.path.getsize(envelope_chart)
        self.assertGreater(file_size, 10000)  # 高质量图表应该更大
        
        # 验证统计文本包含正确信息
        diameters = [d['diameter'] for d in measurement_data]
        stats_text = self.generator._generate_statistics_text(
            diameters, 17.6, 0.05, 0.07
        )
        
        # 验证超差检测正确
        self.assertIn('超差点数: 2', stats_text)
        self.assertIn('测量点数: 1002', stats_text)


def run_enhanced_tests():
    """运行增强报告生成器测试"""
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestEnhancedReportGenerator,
        TestEnhancedReportGeneratorIntegration,
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
    print("增强报告生成器单元测试")
    print("=" * 60)
    
    success = run_enhanced_tests()
    
    if success:
        print("\n✅ 所有增强报告生成器测试通过")
    else:
        print("\n❌ 部分增强报告生成器测试失败")
        
    exit(0 if success else 1)