#!/usr/bin/env python3
"""
DXF产品导入工作流集成测试
测试从DXF文件导入产品到产品选择和加载的完整流程
"""

import unittest
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from modules.product_import_service import ProductImportService
from modules.dxf_product_converter import DXFProductConverter
from models.product_model import ProductModel, get_product_manager
from main_window.main_window import MainWindow


class TestDXFProductWorkflow(unittest.TestCase):
    """测试DXF产品导入工作流"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """测试前准备"""
        self.test_dxf_path = "/Users/vsiyo/Desktop/AIDCIS3-1/AIDCIS3-LFS/assets/dxf/DXF Graph/东重管板.dxf"
        self.converter = DXFProductConverter()
        self.import_service = ProductImportService()
        self.product_manager = get_product_manager()
        
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
    def tearDown(self):
        """测试后清理"""
        # 清理临时数据库
        Path(self.temp_db.name).unlink(missing_ok=True)
    
    def test_dxf_to_product_conversion(self):
        """测试DXF到产品信息的转换"""
        # 转换DXF文件
        product_info = self.converter.convert_dxf_to_product_info(self.test_dxf_path)
        
        # 验证转换结果
        self.assertIsNotNone(product_info)
        self.assertEqual(product_info['product_name'], "东重管板")
        self.assertEqual(product_info['hole_count'], 25210)
        self.assertAlmostEqual(product_info['hole_diameter'], 17.73, places=2)
        self.assertIn(product_info['shape'], ['circular', 'elliptical'])
        
        # 验证完整性
        validation = self.converter.validate_product_info(product_info)
        self.assertTrue(validation['is_valid'])
        self.assertGreater(validation['completeness_score'], 50)
    
    def test_product_import_service_preview(self):
        """测试产品导入服务预览功能"""
        # 预览导入
        preview = self.import_service.preview_dxf_import(self.test_dxf_path)
        
        # 验证预览结果
        self.assertIsNotNone(preview)
        self.assertIn('product_info', preview)
        self.assertIn('validation', preview)
        self.assertFalse(preview.get('existing_product', False))
        
        # 验证产品信息
        product_info = preview['product_info']
        self.assertEqual(product_info['product_name'], "东重管板")
        self.assertEqual(product_info['hole_count'], 25210)
    
    @patch('models.product_model.ProductModelManager.session')
    def test_product_creation_from_dxf(self, mock_session):
        """测试从DXF创建产品"""
        # Mock数据库会话
        mock_session.commit = Mock()
        mock_session.add = Mock()
        mock_session.query = Mock(return_value=Mock(filter=Mock(return_value=Mock(all=Mock(return_value=[])))))
        
        # 导入产品
        product = self.import_service.import_from_dxf(
            self.test_dxf_path,
            product_name="测试东重管板",
            tolerance_upper=0.05,
            tolerance_lower=-0.05
        )
        
        # 验证产品创建
        self.assertIsNotNone(product)
        
    def test_main_window_integration(self):
        """测试主窗口集成"""
        # 创建主窗口
        main_window = MainWindow()
        
        # 验证默认DXF加载
        self.assertIsNotNone(main_window.hole_collection)
        self.assertGreater(len(main_window.hole_collection.holes), 0)
        
        # 验证扇形管理器初始化
        self.assertIsNotNone(main_window.sector_manager)
        
        # 验证动态扇形显示初始化
        self.assertIsNotNone(main_window.dynamic_sector_display)
        
        # 验证检测按钮状态
        self.assertTrue(main_window.start_detection_btn.isEnabled())
        self.assertTrue(main_window.simulate_btn.isEnabled())
        
        # 清理
        main_window.close()
    
    def test_product_selection_workflow(self):
        """测试产品选择工作流"""
        # 创建测试产品
        test_product = Mock(spec=ProductModel)
        test_product.id = 1
        test_product.model_name = "测试产品"
        test_product.model_code = "TEST-001"
        test_product.standard_diameter = 17.73
        test_product.dxf_file_path = self.test_dxf_path
        
        # 创建主窗口
        main_window = MainWindow()
        
        # 模拟产品选择
        main_window.on_product_selected(test_product)
        
        # 验证产品信息更新
        self.assertEqual(main_window.current_product, test_product)
        
        # 验证DXF文件加载（由于是异步，需要等待）
        QTest.qWait(500)
        
        # 验证孔位数据加载
        self.assertIsNotNone(main_window.hole_collection)
        
        # 清理
        main_window.close()
    
    def test_sector_configuration(self):
        """测试分区配置"""
        # 转换DXF并设置分区数
        product_info = self.converter.convert_dxf_to_product_info(self.test_dxf_path)
        
        # 验证默认分区数
        self.assertEqual(product_info['sector_count'], 4)
        
        # 测试自定义分区数
        custom_sectors = [2, 4, 6, 8]
        for sector_count in custom_sectors:
            # 创建产品时指定分区数
            with patch.object(self.import_service, '_create_or_update_product') as mock_create:
                self.import_service.import_from_dxf(
                    self.test_dxf_path,
                    sector_count=sector_count
                )
                
                # 验证分区数被正确传递
                call_args = mock_create.call_args[0][0]
                self.assertEqual(call_args.get('sector_count'), sector_count)
    
    def test_data_completeness_handling(self):
        """测试数据完整性处理"""
        # 转换DXF
        product_info = self.converter.convert_dxf_to_product_info(self.test_dxf_path)
        
        # 验证缺失信息为None
        self.assertIsNone(product_info['material'])
        self.assertIsNone(product_info['thickness'])
        self.assertIsNone(product_info['weight'])
        
        # 验证必需信息存在
        self.assertIsNotNone(product_info['product_name'])
        self.assertIsNotNone(product_info['product_code'])
        self.assertIsNotNone(product_info['hole_count'])
        
        # 验证完整性标记
        self.assertEqual(product_info['data_completeness'], 'partial')
        self.assertTrue(product_info['created_from_dxf'])


if __name__ == '__main__':
    unittest.main()