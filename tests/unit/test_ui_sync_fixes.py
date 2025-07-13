#!/usr/bin/env python3
"""
UI同步修复单元测试
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

class TestUISyncFixes(unittest.TestCase):
    """UI同步修复单元测试"""
    
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
    
    def test_simulation_frequency_1000ms(self):
        """测试模拟频率调整为1000ms"""
        # 启动V2模拟
        self.window._start_simulation_progress_v2()
        
        # 检查定时器间隔
        self.assertTrue(hasattr(self.window, 'simulation_timer_v2'))
        self.assertIsNotNone(self.window.simulation_timer_v2)
        
        # 验证定时器间隔为1000ms
        actual_interval = self.window.simulation_timer_v2.interval()
        self.assertEqual(actual_interval, 1000)
    
    def test_ui_component_validation(self):
        """测试UI组件验证机制"""
        # 设置选中孔位
        self.window.selected_hole = self.test_hole_h00001
        
        # Mock log_message来捕获日志
        self.window.log_message = Mock()
        
        # 调用UI更新
        self.window.update_hole_info_display()
        
        # 验证UI组件验证日志
        log_calls = [call.args[0] for call in self.window.log_message.call_args_list]
        self.assertTrue(any("所有UI组件验证通过" in call for call in log_calls))
    
    def test_ui_label_text_verification(self):
        """测试UI标签文本设置验证"""
        # 设置选中孔位
        self.window.selected_hole = self.test_hole_h00001
        
        # Mock log_message
        self.window.log_message = Mock()
        
        # 调用UI更新
        self.window.update_hole_info_display()
        
        # 验证标签设置结果日志
        log_calls = [call.args[0] for call in self.window.log_message.call_args_list]
        
        # 检查ID标签设置验证
        self.assertTrue(any("ID标签设置结果" in call and "H00001" in call for call in log_calls))
        
        # 检查位置标签设置验证
        self.assertTrue(any("位置标签设置结果" in call for call in log_calls))
        
        # 检查状态标签设置验证
        self.assertTrue(any("状态标签设置结果" in call for call in log_calls))
        
        # 检查半径标签设置验证
        self.assertTrue(any("半径标签设置结果" in call for call in log_calls))
    
    def test_button_state_verification(self):
        """测试按钮状态设置验证"""
        # Mock log_message
        self.window.log_message = Mock()
        
        # 测试H00001（有数据）
        self.window.on_hole_selected(self.test_hole_h00001)
        
        log_calls = [call.args[0] for call in self.window.log_message.call_args_list]
        
        # 验证数据可用性检查日志
        self.assertTrue(any("数据可用性检查: H00001 -> True" in call for call in log_calls))
        
        # 验证按钮状态设置结果日志
        self.assertTrue(any("按钮状态设置结果" in call for call in log_calls))
        self.assertTrue(any("实时监控: 期望=True" in call for call in log_calls))
        self.assertTrue(any("历史数据: 期望=True" in call for call in log_calls))
        
        # 重置Mock
        self.window.log_message.reset_mock()
        
        # 测试H00003（无数据）
        self.window.on_hole_selected(self.test_hole_h00003)
        
        log_calls = [call.args[0] for call in self.window.log_message.call_args_list]
        
        # 验证数据可用性检查日志
        self.assertTrue(any("数据可用性检查: H00003 -> False" in call for call in log_calls))
        self.assertTrue(any("实时监控: 期望=False" in call for call in log_calls))
        self.assertTrue(any("历史数据: 期望=False" in call for call in log_calls))
    
    def test_tooltip_verification(self):
        """测试工具提示设置验证"""
        # Mock log_message
        self.window.log_message = Mock()
        
        # 测试H00001（有数据）
        self.window.on_hole_selected(self.test_hole_h00001)
        
        log_calls = [call.args[0] for call in self.window.log_message.call_args_list]
        
        # 验证工具提示设置结果日志
        self.assertTrue(any("工具提示设置结果" in call for call in log_calls))
        
        # 验证实际工具提示内容
        realtime_tooltip = self.window.goto_realtime_btn.toolTip()
        self.assertIn("H00001", realtime_tooltip)
        self.assertIn("实时监控数据", realtime_tooltip)
    
    @patch('PySide6.QtWidgets.QApplication.processEvents')
    def test_forced_ui_refresh(self, mock_process_events):
        """测试强制UI刷新机制"""
        # 设置选中孔位并更新UI
        self.window.selected_hole = self.test_hole_h00001
        self.window.update_hole_info_display()
        
        # 验证processEvents被调用
        mock_process_events.assert_called()
        
        # 测试右键选择的强制刷新
        mock_process_events.reset_mock()
        self.window.on_hole_selected(self.test_hole_h00001)
        
        # 验证processEvents被调用
        mock_process_events.assert_called()
    
    def test_exception_handling(self):
        """测试异常处理机制"""
        # Mock一个会抛出异常的标签
        self.window.selected_hole_id_label = Mock()
        self.window.selected_hole_id_label.setText.side_effect = Exception("测试异常")
        
        # Mock log_message
        self.window.log_message = Mock()
        
        # 设置选中孔位
        self.window.selected_hole = self.test_hole_h00001
        
        # 调用UI更新（应该捕获异常）
        self.window.update_hole_info_display()
        
        # 验证异常被捕获并记录
        log_calls = [call.args[0] for call in self.window.log_message.call_args_list]
        self.assertTrue(any("UI更新过程异常" in call for call in log_calls))
    
    def test_selected_hole_variable_assignment(self):
        """测试selected_hole变量赋值正确性"""
        # 初始状态
        self.assertIsNone(self.window.selected_hole)
        
        # 通过搜索设置
        self.window.selected_hole = self.test_hole_h00001
        self.assertEqual(self.window.selected_hole.hole_id, 'H00001')
        
        # 通过右键选择设置
        self.window.on_hole_selected(self.test_hole_h00002)
        self.assertEqual(self.window.selected_hole.hole_id, 'H00002')
    
    def test_ui_component_repaint_calls(self):
        """测试UI组件repaint调用"""
        # Mock所有UI标签的repaint方法
        ui_labels = [
            self.window.selected_hole_id_label,
            self.window.selected_hole_position_label,
            self.window.selected_hole_status_label,
            self.window.selected_hole_radius_label
        ]
        
        for label in ui_labels:
            label.repaint = Mock()
        
        # 设置选中孔位并更新
        self.window.selected_hole = self.test_hole_h00001
        self.window.update_hole_info_display()
        
        # 验证所有标签的repaint被调用
        for label in ui_labels:
            label.repaint.assert_called()

if __name__ == '__main__':
    unittest.main()
