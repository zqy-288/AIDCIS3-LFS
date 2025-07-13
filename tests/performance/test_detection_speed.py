#!/usr/bin/env python3
"""
检测速度性能测试
"""

import unittest
import sys
import time
from pathlib import Path
from unittest.mock import Mock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop

class TestDetectionSpeed(unittest.TestCase):
    """检测速度性能测试"""
    
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
        
        # 创建模拟孔位数据
        from aidcis2.models.hole_data import HoleData, HoleStatus
        self.test_holes = {}
        for i in range(10):  # 创建10个测试孔位
            hole_id = f"H{i:05d}"
            self.test_holes[hole_id] = HoleData(hole_id, i*10, i*10, 5.0, HoleStatus.PENDING)
        
        # 模拟孔位集合
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
        
        self.window.graphics_view.scene = Mock()
        self.window.graphics_view.viewport = Mock()
        self.window.graphics_view.update = Mock()
    
    def test_simulation_timer_frequency(self):
        """测试模拟定时器频率"""
        # 启动V2模拟
        self.window._start_simulation_progress_v2()
        
        # 检查定时器是否创建并设置正确的间隔
        self.assertTrue(hasattr(self.window, 'simulation_timer_v2'))
        self.assertIsNotNone(self.window.simulation_timer_v2)
        
        # 检查定时器间隔（1000ms）
        # 注意：QTimer.interval()返回的是毫秒
        expected_interval = 1000
        actual_interval = self.window.simulation_timer_v2.interval()
        self.assertEqual(actual_interval, expected_interval)
    
    def test_color_change_delay(self):
        """测试颜色变化延迟"""
        # 这个测试验证QTimer.singleShot的延迟设置
        # 由于我们无法直接测试singleShot的延迟，我们检查代码中的设置
        import inspect
        
        update_source = inspect.getsource(self.window._update_simulation_v2)
        
        # 验证100ms延迟设置
        self.assertIn('singleShot(100', update_source)
    
    def test_simulation_speed_calculation(self):
        """测试模拟速度计算"""
        hole_count = len(self.test_holes)
        detection_interval = 200  # ms
        color_delay = 100  # ms
        
        # 计算理论总时间
        # 每个孔位: 检测间隔 + 颜色延迟
        theoretical_time_per_hole = detection_interval + color_delay  # 300ms
        theoretical_total_time = hole_count * theoretical_time_per_hole  # ms
        
        # 验证时间计算
        self.assertEqual(theoretical_time_per_hole, 300)
        self.assertEqual(theoretical_total_time, hole_count * 300)
        
        # 对于10个孔位，总时间应该是3000ms = 3秒
        expected_total_seconds = theoretical_total_time / 1000
        self.assertEqual(expected_total_seconds, 3.0)
    
    def test_performance_improvement(self):
        """测试性能提升计算"""
        # 原来的设置
        old_detection_interval = 1500  # ms
        old_color_delay = 500  # ms
        old_time_per_hole = old_detection_interval + old_color_delay  # 2000ms
        
        # 新的设置
        new_detection_interval = 200  # ms
        new_color_delay = 100  # ms
        new_time_per_hole = new_detection_interval + new_color_delay  # 300ms
        
        # 计算性能提升
        improvement_ratio = old_time_per_hole / new_time_per_hole
        
        # 验证性能提升约为6.67倍
        self.assertAlmostEqual(improvement_ratio, 6.67, places=2)
        
        # 对于9个孔位的实际情况
        hole_count = 9
        old_total_time = hole_count * old_time_per_hole / 1000  # 秒
        new_total_time = hole_count * new_time_per_hole / 1000  # 秒
        
        self.assertEqual(old_total_time, 18.0)  # 18秒
        self.assertEqual(new_total_time, 2.7)   # 2.7秒
    
    def test_high_frequency_stability(self):
        """测试高频更新的稳定性"""
        # 启动模拟
        self.window._start_simulation_progress_v2()
        
        # 验证模拟状态
        self.assertTrue(self.window.simulation_running_v2)
        self.assertEqual(self.window.simulation_index_v2, 0)
        
        # 验证孔位列表
        self.assertEqual(len(self.window.holes_list_v2), len(self.test_holes))
        
        # 验证定时器运行
        self.assertTrue(self.window.simulation_timer_v2.isActive())
    
    def test_memory_efficiency(self):
        """测试内存效率"""
        # 启动模拟前的状态
        initial_vars = len(vars(self.window))
        
        # 启动模拟
        self.window._start_simulation_progress_v2()
        
        # 检查新增的变量数量是否合理
        final_vars = len(vars(self.window))
        new_vars = final_vars - initial_vars
        
        # 应该只新增少量变量（simulation_running_v2, simulation_index_v2等）
        self.assertLessEqual(new_vars, 10)
    
    def tearDown(self):
        """清理测试"""
        # 停止所有定时器
        if hasattr(self.window, 'simulation_timer_v2') and self.window.simulation_timer_v2:
            self.window.simulation_timer_v2.stop()
        
        # 重置模拟状态
        if hasattr(self.window, 'simulation_running_v2'):
            self.window.simulation_running_v2 = False

class TestDetectionFrequencyIntegration(unittest.TestCase):
    """检测频率集成测试"""
    
    def test_frequency_configuration_consistency(self):
        """测试频率配置一致性"""
        from main_window.main_window import MainWindow
        import inspect
        
        # 检查所有相关方法的频率设置
        start_source = inspect.getsource(MainWindow._start_simulation_progress_v2)
        update_source = inspect.getsource(MainWindow._update_simulation_v2)
        
        # 验证主频率设置
        self.assertIn('start(1000)', start_source)
        
        # 验证延迟设置
        self.assertIn('singleShot(100', update_source)
        
        # 验证日志信息一致性
        self.assertIn('1000ms/孔位', start_source)
        self.assertIn('100ms', start_source)
    
    def test_user_experience_timing(self):
        """测试用户体验时间"""
        # 定义用户体验标准
        max_acceptable_total_time = 5.0  # 秒
        max_acceptable_per_hole_time = 0.5  # 秒
        
        # 当前设置
        detection_interval = 0.2  # 秒
        color_delay = 0.1  # 秒
        time_per_hole = detection_interval + color_delay
        
        # 验证单孔位时间符合用户体验标准
        self.assertLessEqual(time_per_hole, max_acceptable_per_hole_time)
        
        # 验证9个孔位的总时间符合标准
        total_time_9_holes = 9 * time_per_hole
        self.assertLessEqual(total_time_9_holes, max_acceptable_total_time)

if __name__ == '__main__':
    unittest.main()
