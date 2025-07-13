#!/usr/bin/env python3
"""
UI更新修复单元测试
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import Qt

class TestUIUpdateFix(unittest.TestCase):
    """UI更新修复单元测试"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """设置每个测试"""
        from main_window.main_window import MainWindow
        self.window = MainWindow()
        
        # 创建测试孔位数据
        from aidcis2.models.hole_data import HoleData, HoleStatus
        self.test_hole_h00001 = HoleData('H00001', 100.0, 200.0, 5.0, HoleStatus.PENDING)
        self.test_hole_h00002 = HoleData('H00002', 150.0, 250.0, 5.5, HoleStatus.QUALIFIED)
        self.test_hole_h00003 = HoleData('H00003', 200.0, 300.0, 4.8, HoleStatus.DEFECTIVE)
        
        # 确保UI标签存在
        self.assertIsNotNone(self.window.selected_hole_id_label)
        self.assertIsNotNone(self.window.selected_hole_position_label)
        self.assertIsNotNone(self.window.selected_hole_status_label)
        self.assertIsNotNone(self.window.selected_hole_radius_label)
    
    def test_ui_labels_clear_state(self):
        """测试UI标签清空状态"""
        # 设置为空状态
        self.window.selected_hole = None
        self.window.update_hole_info_display()
        
        # 验证标签内容
        self.assertEqual(self.window.selected_hole_id_label.text(), "未选择")
        self.assertEqual(self.window.selected_hole_position_label.text(), "-")
        self.assertEqual(self.window.selected_hole_status_label.text(), "-")
        self.assertEqual(self.window.selected_hole_radius_label.text(), "-")
    
    def test_ui_labels_h00001_display(self):
        """测试H00001孔位信息显示"""
        # 设置选中孔位
        self.window.selected_hole = self.test_hole_h00001
        self.window.update_hole_info_display()
        
        # 验证标签内容
        self.assertEqual(self.window.selected_hole_id_label.text(), "H00001")
        self.assertEqual(self.window.selected_hole_position_label.text(), "(100.0, 200.0)")
        self.assertEqual(self.window.selected_hole_status_label.text(), "PENDING")
        self.assertEqual(self.window.selected_hole_radius_label.text(), "5.000mm")
    
    def test_ui_labels_h00002_display(self):
        """测试H00002孔位信息显示"""
        # 设置选中孔位
        self.window.selected_hole = self.test_hole_h00002
        self.window.update_hole_info_display()
        
        # 验证标签内容
        self.assertEqual(self.window.selected_hole_id_label.text(), "H00002")
        self.assertEqual(self.window.selected_hole_position_label.text(), "(150.0, 250.0)")
        self.assertEqual(self.window.selected_hole_status_label.text(), "QUALIFIED")
        self.assertEqual(self.window.selected_hole_radius_label.text(), "5.500mm")
    
    def test_ui_labels_h00003_display(self):
        """测试H00003孔位信息显示"""
        # 设置选中孔位
        self.window.selected_hole = self.test_hole_h00003
        self.window.update_hole_info_display()
        
        # 验证标签内容
        self.assertEqual(self.window.selected_hole_id_label.text(), "H00003")
        self.assertEqual(self.window.selected_hole_position_label.text(), "(200.0, 300.0)")
        self.assertEqual(self.window.selected_hole_status_label.text(), "DEFECTIVE")
        self.assertEqual(self.window.selected_hole_radius_label.text(), "4.800mm")
    
    def test_ui_labels_repaint_calls(self):
        """测试UI标签repaint调用"""
        # Mock repaint方法
        self.window.selected_hole_id_label.repaint = Mock()
        self.window.selected_hole_position_label.repaint = Mock()
        self.window.selected_hole_status_label.repaint = Mock()
        self.window.selected_hole_radius_label.repaint = Mock()
        
        # 设置选中孔位并更新
        self.window.selected_hole = self.test_hole_h00001
        self.window.update_hole_info_display()
        
        # 验证repaint被调用
        self.window.selected_hole_id_label.repaint.assert_called_once()
        self.window.selected_hole_position_label.repaint.assert_called_once()
        self.window.selected_hole_status_label.repaint.assert_called_once()
        self.window.selected_hole_radius_label.repaint.assert_called_once()
    
    def test_ui_status_color_styling(self):
        """测试状态颜色样式"""
        # 测试不同状态的颜色
        test_cases = [
            (self.test_hole_h00001, "PENDING", "gray"),
            (self.test_hole_h00002, "QUALIFIED", "green"),
            (self.test_hole_h00003, "DEFECTIVE", "red")
        ]
        
        for hole, expected_status, expected_color in test_cases:
            with self.subTest(hole_id=hole.hole_id):
                self.window.selected_hole = hole
                self.window.update_hole_info_display()
                
                # 验证状态文本
                self.assertEqual(self.window.selected_hole_status_label.text(), expected_status)
                
                # 验证样式包含颜色
                style = self.window.selected_hole_status_label.styleSheet()
                self.assertIn("color:", style)
                self.assertIn("font-weight: bold", style)
    
    @patch('PySide6.QtWidgets.QApplication.processEvents')
    def test_process_events_called(self, mock_process_events):
        """测试QApplication.processEvents被调用"""
        # 设置选中孔位并更新
        self.window.selected_hole = self.test_hole_h00001
        self.window.update_hole_info_display()
        
        # 验证processEvents被调用
        mock_process_events.assert_called_once()
    
    def test_ui_update_logging(self):
        """测试UI更新日志"""
        # Mock log_message方法
        self.window.log_message = Mock()
        
        # 设置选中孔位并更新
        self.window.selected_hole = self.test_hole_h00001
        self.window.update_hole_info_display()
        
        # 验证日志调用
        log_calls = [call.args[0] for call in self.window.log_message.call_args_list]
        
        # 检查关键日志信息
        self.assertTrue(any("🔄 开始UI更新" in call for call in log_calls))
        self.assertTrue(any("UI更新: 显示孔位 H00001" in call for call in log_calls))
        self.assertTrue(any("设置ID标签: 'H00001'" in call for call in log_calls))
        self.assertTrue(any("✅ UI更新完成: H00001" in call for call in log_calls))
    
    def test_variable_reference_fix(self):
        """测试变量引用修复"""
        # 这个测试验证搜索方法中的变量引用是否正确
        import inspect
        
        search_source = inspect.getsource(self.window.perform_search)
        
        # 验证使用了正确的变量引用
        self.assertIn("self.selected_hole.hole_id", search_source)
        self.assertNotIn("hole.hole_id in [\"H00001\", \"H00002\"]", search_source)

if __name__ == '__main__':
    unittest.main()
