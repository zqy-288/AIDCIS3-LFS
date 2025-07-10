#!/usr/bin/env python3
"""
孔位操作集成测试
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

class TestHoleOperationsIntegration(unittest.TestCase):
    """孔位操作集成测试"""
    
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
        mock_collection.__len__ = Mock(return_value=len(self.test_holes))
        self.window.hole_collection = mock_collection
        
        # 模拟图形视图
        self.window.graphics_view = Mock()
        self.window.graphics_view.hole_items = {}
        self.window.graphics_view.update_hole_status = Mock()
        
        # 模拟信号
        self.window.navigate_to_realtime = Mock()
        self.window.navigate_to_history = Mock()
    
    @patch('main_window.QMessageBox.warning')
    def test_goto_realtime_with_data(self, mock_warning):
        """测试跳转到实时监控（有数据）"""
        # 选择有数据的孔位
        self.window.selected_hole = self.test_holes['H00001']
        
        # 执行跳转
        self.window.goto_realtime()
        
        # 不应该显示警告
        mock_warning.assert_not_called()
        
        # 应该发射导航信号
        self.window.navigate_to_realtime.emit.assert_called_with('H00001')
    
    @patch('main_window.QMessageBox.warning')
    def test_goto_realtime_without_data(self, mock_warning):
        """测试跳转到实时监控（无数据）"""
        # 选择无数据的孔位
        self.window.selected_hole = self.test_holes['H00003']
        
        # 执行跳转
        self.window.goto_realtime()
        
        # 应该显示警告
        mock_warning.assert_called_once()
        
        # 不应该发射导航信号
        self.window.navigate_to_realtime.emit.assert_not_called()
    
    @patch('main_window.QMessageBox.warning')
    def test_goto_realtime_no_selection(self, mock_warning):
        """测试跳转到实时监控（未选择孔位）"""
        # 未选择孔位
        self.window.selected_hole = None
        
        # 执行跳转
        self.window.goto_realtime()
        
        # 应该显示警告
        mock_warning.assert_called_once()
    
    @patch('main_window.QMessageBox.warning')
    def test_goto_history_with_data(self, mock_warning):
        """测试跳转到历史数据（有数据）"""
        # 选择有数据的孔位
        self.window.selected_hole = self.test_holes['H00002']
        
        # 执行跳转
        self.window.goto_history()
        
        # 不应该显示警告
        mock_warning.assert_not_called()
        
        # 应该发射导航信号
        self.window.navigate_to_history.emit.assert_called_with('H00002')
    
    @patch('main_window.QMessageBox.warning')
    def test_goto_history_without_data(self, mock_warning):
        """测试跳转到历史数据（无数据）"""
        # 选择无数据的孔位
        self.window.selected_hole = self.test_holes['H00003']
        
        # 执行跳转
        self.window.goto_history()
        
        # 应该显示警告
        mock_warning.assert_called_once()
        
        # 不应该发射导航信号
        self.window.navigate_to_history.emit.assert_not_called()
    
    @patch('main_window.QMessageBox.question')
    @patch('main_window.QMessageBox.information')
    def test_mark_defective_confirmed(self, mock_info, mock_question):
        """测试标记异常（确认）"""
        # 模拟用户确认
        mock_question.return_value = QMessageBox.StandardButton.Yes
        
        # 选择孔位
        self.window.selected_hole = self.test_holes['H00001']
        
        # 执行标记
        self.window.mark_defective()
        
        # 检查状态是否更新
        from aidcis2.models.hole_data import HoleStatus
        self.assertEqual(self.window.selected_hole.status, HoleStatus.DEFECTIVE)
        
        # 应该显示确认信息
        mock_info.assert_called_once()
        
        # 应该更新图形视图
        self.window.graphics_view.update_hole_status.assert_called_with('H00001', HoleStatus.DEFECTIVE)
    
    @patch('main_window.QMessageBox.question')
    def test_mark_defective_cancelled(self, mock_question):
        """测试标记异常（取消）"""
        # 模拟用户取消
        mock_question.return_value = QMessageBox.StandardButton.No
        
        # 选择孔位
        original_status = self.test_holes['H00001'].status
        self.window.selected_hole = self.test_holes['H00001']
        
        # 执行标记
        self.window.mark_defective()
        
        # 状态不应该改变
        self.assertEqual(self.window.selected_hole.status, original_status)
        
        # 不应该更新图形视图
        self.window.graphics_view.update_hole_status.assert_not_called()
    
    def test_search_to_operation_workflow(self):
        """测试搜索到操作的完整工作流"""
        # 1. 搜索孔位
        self.window.search_input.setText('H00001')
        self.window.perform_search()
        
        # 2. 检查孔位是否被选中
        self.assertEqual(self.window.selected_hole.hole_id, 'H00001')
        
        # 3. 检查按钮状态
        self.assertTrue(self.window.goto_realtime_btn.isEnabled())
        self.assertTrue(self.window.goto_history_btn.isEnabled())
        self.assertTrue(self.window.mark_defective_btn.isEnabled())
        
        # 4. 检查工具提示
        self.assertIn('H00001', self.window.goto_realtime_btn.toolTip())
    
    def test_data_availability_integration(self):
        """测试数据可用性检查集成"""
        # 检查H00001（有数据）
        result_h1 = self.window._check_hole_data_availability('H00001')
        self.assertTrue(result_h1['realtime_support'])
        
        # 检查H00003（无数据）
        result_h3 = self.window._check_hole_data_availability('H00003')
        self.assertFalse(result_h3['realtime_support'])
        
        # 数据评分应该不同
        self.assertGreater(result_h1['data_score'], result_h3['data_score'])

if __name__ == '__main__':
    unittest.main()
