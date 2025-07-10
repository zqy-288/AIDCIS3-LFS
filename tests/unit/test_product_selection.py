"""
产品选择界面单元测试
测试ProductSelectionDialog和ProductQuickSelector的功能
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock, Mock
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

# 添加src路径以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

from modules.product_selection import ProductSelectionDialog, ProductQuickSelector
from models.product_model import ProductModelManager, ProductModel


class TestProductSelectionDialog(unittest.TestCase):
    """产品选择对话框测试"""
    
    @classmethod
    def setUpClass(cls):
        """类级别的设置，创建QApplication实例"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """测试前置设置"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # 创建模拟的产品管理器
        self.mock_manager = MagicMock(spec=ProductModelManager)
        
        # 创建测试产品数据
        self.test_products = [
            self._create_mock_product(1, "TEST-001", 10.0, 0.05, -0.05, "测试产品1"),
            self._create_mock_product(2, "TEST-002", 12.0, 0.08, -0.08, "测试产品2"),
            self._create_mock_product(3, "TEST-003", 15.0, 0.10, -0.10, "测试产品3"),
        ]
        
        self.mock_manager.get_all_products.return_value = self.test_products
    
    def tearDown(self):
        """测试后置清理"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def _create_mock_product(self, id, name, diameter, upper, lower, desc):
        """创建模拟产品对象"""
        product = Mock(spec=ProductModel)
        product.id = id
        product.model_name = name
        product.model_code = f"C{id:03d}"
        product.standard_diameter = diameter
        product.tolerance_upper = upper
        product.tolerance_lower = lower
        product.description = desc
        product.is_active = True
        product.dxf_file_path = None
        product.tolerance_range = f"+{upper:.3f}/{lower:.3f}"
        product.diameter_range = (diameter + lower, diameter + upper)
        return product
    
    @patch('modules.product_selection.get_product_manager')
    def test_dialog_initialization(self, mock_get_manager):
        """测试对话框初始化"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductSelectionDialog()
        
        # 验证基本属性
        self.assertEqual(dialog.windowTitle(), "产品型号选择")
        self.assertTrue(dialog.isModal())
        self.assertIsNotNone(dialog.product_table)
        self.assertIsNotNone(dialog.select_btn)
        self.assertIsNotNone(dialog.cancel_btn)
        
        # 验证表格列数
        self.assertEqual(dialog.product_table.columnCount(), 5)
        
        # 验证选择按钮初始状态
        self.assertFalse(dialog.select_btn.isEnabled())
    
    @patch('modules.product_selection.get_product_manager')
    def test_load_products(self, mock_get_manager):
        """测试加载产品列表"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductSelectionDialog()
        
        # 验证产品已加载到表格
        self.assertEqual(dialog.product_table.rowCount(), 3)
        
        # 验证第一行数据
        self.assertEqual(dialog.product_table.item(0, 0).text(), "TEST-001")
        self.assertEqual(dialog.product_table.item(0, 1).text(), "10.00")
        self.assertEqual(dialog.product_table.item(0, 2).text(), "+0.050/-0.050")
        self.assertEqual(dialog.product_table.item(0, 3).text(), "测试产品1")
        self.assertEqual(dialog.product_table.item(0, 4).text(), "启用")
    
    @patch('modules.product_selection.get_product_manager')
    def test_product_selection(self, mock_get_manager):
        """测试产品选择功能"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductSelectionDialog()
        
        # 模拟选择第一行
        dialog.product_table.selectRow(0)
        dialog.on_selection_changed()
        
        # 验证选择按钮已启用
        self.assertTrue(dialog.select_btn.isEnabled())
        
        # 验证选中的产品
        self.assertEqual(dialog.selected_product.model_name, "TEST-001")
        
        # 验证详情显示
        self.assertEqual(dialog.detail_values['model_name'].text(), "TEST-001")
        self.assertEqual(dialog.detail_values['standard_diameter'].text(), "10.000 mm")
    
    @patch('modules.product_selection.get_product_manager')
    def test_product_details_update(self, mock_get_manager):
        """测试产品详情更新"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductSelectionDialog()
        
        # 更新产品详情
        product = self.test_products[1]  # TEST-002
        dialog.update_product_details(product)
        
        # 验证详情显示
        self.assertEqual(dialog.detail_values['model_name'].text(), "TEST-002")
        self.assertEqual(dialog.detail_values['model_code'].text(), "C002")
        self.assertEqual(dialog.detail_values['standard_diameter'].text(), "12.000 mm")
        self.assertEqual(dialog.detail_values['tolerance_range'].text(), "+0.080/-0.080")
        self.assertEqual(dialog.detail_values['diameter_range'].text(), "11.920 - 12.080 mm")
        self.assertEqual(dialog.detail_values['description'].toPlainText(), "测试产品2")
    
    @patch('modules.product_selection.get_product_manager')
    def test_clear_product_details(self, mock_get_manager):
        """测试清空产品详情"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductSelectionDialog()
        
        # 先设置一些详情
        dialog.update_product_details(self.test_products[0])
        
        # 然后清空
        dialog.clear_product_details()
        
        # 验证详情已清空
        self.assertEqual(dialog.detail_values['model_name'].text(), "-")
        self.assertEqual(dialog.detail_values['model_code'].text(), "-")
        self.assertEqual(dialog.detail_values['standard_diameter'].text(), "-")
        self.assertEqual(dialog.detail_values['description'].toPlainText(), "")
    
    @patch('modules.product_selection.get_product_manager')
    def test_product_selected_signal(self, mock_get_manager):
        """测试产品选择信号"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductSelectionDialog()
        
        # 连接信号到模拟槽函数
        signal_received = []
        dialog.product_selected.connect(lambda product: signal_received.append(product))
        
        # 选择产品并确认
        dialog.selected_product = self.test_products[0]
        dialog.select_product()
        
        # 验证信号已发送
        self.assertEqual(len(signal_received), 1)
        self.assertEqual(signal_received[0].model_name, "TEST-001")
    
    @patch('modules.product_selection.get_product_manager')
    @patch('modules.product_selection.QMessageBox')
    def test_select_product_without_selection(self, mock_msgbox, mock_get_manager):
        """测试未选择产品时的确认操作"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductSelectionDialog()
        dialog.selected_product = None
        
        dialog.select_product()
        
        # 验证显示了警告消息
        mock_msgbox.warning.assert_called_once()
    
    @patch('modules.product_selection.get_product_manager')
    @patch('modules.product_selection.QMessageBox')
    def test_load_products_exception(self, mock_msgbox, mock_get_manager):
        """测试加载产品列表异常处理"""
        # 模拟异常
        self.mock_manager.get_all_products.side_effect = Exception("数据库错误")
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductSelectionDialog()
        dialog.load_products()
        
        # 验证显示了错误消息
        mock_msgbox.critical.assert_called_once()
    
    @patch('modules.product_selection.get_product_manager')
    @patch('modules.product_selection.ProductManagementDialog')
    def test_open_product_management(self, mock_management_dialog, mock_get_manager):
        """测试打开产品管理界面"""
        mock_get_manager.return_value = self.mock_manager
        
        # 模拟管理对话框
        mock_dialog_instance = Mock()
        mock_dialog_instance.exec.return_value = QDialog.Accepted
        mock_management_dialog.return_value = mock_dialog_instance
        
        dialog = ProductSelectionDialog()
        
        # 模拟点击管理按钮
        dialog.open_product_management()
        
        # 验证管理对话框被创建和显示
        mock_management_dialog.assert_called_once_with(dialog)
        mock_dialog_instance.exec.assert_called_once()


class TestProductQuickSelector(unittest.TestCase):
    """产品快速选择器测试"""
    
    @classmethod
    def setUpClass(cls):
        """类级别的设置"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """测试前置设置"""
        self.mock_manager = MagicMock(spec=ProductModelManager)
        self.test_products = [
            self._create_mock_product(1, "QUICK-001", 8.0),
            self._create_mock_product(2, "QUICK-002", 9.0),
        ]
        self.mock_manager.get_all_products.return_value = self.test_products
        self.mock_manager.get_product_by_name.return_value = self.test_products[0]
    
    def _create_mock_product(self, id, name, diameter):
        """创建模拟产品对象"""
        product = Mock(spec=ProductModel)
        product.id = id
        product.model_name = name
        product.standard_diameter = diameter
        product.is_active = True
        return product
    
    @patch('modules.product_selection.get_product_manager')
    def test_quick_selector_initialization(self, mock_get_manager):
        """测试快速选择器初始化"""
        mock_get_manager.return_value = self.mock_manager
        
        selector = ProductQuickSelector()
        
        self.assertIsNotNone(selector.product_manager)
        self.assertIsNone(selector.parent)
    
    @patch('modules.product_selection.get_product_manager')
    def test_show_selection_dialog(self, mock_get_manager):
        """测试显示选择对话框"""
        mock_get_manager.return_value = self.mock_manager
        
        selector = ProductQuickSelector()
        dialog = selector.show_selection_dialog()
        
        self.assertIsInstance(dialog, ProductSelectionDialog)
    
    @patch('modules.product_selection.get_product_manager')
    def test_get_active_products(self, mock_get_manager):
        """测试获取启用的产品列表"""
        mock_get_manager.return_value = self.mock_manager
        
        selector = ProductQuickSelector()
        products = selector.get_active_products()
        
        self.assertEqual(len(products), 2)
        self.mock_manager.get_all_products.assert_called_with(active_only=True)
    
    @patch('modules.product_selection.get_product_manager')
    def test_get_product_by_name(self, mock_get_manager):
        """测试根据名称获取产品"""
        mock_get_manager.return_value = self.mock_manager
        
        selector = ProductQuickSelector()
        product = selector.get_product_by_name("QUICK-001")
        
        self.assertIsNotNone(product)
        self.assertEqual(product.model_name, "QUICK-001")
        self.mock_manager.get_product_by_name.assert_called_with("QUICK-001")


class TestProductSelectionIntegration(unittest.TestCase):
    """产品选择界面集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """类级别的设置"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """测试前置设置"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # 创建真实的产品管理器（用于集成测试）
        self.manager = ProductModelManager(db_path=self.db_path)
    
    def tearDown(self):
        """测试后置清理"""
        if self.manager:
            self.manager.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    @patch('modules.product_selection.get_product_manager')
    def test_real_data_integration(self, mock_get_manager):
        """测试与真实数据的集成"""
        mock_get_manager.return_value = self.manager
        
        # 添加测试产品
        self.manager.create_product(
            model_name="INTEGRATION-001",
            standard_diameter=11.0,
            tolerance_upper=0.06,
            tolerance_lower=-0.06,
            description="集成测试产品"
        )
        
        dialog = ProductSelectionDialog()
        
        # 验证产品已正确加载
        products = self.manager.get_all_products()
        self.assertGreaterEqual(len(products), 1)  # 至少有我们创建的产品
        
        # 验证表格显示
        self.assertGreaterEqual(dialog.product_table.rowCount(), 1)
    
    @patch('modules.product_selection.get_product_manager')
    def test_selection_workflow(self, mock_get_manager):
        """测试完整的选择工作流"""
        mock_get_manager.return_value = self.manager
        
        # 创建测试产品
        test_product = self.manager.create_product(
            model_name="WORKFLOW-TEST",
            standard_diameter=13.0,
            tolerance_upper=0.07,
            tolerance_lower=-0.07,
            description="工作流测试产品"
        )
        
        dialog = ProductSelectionDialog()
        
        # 模拟用户选择操作
        # 1. 找到测试产品的行
        target_row = -1
        for row in range(dialog.product_table.rowCount()):
            if dialog.product_table.item(row, 0).text() == "WORKFLOW-TEST":
                target_row = row
                break
        
        self.assertNotEqual(target_row, -1, "未找到测试产品")
        
        # 2. 选择该行
        dialog.product_table.selectRow(target_row)
        dialog.on_selection_changed()
        
        # 3. 验证选择状态
        self.assertTrue(dialog.select_btn.isEnabled())
        self.assertEqual(dialog.selected_product.model_name, "WORKFLOW-TEST")
        
        # 4. 验证详情显示
        self.assertEqual(dialog.detail_values['model_name'].text(), "WORKFLOW-TEST")
        self.assertEqual(dialog.detail_values['standard_diameter'].text(), "13.000 mm")


if __name__ == '__main__':
    unittest.main()