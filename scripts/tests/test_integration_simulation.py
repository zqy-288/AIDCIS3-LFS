#!/usr/bin/env python3
"""
集成测试 - 模拟进度功能
测试模拟进度与各个组件的集成
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest

from main_window import MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from aidcis2.graphics.sector_manager import SectorManager, SectorQuadrant


class TestSimulationIntegration(unittest.TestCase):
    """测试模拟进度集成"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """每个测试前的准备"""
        self.window = MainWindow()
        
        # 创建测试孔位集合
        holes = {}
        for i in range(10):
            holes[f"H{i+1:03d}"] = HoleData(
                hole_id=f"H{i+1:03d}",
                center_x=(i % 3 - 1) * 50,
                center_y=(i // 3 - 1) * 50,
                radius=5,
                status=HoleStatus.PENDING
            )
        
        self.hole_collection = HoleCollection(holes=holes)
    
    def tearDown(self):
        """每个测试后的清理"""
        if hasattr(self.window, 'simulation_timer_v2'):
            self.window.simulation_timer_v2.stop()
        self.window.close()
    
    def test_simulation_initialization(self):
        """测试模拟初始化"""
        # 设置孔位集合
        self.window.hole_collection = self.hole_collection
        self.window.graphics_view.load_holes(self.hole_collection)
        
        # 启用模拟按钮
        self.window.simulate_btn.setEnabled(True)
        
        # 开始模拟
        self.window._start_simulation_progress_v2()
        
        # 验证初始化
        self.assertTrue(self.window.simulation_running_v2)
        self.assertEqual(self.window.simulation_index_v2, 0)
        self.assertEqual(len(self.window.holes_list_v2), 10)
        self.assertEqual(self.window.simulate_btn.text(), "停止模拟")
    
    def test_simulation_stop(self):
        """测试停止模拟"""
        # 初始化并开始模拟
        self.window.hole_collection = self.hole_collection
        self.window._start_simulation_progress_v2()
        
        # 停止模拟
        self.window._start_simulation_progress_v2()
        
        # 验证停止
        self.assertFalse(self.window.simulation_running_v2)
        self.assertEqual(self.window.simulate_btn.text(), "使用模拟进度")
    
    def test_hole_status_update(self):
        """测试孔位状态更新"""
        # 准备模拟
        self.window.hole_collection = self.hole_collection
        self.window.graphics_view.load_holes(self.hole_collection)
        
        # 创建图形项
        for hole_id, hole in self.hole_collection.holes.items():
            item = Mock()
            item.setBrush = Mock()
            item.setPen = Mock()
            item.update = Mock()
            self.window.graphics_view.hole_items[hole_id] = item
        
        # 开始模拟
        self.window._start_simulation_progress_v2()
        
        # 执行一步更新
        self.window._update_simulation_v2()
        
        # 验证第一个孔位被处理
        first_hole = self.window.holes_list_v2[0]
        first_item = self.window.graphics_view.hole_items[first_hole.hole_id]
        
        # 验证蓝色（处理中）被设置
        first_item.setBrush.assert_called()
        first_item.setPen.assert_called()
        first_item.update.assert_called()
    
    @patch('PySide6.QtCore.QTimer.singleShot')
    def test_final_status_assignment(self, mock_timer):
        """测试最终状态分配"""
        # 准备模拟
        self.window.hole_collection = self.hole_collection
        self.window.graphics_view.load_holes(self.hole_collection)
        self.window.sector_manager = Mock(spec=SectorManager)
        
        # 创建模拟图形项
        mock_item = Mock()
        self.window.graphics_view.hole_items = {
            h.hole_id: mock_item for h in self.hole_collection.holes.values()
        }
        
        # 开始模拟并执行一步
        self.window._start_simulation_progress_v2()
        self.window._update_simulation_v2()
        
        # 获取延迟执行的函数
        # 可能在初始化时已经调用了timer，所以检查至少被调用一次
        self.assertGreaterEqual(mock_timer.call_count, 1)
        delay, callback = mock_timer.call_args[0]
        
        # 执行回调
        callback()
        
        # 验证状态更新
        first_hole = self.window.holes_list_v2[0]
        
        # 验证扇形管理器被调用
        self.window.sector_manager.update_hole_status.assert_called_once()
        call_args = self.window.sector_manager.update_hole_status.call_args[0]
        self.assertEqual(call_args[0], first_hole.hole_id)
        self.assertIn(call_args[1], [
            HoleStatus.QUALIFIED,
            HoleStatus.DEFECTIVE,
            HoleStatus.BLIND,
            HoleStatus.TIE_ROD
        ])
    
    @patch('PySide6.QtCore.QTimer.singleShot')
    def test_statistics_update(self, mock_timer):
        """测试统计更新"""
        # 准备模拟
        self.window.hole_collection = self.hole_collection
        self.window.update_status_display = Mock()
        
        # 模拟完整运行
        self.window._start_simulation_progress_v2()
        
        # 验证统计初始化
        expected_stats = {"合格": 0, "异常": 0, "盲孔": 0, "拉杆孔": 0}
        self.assertEqual(self.window.v2_stats, expected_stats)
        
        # 模拟多次更新
        for _ in range(3):
            if self.window.simulation_index_v2 < len(self.window.holes_list_v2):
                # 创建模拟图形项
                hole = self.window.holes_list_v2[self.window.simulation_index_v2]
                mock_item = Mock()
                self.window.graphics_view.hole_items[hole.hole_id] = mock_item
                
                # 执行更新
                self.window._update_simulation_v2()
                
                # 执行延迟的回调（如果有的话）
                if mock_timer.call_count > 0:
                    delay, callback = mock_timer.call_args[0]
                    callback()
        
        # 验证状态显示被更新
        self.window.update_status_display.assert_called()


class TestSectorManagerIntegration(unittest.TestCase):
    """测试扇形管理器集成"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """每个测试前的准备"""
        # 创建分布在4个象限的孔位
        holes = {}
        positions = [
            ("H001", 50, 50),    # 扇形1
            ("H002", -50, 50),   # 扇形2
            ("H003", -50, -50),  # 扇形3
            ("H004", 50, -50),   # 扇形4
        ]
        
        for hole_id, x, y in positions:
            holes[hole_id] = HoleData(
                hole_id=hole_id,
                center_x=x,
                center_y=y,
                radius=5,
                status=HoleStatus.PENDING
            )
        
        self.hole_collection = HoleCollection(holes=holes)
        self.sector_manager = SectorManager()
        self.sector_manager.load_hole_collection(self.hole_collection)
    
    def test_sector_progress_signals(self):
        """测试扇形进度信号"""
        # 连接信号监听器
        sector_updates = []
        overall_updates = []
        
        self.sector_manager.sector_progress_updated.connect(
            lambda s, p: sector_updates.append((s, p))
        )
        self.sector_manager.overall_progress_updated.connect(
            lambda stats: overall_updates.append(stats)
        )
        
        # 先更新孔位集合中的状态
        self.hole_collection.holes["H001"].status = HoleStatus.QUALIFIED
        # 然后通知扇形管理器
        self.sector_manager.update_hole_status("H001", HoleStatus.QUALIFIED)
        
        # 验证信号发射
        self.assertEqual(len(sector_updates), 1)
        self.assertEqual(len(overall_updates), 1)
        
        # 验证扇形更新
        sector, progress = sector_updates[0]
        self.assertEqual(sector, SectorQuadrant.SECTOR_1)  # H001在(50,50)，数学坐标系中是SECTOR_1
        self.assertEqual(progress.completed_holes, 1)
        self.assertEqual(progress.qualified_holes, 1)
    
    def test_cross_sector_updates(self):
        """测试跨扇形更新"""
        updates = []
        self.sector_manager.sector_progress_updated.connect(
            lambda s, p: updates.append(s)
        )
        
        # 更新不同扇形的孔位
        self.hole_collection.holes["H001"].status = HoleStatus.QUALIFIED
        self.sector_manager.update_hole_status("H001", HoleStatus.QUALIFIED)  # H001在(50,50) -> SECTOR_1
        
        self.hole_collection.holes["H003"].status = HoleStatus.DEFECTIVE
        self.sector_manager.update_hole_status("H003", HoleStatus.DEFECTIVE)  # H003在(-50,-50) -> SECTOR_3
        
        # 验证两个扇形都被更新
        self.assertIn(SectorQuadrant.SECTOR_1, updates)  # H001的扇形
        self.assertIn(SectorQuadrant.SECTOR_3, updates)  # H003的扇形
    
    def test_overall_statistics(self):
        """测试整体统计"""
        overall_stats = []
        self.sector_manager.overall_progress_updated.connect(
            lambda stats: overall_stats.append(stats)
        )
        
        # 更新多个孔位 - 先更新数据，再通知管理器
        self.hole_collection.holes["H001"].status = HoleStatus.QUALIFIED
        self.sector_manager.update_hole_status("H001", HoleStatus.QUALIFIED)
        
        self.hole_collection.holes["H002"].status = HoleStatus.QUALIFIED
        self.sector_manager.update_hole_status("H002", HoleStatus.QUALIFIED)
        
        self.hole_collection.holes["H003"].status = HoleStatus.DEFECTIVE
        self.sector_manager.update_hole_status("H003", HoleStatus.DEFECTIVE)
        
        # 获取最新统计
        latest_stats = overall_stats[-1]
        
        # 验证统计数据
        self.assertEqual(latest_stats['total_holes'], 4)
        self.assertEqual(latest_stats['completed_holes'], 3)
        self.assertEqual(latest_stats['qualified_holes'], 2)
        self.assertEqual(latest_stats['defective_holes'], 1)


class TestUIUpdatesIntegration(unittest.TestCase):
    """测试UI更新集成"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """每个测试前的准备"""
        self.window = MainWindow()
        
        # 创建小规模测试数据
        holes = {}
        for i in range(4):
            holes[f"H{i+1:03d}"] = HoleData(
                hole_id=f"H{i+1:03d}",
                center_x=(i % 2 - 0.5) * 100,
                center_y=(i // 2 - 0.5) * 100,
                radius=5,
                status=HoleStatus.PENDING
            )
        
        self.hole_collection = HoleCollection(holes=holes)
    
    def tearDown(self):
        """每个测试后的清理"""
        self.window.close()
    
    def test_status_display_update(self):
        """测试状态显示更新"""
        # 加载数据
        self.window.hole_collection = self.hole_collection
        
        # 初始状态
        self.window.update_status_display()
        
        # 验证初始显示
        self.assertIn("已完成: 0", self.window.completed_count_label.text())
        self.assertIn("待完成: 4", self.window.pending_count_label.text())
        
        # 更新孔位状态
        self.hole_collection.holes["H001"].status = HoleStatus.QUALIFIED
        self.hole_collection.holes["H002"].status = HoleStatus.DEFECTIVE
        
        # 更新显示
        self.window.update_status_display()
        
        # 验证更新
        self.assertIn("已完成: 2", self.window.completed_count_label.text())
        self.assertIn("待完成: 2", self.window.pending_count_label.text())
        self.assertIn("50.0%", self.window.completion_rate_label.text())
    
    def test_log_message_display(self):
        """测试日志消息显示"""
        # 清空日志
        self.window.log_text.clear()
        
        # 添加消息
        test_messages = [
            "🚀 开始测试",
            "✅ 测试完成",
            "❌ 测试失败"
        ]
        
        for msg in test_messages:
            self.window.log_message(msg)
        
        # 获取日志内容
        log_content = self.window.log_text.toPlainText()
        
        # 验证消息存在
        for msg in test_messages:
            self.assertIn(msg, log_content)
        
        # 验证时间戳
        self.assertIn("[", log_content)
        self.assertIn("]", log_content)
    
    def test_button_state_management(self):
        """测试按钮状态管理"""
        # 初始状态
        self.assertFalse(self.window.simulate_btn.isEnabled())
        
        # 加载数据后
        self.window.hole_collection = self.hole_collection
        self.window.graphics_view.load_holes(self.hole_collection)
        self.window.simulate_btn.setEnabled(True)
        
        # 开始模拟
        self.assertTrue(self.window.simulate_btn.isEnabled())
        self.window._start_simulation_progress_v2()
        
        # 模拟运行中
        self.assertEqual(self.window.simulate_btn.text(), "停止模拟")
        
        # 停止模拟
        self.window._start_simulation_progress_v2()
        self.assertEqual(self.window.simulate_btn.text(), "使用模拟进度")


if __name__ == "__main__":
    unittest.main()