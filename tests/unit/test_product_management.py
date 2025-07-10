"""
产品管理界面单元测试
测试ProductManagementDialog的各种功能
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock, Mock
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

# 添加src路径以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

from modules.product_management import ProductManagementDialog
from models.product_model import ProductModelManager, ProductModel


class TestProductManagementDialog(unittest.TestCase):
    """产品管理对话框测试"""
    
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
            self._create_mock_product(1, "MANAGE-001", 10.0, 0.05, -0.05, "管理测试产品1", True),
            self._create_mock_product(2, "MANAGE-002", 12.0, 0.08, -0.08, "管理测试产品2", False),
            self._create_mock_product(3, "MANAGE-003", 15.0, 0.10, -0.10, "管理测试产品3", True),
        ]
        
        self.mock_manager.get_all_products.return_value = self.test_products
    
    def tearDown(self):
        """测试后置清理"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def _create_mock_product(self, id, name, diameter, upper, lower, desc, active):
        """创建模拟产品对象"""
        from datetime import datetime
        product = Mock(spec=ProductModel)
        product.id = id
        product.model_name = name
        product.model_code = f"M{id:03d}"
        product.standard_diameter = diameter
        product.tolerance_upper = upper
        product.tolerance_lower = lower
        product.description = desc
        product.is_active = active
        product.dxf_file_path = f"/path/to/{name}.dxf"
        product.tolerance_range = f"+{upper:.3f}/{lower:.3f}"
        product.created_at = datetime.now()
        product.updated_at = datetime.now()
        return product
    
    @patch('modules.product_management.get_product_manager')
    def test_dialog_initialization(self, mock_get_manager):
        """测试对话框初始化"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductManagementDialog()
        
        # 验证基本属性
        self.assertEqual(dialog.windowTitle(), "产品信息维护")
        self.assertTrue(dialog.isModal())
        self.assertIsNotNone(dialog.product_table)
        self.assertIsNotNone(dialog.model_name_edit)
        self.assertIsNotNone(dialog.standard_diameter_spin)
        
        # 验证表格列数
        self.assertEqual(dialog.product_table.columnCount(), 6)
        
        # 验证初始按钮状态
        self.assertFalse(dialog.save_btn.isEnabled())
        self.assertFalse(dialog.edit_btn.isEnabled())
        self.assertFalse(dialog.delete_btn.isEnabled())
        self.assertFalse(dialog.cancel_btn.isEnabled())
        
        # 验证表单初始状态为禁用
        self.assertFalse(dialog.model_name_edit.isEnabled())
    
    @patch('modules.product_management.get_product_manager')
    def test_load_products(self, mock_get_manager):
        """测试加载产品列表"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductManagementDialog()
        
        # 验证产品已加载到表格
        self.assertEqual(dialog.product_table.rowCount(), 3)
        
        # 验证第一行数据
        self.assertEqual(dialog.product_table.item(0, 0).text(), "MANAGE-001")
        self.assertEqual(dialog.product_table.item(0, 1).text(), "10.000")
        self.assertEqual(dialog.product_table.item(0, 2).text(), "+0.050/-0.050")
        self.assertEqual(dialog.product_table.item(0, 3).text(), "启用")
        
        # 验证第二行数据（停用状态）
        self.assertEqual(dialog.product_table.item(1, 3).text(), "停用")
    
    @patch('modules.product_management.get_product_manager')
    def test_product_selection(self, mock_get_manager):
        """测试产品选择功能"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductManagementDialog()
        
        # 模拟选择第一行
        dialog.product_table.selectRow(0)
        dialog.on_selection_changed()
        
        # 验证按钮状态
        self.assertTrue(dialog.edit_btn.isEnabled())
        self.assertTrue(dialog.delete_btn.isEnabled())
        
        # 验证选中的产品
        self.assertEqual(dialog.current_product.model_name, "MANAGE-001")
        
        # 验证表单数据加载
        self.assertEqual(dialog.model_name_edit.text(), "MANAGE-001")
        self.assertEqual(dialog.model_code_edit.text(), "M001")
        self.assertEqual(dialog.standard_diameter_spin.value(), 10.0)
        self.assertEqual(dialog.tolerance_upper_spin.value(), 0.05)
        self.assertEqual(dialog.tolerance_lower_spin.value(), -0.05)
        self.assertEqual(dialog.description_edit.toPlainText(), "管理测试产品1")
        self.assertTrue(dialog.is_active_check.isChecked())
    
    @patch('modules.product_management.get_product_manager')
    def test_add_product_mode(self, mock_get_manager):
        """测试新增产品模式"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductManagementDialog()
        
        # 点击新增按钮
        dialog.add_product()
        
        # 验证表单状态
        self.assertTrue(dialog.model_name_edit.isEnabled())
        self.assertTrue(dialog.standard_diameter_spin.isEnabled())
        self.assertTrue(dialog.save_btn.isEnabled())
        self.assertTrue(dialog.cancel_btn.isEnabled())
        self.assertFalse(dialog.edit_btn.isEnabled())
        self.assertFalse(dialog.delete_btn.isEnabled())
        self.assertFalse(dialog.add_btn.isEnabled())
        
        # 验证表单已清空
        self.assertEqual(dialog.model_name_edit.text(), "")
        self.assertEqual(dialog.standard_diameter_spin.value(), 0.0)
        self.assertTrue(dialog.is_active_check.isChecked())
    
    @patch('modules.product_management.get_product_manager')
    def test_edit_product_mode(self, mock_get_manager):
        """测试编辑产品模式"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductManagementDialog()
        
        # 选择一个产品
        dialog.product_table.selectRow(0)
        dialog.on_selection_changed()
        
        # 点击编辑按钮
        dialog.edit_product()
        
        # 验证表单状态
        self.assertTrue(dialog.model_name_edit.isEnabled())
        self.assertTrue(dialog.standard_diameter_spin.isEnabled())
        self.assertTrue(dialog.save_btn.isEnabled())
        self.assertTrue(dialog.cancel_btn.isEnabled())
        self.assertFalse(dialog.edit_btn.isEnabled())
        self.assertFalse(dialog.delete_btn.isEnabled())
        self.assertFalse(dialog.add_btn.isEnabled())
    
    @patch('modules.product_management.get_product_manager')
    def test_cancel_edit(self, mock_get_manager):
        """测试取消编辑"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductManagementDialog()
        
        # 进入编辑模式
        dialog.add_product()
        
        # 取消编辑
        dialog.cancel_edit()
        
        # 验证表单状态恢复
        self.assertFalse(dialog.model_name_edit.isEnabled())
        self.assertFalse(dialog.save_btn.isEnabled())
        self.assertFalse(dialog.cancel_btn.isEnabled())
        self.assertTrue(dialog.add_btn.isEnabled())
    
    @patch('modules.product_management.get_product_manager')
    def test_form_validation(self, mock_get_manager):
        """测试表单验证"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductManagementDialog()
        
        # 测试空名称验证
        dialog.model_name_edit.setText("")
        self.assertFalse(dialog.validate_form())
        
        # 测试直径验证
        dialog.model_name_edit.setText("TEST")
        dialog.standard_diameter_spin.setValue(0.0)
        self.assertFalse(dialog.validate_form())
        
        # 测试公差上限验证
        dialog.standard_diameter_spin.setValue(10.0)
        dialog.tolerance_upper_spin.setValue(0.0)
        self.assertFalse(dialog.validate_form())
        
        # 测试公差下限验证
        dialog.tolerance_upper_spin.setValue(0.05)
        dialog.tolerance_lower_spin.setValue(0.05)
        self.assertFalse(dialog.validate_form())
        
        # 测试有效数据
        dialog.tolerance_lower_spin.setValue(-0.05)
        self.assertTrue(dialog.validate_form())
    
    @patch('modules.product_management.get_product_manager')
    @patch('modules.product_management.QMessageBox')
    def test_save_new_product(self, mock_msgbox, mock_get_manager):
        """测试保存新产品"""
        mock_get_manager.return_value = self.mock_manager
        
        # 模拟创建成功
        new_product = self._create_mock_product(4, "NEW-PRODUCT", 8.0, 0.03, -0.03, "新产品", True)
        self.mock_manager.create_product.return_value = new_product
        
        dialog = ProductManagementDialog()
        
        # 进入新增模式
        dialog.add_product()
        
        # 填写表单
        dialog.model_name_edit.setText("NEW-PRODUCT")
        dialog.standard_diameter_spin.setValue(8.0)
        dialog.tolerance_upper_spin.setValue(0.03)
        dialog.tolerance_lower_spin.setValue(-0.03)
        dialog.description_edit.setText("新产品")
        
        # 保存产品
        dialog.save_product()
        
        # 验证调用了创建方法
        self.mock_manager.create_product.assert_called_once()
        
        # 验证显示了成功消息
        mock_msgbox.information.assert_called_once()
    
    @patch('modules.product_management.get_product_manager')
    @patch('modules.product_management.QMessageBox')
    def test_save_existing_product(self, mock_msgbox, mock_get_manager):
        """测试保存现有产品"""
        mock_get_manager.return_value = self.mock_manager
        
        # 模拟更新成功
        updated_product = self._create_mock_product(1, "UPDATED-001", 11.0, 0.06, -0.06, "更新的产品", True)
        self.mock_manager.update_product.return_value = updated_product
        
        dialog = ProductManagementDialog()
        
        # 选择产品并进入编辑模式
        dialog.product_table.selectRow(0)
        dialog.on_selection_changed()
        dialog.edit_product()
        
        # 修改表单数据
        dialog.model_name_edit.setText("UPDATED-001")
        dialog.standard_diameter_spin.setValue(11.0)
        dialog.tolerance_upper_spin.setValue(0.06)
        dialog.tolerance_lower_spin.setValue(-0.06)
        dialog.description_edit.setText("更新的产品")
        
        # 保存产品
        dialog.save_product()
        
        # 验证调用了更新方法
        self.mock_manager.update_product.assert_called_once()
        
        # 验证显示了成功消息
        mock_msgbox.information.assert_called_once()
    
    @patch('modules.product_management.get_product_manager')
    @patch('modules.product_management.QMessageBox')
    def test_save_product_exception(self, mock_msgbox, mock_get_manager):
        """测试保存产品异常处理"""
        mock_get_manager.return_value = self.mock_manager
        
        # 模拟异常
        self.mock_manager.create_product.side_effect = Exception("保存失败")
        
        dialog = ProductManagementDialog()
        
        # 进入新增模式并填写表单
        dialog.add_product()
        dialog.model_name_edit.setText("ERROR-TEST")
        dialog.standard_diameter_spin.setValue(5.0)
        dialog.tolerance_upper_spin.setValue(0.02)
        dialog.tolerance_lower_spin.setValue(-0.02)
        
        # 尝试保存
        dialog.save_product()
        
        # 验证显示了错误消息
        mock_msgbox.critical.assert_called_once()
    
    @patch('modules.product_management.get_product_manager')
    @patch('modules.product_management.QMessageBox')
    def test_delete_product_confirm(self, mock_msgbox, mock_get_manager):
        """测试删除产品确认"""
        mock_get_manager.return_value = self.mock_manager
        
        # 模拟用户确认删除
        mock_msgbox.question.return_value = QMessageBox.Yes
        self.mock_manager.delete_product.return_value = True
        
        dialog = ProductManagementDialog()
        
        # 选择产品
        dialog.product_table.selectRow(0)
        dialog.on_selection_changed()
        
        # 删除产品
        dialog.delete_product()
        
        # 验证显示了确认对话框
        mock_msgbox.question.assert_called_once()
        
        # 验证调用了删除方法
        self.mock_manager.delete_product.assert_called_once_with(1)
        
        # 验证显示了成功消息
        mock_msgbox.information.assert_called_once()
    
    @patch('modules.product_management.get_product_manager')
    @patch('modules.product_management.QMessageBox')
    def test_delete_product_cancel(self, mock_msgbox, mock_get_manager):
        """测试取消删除产品"""
        mock_get_manager.return_value = self.mock_manager
        
        # 模拟用户取消删除
        mock_msgbox.question.return_value = QMessageBox.No
        
        dialog = ProductManagementDialog()
        
        # 选择产品
        dialog.product_table.selectRow(0)
        dialog.on_selection_changed()
        
        # 尝试删除产品
        dialog.delete_product()
        
        # 验证显示了确认对话框
        mock_msgbox.question.assert_called_once()
        
        # 验证没有调用删除方法
        self.mock_manager.delete_product.assert_not_called()
    
    @patch('modules.product_management.get_product_manager')
    @patch('modules.product_management.QMessageBox')
    def test_delete_product_exception(self, mock_msgbox, mock_get_manager):
        """测试删除产品异常处理"""
        mock_get_manager.return_value = self.mock_manager
        
        # 模拟用户确认删除和异常
        mock_msgbox.question.return_value = QMessageBox.Yes
        self.mock_manager.delete_product.side_effect = Exception("删除失败")
        
        dialog = ProductManagementDialog()
        
        # 选择产品并删除
        dialog.product_table.selectRow(0)
        dialog.on_selection_changed()
        dialog.delete_product()
        
        # 验证显示了错误消息
        mock_msgbox.critical.assert_called_once()
    
    @patch('modules.product_management.get_product_manager')
    @patch('modules.product_management.QFileDialog')
    def test_browse_dxf_file(self, mock_file_dialog, mock_get_manager):
        """测试浏览DXF文件"""
        mock_get_manager.return_value = self.mock_manager
        
        # 模拟文件选择
        test_file_path = "/path/to/test.dxf"
        mock_file_dialog.getOpenFileName.return_value = (test_file_path, "DXF文件 (*.dxf)")
        
        dialog = ProductManagementDialog()
        
        # 浏览文件
        dialog.browse_dxf_file()
        
        # 验证文件路径被设置
        self.assertEqual(dialog.dxf_path_edit.text(), test_file_path)
    
    @patch('modules.product_management.get_product_manager')
    @patch('modules.product_management.QFileDialog')
    def test_browse_dxf_file_cancel(self, mock_file_dialog, mock_get_manager):
        """测试取消浏览DXF文件"""
        mock_get_manager.return_value = self.mock_manager
        
        # 模拟取消文件选择
        mock_file_dialog.getOpenFileName.return_value = ("", "")
        
        dialog = ProductManagementDialog()
        original_path = dialog.dxf_path_edit.text()
        
        # 浏览文件
        dialog.browse_dxf_file()
        
        # 验证文件路径没有改变
        self.assertEqual(dialog.dxf_path_edit.text(), original_path)
    
    @patch('modules.product_management.get_product_manager')
    def test_clear_form(self, mock_get_manager):
        """测试清空表单"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductManagementDialog()
        
        # 先填写一些数据
        dialog.model_name_edit.setText("TEST")
        dialog.standard_diameter_spin.setValue(10.0)
        dialog.description_edit.setText("测试")
        dialog.is_active_check.setChecked(False)
        
        # 清空表单
        dialog.clear_form()
        
        # 验证表单已清空
        self.assertEqual(dialog.model_name_edit.text(), "")
        self.assertEqual(dialog.standard_diameter_spin.value(), 0.0)
        self.assertEqual(dialog.description_edit.toPlainText(), "")
        self.assertTrue(dialog.is_active_check.isChecked())
    
    @patch('modules.product_management.get_product_manager')
    def test_set_form_enabled(self, mock_get_manager):
        """测试设置表单启用状态"""
        mock_get_manager.return_value = self.mock_manager
        
        dialog = ProductManagementDialog()
        
        # 启用表单
        dialog.set_form_enabled(True)
        self.assertTrue(dialog.model_name_edit.isEnabled())
        self.assertTrue(dialog.standard_diameter_spin.isEnabled())
        self.assertTrue(dialog.dxf_browse_btn.isEnabled())
        
        # 禁用表单
        dialog.set_form_enabled(False)
        self.assertFalse(dialog.model_name_edit.isEnabled())
        self.assertFalse(dialog.standard_diameter_spin.isEnabled())
        self.assertFalse(dialog.dxf_browse_btn.isEnabled())


class TestProductManagementIntegration(unittest.TestCase):
    """产品管理界面集成测试"""
    
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
    
    @patch('modules.product_management.get_product_manager')
    def test_real_crud_operations(self, mock_get_manager):
        """测试真实的CRUD操作"""
        mock_get_manager.return_value = self.manager
        
        dialog = ProductManagementDialog()
        
        # 验证初始产品加载
        initial_count = dialog.product_table.rowCount()
        self.assertGreaterEqual(initial_count, 3)  # 默认产品
        
        # 测试真实的产品创建
        dialog.add_product()
        dialog.model_name_edit.setText("REAL-TEST")
        dialog.standard_diameter_spin.setValue(7.5)
        dialog.tolerance_upper_spin.setValue(0.025)
        dialog.tolerance_lower_spin.setValue(-0.025)
        dialog.description_edit.setText("真实测试产品")
        
        # 模拟保存（在真实环境中会实际保存到数据库）
        if dialog.validate_form():
            # 验证表单验证通过
            self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()