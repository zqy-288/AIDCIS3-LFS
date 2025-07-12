#!/usr/bin/env python3
"""
测试产品导入服务
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.product_import_service import ProductImportService
from models.product_model import ProductModel


class TestProductImportService(unittest.TestCase):
    """测试产品导入服务"""
    
    def setUp(self):
        """测试前准备"""
        self.service = ProductImportService()
        self.test_dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        
        # Mock产品管理器
        self.mock_product_manager = Mock()
        self.service.product_manager = self.mock_product_manager
    
    def test_preview_dxf_import(self):
        """测试DXF导入预览"""
        # Mock检查现有产品
        self.mock_product_manager.search_products.return_value = []
        
        # 预览导入
        preview = self.service.preview_dxf_import(self.test_dxf_path)
        
        # 验证预览结果
        self.assertIsNotNone(preview)
        self.assertIn('product_info', preview)
        self.assertIn('validation', preview)
        self.assertFalse(preview['existing_product'])
        
        # 验证产品信息
        product_info = preview['product_info']
        self.assertEqual(product_info['product_name'], "东重管板")
        self.assertEqual(product_info['hole_count'], 25210)
    
    def test_apply_user_overrides(self):
        """测试应用用户自定义值"""
        # 原始产品信息
        product_info = {
            'product_name': '原始名称',
            'hole_diameter': 17.5,
            'material': None
        }
        
        # 用户覆盖
        overrides = {
            'product_name': '新名称',
            'standard_diameter': 18.0,
            'material': 'Steel',
            'invalid_field': 'ignored'  # 应该被忽略
        }
        
        # 应用覆盖
        self.service._apply_user_overrides(product_info, overrides)
        
        # 验证结果
        self.assertEqual(product_info['product_name'], '新名称')
        self.assertEqual(product_info['hole_diameter'], 18.0)
        self.assertEqual(product_info['material'], 'Steel')
        self.assertNotIn('invalid_field', product_info)
    
    def test_check_existing_product_by_code(self):
        """测试按产品编号检查现有产品"""
        # 创建模拟产品
        mock_product = Mock()
        mock_product.model_code = 'TEST-001'
        mock_product.model_name = '测试产品'
        
        # Mock搜索结果 - 只在第一次调用时返回产品
        self.mock_product_manager.search_products.side_effect = [[mock_product], []]
        
        # 检查产品
        product_info = {'product_code': 'TEST-001', 'product_name': '测试产品'}
        existing = self.service._check_existing_product(product_info)
        
        # 验证结果
        self.assertIsNotNone(existing)
        self.assertEqual(existing.model_code, 'TEST-001')
    
    def test_generate_description(self):
        """测试生成产品描述"""
        # 测试数据
        product_info = {
            'dxf_file_path': '/path/to/test.dxf',
            'hole_count': 100,
            'hole_diameter': 17.5,
            'shape': 'circular',
            'outer_diameter': 1000,
            'inner_diameter': 800,
            'material': None
        }
        
        # 生成描述
        description = self.service._generate_description(product_info)
        
        # 验证描述内容
        self.assertIn('从DXF文件导入: test.dxf', description)
        self.assertIn('孔位数量: 100', description)
        self.assertIn('孔径: 17.50mm', description)
        self.assertIn('形状: circular', description)
        self.assertIn('外形尺寸: 1000.0 x 800.0mm', description)
        self.assertIn('数据完整性:', description)
    
    @patch('modules.product_import_service.ProductImportService.import_completed')
    def test_import_from_dxf_success(self, mock_signal):
        """测试成功导入DXF"""
        # Mock产品创建
        mock_product = Mock(spec=ProductModel)
        mock_product.id = 1
        self.mock_product_manager.create_product.return_value = mock_product
        self.mock_product_manager.search_products.return_value = []
        
        # 执行导入
        result = self.service.import_from_dxf(self.test_dxf_path)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result, mock_product)
        
        # 验证信号发射
        self.assertTrue(mock_signal.emit.called)
    
    def test_import_existing_product_without_force(self):
        """测试导入已存在的产品（不强制更新）"""
        # Mock现有产品
        mock_product = Mock(spec=ProductModel)
        mock_product.model_code = 'PROD-202412111234'
        self.mock_product_manager.search_products.return_value = [mock_product]
        
        # 执行导入
        result = self.service.import_from_dxf(self.test_dxf_path)
        
        # 验证结果
        self.assertIsNone(result)
    
    def test_import_existing_product_with_force(self):
        """测试导入已存在的产品（强制更新）"""
        # Mock现有产品
        mock_product = Mock(spec=ProductModel)
        mock_product.model_code = 'PROD-202412111234'
        self.mock_product_manager.search_products.return_value = [mock_product]
        self.mock_product_manager.session = Mock()
        
        # 执行导入（强制更新）
        result = self.service.import_from_dxf(self.test_dxf_path, force_update=True)
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result, mock_product)
        
        # 验证提交被调用
        self.mock_product_manager.session.commit.assert_called_once()
    
    def test_batch_import(self):
        """测试批量导入"""
        # 创建测试目录结构
        test_dir = Path(__file__).parent / "test_dxf_files"
        
        # Mock glob结果
        with patch('pathlib.Path.glob') as mock_glob:
            mock_glob.return_value = [
                Path('file1.dxf'),
                Path('file2.dxf')
            ]
            
            # Mock单个导入结果
            mock_product = Mock(spec=ProductModel)
            self.service.import_from_dxf = Mock(side_effect=[mock_product, None])
            
            # 执行批量导入
            results = self.service.batch_import_from_directory(str(test_dir))
            
            # 验证结果
            self.assertEqual(len(results), 2)
            self.assertTrue(results[0]['success'])
            self.assertFalse(results[1]['success'])


if __name__ == '__main__':
    unittest.main()