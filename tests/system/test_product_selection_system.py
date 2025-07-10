"""
产品型号选择功能系统测试
端到端测试完整的用户工作流程
"""

import unittest
import tempfile
import os
import sys
import time
from unittest.mock import patch, MagicMock, Mock
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

# 添加src路径以便导入模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

from models.product_model import ProductModelManager, ProductModel
from modules.product_selection import ProductSelectionDialog, ProductQuickSelector
from modules.product_management import ProductManagementDialog


class TestProductSelectionSystemWorkflow(unittest.TestCase):
    """产品选择系统工作流测试"""
    
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
    
    def tearDown(self):
        """测试后置清理"""
        if self.manager:
            self.manager.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    @patch('models.product_model.get_product_manager')
    @patch('modules.product_selection.get_product_manager')
    @patch('modules.product_management.get_product_manager')
    def test_complete_product_management_workflow(self, mock_mgmt_manager, mock_sel_manager, mock_model_manager):
        """测试完整的产品管理工作流"""
        # 统一使用同一个管理器实例
        mock_mgmt_manager.return_value = self.manager
        mock_sel_manager.return_value = self.manager
        mock_model_manager.return_value = self.manager
        
        # 场景1: 管理员创建新产品
        print("场景1: 管理员创建新产品")
        
        # 打开产品管理界面
        mgmt_dialog = ProductManagementDialog()
        initial_count = mgmt_dialog.product_table.rowCount()
        print(f"初始产品数量: {initial_count}")
        
        # 点击新增产品
        mgmt_dialog.add_product()
        
        # 填写产品信息
        product_data = {
            'model_name': 'SYS-TEST-001',
            'model_code': 'ST001',
            'standard_diameter': 22.0,
            'tolerance_upper': 0.18,
            'tolerance_lower': -0.18,
            'description': '系统测试产品1'
        }
        
        mgmt_dialog.model_name_edit.setText(product_data['model_name'])
        mgmt_dialog.model_code_edit.setText(product_data['model_code'])
        mgmt_dialog.standard_diameter_spin.setValue(product_data['standard_diameter'])
        mgmt_dialog.tolerance_upper_spin.setValue(product_data['tolerance_upper'])
        mgmt_dialog.tolerance_lower_spin.setValue(product_data['tolerance_lower'])
        mgmt_dialog.description_edit.setText(product_data['description'])
        
        # 验证表单有效性
        self.assertTrue(mgmt_dialog.validate_form())
        
        # 实际创建产品（模拟保存操作）
        created_product = self.manager.create_product(**product_data)
        self.assertIsNotNone(created_product)
        print(f"创建产品成功: {created_product.model_name}")
        
        # 场景2: 用户选择产品
        print("场景2: 用户选择产品")
        
        # 打开产品选择界面
        selection_dialog = ProductSelectionDialog()
        
        # 验证新创建的产品出现在列表中
        found_product = False
        target_row = -1
        for row in range(selection_dialog.product_table.rowCount()):
            if selection_dialog.product_table.item(row, 0).text() == product_data['model_name']:
                found_product = True
                target_row = row
                break
        
        self.assertTrue(found_product, "新创建的产品未在选择列表中找到")
        print(f"在选择列表中找到产品: 第{target_row}行")
        
        # 选择产品
        selection_dialog.product_table.selectRow(target_row)
        selection_dialog.on_selection_changed()
        
        # 验证产品详情显示
        self.assertEqual(selection_dialog.selected_product.model_name, product_data['model_name'])
        self.assertEqual(selection_dialog.detail_values['model_name'].text(), product_data['model_name'])
        self.assertEqual(selection_dialog.detail_values['model_code'].text(), product_data['model_code'])
        print("产品详情显示正确")
        
        # 模拟确认选择
        selected_products = []
        selection_dialog.product_selected.connect(lambda p: selected_products.append(p))
        selection_dialog.select_product()
        
        self.assertEqual(len(selected_products), 1)
        self.assertEqual(selected_products[0].model_name, product_data['model_name'])
        print("产品选择信号发送成功")
        
        # 场景3: 修改产品信息
        print("场景3: 修改产品信息")
        
        # 重新打开管理界面
        mgmt_dialog2 = ProductManagementDialog()
        
        # 找到并选择刚创建的产品
        found_in_mgmt = False
        for row in range(mgmt_dialog2.product_table.rowCount()):
            if mgmt_dialog2.product_table.item(row, 0).text() == product_data['model_name']:
                mgmt_dialog2.product_table.selectRow(row)
                mgmt_dialog2.on_selection_changed()
                found_in_mgmt = True
                break
        
        self.assertTrue(found_in_mgmt, "在管理界面中未找到产品")
        
        # 进入编辑模式
        mgmt_dialog2.edit_product()
        
        # 修改描述
        new_description = "系统测试产品1 - 已修改"
        mgmt_dialog2.description_edit.setText(new_description)
        
        # 实际更新产品
        updated_product = self.manager.update_product(
            created_product.id,
            description=new_description
        )
        self.assertEqual(updated_product.description, new_description)
        print("产品信息修改成功")
        
        # 场景4: 验证修改后的产品在选择界面中正确显示
        print("场景4: 验证修改后的产品显示")
        
        selection_dialog3 = ProductSelectionDialog()
        
        # 找到修改后的产品
        for row in range(selection_dialog3.product_table.rowCount()):
            if selection_dialog3.product_table.item(row, 0).text() == product_data['model_name']:
                selection_dialog3.product_table.selectRow(row)
                selection_dialog3.on_selection_changed()
                
                # 验证修改后的描述
                displayed_description = selection_dialog3.detail_values['description'].toPlainText()
                self.assertEqual(displayed_description, new_description)
                print("修改后的产品信息显示正确")
                break
        
        print("完整工作流测试通过")
    
    @patch('models.product_model.get_product_manager')
    @patch('modules.product_selection.get_product_manager')
    @patch('modules.product_management.get_product_manager')
    def test_error_recovery_workflow(self, mock_mgmt_manager, mock_sel_manager, mock_model_manager):
        """测试错误恢复工作流"""
        mock_mgmt_manager.return_value = self.manager
        mock_sel_manager.return_value = self.manager
        mock_model_manager.return_value = self.manager
        
        print("测试错误恢复工作流")
        
        # 场景1: 尝试创建重复名称的产品
        mgmt_dialog = ProductManagementDialog()
        
        # 先创建一个产品
        original_product = self.manager.create_product(
            model_name="DUPLICATE-TEST",
            standard_diameter=15.0,
            tolerance_upper=0.10,
            tolerance_lower=-0.10
        )
        
        # 尝试创建同名产品
        mgmt_dialog.add_product()
        mgmt_dialog.model_name_edit.setText("DUPLICATE-TEST")
        mgmt_dialog.standard_diameter_spin.setValue(16.0)
        mgmt_dialog.tolerance_upper_spin.setValue(0.11)
        mgmt_dialog.tolerance_lower_spin.setValue(-0.11)
        
        # 应该验证通过，但实际保存时会失败
        self.assertTrue(mgmt_dialog.validate_form())
        
        # 模拟保存失败
        with self.assertRaises(ValueError):
            self.manager.create_product(
                model_name="DUPLICATE-TEST",
                standard_diameter=16.0,
                tolerance_upper=0.11,
                tolerance_lower=-0.11
            )
        
        print("重复名称错误处理正确")
        
        # 场景2: 测试无效数据的处理
        mgmt_dialog.clear_form()
        mgmt_dialog.add_product()
        
        # 设置无效的公差值
        mgmt_dialog.model_name_edit.setText("INVALID-TEST")
        mgmt_dialog.standard_diameter_spin.setValue(10.0)
        mgmt_dialog.tolerance_upper_spin.setValue(-0.05)  # 错误：上限为负
        mgmt_dialog.tolerance_lower_spin.setValue(0.05)   # 错误：下限为正
        
        # 验证表单应该失败
        self.assertFalse(mgmt_dialog.validate_form())
        print("无效数据验证正确")
    
    @patch('models.product_model.get_product_manager')
    @patch('modules.product_selection.get_product_manager')
    def test_performance_with_large_dataset(self, mock_sel_manager, mock_model_manager):
        """测试大数据集性能"""
        mock_sel_manager.return_value = self.manager
        mock_model_manager.return_value = self.manager
        
        print("测试大数据集性能")
        
        # 创建100个产品（模拟大数据集）
        start_time = time.time()
        
        products = []
        for i in range(100):
            try:
                product = self.manager.create_product(
                    model_name=f"PERF-{i:03d}",
                    standard_diameter=10.0 + i * 0.1,
                    tolerance_upper=0.05 + i * 0.001,
                    tolerance_lower=-(0.05 + i * 0.001),
                    description=f"性能测试产品{i}"
                )
                products.append(product)
            except Exception as e:
                print(f"创建产品{i}失败: {str(e)}")
        
        create_time = time.time() - start_time
        print(f"创建{len(products)}个产品耗时: {create_time:.2f}秒")
        
        # 测试选择界面加载性能
        start_time = time.time()
        selection_dialog = ProductSelectionDialog()
        load_time = time.time() - start_time
        
        print(f"加载选择界面耗时: {load_time:.2f}秒")
        print(f"显示产品数量: {selection_dialog.product_table.rowCount()}")
        
        # 验证加载时间合理（应该在5秒内）
        self.assertLess(load_time, 5.0, "选择界面加载时间过长")
        
        # 测试搜索性能
        start_time = time.time()
        search_results = self.manager.search_products("PERF")
        search_time = time.time() - start_time
        
        print(f"搜索耗时: {search_time:.2f}秒，找到{len(search_results)}个结果")
        self.assertLess(search_time, 1.0, "搜索时间过长")
    
    @patch('models.product_model.get_product_manager')
    @patch('modules.product_selection.get_product_manager')
    @patch('modules.product_management.get_product_manager')
    def test_concurrent_access_workflow(self, mock_mgmt_manager, mock_sel_manager, mock_model_manager):
        """测试并发访问工作流"""
        mock_mgmt_manager.return_value = self.manager
        mock_sel_manager.return_value = self.manager
        mock_model_manager.return_value = self.manager
        
        print("测试并发访问工作流")
        
        # 模拟多个用户同时访问
        # 用户1: 创建产品选择对话框
        selection_dialog1 = ProductSelectionDialog()
        initial_count1 = selection_dialog1.product_table.rowCount()
        
        # 用户2: 创建产品管理对话框
        mgmt_dialog = ProductManagementDialog()
        initial_count2 = mgmt_dialog.product_table.rowCount()
        
        # 验证两个界面看到相同的数据
        self.assertEqual(initial_count1, initial_count2)
        
        # 用户2创建新产品
        new_product = self.manager.create_product(
            model_name="CONCURRENT-TEST",
            standard_diameter=28.0,
            tolerance_upper=0.22,
            tolerance_lower=-0.22,
            description="并发测试产品"
        )
        
        # 用户1刷新界面（模拟重新加载）
        selection_dialog2 = ProductSelectionDialog()
        new_count = selection_dialog2.product_table.rowCount()
        
        # 验证用户1能看到新创建的产品
        self.assertEqual(new_count, initial_count1 + 1)
        print("并发访问数据一致性验证通过")
    
    @patch('models.product_model.get_product_manager')
    @patch('modules.product_selection.get_product_manager')
    def test_user_experience_workflow(self, mock_sel_manager, mock_model_manager):
        """测试用户体验工作流"""
        mock_sel_manager.return_value = self.manager
        mock_model_manager.return_value = self.manager
        
        print("测试用户体验工作流")
        
        # 创建一些测试产品
        test_products = []
        for i in range(5):
            product = self.manager.create_product(
                model_name=f"UX-TEST-{i:02d}",
                standard_diameter=5.0 + i * 2.0,
                tolerance_upper=0.02 + i * 0.01,
                tolerance_lower=-(0.02 + i * 0.01),
                description=f"用户体验测试产品{i}"
            )
            test_products.append(product)
        
        # 场景1: 用户快速浏览产品列表
        selection_dialog = ProductSelectionDialog()
        
        # 验证产品按名称排序显示
        displayed_names = []
        for row in range(selection_dialog.product_table.rowCount()):
            name = selection_dialog.product_table.item(row, 0).text()
            if name.startswith("UX-TEST"):
                displayed_names.append(name)
        
        # 验证排序正确
        sorted_names = sorted(displayed_names)
        self.assertEqual(displayed_names, sorted_names, "产品列表未正确排序")
        print("产品列表排序正确")
        
        # 场景2: 用户查看产品详情
        for i, name in enumerate(displayed_names[:3]):  # 测试前3个
            for row in range(selection_dialog.product_table.rowCount()):
                if selection_dialog.product_table.item(row, 0).text() == name:
                    selection_dialog.product_table.selectRow(row)
                    selection_dialog.on_selection_changed()
                    
                    # 验证详情正确显示
                    self.assertEqual(selection_dialog.detail_values['model_name'].text(), name)
                    self.assertNotEqual(selection_dialog.detail_values['standard_diameter'].text(), "-")
                    self.assertNotEqual(selection_dialog.detail_values['tolerance_range'].text(), "-")
                    break
        
        print("产品详情显示正确")
        
        # 场景3: 用户进行产品选择
        # 选择第一个测试产品
        for row in range(selection_dialog.product_table.rowCount()):
            if selection_dialog.product_table.item(row, 0).text() == displayed_names[0]:
                selection_dialog.product_table.selectRow(row)
                selection_dialog.on_selection_changed()
                
                # 验证选择按钮状态
                self.assertTrue(selection_dialog.select_btn.isEnabled())
                
                # 模拟确认选择
                selected_products = []
                selection_dialog.product_selected.connect(lambda p: selected_products.append(p))
                selection_dialog.select_product()
                
                self.assertEqual(len(selected_products), 1)
                self.assertEqual(selected_products[0].model_name, displayed_names[0])
                break
        
        print("产品选择流程正确")


class TestMainWindowSystemIntegration(unittest.TestCase):
    """主窗口系统集成测试"""
    
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
    
    def test_main_window_system_simulation(self):
        """主窗口系统模拟测试"""
        print("主窗口系统模拟测试")
        
        # 由于主窗口可能有复杂的依赖，我们创建一个简化的模拟
        class MockMainWindowSystem:
            def __init__(self, product_manager):
                self.product_manager = product_manager
                self.current_product = None
                self.ui_state = "ready"
                self.log = []
            
            def select_product_model(self):
                """模拟产品选择"""
                self.log.append("打开产品选择对话框")
                # 模拟用户选择了一个产品
                products = self.product_manager.get_all_products()
                if products:
                    selected_product = products[0]
                    self.on_product_selected(selected_product)
                    return selected_product
                return None
            
            def on_product_selected(self, product):
                """模拟产品选择处理"""
                self.current_product = product
                self.ui_state = "product_selected"
                self.log.append(f"选择产品: {product.model_name}")
                self.update_product_info_display(product)
            
            def update_product_info_display(self, product):
                """模拟更新产品信息显示"""
                self.log.append(f"显示产品信息: {product.model_name}")
                self.log.append(f"标准直径: {product.standard_diameter}mm")
                self.log.append(f"公差范围: {product.tolerance_range}")
            
            def open_product_management(self):
                """模拟打开产品管理"""
                self.log.append("打开产品管理界面")
                self.ui_state = "management_open"
        
        # 创建模拟系统
        mock_system = MockMainWindowSystem(self.manager)
        
        # 测试产品选择流程
        selected = mock_system.select_product_model()
        self.assertIsNotNone(selected)
        self.assertEqual(mock_system.ui_state, "product_selected")
        self.assertIsNotNone(mock_system.current_product)
        
        # 验证日志记录
        expected_logs = [
            "打开产品选择对话框",
            f"选择产品: {selected.model_name}",
            f"显示产品信息: {selected.model_name}"
        ]
        
        for expected in expected_logs:
            self.assertIn(expected, mock_system.log)
        
        # 测试产品管理流程
        mock_system.open_product_management()
        self.assertEqual(mock_system.ui_state, "management_open")
        self.assertIn("打开产品管理界面", mock_system.log)
        
        print("主窗口系统模拟测试通过")
        print(f"处理日志: {len(mock_system.log)}条")


if __name__ == '__main__':
    # 设置测试详细输出
    unittest.main(verbosity=2)