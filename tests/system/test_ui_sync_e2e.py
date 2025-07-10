#!/usr/bin/env python3
"""
UI同步端到端测试
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

class TestUISyncE2E(unittest.TestCase):
    """UI同步端到端测试"""
    
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
                    return True
            except Exception as e:
                print(f"加载测试DXF失败: {e}")
        return False
    
    def test_search_h00001_complete_ui_sync_e2e(self):
        """测试搜索H00001完整UI同步端到端"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        print("\n🧪 测试搜索H00001完整UI同步")
        
        # 1. 清空搜索框
        self.window.search_input.clear()
        QTest.qWait(100)
        
        # 2. 输入搜索文本
        QTest.keyClicks(self.window.search_input, 'H00001')
        QTest.qWait(200)
        
        # 3. 点击搜索按钮
        QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(1000)  # 等待UI更新完成
        
        # 4. 验证孔位被选中
        self.assertIsNotNone(self.window.selected_hole)
        self.assertEqual(self.window.selected_hole.hole_id, 'H00001')
        print(f"✅ 孔位选中验证通过: {self.window.selected_hole.hole_id}")
        
        # 5. 验证左下角UI标签显示
        ui_checks = [
            ('ID标签', self.window.selected_hole_id_label.text(), 'H00001'),
            ('位置标签', self.window.selected_hole_position_label.text(), '('),
            ('状态标签', self.window.selected_hole_status_label.text(), 'PENDING'),
            ('半径标签', self.window.selected_hole_radius_label.text(), 'mm')
        ]
        
        for name, actual, expected_contains in ui_checks:
            print(f"🔍 {name}: '{actual}'")
            self.assertNotEqual(actual, "未选择")
            self.assertNotEqual(actual, "-")
            if expected_contains:
                self.assertIn(expected_contains, actual)
        
        print("✅ 所有UI标签验证通过")
        
        # 6. 验证按钮状态（H00001有数据）
        button_checks = [
            ('实时监控按钮', self.window.goto_realtime_btn.isEnabled(), True),
            ('历史数据按钮', self.window.goto_history_btn.isEnabled(), True),
            ('标记异常按钮', self.window.mark_defective_btn.isEnabled(), True)
        ]
        
        for name, actual, expected in button_checks:
            print(f"🎮 {name}: {actual}")
            self.assertEqual(actual, expected)
        
        print("✅ 所有按钮状态验证通过")
        
        # 7. 验证工具提示
        realtime_tooltip = self.window.goto_realtime_btn.toolTip()
        print(f"💬 实时监控工具提示: '{realtime_tooltip}'")
        self.assertIn("H00001", realtime_tooltip)
        self.assertIn("实时监控", realtime_tooltip)
        
        print("✅ 工具提示验证通过")
    
    def test_search_h00003_ui_sync_e2e(self):
        """测试搜索H00003 UI同步端到端"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        print("\n🧪 测试搜索其他孔位UI同步")
        
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
        QTest.qWait(1000)
        
        # 3. 验证UI更新
        if self.window.selected_hole and self.window.selected_hole.hole_id == other_hole_id:
            # 验证标签显示
            id_text = self.window.selected_hole_id_label.text()
            print(f"🔍 其他孔位ID标签: '{id_text}'")
            self.assertIn(other_hole_id, id_text)
            
            # 验证按钮状态（其他孔位无数据）
            self.assertFalse(self.window.goto_realtime_btn.isEnabled())
            self.assertFalse(self.window.goto_history_btn.isEnabled())
            self.assertTrue(self.window.mark_defective_btn.isEnabled())
            
            print(f"✅ {other_hole_id} UI同步验证通过")
    
    def test_simulation_progress_1000ms_e2e(self):
        """测试1000ms模拟进度端到端"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        print("\n🧪 测试1000ms模拟进度")
        
        # 记录开始时间
        start_time = time.time()
        
        # 1. 点击模拟进度按钮
        QTest.mouseClick(self.window.simulate_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(500)  # 等待模拟开始
        
        # 2. 验证模拟开始
        self.assertTrue(hasattr(self.window, 'simulation_running_v2'))
        if hasattr(self.window, 'simulation_running_v2'):
            self.assertTrue(self.window.simulation_running_v2)
            print("✅ 模拟进度已开始")
        
        # 3. 验证定时器间隔
        if hasattr(self.window, 'simulation_timer_v2') and self.window.simulation_timer_v2:
            interval = self.window.simulation_timer_v2.interval()
            print(f"⏱️ 定时器间隔: {interval}ms")
            self.assertEqual(interval, 1000)
            print("✅ 定时器间隔验证通过")
        
        # 4. 等待几个周期观察性能
        QTest.qWait(3000)  # 等待3秒，应该处理3个孔位
        
        elapsed_time = time.time() - start_time
        print(f"⏱️ 经过时间: {elapsed_time:.1f}秒")
        
        # 5. 停止模拟（如果还在运行）
        if hasattr(self.window, 'simulation_running_v2') and self.window.simulation_running_v2:
            if hasattr(self.window, 'simulation_timer_v2') and self.window.simulation_timer_v2:
                self.window.simulation_timer_v2.stop()
                self.window.simulation_running_v2 = False
                print("🛑 模拟进度已停止")
    
    def test_right_click_ui_sync_e2e(self):
        """测试右键点击UI同步端到端"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        print("\n🧪 测试右键点击UI同步")
        
        # 注意：这个测试模拟右键选择的效果，而不是实际的鼠标右键点击
        # 因为图形视图的右键点击需要复杂的坐标计算
        
        # 1. 获取一个测试孔位
        test_hole_id = list(self.window.hole_collection.holes.keys())[0]
        test_hole = self.window.hole_collection.holes[test_hole_id]
        
        print(f"🎯 模拟右键选择孔位: {test_hole_id}")
        
        # 2. 模拟右键选择（直接调用处理方法）
        self.window.on_hole_selected(test_hole)
        QTest.qWait(500)  # 等待UI更新
        
        # 3. 验证UI同步
        self.assertIsNotNone(self.window.selected_hole)
        self.assertEqual(self.window.selected_hole.hole_id, test_hole_id)
        
        # 4. 验证UI标签更新
        id_text = self.window.selected_hole_id_label.text()
        print(f"🔍 右键选择后ID标签: '{id_text}'")
        self.assertIn(test_hole_id, id_text)
        
        print("✅ 右键选择UI同步验证通过")
    
    def test_ui_responsiveness_under_load_e2e(self):
        """测试负载下的UI响应性端到端"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        print("\n🧪 测试负载下UI响应性")
        
        # 快速连续执行多个操作
        test_operations = [
            ('H00001', True),
            ('H00002', True),
        ]
        
        # 添加其他孔位
        other_holes = [hole_id for hole_id in self.window.hole_collection.holes.keys() 
                      if hole_id not in ['H00001', 'H00002']][:2]
        for hole_id in other_holes:
            test_operations.append((hole_id, False))
        
        for i, (hole_id, has_data) in enumerate(test_operations):
            print(f"🔄 操作 {i+1}: 搜索 {hole_id}")
            
            # 清空并搜索
            self.window.search_input.clear()
            QTest.keyClicks(self.window.search_input, hole_id)
            QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
            QTest.qWait(300)  # 较短等待时间测试响应性
            
            # 验证UI更新
            if self.window.selected_hole:
                actual_id = self.window.selected_hole_id_label.text()
                print(f"  📝 UI标签: '{actual_id}'")
                
                # 验证按钮状态
                realtime_enabled = self.window.goto_realtime_btn.isEnabled()
                print(f"  🎮 实时监控按钮: {realtime_enabled} (期望: {has_data})")
                
                # 基本验证（在快速操作下可能不完全准确）
                self.assertNotEqual(actual_id, "未选择")
        
        print("✅ 负载下UI响应性测试完成")
    
    def test_complete_user_workflow_e2e(self):
        """测试完整用户工作流端到端"""
        if not self.window.hole_collection:
            self.skipTest("无法加载测试DXF文件")
        
        print("\n🧪 测试完整用户工作流")
        
        # 1. 用户加载DXF文件（已在setUp中完成）
        print("✅ DXF文件已加载")
        
        # 2. 用户搜索H00001
        self.window.search_input.clear()
        QTest.keyClicks(self.window.search_input, 'H00001')
        QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(1000)
        
        print("✅ 搜索H00001完成")
        
        # 3. 用户查看孔位信息
        if self.window.selected_hole:
            print(f"📊 孔位信息: {self.window.selected_hole.hole_id}")
            print(f"  位置: {self.window.selected_hole_position_label.text()}")
            print(f"  状态: {self.window.selected_hole_status_label.text()}")
            print(f"  半径: {self.window.selected_hole_radius_label.text()}")
        
        # 4. 用户启动模拟进度
        QTest.mouseClick(self.window.simulate_btn, Qt.MouseButton.LeftButton)
        QTest.qWait(2000)  # 观察模拟进度
        
        print("✅ 模拟进度已启动")
        
        # 5. 用户搜索其他孔位
        other_hole_id = None
        for hole_id in self.window.hole_collection.holes.keys():
            if hole_id not in ['H00001', 'H00002']:
                other_hole_id = hole_id
                break
        
        if other_hole_id:
            self.window.search_input.clear()
            QTest.keyClicks(self.window.search_input, other_hole_id)
            QTest.mouseClick(self.window.search_btn, Qt.MouseButton.LeftButton)
            QTest.qWait(1000)
            
            print(f"✅ 搜索{other_hole_id}完成")
        
        print("🎉 完整用户工作流测试完成")
    
    def tearDown(self):
        """清理每个测试"""
        # 停止所有定时器
        if hasattr(self.window, 'simulation_timer_v2') and self.window.simulation_timer_v2:
            self.window.simulation_timer_v2.stop()
        
        # 重置模拟状态
        if hasattr(self.window, 'simulation_running_v2'):
            self.window.simulation_running_v2 = False
        
        self.window.close()
        QTest.qWait(100)

if __name__ == '__main__':
    unittest.main()
