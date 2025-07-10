"""
报告管理器组件单元测试
测试报告管理界面组件的功能
"""

import unittest
import tempfile
import os
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, QTimer

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# 模拟PySide6组件
class MockQWidget:
    def __init__(self):
        pass
    def setLayout(self, layout):
        pass

class MockQVBoxLayout:
    def __init__(self):
        pass
    def addWidget(self, widget):
        pass
    def addLayout(self, layout):
        pass

class MockQHBoxLayout:
    def __init__(self):
        pass
    def addWidget(self, widget):
        pass

class MockQTabWidget:
    def __init__(self):
        pass
    def addTab(self, widget, title):
        pass

class MockQLabel:
    def __init__(self, text=""):
        self.text = text
    def setText(self, text):
        self.text = text

class MockQPushButton:
    def __init__(self, text=""):
        self.text = text
        self._enabled = True
        self._clicked_handlers = []
    def clicked(self):
        return MockSignal()
    def setEnabled(self, enabled):
        self._enabled = enabled
    def setText(self, text):
        self.text = text

class MockQLineEdit:
    def __init__(self):
        self.text = ""
    def setText(self, text):
        self.text = text
    def text(self):
        return self.text

class MockQComboBox:
    def __init__(self):
        self.current_index = 0
        self.items = []
    def addItem(self, item):
        self.items.append(item)
    def currentIndex(self):
        return self.current_index
    def setCurrentIndex(self, index):
        self.current_index = index

class MockQProgressBar:
    def __init__(self):
        self.value = 0
        self.minimum = 0
        self.maximum = 100
    def setValue(self, value):
        self.value = value
    def setRange(self, min_val, max_val):
        self.minimum = min_val
        self.maximum = max_val

class MockQTableWidget:
    def __init__(self):
        self.row_count = 0
        self.column_count = 0
    def setRowCount(self, count):
        self.row_count = count
    def setColumnCount(self, count):
        self.column_count = count
    def setHorizontalHeaderLabels(self, labels):
        pass
    def setItem(self, row, col, item):
        pass

class MockQTableWidgetItem:
    def __init__(self, text=""):
        self.text = text

class MockQSignal:
    def __init__(self):
        self._handlers = []
    def connect(self, handler):
        self._handlers.append(handler)
    def emit(self, *args):
        for handler in self._handlers:
            handler(*args)

class MockSignal:
    def __init__(self):
        self._handlers = []
    def connect(self, handler):
        self._handlers.append(handler)
    def emit(self, *args):
        for handler in self._handlers:
            handler(*args)

# 模拟PySide6模块
sys.modules['PySide6'] = Mock()
sys.modules['PySide6.QtWidgets'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()

# 设置模拟类
import PySide6.QtWidgets as QtWidgets
import PySide6.QtCore as QtCore

QtWidgets.QWidget = MockQWidget
QtWidgets.QVBoxLayout = MockQVBoxLayout
QtWidgets.QHBoxLayout = MockQHBoxLayout
QtWidgets.QTabWidget = MockQTabWidget
QtWidgets.QLabel = MockQLabel
QtWidgets.QPushButton = MockQPushButton
QtWidgets.QLineEdit = MockQLineEdit
QtWidgets.QComboBox = MockQComboBox
QtWidgets.QProgressBar = MockQProgressBar
QtWidgets.QTableWidget = MockQTableWidget
QtWidgets.QTableWidgetItem = MockQTableWidgetItem

QtCore.QTimer = Mock()
QtCore.Signal = MockQSignal


class TestReportManagerWidget(unittest.TestCase):
    """测试报告管理器组件"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        
        # 延迟导入以确保模拟组件已设置
        from modules.report_manager_widget import ReportManagerWidget
        
        with patch('modules.report_manager_widget.ReportGenerator'):
            with patch('modules.report_manager_widget.EnhancedReportGenerator'):
                self.widget = ReportManagerWidget()
        
        # 设置临时目录
        self.widget.output_dir = Path(self.temp_dir)
        
        # 模拟测试数据
        self.test_workpiece_info = {
            'model': 'CP1400',
            'serial': 'SN-TEST-001', 
            'operator': '测试用户'
        }
        
        self.test_hole_data = {
            'total_holes': 100,
            'current_hole_id': 'H001'
        }
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_init(self):
        """测试初始化"""
        # 验证基本属性
        self.assertIsNotNone(self.widget.report_generator)
        self.assertIsNotNone(self.widget.enhanced_generator)
        self.assertEqual(self.widget.current_progress, 0)
        
    def test_setup_ui(self):
        """测试界面设置"""
        # 验证组件存在
        self.assertIsNotNone(self.widget.tab_widget)
        self.assertIsNotNone(self.widget.generation_tab)
        self.assertIsNotNone(self.widget.export_tab)
        self.assertIsNotNone(self.widget.history_tab)
        
    def test_setup_generation_tab(self):
        """测试报告生成选项卡设置"""
        # 验证输入组件
        self.assertIsNotNone(self.widget.model_input)
        self.assertIsNotNone(self.widget.serial_input)
        self.assertIsNotNone(self.widget.operator_input)
        
        # 验证按钮
        self.assertIsNotNone(self.widget.pdf_button)
        self.assertIsNotNone(self.widget.web_button)
        
        # 验证进度条
        self.assertIsNotNone(self.widget.progress_bar)
        self.assertIsNotNone(self.widget.status_label)
        
    def test_setup_export_tab(self):
        """测试数据导出选项卡设置"""
        # 验证导出按钮
        self.assertIsNotNone(self.widget.excel_button)
        self.assertIsNotNone(self.widget.csv_button)
        
        # 验证选项
        self.assertIsNotNone(self.widget.data_range_combo)
        
    def test_setup_history_tab(self):
        """测试报告历史选项卡设置"""
        # 验证搜索组件
        self.assertIsNotNone(self.widget.search_input)
        self.assertIsNotNone(self.widget.search_button)
        
        # 验证历史表格
        self.assertIsNotNone(self.widget.history_table)
        
        # 验证操作按钮
        self.assertIsNotNone(self.widget.open_button)
        self.assertIsNotNone(self.widget.delete_button)
        
    def test_get_workpiece_info(self):
        """测试获取工件信息"""
        # 设置输入值
        self.widget.model_input.setText("CP1400")
        self.widget.serial_input.setText("SN-TEST-001")
        self.widget.operator_input.setText("测试用户")
        
        workpiece_info = self.widget._get_workpiece_info()
        
        self.assertEqual(workpiece_info['model'], "CP1400")
        self.assertEqual(workpiece_info['serial'], "SN-TEST-001")
        self.assertEqual(workpiece_info['operator'], "测试用户")
        self.assertIn('start_time', workpiece_info)
        self.assertIn('end_time', workpiece_info)
        
    def test_validate_inputs_valid(self):
        """测试有效输入验证"""
        # 设置有效输入
        self.widget.model_input.setText("CP1400")
        self.widget.serial_input.setText("SN-TEST-001")
        self.widget.operator_input.setText("测试用户")
        
        is_valid, message = self.widget._validate_inputs()
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "")
        
    def test_validate_inputs_invalid(self):
        """测试无效输入验证"""
        # 测试空模型
        self.widget.model_input.setText("")
        self.widget.serial_input.setText("SN-TEST-001")
        self.widget.operator_input.setText("测试用户")
        
        is_valid, message = self.widget._validate_inputs()
        
        self.assertFalse(is_valid)
        self.assertIn("产品型号", message)
        
        # 测试空序列号
        self.widget.model_input.setText("CP1400")
        self.widget.serial_input.setText("")
        self.widget.operator_input.setText("测试用户")
        
        is_valid, message = self.widget._validate_inputs()
        
        self.assertFalse(is_valid)
        self.assertIn("工件序列号", message)
        
        # 测试空操作员
        self.widget.model_input.setText("CP1400")
        self.widget.serial_input.setText("SN-TEST-001")
        self.widget.operator_input.setText("")
        
        is_valid, message = self.widget._validate_inputs()
        
        self.assertFalse(is_valid)
        self.assertIn("操作员", message)
        
    def test_update_progress(self):
        """测试进度更新"""
        initial_progress = self.widget.current_progress
        
        self.widget._update_progress(50)
        
        # 验证进度值更新
        self.assertEqual(self.widget.progress_bar.value, 50)
        self.assertGreater(self.widget.current_progress, initial_progress)
        
    def test_update_status(self):
        """测试状态更新"""
        test_status = "正在生成报告..."
        
        self.widget._update_status(test_status)
        
        # 验证状态文本更新
        self.assertEqual(self.widget.status_label.text, test_status)
        
    def test_reset_progress(self):
        """测试进度重置"""
        # 设置一些进度
        self.widget._update_progress(75)
        self.widget._update_status("处理中...")
        
        # 重置进度
        self.widget._reset_progress()
        
        # 验证重置
        self.assertEqual(self.widget.progress_bar.value, 0)
        self.assertEqual(self.widget.status_label.text, "准备就绪")
        self.assertEqual(self.widget.current_progress, 0)
        
    @patch('modules.report_manager_widget.ReportGenerationThread')
    def test_generate_pdf_report(self, mock_thread_class):
        """测试PDF报告生成"""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        # 设置有效输入
        self.widget.model_input.setText("CP1400")
        self.widget.serial_input.setText("SN-TEST-001")
        self.widget.operator_input.setText("测试用户")
        
        # 触发PDF生成
        self.widget._generate_pdf_report()
        
        # 验证线程创建和启动
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()
        
        # 验证按钮状态
        self.assertFalse(self.widget.pdf_button._enabled)
        
    @patch('modules.report_manager_widget.ReportGenerationThread')
    def test_generate_web_report(self, mock_thread_class):
        """测试Web报告生成"""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        # 设置有效输入
        self.widget.model_input.setText("CP1400")
        self.widget.serial_input.setText("SN-TEST-001")
        self.widget.operator_input.setText("测试用户")
        
        # 触发Web报告生成
        self.widget._generate_web_report()
        
        # 验证线程创建和启动
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()
        
    @patch('modules.report_manager_widget.ReportGenerationThread')
    def test_export_excel(self, mock_thread_class):
        """测试Excel导出"""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        # 设置有效输入
        self.widget.model_input.setText("CP1400")
        self.widget.serial_input.setText("SN-TEST-001")
        self.widget.operator_input.setText("测试用户")
        
        # 触发Excel导出
        self.widget._export_excel()
        
        # 验证线程创建和启动
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()
        
    @patch('modules.report_manager_widget.ReportGenerationThread')
    def test_export_csv(self, mock_thread_class):
        """测试CSV导出"""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        # 设置有效输入
        self.widget.model_input.setText("CP1400")
        self.widget.serial_input.setText("SN-TEST-001")
        self.widget.operator_input.setText("测试用户")
        
        # 触发CSV导出
        self.widget._export_csv()
        
        # 验证线程创建和启动
        mock_thread_class.assert_called_once()
        mock_thread.start.assert_called_once()
        
    def test_on_generation_completed(self):
        """测试生成完成处理"""
        test_file_path = os.path.join(self.temp_dir, "test_report.pdf")
        with open(test_file_path, 'w') as f:
            f.write("test content")
            
        # 模拟生成完成
        self.widget._on_generation_completed("PDF", test_file_path)
        
        # 验证状态更新
        self.assertEqual(self.widget.status_label.text, "PDF报告生成完成")
        
        # 验证按钮状态恢复
        self.assertTrue(self.widget.pdf_button._enabled)
        
    def test_on_generation_failed(self):
        """测试生成失败处理"""
        error_message = "测试错误信息"
        
        # 模拟生成失败
        self.widget._on_generation_failed("PDF", error_message)
        
        # 验证状态更新
        self.assertIn("失败", self.widget.status_label.text)
        self.assertIn(error_message, self.widget.status_label.text)
        
        # 验证按钮状态恢复
        self.assertTrue(self.widget.pdf_button._enabled)
        
    def test_refresh_history(self):
        """测试历史记录刷新"""
        # 创建一些测试文件
        test_files = [
            "检测报告_CP1400_20250710_143022.pdf",
            "检测数据_CP1400_20250710_143022.xlsx",
            "检测数据_CP1400_20250710_143022.csv"
        ]
        
        for filename in test_files:
            test_path = os.path.join(self.temp_dir, filename)
            with open(test_path, 'w') as f:
                f.write("test content")
                
        # 刷新历史记录
        self.widget._refresh_history()
        
        # 验证表格行数
        expected_rows = len(test_files)
        self.assertEqual(self.widget.history_table.row_count, expected_rows)
        
    def test_search_history(self):
        """测试历史记录搜索"""
        # 设置搜索关键词
        self.widget.search_input.setText("CP1400")
        
        # 创建测试文件
        test_files = [
            "检测报告_CP1400_20250710_143022.pdf",
            "检测报告_CP1500_20250710_143022.pdf", 
            "检测数据_CP1400_20250710_143022.xlsx"
        ]
        
        for filename in test_files:
            test_path = os.path.join(self.temp_dir, filename)
            with open(test_path, 'w') as f:
                f.write("test content")
                
        # 执行搜索
        self.widget._search_history()
        
        # 验证搜索结果（应该过滤掉CP1500）
        # 这里实际的验证依赖于具体的搜索实现
        
    @patch('os.startfile')
    @patch('subprocess.run')
    def test_open_selected_report(self, mock_subprocess, mock_startfile):
        """测试打开选中的报告"""
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "test_report.pdf")
        with open(test_file, 'w') as f:
            f.write("test content")
            
        # 模拟文件选择
        with patch.object(self.widget, '_get_selected_file_path', return_value=test_file):
            self.widget._open_selected_report()
            
        # 验证文件打开尝试（具体实现取决于操作系统）
        
    def test_delete_selected_report(self):
        """测试删除选中的报告"""
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "test_report.pdf")
        with open(test_file, 'w') as f:
            f.write("test content")
            
        self.assertTrue(os.path.exists(test_file))
        
        # 模拟文件选择和确认删除
        with patch.object(self.widget, '_get_selected_file_path', return_value=test_file):
            with patch('PySide6.QtWidgets.QMessageBox.question', return_value=16384):  # Yes button
                self.widget._delete_selected_report()
                
        # 验证文件被删除
        self.assertFalse(os.path.exists(test_file))
        
    def test_enable_generation_buttons(self):
        """测试启用生成按钮"""
        # 禁用所有按钮
        self.widget.pdf_button.setEnabled(False)
        self.widget.web_button.setEnabled(False)
        self.widget.excel_button.setEnabled(False)
        self.widget.csv_button.setEnabled(False)
        
        # 启用按钮
        self.widget._enable_generation_buttons(True)
        
        # 验证按钮状态
        self.assertTrue(self.widget.pdf_button._enabled)
        self.assertTrue(self.widget.web_button._enabled)
        self.assertTrue(self.widget.excel_button._enabled)
        self.assertTrue(self.widget.csv_button._enabled)
        
    def test_disable_generation_buttons(self):
        """测试禁用生成按钮"""
        # 启用所有按钮
        self.widget.pdf_button.setEnabled(True)
        self.widget.web_button.setEnabled(True)
        self.widget.excel_button.setEnabled(True)
        self.widget.csv_button.setEnabled(True)
        
        # 禁用按钮
        self.widget._enable_generation_buttons(False)
        
        # 验证按钮状态
        self.assertFalse(self.widget.pdf_button._enabled)
        self.assertFalse(self.widget.web_button._enabled)
        self.assertFalse(self.widget.excel_button._enabled)
        self.assertFalse(self.widget.csv_button._enabled)


class TestReportManagerWidgetIntegration(unittest.TestCase):
    """报告管理器组件集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        
        from modules.report_manager_widget import ReportManagerWidget
        
        with patch('modules.report_manager_widget.ReportGenerator'):
            with patch('modules.report_manager_widget.EnhancedReportGenerator'):
                self.widget = ReportManagerWidget()
                
        self.widget.output_dir = Path(self.temp_dir)
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_full_ui_workflow(self):
        """测试完整的UI工作流程"""
        # 1. 设置工件信息
        self.widget.model_input.setText("CP1400")
        self.widget.serial_input.setText("SN-INTEGRATION-001")
        self.widget.operator_input.setText("集成测试用户")
        
        # 2. 验证输入
        is_valid, message = self.widget._validate_inputs()
        self.assertTrue(is_valid)
        
        # 3. 获取工件信息
        workpiece_info = self.widget._get_workpiece_info()
        self.assertEqual(workpiece_info['model'], "CP1400")
        self.assertEqual(workpiece_info['serial'], "SN-INTEGRATION-001")
        self.assertEqual(workpiece_info['operator'], "集成测试用户")
        
        # 4. 模拟进度更新
        self.widget._update_progress(25)
        self.widget._update_status("正在生成图表...")
        self.assertEqual(self.widget.progress_bar.value, 25)
        
        self.widget._update_progress(50)
        self.widget._update_status("正在生成PDF...")
        self.assertEqual(self.widget.progress_bar.value, 50)
        
        self.widget._update_progress(100)
        self.widget._update_status("生成完成")
        self.assertEqual(self.widget.progress_bar.value, 100)
        
        # 5. 重置进度
        self.widget._reset_progress()
        self.assertEqual(self.widget.progress_bar.value, 0)
        self.assertEqual(self.widget.status_label.text, "准备就绪")
        
    def test_history_management_workflow(self):
        """测试历史管理工作流程"""
        # 创建模拟历史文件
        test_files = [
            "检测报告_CP1400_20250710_100000.pdf",
            "检测报告_CP1400_20250710_110000.pdf",
            "检测数据_CP1400_20250710_100000.xlsx",
            "检测数据_CP1500_20250710_120000.csv"
        ]
        
        for filename in test_files:
            test_path = os.path.join(self.temp_dir, filename)
            with open(test_path, 'w') as f:
                f.write(f"test content for {filename}")
                
        # 刷新历史记录
        self.widget._refresh_history()
        
        # 验证历史记录加载
        self.assertEqual(self.widget.history_table.row_count, len(test_files))
        
        # 测试搜索功能
        self.widget.search_input.setText("CP1400")
        self.widget._search_history()
        
        # 搜索应该过滤掉CP1500的文件
        # 具体验证取决于搜索实现
        
        # 测试文件删除
        test_file_to_delete = os.path.join(self.temp_dir, test_files[0])
        self.assertTrue(os.path.exists(test_file_to_delete))
        
        with patch.object(self.widget, '_get_selected_file_path', 
                         return_value=test_file_to_delete):
            with patch('PySide6.QtWidgets.QMessageBox.question', 
                      return_value=16384):  # Yes
                self.widget._delete_selected_report()
                
        self.assertFalse(os.path.exists(test_file_to_delete))
        
        print("✅ 报告管理器组件集成测试完成")


def run_report_manager_tests():
    """运行报告管理器组件测试"""
    test_suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestReportManagerWidget,
        TestReportManagerWidgetIntegration,
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
    print("报告管理器组件单元测试")
    print("=" * 60)
    
    success = run_report_manager_tests()
    
    if success:
        print("\n✅ 所有报告管理器组件测试通过")
    else:
        print("\n❌ 部分报告管理器组件测试失败")
        
    exit(0 if success else 1)