#!/usr/bin/env python3
"""
搜索功能集成测试和系统测试
流程2：集成测试和系统测试
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 设置Qt应用程序
os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # 无头模式测试

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QStringListModel
from PySide6.QtTest import QTest

# 导入被测试的组件
from aidcis2.ui.main_window import AIDCIS2MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


class SearchIntegrationTest(unittest.TestCase):
    """搜索功能集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """设置每个测试"""
        self.main_window = AIDCIS2MainWindow()
        
        # 创建测试数据
        self.test_holes = {
            'H00001': HoleData('H00001', 10.0, 20.0, 8.865, HoleStatus.PENDING),
            'H00002': HoleData('H00002', 30.0, 40.0, 8.865, HoleStatus.QUALIFIED),
            'H00101': HoleData('H00101', 50.0, 60.0, 8.865, HoleStatus.DEFECTIVE),
            'H00201': HoleData('H00201', 70.0, 80.0, 8.865, HoleStatus.PENDING),
            'H01001': HoleData('H01001', 90.0, 100.0, 8.865, HoleStatus.QUALIFIED),
        }
        
        self.test_collection = HoleCollection(
            holes=self.test_holes,
            metadata={'test': True}
        )
    
    def test_completer_integration(self):
        """测试自动补全器集成"""
        print("\n🔧 测试1：自动补全器集成测试")
        
        # 1. 验证补全器初始化
        self.assertIsNotNone(self.main_window.completer)
        self.assertIsNotNone(self.main_window.completer_model)
        self.assertEqual(self.main_window.search_input.completer(), self.main_window.completer)
        print("   ✅ 补全器初始化正确")
        
        # 2. 设置测试数据
        self.main_window.hole_collection = self.test_collection
        self.main_window.update_completer_data()
        
        # 3. 验证补全数据
        string_list = self.main_window.completer_model.stringList()
        expected_ids = ['H00001', 'H00002', 'H00101', 'H00201', 'H01001']
        self.assertEqual(sorted(string_list), sorted(expected_ids))
        print("   ✅ 补全数据更新正确")
        
        # 4. 验证补全器配置
        self.assertEqual(self.main_window.completer.caseSensitivity(), Qt.CaseInsensitive)
        self.assertEqual(self.main_window.completer.filterMode(), Qt.MatchContains)
        self.assertEqual(self.main_window.completer.maxVisibleItems(), 10)
        print("   ✅ 补全器配置正确")
    
    def test_search_button_integration(self):
        """测试搜索按钮集成"""
        print("\n🔧 测试2：搜索按钮集成测试")
        
        # 1. 验证搜索按钮存在
        self.assertIsNotNone(self.main_window.search_btn)
        self.assertEqual(self.main_window.search_btn.text(), "搜索")
        print("   ✅ 搜索按钮创建正确")
        
        # 2. 设置测试数据
        self.main_window.hole_collection = self.test_collection
        
        # 3. 模拟图形视图
        mock_graphics_view = Mock()
        self.main_window.graphics_view = mock_graphics_view
        
        # 4. 测试搜索功能
        self.main_window.search_input.setText("H001")
        self.main_window.perform_search()
        
        # 5. 验证搜索调用
        mock_graphics_view.highlight_holes.assert_called_once()
        args, kwargs = mock_graphics_view.highlight_holes.call_args
        self.assertTrue(kwargs.get('search_highlight', False))
        print("   ✅ 搜索功能调用正确")
    
    def test_search_logic_integration(self):
        """测试搜索逻辑集成"""
        print("\n🔧 测试3：搜索逻辑集成测试")
        
        # 设置测试数据
        self.main_window.hole_collection = self.test_collection
        mock_graphics_view = Mock()
        self.main_window.graphics_view = mock_graphics_view
        
        # 测试用例
        test_cases = [
            ("H00", 3),  # 应该匹配 H00001, H00002, H00101, H00201
            ("001", 3),  # 应该匹配 H00001, H00101, H01001
            ("H001", 2), # 应该匹配 H00101, H01001
            ("qualified", 0), # 不应该匹配任何（只搜索ID）
            ("", 0),     # 空搜索应该清空
        ]
        
        for search_text, expected_count in test_cases:
            with self.subTest(search_text=search_text):
                self.main_window.search_input.setText(search_text)
                self.main_window.perform_search()
                
                if expected_count == 0 and search_text == "":
                    # 空搜索应该调用清空
                    mock_graphics_view.highlight_holes.assert_called_with([], search_highlight=True)
                elif expected_count > 0:
                    # 验证调用了highlight_holes
                    self.assertTrue(mock_graphics_view.highlight_holes.called)
                
                print(f"   ✅ 搜索 '{search_text}' 测试通过")
    
    def test_keyboard_shortcuts_integration(self):
        """测试键盘快捷键集成"""
        print("\n🔧 测试4：键盘快捷键集成测试")
        
        # 设置测试数据
        self.main_window.hole_collection = self.test_collection
        mock_graphics_view = Mock()
        self.main_window.graphics_view = mock_graphics_view
        
        # 测试回车键触发搜索
        self.main_window.search_input.setText("H001")
        
        # 模拟回车键按下
        QTest.keyPress(self.main_window.search_input, Qt.Key_Return)
        
        # 验证搜索被触发
        self.assertTrue(mock_graphics_view.highlight_holes.called)
        print("   ✅ 回车键触发搜索正确")


class SearchSystemTest(unittest.TestCase):
    """搜索功能系统测试"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """设置每个测试"""
        self.main_window = AIDCIS2MainWindow()
    
    def test_end_to_end_search_workflow(self):
        """测试端到端搜索工作流"""
        print("\n🔧 系统测试1：端到端搜索工作流")
        
        # 1. 模拟加载数据
        print("   📝 步骤1：模拟数据加载")
        with patch.object(self.main_window, '_create_simulation_data') as mock_create:
            # 设置模拟数据
            test_holes = {
                f'H{i:05d}': HoleData(f'H{i:05d}', i*10.0, i*10.0, 8.865, HoleStatus.PENDING)
                for i in range(1, 101)  # 100个孔位
            }
            test_collection = HoleCollection(holes=test_holes, metadata={'test': True})
            
            def mock_create_data():
                self.main_window.hole_collection = test_collection
                self.main_window.update_completer_data()
            
            mock_create.side_effect = mock_create_data
            
            # 触发数据加载
            self.main_window.load_simulation_data()
            
            # 验证数据加载
            self.assertIsNotNone(self.main_window.hole_collection)
            self.assertEqual(len(self.main_window.hole_collection), 100)
            print("   ✅ 数据加载成功")
        
        # 2. 验证补全数据更新
        print("   📝 步骤2：验证补全数据")
        string_list = self.main_window.completer_model.stringList()
        self.assertEqual(len(string_list), 100)
        self.assertIn('H00001', string_list)
        self.assertIn('H00100', string_list)
        print("   ✅ 补全数据更新成功")
        
        # 3. 模拟用户搜索操作
        print("   📝 步骤3：模拟用户搜索")
        mock_graphics_view = Mock()
        self.main_window.graphics_view = mock_graphics_view
        
        # 用户输入搜索文本
        self.main_window.search_input.setText("H001")
        
        # 用户点击搜索按钮
        QTest.mouseClick(self.main_window.search_btn, Qt.LeftButton)
        
        # 验证搜索结果
        mock_graphics_view.highlight_holes.assert_called_once()
        args, kwargs = mock_graphics_view.highlight_holes.call_args
        matched_holes = args[0]
        self.assertTrue(len(matched_holes) > 0)
        self.assertTrue(kwargs.get('search_highlight', False))
        print("   ✅ 搜索操作成功")
    
    def test_performance_with_large_dataset(self):
        """测试大数据集性能"""
        print("\n🔧 系统测试2：大数据集性能测试")
        
        # 创建大数据集（1000个孔位）
        large_holes = {
            f'H{i:05d}': HoleData(f'H{i:05d}', i*10.0, i*10.0, 8.865, HoleStatus.PENDING)
            for i in range(1, 1001)
        }
        large_collection = HoleCollection(holes=large_holes, metadata={'test': True})
        
        # 设置数据
        self.main_window.hole_collection = large_collection
        
        # 测试补全数据更新性能
        import time
        start_time = time.time()
        self.main_window.update_completer_data()
        update_time = time.time() - start_time
        
        self.assertLess(update_time, 1.0)  # 应该在1秒内完成
        print(f"   ✅ 补全数据更新耗时: {update_time:.3f}秒")
        
        # 测试搜索性能
        mock_graphics_view = Mock()
        self.main_window.graphics_view = mock_graphics_view
        
        start_time = time.time()
        self.main_window.search_input.setText("H001")
        self.main_window.perform_search()
        search_time = time.time() - start_time
        
        self.assertLess(search_time, 0.1)  # 搜索应该在0.1秒内完成
        print(f"   ✅ 搜索操作耗时: {search_time:.3f}秒")
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n🔧 系统测试3：错误处理测试")
        
        # 1. 测试无数据时的搜索
        self.main_window.hole_collection = None
        self.main_window.search_input.setText("H001")
        
        # 应该不会抛出异常
        try:
            self.main_window.perform_search()
            print("   ✅ 无数据搜索处理正确")
        except Exception as e:
            self.fail(f"无数据搜索时抛出异常: {e}")
        
        # 2. 测试空字符串搜索
        test_collection = HoleCollection(holes={}, metadata={})
        self.main_window.hole_collection = test_collection
        mock_graphics_view = Mock()
        self.main_window.graphics_view = mock_graphics_view
        
        self.main_window.search_input.setText("")
        self.main_window.perform_search()
        
        # 应该调用清空高亮
        mock_graphics_view.highlight_holes.assert_called_with([], search_highlight=True)
        print("   ✅ 空字符串搜索处理正确")


def run_integration_tests():
    """运行集成测试和系统测试"""
    print("=" * 80)
    print("🔧 搜索功能集成测试和系统测试")
    print("流程2：集成测试和系统测试")
    print("=" * 80)
    
    # 创建测试套件
    integration_suite = unittest.TestLoader().loadTestsFromTestCase(SearchIntegrationTest)
    system_suite = unittest.TestLoader().loadTestsFromTestCase(SearchSystemTest)
    
    # 运行集成测试
    print("\n📋 集成测试阶段")
    print("-" * 50)
    integration_runner = unittest.TextTestRunner(verbosity=0)
    integration_result = integration_runner.run(integration_suite)
    
    # 运行系统测试
    print("\n📋 系统测试阶段")
    print("-" * 50)
    system_runner = unittest.TextTestRunner(verbosity=0)
    system_result = system_runner.run(system_suite)
    
    # 汇总结果
    total_tests = integration_result.testsRun + system_result.testsRun
    total_failures = len(integration_result.failures) + len(system_result.failures)
    total_errors = len(integration_result.errors) + len(system_result.errors)
    
    print("\n" + "=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)
    print(f"总测试数: {total_tests}")
    print(f"成功: {total_tests - total_failures - total_errors}")
    print(f"失败: {total_failures}")
    print(f"错误: {total_errors}")
    
    if total_failures == 0 and total_errors == 0:
        print("\n🎉 所有测试通过！搜索功能集成测试和系统测试完成")
        print("✅ 可以进入下一个流程：用户验收测试")
    else:
        print("\n❌ 存在测试失败，需要修复后重新测试")
    
    print("=" * 80)
    
    return total_failures == 0 and total_errors == 0


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
