#!/usr/bin/env python3
"""
搜索到UI更新集成测试
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import QApplication

class TestSearchUIIntegration(unittest.TestCase):
    """搜索到UI更新集成测试"""
    
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
    
    def test_search_h00001_complete_flow(self):
        """测试搜索H00001的完整流程"""
        # 设置搜索文本
        self.window.search_input.setText('H00001')
        
        # 执行搜索
        self.window.perform_search()
        
        # 验证孔位被选中
        self.assertIsNotNone(self.window.selected_hole)
        self.assertEqual(self.window.selected_hole.hole_id, 'H00001')
        
        # 验证UI标签更新
        self.assertEqual(self.window.selected_hole_id_label.text(), "H00001")
        self.assertEqual(self.window.selected_hole_position_label.text(), "(100.0, 200.0)")
        self.assertEqual(self.window.selected_hole_status_label.text(), "PENDING")
        self.assertEqual(self.window.selected_hole_radius_label.text(), "5.000mm")
        
        # 验证按钮状态（H00001有数据）
        self.assertTrue(self.window.goto_realtime_btn.isEnabled())
        self.assertTrue(self.window.goto_history_btn.isEnabled())
        self.assertTrue(self.window.mark_defective_btn.isEnabled())
        
        # 验证工具提示
        self.assertIn("H00001", self.window.goto_realtime_btn.toolTip())
        self.assertIn("实时监控数据", self.window.goto_realtime_btn.toolTip())
        
        # 验证数据检查被调用
        self.window._check_hole_data_availability.assert_called_with('H00001')
    
    def test_search_h00002_complete_flow(self):
        """测试搜索H00002的完整流程"""
        # 设置搜索文本
        self.window.search_input.setText('H00002')
        
        # 执行搜索
        self.window.perform_search()
        
        # 验证孔位被选中
        self.assertIsNotNone(self.window.selected_hole)
        self.assertEqual(self.window.selected_hole.hole_id, 'H00002')
        
        # 验证UI标签更新
        self.assertEqual(self.window.selected_hole_id_label.text(), "H00002")
        self.assertEqual(self.window.selected_hole_position_label.text(), "(150.0, 250.0)")
        self.assertEqual(self.window.selected_hole_status_label.text(), "QUALIFIED")
        self.assertEqual(self.window.selected_hole_radius_label.text(), "5.500mm")
        
        # 验证按钮状态（H00002有数据）
        self.assertTrue(self.window.goto_realtime_btn.isEnabled())
        self.assertTrue(self.window.goto_history_btn.isEnabled())
        self.assertTrue(self.window.mark_defective_btn.isEnabled())
        
        # 验证数据检查被调用
        self.window._check_hole_data_availability.assert_called_with('H00002')
    
    def test_search_h00003_complete_flow(self):
        """测试搜索H00003的完整流程"""
        # 设置搜索文本
        self.window.search_input.setText('H00003')
        
        # 执行搜索
        self.window.perform_search()
        
        # 验证孔位被选中
        self.assertIsNotNone(self.window.selected_hole)
        self.assertEqual(self.window.selected_hole.hole_id, 'H00003')
        
        # 验证UI标签更新
        self.assertEqual(self.window.selected_hole_id_label.text(), "H00003")
        self.assertEqual(self.window.selected_hole_position_label.text(), "(200.0, 300.0)")
        self.assertEqual(self.window.selected_hole_status_label.text(), "DEFECTIVE")
        self.assertEqual(self.window.selected_hole_radius_label.text(), "4.800mm")
        
        # 验证按钮状态（H00003无数据）
        self.assertFalse(self.window.goto_realtime_btn.isEnabled())
        self.assertFalse(self.window.goto_history_btn.isEnabled())
        self.assertTrue(self.window.mark_defective_btn.isEnabled())  # 标记异常总是可用
        
        # 验证工具提示
        self.assertIn("H00003", self.window.goto_realtime_btn.toolTip())
        self.assertIn("无实时监控数据", self.window.goto_realtime_btn.toolTip())
        
        # 验证数据检查被调用
        self.window._check_hole_data_availability.assert_called_with('H00003')
    
    def test_search_partial_match_multiple_results(self):
        """测试部分匹配多个结果"""
        # 设置搜索文本（匹配H00001, H00002, H00003）
        self.window.search_input.setText('H000')
        
        # 执行搜索
        self.window.perform_search()
        
        # 验证高亮方法被调用
        self.window.graphics_view.highlight_holes.assert_called_once()
        
        # 获取高亮的孔位
        call_args = self.window.graphics_view.highlight_holes.call_args
        highlighted_holes = call_args[0][0]  # 第一个参数
        
        # 验证所有匹配的孔位都被高亮
        highlighted_ids = [hole.hole_id for hole in highlighted_holes]
        self.assertIn('H00001', highlighted_ids)
        self.assertIn('H00002', highlighted_ids)
        self.assertIn('H00003', highlighted_ids)
    
    def test_search_exact_match_priority(self):
        """测试精确匹配优先级"""
        # 添加更多测试数据
        self.test_holes['H0000'] = HoleData('H0000', 50.0, 100.0, 3.0, HoleStatus.PENDING)
        
        # 设置搜索文本（H0000应该精确匹配）
        self.window.search_input.setText('H0000')
        
        # 执行搜索
        self.window.perform_search()
        
        # 验证精确匹配被选中
        self.assertIsNotNone(self.window.selected_hole)
        self.assertEqual(self.window.selected_hole.hole_id, 'H0000')
        
        # 验证UI更新
        self.assertEqual(self.window.selected_hole_id_label.text(), "H0000")
    
    def test_search_no_results(self):
        """测试搜索无结果"""
        # 设置搜索文本（无匹配）
        self.window.search_input.setText('INVALID')
        
        # 执行搜索
        self.window.perform_search()
        
        # 验证没有孔位被选中
        # 注意：这里不应该改变之前的选中状态
        # 如果之前没有选中，应该保持None
    
    def test_search_clear_functionality(self):
        """测试清空搜索功能"""
        # 先搜索一个孔位
        self.window.search_input.setText('H00001')
        self.window.perform_search()
        
        # 验证孔位被选中
        self.assertIsNotNone(self.window.selected_hole)
        
        # 清空搜索
        self.window.search_input.setText('')
        self.window.perform_search()
        
        # 验证清除高亮被调用
        self.window.graphics_view.clear_search_highlight.assert_called_once()
    
    @patch('PySide6.QtWidgets.QApplication.processEvents')
    def test_ui_refresh_integration(self, mock_process_events):
        """测试UI刷新集成"""
        # 执行搜索
        self.window.search_input.setText('H00001')
        self.window.perform_search()
        
        # 验证processEvents被调用（UI强制刷新）
        mock_process_events.assert_called()
    
    def test_button_tooltip_integration(self):
        """测试按钮工具提示集成"""
        # 测试有数据的孔位
        self.window.search_input.setText('H00001')
        self.window.perform_search()
        
        realtime_tooltip = self.window.goto_realtime_btn.toolTip()
        history_tooltip = self.window.goto_history_btn.toolTip()
        mark_tooltip = self.window.mark_defective_btn.toolTip()
        
        self.assertIn("H00001", realtime_tooltip)
        self.assertIn("实时监控数据", realtime_tooltip)
        self.assertIn("H00001", history_tooltip)
        self.assertIn("历史数据", history_tooltip)
        self.assertIn("H00001", mark_tooltip)
        self.assertIn("标记为异常", mark_tooltip)
        
        # 测试无数据的孔位
        self.window.search_input.setText('H00003')
        self.window.perform_search()
        
        realtime_tooltip = self.window.goto_realtime_btn.toolTip()
        history_tooltip = self.window.goto_history_btn.toolTip()
        
        self.assertIn("H00003", realtime_tooltip)
        self.assertIn("无实时监控数据", realtime_tooltip)
        self.assertIn("H00003", history_tooltip)
        self.assertIn("无历史数据", history_tooltip)

if __name__ == '__main__':
    unittest.main()
