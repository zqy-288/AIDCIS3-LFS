"""
产品模型单元测试
测试ProductModel和ProductModelManager的各种功能
"""

import unittest
import tempfile
import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

# 添加src路径以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

from models.product_model import ProductModel, ProductModelManager, get_product_manager


class TestProductModel(unittest.TestCase):
    """产品模型实体测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.product_data = {
            'id': 1,
            'model_name': 'TEST-001',
            'model_code': 'T001',
            'standard_diameter': 10.0,
            'tolerance_upper': 0.05,
            'tolerance_lower': -0.05,
            'description': '测试产品',
            'is_active': True,
            'dxf_file_path': '/path/to/test.dxf',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
    
    def test_product_model_creation(self):
        """测试产品模型创建"""
        product = ProductModel(**self.product_data)
        
        self.assertEqual(product.model_name, 'TEST-001')
        self.assertEqual(product.standard_diameter, 10.0)
        self.assertEqual(product.tolerance_upper, 0.05)
        self.assertEqual(product.tolerance_lower, -0.05)
    
    def test_tolerance_range_property(self):
        """测试公差范围属性"""
        product = ProductModel(**self.product_data)
        expected_range = "+0.050/-0.050"
        
        self.assertEqual(product.tolerance_range, expected_range)
    
    def test_diameter_range_property(self):
        """测试直径范围属性"""
        product = ProductModel(**self.product_data)
        min_dia, max_dia = product.diameter_range
        
        self.assertEqual(min_dia, 9.95)  # 10.0 + (-0.05)
        self.assertEqual(max_dia, 10.05)  # 10.0 + 0.05
    
    def test_is_diameter_in_range(self):
        """测试直径是否在公差范围内"""
        product = ProductModel(**self.product_data)
        
        # 在范围内的直径
        self.assertTrue(product.is_diameter_in_range(10.0))
        self.assertTrue(product.is_diameter_in_range(9.95))
        self.assertTrue(product.is_diameter_in_range(10.05))
        self.assertTrue(product.is_diameter_in_range(10.02))
        
        # 超出范围的直径
        self.assertFalse(product.is_diameter_in_range(9.94))
        self.assertFalse(product.is_diameter_in_range(10.06))
        self.assertFalse(product.is_diameter_in_range(8.0))
        self.assertFalse(product.is_diameter_in_range(12.0))
    
    def test_to_dict(self):
        """测试转换为字典"""
        product = ProductModel(**self.product_data)
        result = product.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['model_name'], 'TEST-001')
        self.assertEqual(result['standard_diameter'], 10.0)
        self.assertIn('created_at', result)
        self.assertIn('updated_at', result)
    
    def test_repr(self):
        """测试字符串表示"""
        product = ProductModel(**self.product_data)
        repr_str = repr(product)
        
        self.assertIn('TEST-001', repr_str)
        self.assertIn('10.0', repr_str)
        self.assertIn('ProductModel', repr_str)


class TestProductModelManager(unittest.TestCase):
    """产品模型管理器测试"""
    
    def setUp(self):
        """测试前置设置"""
        # 创建临时数据库文件
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # 创建管理器实例
        self.manager = ProductModelManager(db_path=self.db_path)
    
    def tearDown(self):
        """测试后置清理"""
        if self.manager:
            self.manager.close()
        
        # 删除临时数据库文件
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_manager_initialization(self):
        """测试管理器初始化"""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager.session)
        self.assertIsNotNone(self.manager.engine)
        
        # 检查默认数据是否已创建
        products = self.manager.get_all_products()
        self.assertGreaterEqual(len(products), 3)  # 至少有3个默认产品
    
    def test_create_product(self):
        """测试创建产品"""
        product = self.manager.create_product(
            model_name="TEST-CREATE",
            standard_diameter=8.0,
            tolerance_upper=0.03,
            tolerance_lower=-0.03,
            model_code="TC001",
            description="创建测试产品"
        )
        
        self.assertIsNotNone(product)
        self.assertEqual(product.model_name, "TEST-CREATE")
        self.assertEqual(product.standard_diameter, 8.0)
        self.assertEqual(product.model_code, "TC001")
        self.assertEqual(product.description, "创建测试产品")
        self.assertTrue(product.is_active)
    
    def test_create_duplicate_product(self):
        """测试创建重复产品名称"""
        # 创建第一个产品
        self.manager.create_product(
            model_name="DUPLICATE-TEST",
            standard_diameter=8.0,
            tolerance_upper=0.03,
            tolerance_lower=-0.03
        )
        
        # 尝试创建重复名称的产品
        with self.assertRaises(ValueError) as context:
            self.manager.create_product(
                model_name="DUPLICATE-TEST",
                standard_diameter=9.0,
                tolerance_upper=0.04,
                tolerance_lower=-0.04
            )
        
        self.assertIn("已存在", str(context.exception))
    
    def test_get_product_by_id(self):
        """测试根据ID获取产品"""
        # 创建产品
        created_product = self.manager.create_product(
            model_name="TEST-GET-ID",
            standard_diameter=7.0,
            tolerance_upper=0.02,
            tolerance_lower=-0.02
        )
        
        # 根据ID获取产品
        retrieved_product = self.manager.get_product_by_id(created_product.id)
        
        self.assertIsNotNone(retrieved_product)
        self.assertEqual(retrieved_product.id, created_product.id)
        self.assertEqual(retrieved_product.model_name, "TEST-GET-ID")
    
    def test_get_product_by_name(self):
        """测试根据名称获取产品"""
        # 创建产品
        self.manager.create_product(
            model_name="TEST-GET-NAME",
            standard_diameter=6.0,
            tolerance_upper=0.025,
            tolerance_lower=-0.025
        )
        
        # 根据名称获取产品
        retrieved_product = self.manager.get_product_by_name("TEST-GET-NAME")
        
        self.assertIsNotNone(retrieved_product)
        self.assertEqual(retrieved_product.model_name, "TEST-GET-NAME")
        self.assertEqual(retrieved_product.standard_diameter, 6.0)
    
    def test_update_product(self):
        """测试更新产品"""
        # 创建产品
        product = self.manager.create_product(
            model_name="TEST-UPDATE",
            standard_diameter=5.0,
            tolerance_upper=0.02,
            tolerance_lower=-0.02
        )
        
        # 更新产品
        updated_product = self.manager.update_product(
            product.id,
            standard_diameter=5.5,
            description="更新后的描述",
            is_active=False
        )
        
        self.assertEqual(updated_product.standard_diameter, 5.5)
        self.assertEqual(updated_product.description, "更新后的描述")
        self.assertFalse(updated_product.is_active)
        self.assertEqual(updated_product.model_name, "TEST-UPDATE")  # 未更新的字段保持不变
    
    def test_update_nonexistent_product(self):
        """测试更新不存在的产品"""
        with self.assertRaises(ValueError) as context:
            self.manager.update_product(99999, description="测试")
        
        self.assertIn("不存在", str(context.exception))
    
    def test_delete_product(self):
        """测试删除产品"""
        # 创建产品
        product = self.manager.create_product(
            model_name="TEST-DELETE",
            standard_diameter=4.0,
            tolerance_upper=0.01,
            tolerance_lower=-0.01
        )
        
        product_id = product.id
        
        # 删除产品
        result = self.manager.delete_product(product_id)
        self.assertTrue(result)
        
        # 验证产品已被删除
        deleted_product = self.manager.get_product_by_id(product_id)
        self.assertIsNone(deleted_product)
    
    def test_delete_nonexistent_product(self):
        """测试删除不存在的产品"""
        with self.assertRaises(ValueError) as context:
            self.manager.delete_product(99999)
        
        self.assertIn("不存在", str(context.exception))
    
    def test_activate_deactivate_product(self):
        """测试激活和停用产品"""
        # 创建产品
        product = self.manager.create_product(
            model_name="TEST-ACTIVATE",
            standard_diameter=3.0,
            tolerance_upper=0.015,
            tolerance_lower=-0.015
        )
        
        # 停用产品
        deactivated = self.manager.deactivate_product(product.id)
        self.assertFalse(deactivated.is_active)
        
        # 激活产品
        activated = self.manager.activate_product(product.id)
        self.assertTrue(activated.is_active)
    
    def test_search_products(self):
        """测试搜索产品"""
        # 创建几个测试产品
        self.manager.create_product(
            model_name="SEARCH-001",
            standard_diameter=2.0,
            tolerance_upper=0.01,
            tolerance_lower=-0.01,
            description="搜索测试产品1"
        )
        self.manager.create_product(
            model_name="SEARCH-002",
            standard_diameter=2.5,
            tolerance_upper=0.01,
            tolerance_lower=-0.01,
            description="另一个搜索测试"
        )
        self.manager.create_product(
            model_name="OTHER-001",
            standard_diameter=3.0,
            tolerance_upper=0.01,
            tolerance_lower=-0.01,
            description="其他产品"
        )
        
        # 搜索包含"SEARCH"的产品
        search_results = self.manager.search_products("SEARCH")
        self.assertEqual(len(search_results), 2)
        
        # 搜索描述中包含"搜索"的产品
        search_results = self.manager.search_products("搜索")
        self.assertGreaterEqual(len(search_results), 2)
    
    def test_get_products_by_diameter_range(self):
        """测试根据直径范围获取产品"""
        # 创建不同直径的产品
        self.manager.create_product(
            model_name="DIA-SMALL", standard_diameter=1.0,
            tolerance_upper=0.01, tolerance_lower=-0.01
        )
        self.manager.create_product(
            model_name="DIA-MEDIUM", standard_diameter=5.0,
            tolerance_upper=0.01, tolerance_lower=-0.01
        )
        self.manager.create_product(
            model_name="DIA-LARGE", standard_diameter=20.0,
            tolerance_upper=0.01, tolerance_lower=-0.01
        )
        
        # 获取直径在2-10范围内的产品
        results = self.manager.get_products_by_diameter_range(2.0, 10.0)
        
        # 验证结果
        diameters = [p.standard_diameter for p in results]
        for diameter in diameters:
            self.assertTrue(2.0 <= diameter <= 10.0)
    
    def test_get_all_products_active_only(self):
        """测试获取所有产品（仅启用）"""
        # 创建启用和停用的产品
        active_product = self.manager.create_product(
            model_name="ACTIVE-TEST", standard_diameter=1.5,
            tolerance_upper=0.01, tolerance_lower=-0.01
        )
        inactive_product = self.manager.create_product(
            model_name="INACTIVE-TEST", standard_diameter=1.6,
            tolerance_upper=0.01, tolerance_lower=-0.01
        )
        
        # 停用一个产品
        self.manager.deactivate_product(inactive_product.id)
        
        # 获取仅启用的产品
        active_products = self.manager.get_all_products(active_only=True)
        active_names = [p.model_name for p in active_products]
        
        self.assertIn("ACTIVE-TEST", active_names)
        self.assertNotIn("INACTIVE-TEST", active_names)
        
        # 获取所有产品（包括停用的）
        all_products = self.manager.get_all_products(active_only=False)
        all_names = [p.model_name for p in all_products]
        
        self.assertIn("ACTIVE-TEST", all_names)
        self.assertIn("INACTIVE-TEST", all_names)


class TestGetProductManager(unittest.TestCase):
    """测试get_product_manager单例函数"""
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = get_product_manager()
        manager2 = get_product_manager()
        
        # 应该返回同一个实例
        self.assertIs(manager1, manager2)
    
    @patch('models.product_model._product_manager', None)
    def test_manager_creation(self):
        """测试管理器创建"""
        # 重置全局变量
        import models.product_model
        models.product_model._product_manager = None
        
        manager = get_product_manager()
        self.assertIsNotNone(manager)
        self.assertIsInstance(manager, ProductModelManager)


if __name__ == '__main__':
    unittest.main()