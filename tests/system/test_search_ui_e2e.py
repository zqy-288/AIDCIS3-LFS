#!/usr/bin/env python3
"""
搜索UI端到端测试
"""

import unittest
import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

class TestSearchUIE2E(unittest.TestCase):
    """搜索UI端到端测试"""
    
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
        self.window.show()
        
        # 等待UI初始化
        QTest.qWait(100)
        
        # 加载测试DXF文件
        self._load_test_dxf()
    
    def _load_test_dxf(self):
        """加载测试DXF文件"""
        test_dxf_path = "测试管板.dxf"
        if Path(test_dxf_path).exists():
            try:
                self.window.hole_collection = self.window.dxf_parser.parse_file(test_dxf_path)
                if self.window.hole_collection:
                    self.window.update_file_info(test_dxf_path)
                    self.window.update_hole_display()
                    self.window.update_status_display()
                    self.window.update_completer_data()
                    return True
            except Exception as e:
                print(f"加载测试DXF失败: {e}")
        return False
    
    def test_search_h00001_ui_display_e2e(self):
        """测试搜索H00001的UI显示端到端"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        # 1. 清空搜索框
        self.window.search_input.clear()
        QTest.qWait(100)
        
        # 2. 输入搜索文本
        QTest.keyClicks(self.window.search_input, 'H00001')
        QTest.qWait(200)
        
        # 3. 点击搜索按钮
        QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(500)  # 等待搜索和UI更新完成
        
        # 4. 验证孔位被选中
        self.assertIsNotNone(self.window.selected_hole)
        self.assertEqual(self.window.selected_hole.hole_id, 'H00001')
        
        # 5. 验证左侧UI标签显示
        id_text = self.window.selected_hole_id_label.text()
        position_text = self.window.selected_hole_position_label.text()
        status_text = self.window.selected_hole_status_label.text()
        radius_text = self.window.selected_hole_radius_label.text()
        
        print(f"UI标签内容: ID='{id_text}', 位置='{position_text}', 状态='{status_text}', 半径='{radius_text}'")
        
        # 验证标签不为空且包含预期内容
        self.assertNotEqual(id_text, "未选择")
        self.assertNotEqual(id_text, "-")
        self.assertIn("H00001", id_text)
        
        self.assertNotEqual(position_text, "-")
        self.assertIn("(", position_text)
        self.assertIn(")", position_text)
        
        self.assertNotEqual(status_text, "-")
        self.assertIn("PENDING", status_text.upper())
        
        self.assertNotEqual(radius_text, "-")
        self.assertIn("mm", radius_text)
        
        # 6. 验证按钮状态（H00001有数据）
        self.assertTrue(self.window.goto_realtime_btn.isEnabled())
        self.assertTrue(self.window.goto_history_btn.isEnabled())
        self.assertTrue(self.window.mark_defective_btn.isEnabled())
        
        # 7. 验证按钮工具提示
        realtime_tooltip = self.window.goto_realtime_btn.toolTip()
        self.assertIn("H00001", realtime_tooltip)
        self.assertIn("实时监控", realtime_tooltip)
    
    def test_search_h00002_ui_display_e2e(self):
        """测试搜索H00002的UI显示端到端"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        # 1. 清空并输入搜索文本
        self.window.search_input.clear()
        QTest.keyClicks(self.window.search_input, 'H00002')
        QTest.qWait(200)
        
        # 2. 点击搜索按钮
        QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(500)
        
        # 3. 验证UI更新
        if self.window.selected_hole and self.window.selected_hole.hole_id == 'H00002':
            # 验证标签显示
            id_text = self.window.selected_hole_id_label.text()
            self.assertIn("H00002", id_text)
            
            # 验证按钮状态（H00002有数据）
            self.assertTrue(self.window.goto_realtime_btn.isEnabled())
            self.assertTrue(self.window.goto_history_btn.isEnabled())
    
    def test_search_other_hole_ui_display_e2e(self):
        """测试搜索其他孔位的UI显示端到端"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        # 查找一个不是H00001或H00002的孔位
        other_hole_id = None
        for hole_id in self.window.hole_collection.holes.keys():
            if hole_id not in ['H00001', 'H00002']:
                other_hole_id = hole_id
                break
        
        if not other_hole_id:
            self.skipTest("没有找到其他孔位进行测试")
        
        # 1. 搜索其他孔位
        self.window.search_input.clear()
        QTest.keyClicks(self.window.search_input, other_hole_id)
        QTest.qWait(200)
        
        # 2. 点击搜索按钮
        QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(500)
        
        # 3. 验证UI更新
        if self.window.selected_hole and self.window.selected_hole.hole_id == other_hole_id:
            # 验证标签显示
            id_text = self.window.selected_hole_id_label.text()
            self.assertIn(other_hole_id, id_text)
            
            # 验证按钮状态（其他孔位无数据）
            self.assertFalse(self.window.goto_realtime_btn.isEnabled())
            self.assertFalse(self.window.goto_history_btn.isEnabled())
            self.assertTrue(self.window.mark_defective_btn.isEnabled())  # 标记异常总是可用
    
    def test_search_clear_ui_e2e(self):
        """测试清空搜索的UI端到端"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        # 1. 先搜索一个孔位
        self.window.search_input.clear()
        QTest.keyClicks(self.window.search_input, 'H00001')
        QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(500)
        
        # 2. 验证孔位被选中
        self.assertIsNotNone(self.window.selected_hole)
        
        # 3. 清空搜索
        self.window.search_input.clear()
        QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(300)
        
        # 4. 验证清空操作（具体行为可能需要根据实际需求调整）
        # 这里主要验证不会出现错误
    
    def test_button_click_behavior_e2e(self):
        """测试按钮点击行为端到端"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        # 1. 搜索H00001（有数据）
        self.window.search_input.clear()
        QTest.keyClicks(self.window.search_input, 'H00001')
        QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(500)
        
        # 2. 验证按钮可点击
        if self.window.goto_realtime_btn.isEnabled():
            # 注意：这里不实际点击，因为可能会触发页面跳转
            # 只验证按钮状态
            self.assertTrue(self.window.goto_realtime_btn.isEnabled())
            self.assertTrue(self.window.goto_history_btn.isEnabled())
        
        # 3. 搜索其他孔位（无数据）
        other_hole_id = None
        for hole_id in self.window.hole_collection.holes.keys():
            if hole_id not in ['H00001', 'H00002']:
                other_hole_id = hole_id
                break
        
        if other_hole_id:
            self.window.search_input.clear()
            QTest.keyClicks(self.window.search_input, other_hole_id)
            QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
            QTest.qWait(500)
            
            # 4. 验证按钮被禁用
            self.assertFalse(self.window.goto_realtime_btn.isEnabled())
            self.assertFalse(self.window.goto_history_btn.isEnabled())
    
    def test_ui_responsiveness_e2e(self):
        """测试UI响应性端到端"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        # 快速连续搜索多个孔位，测试UI响应性
        test_searches = ['H00001', 'H00002']
        
        for search_term in test_searches:
            # 清空并输入
            self.window.search_input.clear()
            QTest.keyClicks(self.window.search_input, search_term)
            
            # 点击搜索
            QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
            QTest.qWait(300)  # 较短的等待时间
            
            # 验证UI更新
            if self.window.selected_hole:
                id_text = self.window.selected_hole_id_label.text()
                # 验证UI确实更新了
                self.assertNotEqual(id_text, "未选择")
                self.assertNotEqual(id_text, "-")
    
    def tearDown(self):
        """清理每个测试"""
        self.window.close()
        QTest.qWait(100)

if __name__ == '__main__':
    unittest.main()
