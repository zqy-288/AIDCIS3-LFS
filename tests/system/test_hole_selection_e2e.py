#!/usr/bin/env python3
"""
孔位选择端到端测试
"""

import unittest
import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

class TestHoleSelectionE2E(unittest.TestCase):
    """孔位选择端到端测试"""
    
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
                    
                    # 启用按钮
                    self.window.start_detection_btn.setEnabled(True)
                    self.window.simulate_btn.setEnabled(True)
                    
                    return True
            except Exception as e:
                print(f"加载测试DXF失败: {e}")
        return False
    
    def test_search_h00001_complete_workflow(self):
        """测试搜索H00001的完整工作流"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        # 1. 输入搜索文本
        self.window.search_input.setText('H00001')
        QTest.qWait(100)
        
        # 2. 点击搜索按钮
        QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(500)  # 等待搜索完成
        
        # 3. 验证孔位被选中
        self.assertIsNotNone(self.window.selected_hole)
        if self.window.selected_hole:
            self.assertEqual(self.window.selected_hole.hole_id, 'H00001')
        
        # 4. 验证UI更新
        self.assertIn('H00001', self.window.selected_hole_id_label.text())
        
        # 5. 验证按钮状态（H00001有数据）
        self.assertTrue(self.window.goto_realtime_btn.isEnabled())
        self.assertTrue(self.window.goto_history_btn.isEnabled())
        self.assertTrue(self.window.mark_defective_btn.isEnabled())
    
    def test_search_h00003_complete_workflow(self):
        """测试搜索H00003的完整工作流"""
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
        
        # 1. 输入搜索文本
        self.window.search_input.setText(other_hole_id)
        QTest.qWait(100)
        
        # 2. 点击搜索按钮
        QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(500)
        
        # 3. 验证孔位被选中
        self.assertIsNotNone(self.window.selected_hole)
        if self.window.selected_hole:
            self.assertEqual(self.window.selected_hole.hole_id, other_hole_id)
        
        # 4. 验证按钮状态（其他孔位无数据）
        self.assertFalse(self.window.goto_realtime_btn.isEnabled())
        self.assertFalse(self.window.goto_history_btn.isEnabled())
        self.assertTrue(self.window.mark_defective_btn.isEnabled())  # 标记异常总是可用
    
    def test_clear_search_workflow(self):
        """测试清空搜索的工作流"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        # 1. 先搜索一个孔位
        self.window.search_input.setText('H00001')
        QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(300)
        
        # 2. 清空搜索
        self.window.search_input.clear()
        QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(300)
        
        # 3. 验证搜索被清空（这里可能需要根据实际行为调整）
        # 注意：清空搜索的具体行为可能需要根据实际需求调整
    
    def test_simulation_color_change_workflow(self):
        """测试模拟进度颜色变化工作流"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        # 1. 点击模拟进度按钮
        QTest.mouseClick(self.window.simulate_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(1000)  # 等待模拟开始
        
        # 2. 验证模拟是否开始
        self.assertTrue(hasattr(self.window, 'simulation_running_v2'))
        
        # 3. 等待一些颜色变化
        QTest.qWait(3000)  # 等待几个孔位的处理
        
        # 4. 停止模拟
        if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
            QTest.mouseClick(self.window.simulate_btn, Qt.MouseButton.LeftButton)
            QTest.qWait(500)
    
    def test_color_test_workflow(self):
        """测试颜色测试工作流（已移除功能）"""
        # 颜色测试功能已被移除，跳过此测试
        self.skipTest("颜色测试功能已移除")
    
    def test_button_tooltip_workflow(self):
        """测试按钮工具提示工作流"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        # 1. 搜索H00001
        self.window.search_input.setText('H00001')
        QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(500)
        
        # 2. 检查工具提示
        realtime_tooltip = self.window.goto_realtime_btn.toolTip()
        history_tooltip = self.window.goto_history_btn.toolTip()
        
        self.assertIn('H00001', realtime_tooltip)
        self.assertIn('H00001', history_tooltip)
        
        # 3. 搜索其他孔位
        other_hole_id = None
        for hole_id in self.window.hole_collection.holes.keys():
            if hole_id not in ['H00001', 'H00002']:
                other_hole_id = hole_id
                break
        
        if other_hole_id:
            self.window.search_input.setText(other_hole_id)
            QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
            QTest.qWait(500)
            
            # 4. 检查工具提示变化
            realtime_tooltip = self.window.goto_realtime_btn.toolTip()
            history_tooltip = self.window.goto_history_btn.toolTip()
            
            self.assertIn('无', realtime_tooltip)
            self.assertIn('无', history_tooltip)
    
    def tearDown(self):
        """清理每个测试"""
        if hasattr(self.window, 'simulation_timer_v2') and self.window.simulation_timer_v2:
            self.window.simulation_timer_v2.stop()
        if hasattr(self.window, 'color_test_timer') and self.window.color_test_timer:
            self.window.color_test_timer.stop()
        
        self.window.close()
        QTest.qWait(100)

if __name__ == '__main__':
    unittest.main()
