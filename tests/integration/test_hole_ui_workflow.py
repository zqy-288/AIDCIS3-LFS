#!/usr/bin/env python3
"""
孔位UI工作流集成测试
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import QApplication

class TestHoleUIWorkflow(unittest.TestCase):
    """孔位UI工作流集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """设置每个测试"""
        from main_window import MainWindow
        self.window = MainWindow()
        
        # 创建测试孔位数据
        from aidcis2.models.hole_data import HoleData, HoleStatus
        self.test_holes = {
            'H00001': HoleData('H00001', 100.0, 200.0, 5.0, HoleStatus.PENDING),
            'H00002': HoleData('H00002', 150.0, 250.0, 5.5, HoleStatus.QUALIFIED),
            'H00003': HoleData('H00003', 200.0, 300.0, 4.8, HoleStatus.DEFECTIVE)
        }
        
        # 模拟孔位集合
        mock_collection = Mock()
        mock_collection.holes = self.test_holes
        self.window.hole_collection = mock_collection
        
        # 模拟图形视图
        self.window.graphics_view = Mock()
        self.window.graphics_view.highlight_holes = Mock()
        self.window.graphics_view.clear_search_highlight = Mock()
        
        # Mock数据检查方法
        self.window._check_hole_data_availability = Mock()
    
    def test_search_to_ui_update_workflow_h00001(self):
        """测试搜索H00001到UI更新的完整工作流"""
        # 1. 执行搜索
        self.window.search_input.setText('H00001')
        self.window.perform_search()
        
        # 2. 验证孔位被选中
        self.assertIsNotNone(self.window.selected_hole)
        self.assertEqual(self.window.selected_hole.hole_id, 'H00001')
        
        # 3. 验证UI标签更新
        self.assertEqual(self.window.selected_hole_id_label.text(), "H00001")
        self.assertIn("100.0", self.window.selected_hole_position_label.text())
        self.assertIn("200.0", self.window.selected_hole_position_label.text())
        self.assertEqual(self.window.selected_hole_status_label.text(), "PENDING")
        self.assertEqual(self.window.selected_hole_radius_label.text(), "5.000mm")
        
        # 4. 验证按钮状态（H00001有数据）
        self.assertTrue(self.window.goto_realtime_btn.isEnabled())
        self.assertTrue(self.window.goto_history_btn.isEnabled())
        self.assertTrue(self.window.mark_defective_btn.isEnabled())
        
        # 5. 验证工具提示
        realtime_tooltip = self.window.goto_realtime_btn.toolTip()
        self.assertIn("H00001", realtime_tooltip)
        self.assertIn("实时监控数据", realtime_tooltip)
        
        # 6. 验证数据检查被调用
        self.window._check_hole_data_availability.assert_called_with('H00001')
    
    def test_search_to_ui_update_workflow_h00003(self):
        """测试搜索H00003到UI更新的完整工作流"""
        # 1. 执行搜索
        self.window.search_input.setText('H00003')
        self.window.perform_search()
        
        # 2. 验证孔位被选中
        self.assertIsNotNone(self.window.selected_hole)
        self.assertEqual(self.window.selected_hole.hole_id, 'H00003')
        
        # 3. 验证UI标签更新
        self.assertEqual(self.window.selected_hole_id_label.text(), "H00003")
        self.assertIn("200.0", self.window.selected_hole_position_label.text())
        self.assertIn("300.0", self.window.selected_hole_position_label.text())
        self.assertEqual(self.window.selected_hole_status_label.text(), "DEFECTIVE")
        self.assertEqual(self.window.selected_hole_radius_label.text(), "4.800mm")
        
        # 4. 验证按钮状态（H00003无数据）
        self.assertFalse(self.window.goto_realtime_btn.isEnabled())
        self.assertFalse(self.window.goto_history_btn.isEnabled())
        self.assertTrue(self.window.mark_defective_btn.isEnabled())  # 标记异常总是可用
        
        # 5. 验证工具提示
        realtime_tooltip = self.window.goto_realtime_btn.toolTip()
        self.assertIn("H00003", realtime_tooltip)
        self.assertIn("无实时监控数据", realtime_tooltip)
    
    def test_right_click_to_ui_sync_workflow(self):
        """测试右键选择到UI同步的完整工作流"""
        # 1. 模拟右键选择H00002
        hole = self.test_holes['H00002']
        self.window.on_hole_selected(hole)
        
        # 2. 验证孔位被选中
        self.assertIsNotNone(self.window.selected_hole)
        self.assertEqual(self.window.selected_hole.hole_id, 'H00002')
        
        # 3. 验证UI标签更新
        self.assertEqual(self.window.selected_hole_id_label.text(), "H00002")
        self.assertIn("150.0", self.window.selected_hole_position_label.text())
        self.assertIn("250.0", self.window.selected_hole_position_label.text())
        self.assertEqual(self.window.selected_hole_status_label.text(), "QUALIFIED")
        self.assertEqual(self.window.selected_hole_radius_label.text(), "5.500mm")
        
        # 4. 验证按钮状态（H00002有数据）
        self.assertTrue(self.window.goto_realtime_btn.isEnabled())
        self.assertTrue(self.window.goto_history_btn.isEnabled())
        self.assertTrue(self.window.mark_defective_btn.isEnabled())
        
        # 5. 验证数据检查被调用
        self.window._check_hole_data_availability.assert_called_with('H00002')
    
    def test_simulation_progress_timing_integration(self):
        """测试模拟进度时间控制集成功能"""
        # 创建模拟孔位数据
        mock_collection = Mock()
        mock_collection.holes = self.test_holes
        self.window.hole_collection = mock_collection
        
        # 模拟图形视图
        self.window.graphics_view = Mock()
        self.window.graphics_view.hole_items = {
            hole_id: Mock() for hole_id in self.test_holes.keys()
        }
        
        # 为每个图形项添加必要的方法
        for hole_item in self.window.graphics_view.hole_items.values():
            hole_item.setBrush = Mock()
            hole_item.setPen = Mock()
            hole_item.update = Mock()
            hole_item.brush.return_value.color.return_value.name.return_value = "#c8c8c8"
        
        # 启动模拟进度
        self.window._start_simulation_progress_v2()
        
        # 验证定时器设置
        self.assertTrue(hasattr(self.window, 'simulation_timer_v2'))
        self.assertIsNotNone(self.window.simulation_timer_v2)
        self.assertEqual(self.window.simulation_timer_v2.interval(), 1000)
        
        # 验证模拟状态
        self.assertTrue(self.window.simulation_running_v2)
        self.assertEqual(self.window.simulation_index_v2, 0)
    
    def test_data_availability_logic_integration(self):
        """测试数据可用性逻辑集成"""
        # 测试H00001和H00002的数据可用性
        test_cases = [
            ('H00001', True),
            ('H00002', True),
            ('H00003', False),
            ('H00004', False)
        ]
        
        for hole_id, expected_has_data in test_cases:
            with self.subTest(hole_id=hole_id):
                # 创建测试孔位
                from aidcis2.models.hole_data import HoleData, HoleStatus
                test_hole = HoleData(hole_id, 100.0, 200.0, 5.0, HoleStatus.PENDING)
                
                # 模拟右键选择
                self.window.on_hole_selected(test_hole)
                
                # 验证按钮状态
                self.assertEqual(self.window.goto_realtime_btn.isEnabled(), expected_has_data)
                self.assertEqual(self.window.goto_history_btn.isEnabled(), expected_has_data)
                self.assertTrue(self.window.mark_defective_btn.isEnabled())  # 总是启用
    
    def test_ui_state_consistency_across_operations(self):
        """测试跨操作的UI状态一致性"""
        # 1. 通过搜索选择H00001
        self.window.search_input.setText('H00001')
        self.window.perform_search()
        
        # 记录搜索后的UI状态
        search_id = self.window.selected_hole_id_label.text()
        search_position = self.window.selected_hole_position_label.text()
        search_realtime_enabled = self.window.goto_realtime_btn.isEnabled()
        
        # 2. 通过右键选择同一个孔位
        hole = self.test_holes['H00001']
        self.window.on_hole_selected(hole)
        
        # 记录右键选择后的UI状态
        click_id = self.window.selected_hole_id_label.text()
        click_position = self.window.selected_hole_position_label.text()
        click_realtime_enabled = self.window.goto_realtime_btn.isEnabled()
        
        # 3. 验证状态一致性
        self.assertEqual(search_id, click_id)
        self.assertEqual(search_position, click_position)
        self.assertEqual(search_realtime_enabled, click_realtime_enabled)
    
    def test_error_recovery_workflow(self):
        """测试错误恢复工作流"""
        # 1. 模拟UI组件异常
        original_setText = self.window.selected_hole_id_label.setText
        self.window.selected_hole_id_label.setText = Mock(side_effect=Exception("UI异常"))
        
        # Mock log_message来捕获错误日志
        self.window.log_message = Mock()
        
        # 2. 尝试更新UI（应该捕获异常）
        self.window.selected_hole = self.test_holes['H00001']
        self.window.update_hole_info_display()
        
        # 3. 验证异常被捕获
        log_calls = [call.args[0] for call in self.window.log_message.call_args_list]
        self.assertTrue(any("UI更新过程异常" in call for call in log_calls))
        
        # 4. 恢复正常功能
        self.window.selected_hole_id_label.setText = original_setText
        
        # 5. 验证功能恢复
        self.window.update_hole_info_display()
        self.assertEqual(self.window.selected_hole_id_label.text(), "H00001")
    
    @patch('PySide6.QtWidgets.QApplication.processEvents')
    def test_ui_refresh_integration(self, mock_process_events):
        """测试UI刷新集成"""
        # 1. 搜索操作
        self.window.search_input.setText('H00001')
        self.window.perform_search()
        
        # 验证搜索后的UI刷新
        self.assertTrue(mock_process_events.called)
        
        # 2. 重置Mock
        mock_process_events.reset_mock()
        
        # 3. 右键选择操作
        hole = self.test_holes['H00002']
        self.window.on_hole_selected(hole)
        
        # 验证右键选择后的UI刷新
        self.assertTrue(mock_process_events.called)

if __name__ == '__main__':
    unittest.main()
