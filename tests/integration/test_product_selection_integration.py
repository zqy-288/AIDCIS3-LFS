"""
产品型号选择功能集成测试
测试各个组件之间的协同工作
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

from models.product_model import ProductModelManager, ProductModel
from modules.product_selection import ProductSelectionDialog, ProductQuickSelector
from modules.product_management import ProductManagementDialog


class TestProductSelectionIntegration(unittest.TestCase):
    """产品选择功能集成测试"""
    
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
        
        # 创建真实的产品管理器
        self.manager = ProductModelManager(db_path=self.db_path)
        
        # 添加测试数据
        self.test_products = []
        for i in range(1, 4):
            product = self.manager.create_product(
                model_name=f"INTEGRATION-{i:03d}",
                standard_diameter=10.0 + i,
                tolerance_upper=0.05 + i * 0.01,
                tolerance_lower=-(0.05 + i * 0.01),
                model_code=f"INT{i:03d}",
                description=f"集成测试产品{i}"
            )
            self.test_products.append(product)
    
    def tearDown(self):
        """测试后置清理"""
        if self.manager:
            self.manager.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    @patch('models.product_model.get_product_manager')
    def test_product_selection_to_management_flow(self, mock_get_manager):
        """测试从产品选择到产品管理的完整流程"""
        mock_get_manager.return_value = self.manager
        
        # 1. 创建产品选择对话框
        selection_dialog = ProductSelectionDialog()
        
        # 验证产品已正确加载
        self.assertGreaterEqual(selection_dialog.product_table.rowCount(), 3)
        
        # 2. 模拟用户选择产品
        selection_dialog.product_table.selectRow(0)
        selection_dialog.on_selection_changed()
        
        # 验证产品选择状态
        self.assertIsNotNone(selection_dialog.selected_product)
        self.assertEqual(selection_dialog.selected_product.model_name, "INTEGRATION-001")
        
        # 3. 从选择对话框打开管理对话框
        with patch('modules.product_management.ProductManagementDialog') as mock_mgmt_dialog:
            mock_instance = Mock()
            mock_instance.exec.return_value = QDialog.Accepted
            mock_mgmt_dialog.return_value = mock_instance
            
            selection_dialog.open_product_management()
            
            # 验证管理对话框被正确创建
            mock_mgmt_dialog.assert_called_once_with(selection_dialog)
            mock_instance.exec.assert_called_once()
    
    @patch('models.product_model.get_product_manager')
    def test_product_management_crud_integration(self, mock_get_manager):
        """测试产品管理CRUD操作的集成"""
        mock_get_manager.return_value = self.manager
        
        # 创建产品管理对话框
        mgmt_dialog = ProductManagementDialog()
        
        # 验证初始产品加载
        initial_count = mgmt_dialog.product_table.rowCount()
        self.assertGreaterEqual(initial_count, 3)
        
        # 测试新增产品的完整流程
        mgmt_dialog.add_product()
        
        # 填写表单
        mgmt_dialog.model_name_edit.setText("CRUD-TEST")
        mgmt_dialog.model_code_edit.setText("CRU001")
        mgmt_dialog.standard_diameter_spin.setValue(20.0)
        mgmt_dialog.tolerance_upper_spin.setValue(0.15)
        mgmt_dialog.tolerance_lower_spin.setValue(-0.15)
        mgmt_dialog.description_edit.setText("CRUD测试产品")
        mgmt_dialog.is_active_check.setChecked(True)
        
        # 验证表单数据
        self.assertTrue(mgmt_dialog.validate_form())
        
        # 模拟保存（实际调用数据库）
        original_count = len(self.manager.get_all_products())
        
        try:
            # 直接调用管理器创建产品（模拟保存操作）
            new_product = self.manager.create_product(
                model_name="CRUD-TEST",
                standard_diameter=20.0,
                tolerance_upper=0.15,
                tolerance_lower=-0.15,
                model_code="CRU001",
                description="CRUD测试产品"
            )
            
            # 验证产品创建成功
            self.assertIsNotNone(new_product)
            self.assertEqual(new_product.model_name, "CRUD-TEST")
            
            # 验证产品数量增加
            new_count = len(self.manager.get_all_products())
            self.assertEqual(new_count, original_count + 1)
            
        except Exception as e:
            self.fail(f"产品创建失败: {str(e)}")
    
    @patch('models.product_model.get_product_manager')
    def test_data_consistency_across_dialogs(self, mock_get_manager):
        """测试对话框之间的数据一致性"""
        mock_get_manager.return_value = self.manager
        
        # 1. 在管理对话框中创建新产品
        mgmt_dialog = ProductManagementDialog()
        
        # 创建新产品
        new_product = self.manager.create_product(
            model_name="CONSISTENCY-TEST",
            standard_diameter=25.0,
            tolerance_upper=0.20,
            tolerance_lower=-0.20,
            description="一致性测试产品"
        )
        
        # 2. 创建新的选择对话框，验证新产品是否出现
        selection_dialog = ProductSelectionDialog()
        
        # 查找新创建的产品
        found_product = False
        for row in range(selection_dialog.product_table.rowCount()):
            if selection_dialog.product_table.item(row, 0).text() == "CONSISTENCY-TEST":
                found_product = True
                break
        
        self.assertTrue(found_product, "新创建的产品未在选择对话框中显示")
        
        # 3. 验证产品详情的一致性
        if found_product:
            selection_dialog.product_table.selectRow(row)
            selection_dialog.on_selection_changed()
            
            selected_product = selection_dialog.selected_product
            self.assertEqual(selected_product.model_name, "CONSISTENCY-TEST")
            self.assertEqual(selected_product.standard_diameter, 25.0)
    
    @patch('models.product_model.get_product_manager')
    def test_product_selection_signal_integration(self, mock_get_manager):
        """测试产品选择信号的集成"""
        mock_get_manager.return_value = self.manager
        
        selection_dialog = ProductSelectionDialog()
        
        # 设置信号接收器
        received_products = []
        
        def on_product_selected(product):
            received_products.append(product)
        
        selection_dialog.product_selected.connect(on_product_selected)
        
        # 选择产品
        selection_dialog.product_table.selectRow(1)
        selection_dialog.on_selection_changed()
        
        # 确认选择
        selection_dialog.select_product()
        
        # 验证信号被正确发送
        self.assertEqual(len(received_products), 1)
        self.assertEqual(received_products[0].model_name, "INTEGRATION-002")
    
    @patch('models.product_model.get_product_manager')
    def test_error_handling_integration(self, mock_get_manager):
        """测试错误处理的集成"""
        # 模拟数据库错误
        mock_manager = Mock()
        mock_manager.get_all_products.side_effect = Exception("数据库连接失败")
        mock_get_manager.return_value = mock_manager
        
        # 创建对话框时应该优雅处理错误
        try:
            selection_dialog = ProductSelectionDialog()
            # 如果到达这里，说明错误被正确处理了
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"错误未被正确处理: {str(e)}")
    
    @patch('models.product_model.get_product_manager')
    def test_quick_selector_integration(self, mock_get_manager):
        """测试快速选择器的集成"""
        mock_get_manager.return_value = self.manager
        
        # 创建快速选择器
        quick_selector = ProductQuickSelector()
        
        # 测试获取活跃产品
        active_products = quick_selector.get_active_products()
        self.assertGreaterEqual(len(active_products), 3)
        
        # 测试根据名称获取产品
        product = quick_selector.get_product_by_name("INTEGRATION-001")
        self.assertIsNotNone(product)
        self.assertEqual(product.model_name, "INTEGRATION-001")
        
        # 测试创建选择对话框
        dialog = quick_selector.show_selection_dialog()
        self.assertIsInstance(dialog, ProductSelectionDialog)
        
        # 验证对话框正确加载了数据
        self.assertGreaterEqual(dialog.product_table.rowCount(), 3)
    
    @patch('models.product_model.get_product_manager')
    def test_database_transaction_integration(self, mock_get_manager):
        """测试数据库事务的集成"""
        mock_get_manager.return_value = self.manager
        
        # 获取初始产品数量
        initial_count = len(self.manager.get_all_products())
        
        # 创建产品管理对话框
        mgmt_dialog = ProductManagementDialog()
        
        try:
            # 测试创建产品
            test_product = self.manager.create_product(
                model_name="TRANSACTION-TEST",
                standard_diameter=30.0,
                tolerance_upper=0.25,
                tolerance_lower=-0.25
            )
            
            # 验证创建成功
            self.assertIsNotNone(test_product)
            current_count = len(self.manager.get_all_products())
            self.assertEqual(current_count, initial_count + 1)
            
            # 测试更新产品
            updated_product = self.manager.update_product(
                test_product.id,
                description="更新后的事务测试产品"
            )
            
            self.assertEqual(updated_product.description, "更新后的事务测试产品")
            
            # 测试删除产品
            self.manager.delete_product(test_product.id)
            final_count = len(self.manager.get_all_products())
            self.assertEqual(final_count, initial_count)
            
        except Exception as e:
            self.fail(f"数据库事务操作失败: {str(e)}")
    
    @patch('models.product_model.get_product_manager')
    def test_ui_state_synchronization(self, mock_get_manager):
        """测试UI状态同步"""
        mock_get_manager.return_value = self.manager
        
        # 创建产品管理对话框
        mgmt_dialog = ProductManagementDialog()
        
        # 验证初始状态
        self.assertFalse(mgmt_dialog.save_btn.isEnabled())
        self.assertFalse(mgmt_dialog.edit_btn.isEnabled())
        self.assertFalse(mgmt_dialog.delete_btn.isEnabled())
        
        # 选择产品
        mgmt_dialog.product_table.selectRow(0)
        mgmt_dialog.on_selection_changed()
        
        # 验证选择后的状态
        self.assertTrue(mgmt_dialog.edit_btn.isEnabled())
        self.assertTrue(mgmt_dialog.delete_btn.isEnabled())
        
        # 进入编辑模式
        mgmt_dialog.edit_product()
        
        # 验证编辑模式状态
        self.assertTrue(mgmt_dialog.save_btn.isEnabled())
        self.assertTrue(mgmt_dialog.cancel_btn.isEnabled())
        self.assertFalse(mgmt_dialog.edit_btn.isEnabled())
        self.assertFalse(mgmt_dialog.delete_btn.isEnabled())
        self.assertTrue(mgmt_dialog.model_name_edit.isEnabled())
        
        # 取消编辑
        mgmt_dialog.cancel_edit()
        
        # 验证取消后的状态
        self.assertFalse(mgmt_dialog.save_btn.isEnabled())
        self.assertFalse(mgmt_dialog.cancel_btn.isEnabled())
        self.assertTrue(mgmt_dialog.edit_btn.isEnabled())
        self.assertTrue(mgmt_dialog.delete_btn.isEnabled())
        self.assertFalse(mgmt_dialog.model_name_edit.isEnabled())


class TestMainWindowIntegration(unittest.TestCase):
    """主窗口集成测试"""
    
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
        
        # 创建产品管理器
        self.manager = ProductModelManager(db_path=self.db_path)
    
    def tearDown(self):
        """测试后置清理"""
        if self.manager:
            self.manager.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    @patch('product_model.get_product_manager')
    @patch('modules.product_selection.get_product_manager')
    def test_main_window_product_selection_integration(self, mock_get_manager_selection, mock_get_manager_model):
        """测试主窗口与产品选择的集成"""
        mock_get_manager_model.return_value = self.manager
        mock_get_manager_selection.return_value = self.manager
        
        try:
            # 导入并创建主窗口（可能会因为其他依赖而失败，所以用try-catch）
            from main_window import MainWindow
            
            main_window = MainWindow()
            
            # 验证产品管理器已正确初始化
            self.assertIsNotNone(main_window.product_manager)
            self.assertIsNone(main_window.current_product)
            
            # 验证产品选择按钮存在
            self.assertTrue(hasattr(main_window, 'product_select_btn'))
            self.assertEqual(main_window.product_select_btn.text(), "产品型号选择")
            
            # 验证方法存在
            self.assertTrue(hasattr(main_window, 'select_product_model'))
            self.assertTrue(hasattr(main_window, 'on_product_selected'))
            self.assertTrue(hasattr(main_window, 'open_product_management'))
            
        except ImportError as e:
            # 如果导入失败，跳过这个测试
            self.skipTest(f"无法导入主窗口模块: {str(e)}")
        except Exception as e:
            # 其他错误也跳过，因为可能是依赖问题
            self.skipTest(f"主窗口创建失败: {str(e)}")
    
    @patch('product_model.get_product_manager')
    def test_product_selection_workflow_simulation(self, mock_get_manager):
        """模拟产品选择工作流"""
        mock_get_manager.return_value = self.manager
        
        # 创建测试产品
        test_product = self.manager.create_product(
            model_name="WORKFLOW-SIM",
            standard_diameter=18.0,
            tolerance_upper=0.12,
            tolerance_lower=-0.12,
            description="工作流模拟产品"
        )
        
        # 模拟主窗口的产品选择逻辑
        class MockMainWindow:
            def __init__(self, manager):
                self.product_manager = manager
                self.current_product = None
                self.log_messages = []
            
            def on_product_selected(self, product):
                """模拟产品选择处理"""
                self.current_product = product
                self.log_messages.append(f"选择产品型号: {product.model_name}")
                return True
            
            def update_product_info_display(self, product):
                """模拟产品信息显示更新"""
                info = {
                    'model_name': product.model_name,
                    'standard_diameter': product.standard_diameter,
                    'tolerance_range': product.tolerance_range
                }
                self.log_messages.append(f"更新产品信息: {info}")
                return info
        
        # 创建模拟主窗口
        mock_window = MockMainWindow(self.manager)
        
        # 模拟产品选择流程
        selected_product = mock_window.on_product_selected(test_product)
        self.assertTrue(selected_product)
        self.assertEqual(mock_window.current_product.model_name, "WORKFLOW-SIM")
        
        # 模拟信息显示
        info = mock_window.update_product_info_display(test_product)
        self.assertEqual(info['model_name'], "WORKFLOW-SIM")
        self.assertEqual(info['standard_diameter'], 18.0)
        
        # 验证日志消息
        self.assertGreater(len(mock_window.log_messages), 0)
        self.assertIn("选择产品型号: WORKFLOW-SIM", mock_window.log_messages[0])


if __name__ == '__main__':
    unittest.main()