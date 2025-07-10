#!/usr/bin/env python3
"""
孔位选择功能单元测试
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

class TestHoleSelection(unittest.TestCase):
    """孔位选择功能单元测试"""
    
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
        
        # 创建模拟孔位数据
        from aidcis2.models.hole_data import HoleData, HoleStatus
        self.test_holes = {
            'H00001': HoleData('H00001', 100.0, 200.0, 5.0, HoleStatus.PENDING),
            'H00002': HoleData('H00002', 150.0, 250.0, 5.0, HoleStatus.PENDING),
            'H00003': HoleData('H00003', 200.0, 300.0, 5.0, HoleStatus.PENDING)
        }
        
        # 模拟孔位集合
        mock_collection = Mock()
        mock_collection.holes = self.test_holes
        self.window.hole_collection = mock_collection
        
        # 模拟图形视图
        self.window.graphics_view = Mock()
        self.window.graphics_view.hole_items = {}
        self.window.graphics_view.clear_search_highlight = Mock()
        self.window.graphics_view.highlight_holes = Mock()
    
    def test_data_availability_check_h00001(self):
        """测试H00001数据可用性检查"""
        result = self.window._check_hole_data_availability('H00001')
        
        # H00001应该支持实时监控
        self.assertTrue(result['realtime_support'])
        self.assertIn('csv_files', result)
        self.assertIn('image_files', result)
        self.assertIn('data_score', result)
    
    def test_data_availability_check_h00003(self):
        """测试H00003数据可用性检查"""
        result = self.window._check_hole_data_availability('H00003')
        
        # H00003不应该支持实时监控
        self.assertFalse(result['realtime_support'])
    
    def test_hole_selection_with_data(self):
        """测试选择有数据的孔位"""
        hole = self.test_holes['H00001']
        self.window.on_hole_selected(hole)
        
        # 检查选中的孔位
        self.assertEqual(self.window.selected_hole, hole)
        
        # 检查按钮状态（有数据的孔位）
        self.assertTrue(self.window.goto_realtime_btn.isEnabled())
        self.assertTrue(self.window.goto_history_btn.isEnabled())
        self.assertTrue(self.window.mark_defective_btn.isEnabled())
    
    def test_hole_selection_without_data(self):
        """测试选择无数据的孔位"""
        hole = self.test_holes['H00003']
        self.window.on_hole_selected(hole)
        
        # 检查选中的孔位
        self.assertEqual(self.window.selected_hole, hole)
        
        # 检查按钮状态（无数据的孔位）
        self.assertFalse(self.window.goto_realtime_btn.isEnabled())
        self.assertFalse(self.window.goto_history_btn.isEnabled())
        self.assertTrue(self.window.mark_defective_btn.isEnabled())  # 标记异常总是可用
    
    def test_search_single_match(self):
        """测试搜索单个匹配结果"""
        self.window.search_input.setText('H00001')
        self.window.perform_search()
        
        # 检查是否选中了正确的孔位
        self.assertEqual(self.window.selected_hole.hole_id, 'H00001')
        
        # 检查是否调用了高亮方法
        self.window.graphics_view.highlight_holes.assert_called()
    
    def test_search_multiple_matches(self):
        """测试搜索多个匹配结果"""
        self.window.search_input.setText('H000')
        self.window.perform_search()
        
        # 应该调用高亮方法
        self.window.graphics_view.highlight_holes.assert_called()
    
    def test_search_no_matches(self):
        """测试搜索无匹配结果"""
        self.window.search_input.setText('INVALID')
        self.window.perform_search()
        
        # 不应该选中任何孔位
        self.assertIsNone(self.window.selected_hole)
    
    def test_clear_search(self):
        """测试清空搜索"""
        self.window.search_input.setText('')
        self.window.perform_search()
        
        # 应该调用清除高亮方法
        self.window.graphics_view.clear_search_highlight.assert_called()
    
    def test_hole_info_display_update(self):
        """测试孔位信息显示更新"""
        hole = self.test_holes['H00001']
        self.window.selected_hole = hole
        self.window.update_hole_info_display()
        
        # 检查UI标签是否更新
        self.assertIn('H00001', self.window.selected_hole_id_label.text())
        self.assertIn('100.0', self.window.selected_hole_position_label.text())
        self.assertIn('200.0', self.window.selected_hole_position_label.text())
    
    def test_hole_info_display_clear(self):
        """测试清空孔位信息显示"""
        self.window.selected_hole = None
        self.window.update_hole_info_display()

        # 检查UI标签是否清空
        self.assertIn('未选择', self.window.selected_hole_id_label.text())
        self.assertEqual('-', self.window.selected_hole_position_label.text())

    def test_simulation_frequency_settings(self):
        """测试模拟检测频率设置"""
        import inspect

        # 检查V2模拟方法的频率设置
        start_source = inspect.getsource(self.window._start_simulation_progress_v2)

        # 验证1000ms检测频率
        self.assertIn('start(1000)', start_source)

        # 验证日志信息
        self.assertIn('高频检测模式', start_source)
        self.assertIn('1000ms/孔位', start_source)

        # 检查颜色变化延迟
        update_source = inspect.getsource(self.window._update_simulation_v2)
        self.assertIn('singleShot(100', update_source)

if __name__ == '__main__':
    unittest.main()
