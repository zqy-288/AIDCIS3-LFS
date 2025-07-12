#!/usr/bin/env python3
"""
测试DXF文件导入产品功能
"""

import unittest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.dxf_product_converter import DXFProductConverter


class TestDXFToProductImport(unittest.TestCase):
    """测试DXF到产品信息的转换"""
    
    def setUp(self):
        """测试前准备"""
        self.converter = DXFProductConverter()
        self.test_dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
    
    def test_extract_product_name(self):
        """测试产品名称提取"""
        # 测试各种文件名格式
        test_cases = [
            ("/path/东重管板.dxf", "东重管板"),
            ("/path/东重管板_v1.2.dxf", "东重管板"),
            ("/path/东重管板-20241211.dxf", "东重管板"),
            ("/path/测试管板_v2.0.dxf", "测试管板"),
        ]
        
        for file_path, expected_name in test_cases:
            with self.subTest(file_path=file_path):
                name = self.converter.extract_product_name(file_path)
                self.assertEqual(name, expected_name)
    
    def test_generate_product_code(self):
        """测试产品编号生成"""
        # 测试带字母的产品名
        code = self.converter.generate_product_code("TestProduct")
        self.assertTrue(code.startswith("TESTPRODUCT-"))
        self.assertEqual(len(code), 24)  # TESTPRODUCT-YYYYMMDDHHmm
        
        # 测试纯中文名称
        code = self.converter.generate_product_code("东重管板")
        self.assertTrue(code.startswith("PROD-"))
    
    def test_convert_dongzhong_dxf(self):
        """测试东重管板DXF文件转换"""
        # 转换DXF文件
        product_info = self.converter.convert_dxf_to_product_info(self.test_dxf_path)
        
        # 验证转换结果
        self.assertIsNotNone(product_info)
        
        # 验证必需字段
        self.assertEqual(product_info['product_name'], "东重管板")
        self.assertIsNotNone(product_info['product_code'])
        self.assertEqual(product_info['hole_count'], 25210)
        self.assertAlmostEqual(product_info['hole_diameter'], 17.73, places=2)
        
        # 验证形状判断
        self.assertIn(product_info['shape'], ['circular', 'elliptical'])
        
        # 验证文件信息
        self.assertEqual(product_info['dxf_file_path'], self.test_dxf_path)
        self.assertGreater(product_info['dxf_file_size'], 0)
        
        # 验证分区配置
        self.assertEqual(product_info['sector_count'], 4)
        
        # 验证缺失信息为None
        self.assertIsNone(product_info['material'])
        self.assertIsNone(product_info['thickness'])
        self.assertIsNone(product_info['weight'])
        
        # 验证元数据
        self.assertTrue(product_info['created_from_dxf'])
        self.assertEqual(product_info['data_completeness'], 'partial')
    
    def test_validate_product_info(self):
        """测试产品信息验证"""
        # 创建测试数据
        product_info = {
            'product_code': 'TEST-001',
            'product_name': '测试产品',
            'hole_count': 100,
            'hole_diameter': None,
            'material': None
        }
        
        # 验证
        validation_result = self.converter.validate_product_info(product_info)
        
        # 检查验证结果
        self.assertTrue(validation_result['is_valid'])  # 必需字段都有
        self.assertEqual(len(validation_result['missing_required']), 0)
        self.assertIn('hole_diameter', validation_result['missing_important'])
        self.assertIn('material', validation_result['missing_important'])
        
        # 测试缺少必需字段
        product_info_invalid = {
            'product_name': '测试产品',
            'hole_count': 100
        }
        
        validation_result = self.converter.validate_product_info(product_info_invalid)
        self.assertFalse(validation_result['is_valid'])
        self.assertIn('product_code', validation_result['missing_required'])
    
    def test_completeness_score(self):
        """测试完整性评分"""
        # 完整数据
        complete_info = {
            'product_code': 'TEST-001',
            'product_name': '测试产品',
            'hole_count': 100,
            'hole_diameter': 17.5,
            'shape': 'circular',
            'outer_diameter': 1000,
            'inner_diameter': 1000,
            'material': 'Steel',
            'thickness': 50,
            'weight': 100,
            'manufacturer': 'Test Corp',
            'specifications': 'Test Spec',
            'dxf_file_path': '/test.dxf',
            'sector_count': 4
        }
        
        validation_result = self.converter.validate_product_info(complete_info)
        self.assertEqual(validation_result['completeness_score'], 100.0)
        
        # 部分数据
        partial_info = {
            'product_code': 'TEST-001',
            'product_name': '测试产品',
            'hole_count': 100,
            'dxf_file_path': '/test.dxf'
        }
        
        validation_result = self.converter.validate_product_info(partial_info)
        self.assertLess(validation_result['completeness_score'], 50)


if __name__ == '__main__':
    unittest.main()