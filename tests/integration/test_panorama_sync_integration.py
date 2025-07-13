"""
集成测试：全景图同步系统集成
测试数据库、同步管理器和全景图组件的集成功能
"""

import unittest
import sys
import os
import tempfile
import time
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from aidcis2.data_management.panorama_sync_manager import PanoramaSyncManager, StatusUpdateBuffer
from aidcis2.graphics.dynamic_sector_view import CompletePanoramaWidget
from aidcis2.models.hole_data import HoleStatus
from modules.models import DatabaseManager, HoleStatusUpdate, Hole, Workpiece


class TestPanoramaSyncIntegration(unittest.TestCase):
    """测试全景图同步系统集成"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # 创建数据库管理器
        self.db_manager = DatabaseManager(f"sqlite:///{self.temp_db.name}")
        self.db_manager.create_tables()
        
        # 创建全景图组件（模拟）
        self.panorama_widget = Mock(spec=CompletePanoramaWidget)
        self.panorama_widget.batch_update_from_db = Mock()
        self.panorama_widget.batch_update_hole_status = Mock()
        self.panorama_widget.set_panorama_sync_manager = Mock()
        self.panorama_widget.enable_db_sync = Mock()
        
        # 创建同步管理器
        self.sync_manager = PanoramaSyncManager(self.db_manager, self.panorama_widget)
        
        # 创建测试数据
        self._create_test_workpiece_and_holes()
    
    def tearDown(self):
        """测试后清理"""
        self.sync_manager.stop_sync()
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def _create_test_workpiece_and_holes(self):
        """创建测试工件和孔位"""
        session = self.db_manager.get_session()
        try:
            # 创建工件
            workpiece = Workpiece(
                workpiece_id="INTEGRATION-TEST-001",
                name="集成测试工件",
                type="test_integration",
                hole_count=10
            )
            session.add(workpiece)
            session.flush()
            
            # 创建10个孔位
            self.test_holes = []
            for i in range(10):
                hole = Hole(
                    hole_id=f"H{i+1:03d}",
                    workpiece_id=workpiece.id,
                    position_x=i * 10.0,
                    position_y=i * 10.0,
                    target_diameter=25.0,
                    tolerance=0.1,
                    status='pending'
                )
                self.test_holes.append(hole)
                session.add(hole)
            
            session.commit()
            self.test_workpiece_id = workpiece.id
            
        finally:
            self.db_manager.close_session(session)
    
    def test_end_to_end_status_update_flow(self):
        """测试端到端状态更新流程"""
        print("\n=== 测试端到端状态更新流程 ===")
        
        # 1. 更新几个孔位状态（模拟检测系统更新）
        updates = [
            ("H001", "qualified", "detection"),
            ("H002", "defective", "detection"),
            ("H003", "qualified", "detection"),
            ("H004", "processing", "detection"),
            ("H005", "blind", "manual")
        ]
        
        print("1. 添加状态更新到数据库...")
        for hole_id, status, source in updates:
            result = self.db_manager.update_hole_status(hole_id, status, source)
            self.assertTrue(result, f"更新 {hole_id} 失败")
        
        # 2. 验证数据库中有待同步的更新
        pending_updates = self.db_manager.get_pending_status_updates()
        self.assertEqual(len(pending_updates), 5, "待同步更新数量不正确")
        print(f"2. 数据库中有 {len(pending_updates)} 个待同步更新")
        
        # 3. 执行同步
        print("3. 执行同步...")
        self.sync_manager.sync_updates()
        
        # 4. 验证全景图组件被调用
        self.panorama_widget.batch_update_hole_status.assert_called_once()
        call_args = self.panorama_widget.batch_update_hole_status.call_args[0][0]
        print(f"4. 全景图更新调用参数: {call_args}")
        
        # 验证状态映射正确
        expected_mappings = {
            "H001": HoleStatus.QUALIFIED,
            "H002": HoleStatus.DEFECTIVE,
            "H003": HoleStatus.QUALIFIED,
            "H004": HoleStatus.PROCESSING,
            "H005": HoleStatus.BLIND
        }
        
        for hole_id, expected_status in expected_mappings.items():
            self.assertEqual(call_args[hole_id], expected_status, 
                           f"孔位 {hole_id} 状态映射错误")
        
        # 5. 验证数据库中的更新被标记为已同步
        remaining_pending = self.db_manager.get_pending_status_updates()
        self.assertEqual(len(remaining_pending), 0, "仍有未同步的更新")
        print("5. 所有更新已标记为已同步")
        
        # 6. 验证统计信息
        stats = self.db_manager.get_status_update_stats()
        self.assertEqual(stats['total_updates'], 5)
        self.assertEqual(stats['synced_updates'], 5)
        self.assertEqual(stats['sync_rate'], 100.0)
        print(f"6. 同步统计: {stats}")
    
    def test_batch_processing_with_buffer(self):
        """测试使用缓冲区的批量处理"""
        print("\n=== 测试批量处理缓冲区 ===")
        
        # 创建状态更新缓冲区
        buffer = StatusUpdateBuffer(self.db_manager, buffer_size=3, flush_interval=0.5)
        
        # 添加多个更新（但不超过缓冲区大小）
        print("1. 添加更新到缓冲区...")
        buffer.add_update("H001", "qualified", "detection")
        buffer.add_update("H002", "defective", "detection")
        
        # 此时缓冲区不应刷新
        pending_updates = self.db_manager.get_pending_status_updates()
        self.assertEqual(len(pending_updates), 0, "缓冲区过早刷新")
        
        # 添加第三个更新，应该触发刷新
        print("2. 添加第三个更新触发缓冲区刷新...")
        buffer.add_update("H003", "qualified", "detection")
        
        # 现在应该有3个待同步更新
        pending_updates = self.db_manager.get_pending_status_updates()
        self.assertEqual(len(pending_updates), 3, "缓冲区刷新后数据不正确")
        
        # 执行同步
        print("3. 执行同步...")
        self.sync_manager.sync_updates()
        
        # 验证全景图被更新
        self.panorama_widget.batch_update_hole_status.assert_called_once()
        
        # 验证所有更新都被同步
        remaining_pending = self.db_manager.get_pending_status_updates()
        self.assertEqual(len(remaining_pending), 0, "批量同步后仍有待同步更新")
        print("4. 批量同步完成")
    
    def test_automatic_sync_timer(self):
        """测试自动同步定时器"""
        print("\n=== 测试自动同步定时器 ===")
        
        # 启动自动同步（短间隔用于测试）
        self.sync_manager.start_sync(100)  # 100ms间隔
        self.assertTrue(self.sync_manager.sync_timer.isActive(), "定时器未启动")
        print("1. 自动同步定时器已启动")
        
        # 添加状态更新
        self.db_manager.update_hole_status("H001", "qualified", "auto_test")
        print("2. 添加状态更新")
        
        # 等待定时器触发（最多等待1秒）
        print("3. 等待自动同步...")
        start_time = time.time()
        while time.time() - start_time < 1.0:
            pending_updates = self.db_manager.get_pending_status_updates()
            if len(pending_updates) == 0:
                break
            time.sleep(0.05)  # 50ms检查一次
        
        # 验证自动同步完成
        pending_updates = self.db_manager.get_pending_status_updates()
        self.assertEqual(len(pending_updates), 0, "自动同步未完成")
        print("4. 自动同步完成")
        
        # 停止定时器
        self.sync_manager.stop_sync()
        self.assertFalse(self.sync_manager.sync_timer.isActive(), "定时器未停止")
        print("5. 定时器已停止")
    
    def test_panorama_widget_integration(self):
        """测试与全景图组件的集成"""
        print("\n=== 测试全景图组件集成 ===")
        
        # 创建真实的全景图组件（简化版）
        class MockPanoramaWidget:
            def __init__(self):
                self.updated_holes = {}
                self.batch_update_calls = 0
                
            def batch_update_hole_status(self, status_updates):
                self.batch_update_calls += 1
                self.updated_holes.update(status_updates)
                print(f"  批量更新调用 #{self.batch_update_calls}: {len(status_updates)} 个孔位")
            
            def batch_update_from_db(self, updates_list):
                # 转换格式并调用批量更新
                status_updates = {}
                for update in updates_list:
                    hole_id = update['hole_id']
                    new_status = update['new_status']
                    status_mapping = {
                        'pending': HoleStatus.PENDING,
                        'qualified': HoleStatus.QUALIFIED,
                        'defective': HoleStatus.DEFECTIVE,
                        'blind': HoleStatus.BLIND,
                        'tie_rod': HoleStatus.TIE_ROD,
                        'processing': HoleStatus.PROCESSING
                    }
                    if new_status in status_mapping:
                        status_updates[hole_id] = status_mapping[new_status]
                
                self.batch_update_hole_status(status_updates)
        
        # 使用真实的模拟组件
        real_mock_widget = MockPanoramaWidget()
        self.sync_manager.set_panorama_widget(real_mock_widget)
        print("1. 设置真实模拟全景图组件")
        
        # 添加多个状态更新
        updates = [
            ("H001", "qualified"),
            ("H002", "defective"),
            ("H003", "blind"),
            ("H004", "processing")
        ]
        
        print("2. 添加多个状态更新...")
        for hole_id, status in updates:
            self.db_manager.update_hole_status(hole_id, status, "integration_test")
        
        # 执行同步
        print("3. 执行同步...")
        self.sync_manager.sync_updates()
        
        # 验证全景图组件状态
        self.assertEqual(real_mock_widget.batch_update_calls, 1, "批量更新调用次数不正确")
        self.assertEqual(len(real_mock_widget.updated_holes), 4, "更新的孔位数量不正确")
        
        # 验证具体状态
        expected_states = {
            "H001": HoleStatus.QUALIFIED,
            "H002": HoleStatus.DEFECTIVE,
            "H003": HoleStatus.BLIND,
            "H004": HoleStatus.PROCESSING
        }
        
        for hole_id, expected_status in expected_states.items():
            actual_status = real_mock_widget.updated_holes.get(hole_id)
            self.assertEqual(actual_status, expected_status, 
                           f"孔位 {hole_id} 状态不正确: 期望 {expected_status}, 实际 {actual_status}")
        
        print("4. 全景图组件集成验证完成")
    
    def test_error_handling_and_recovery(self):
        """测试错误处理和恢复"""
        print("\n=== 测试错误处理和恢复 ===")
        
        # 模拟全景图组件错误
        error_widget = Mock()
        error_widget.batch_update_hole_status.side_effect = Exception("模拟全景图组件错误")
        
        self.sync_manager.set_panorama_widget(error_widget)
        print("1. 设置错误模拟全景图组件")
        
        # 添加状态更新
        self.db_manager.update_hole_status("H001", "qualified", "error_test")
        print("2. 添加状态更新")
        
        # 执行同步（应该捕获错误）
        print("3. 执行同步（预期有错误）...")
        initial_error_count = self.sync_manager.sync_errors
        self.sync_manager.sync_updates()
        
        # 验证错误被记录
        self.assertGreater(self.sync_manager.sync_errors, initial_error_count, "错误未被记录")
        print(f"4. 错误已记录，错误计数: {self.sync_manager.sync_errors}")
        
        # 恢复正常组件
        normal_widget = Mock()
        normal_widget.batch_update_hole_status = Mock()
        self.sync_manager.set_panorama_widget(normal_widget)
        print("5. 恢复正常全景图组件")
        
        # 再次同步（应该成功）
        self.sync_manager.sync_updates()
        normal_widget.batch_update_hole_status.assert_called_once()
        print("6. 恢复后同步成功")
    
    def test_concurrent_updates_handling(self):
        """测试并发更新处理"""
        print("\n=== 测试并发更新处理 ===")
        
        # 快速连续添加多个更新（模拟并发）
        print("1. 快速连续添加更新...")
        for i in range(10):
            hole_id = f"H{i+1:03d}"
            status = "qualified" if i % 2 == 0 else "defective"
            self.db_manager.update_hole_status(hole_id, status, f"concurrent_test_{i}")
            time.sleep(0.001)  # 1ms间隔
        
        # 验证所有更新都在数据库中
        pending_updates = self.db_manager.get_pending_status_updates()
        self.assertEqual(len(pending_updates), 10, "并发更新丢失")
        print(f"2. 数据库中有 {len(pending_updates)} 个待同步更新")
        
        # 执行同步
        print("3. 执行并发更新同步...")
        self.sync_manager.sync_updates()
        
        # 验证所有更新都被处理
        remaining_pending = self.db_manager.get_pending_status_updates()
        self.assertEqual(len(remaining_pending), 0, "并发更新同步不完整")
        print("4. 并发更新同步完成")
        
        # 验证全景图组件收到正确数量的更新
        self.panorama_widget.batch_update_hole_status.assert_called_once()
        call_args = self.panorama_widget.batch_update_hole_status.call_args[0][0]
        self.assertEqual(len(call_args), 10, "全景图组件收到的更新数量不正确")
        print(f"5. 全景图组件收到 {len(call_args)} 个更新")
    
    def test_performance_with_large_batch(self):
        """测试大批量更新性能"""
        print("\n=== 测试大批量更新性能 ===")
        
        # 创建大量孔位数据
        session = self.db_manager.get_session()
        try:
            for i in range(100, 200):  # 添加100个额外孔位
                hole = Hole(
                    hole_id=f"H{i+1:03d}",
                    workpiece_id=self.test_workpiece_id,
                    position_x=i * 10.0,
                    position_y=i * 10.0,
                    target_diameter=25.0,
                    tolerance=0.1,
                    status='pending'
                )
                session.add(hole)
            session.commit()
        finally:
            self.db_manager.close_session(session)
        
        print("1. 创建了100个额外孔位")
        
        # 批量更新所有孔位状态
        print("2. 批量更新所有孔位状态...")
        start_time = time.time()
        
        for i in range(100, 200):
            hole_id = f"H{i+1:03d}"
            status = "qualified" if i % 3 == 0 else ("defective" if i % 3 == 1 else "blind")
            self.db_manager.update_hole_status(hole_id, status, "performance_test")
        
        db_update_time = time.time() - start_time
        print(f"3. 数据库更新耗时: {db_update_time:.3f}秒")
        
        # 执行同步
        start_time = time.time()
        self.sync_manager.sync_updates()
        sync_time = time.time() - start_time
        
        print(f"4. 同步耗时: {sync_time:.3f}秒")
        
        # 验证性能指标（简单检查）
        self.assertLess(db_update_time, 5.0, "数据库更新耗时过长")
        self.assertLess(sync_time, 2.0, "同步耗时过长")
        
        # 验证结果
        remaining_pending = self.db_manager.get_pending_status_updates()
        self.assertEqual(len(remaining_pending), 0, "大批量同步不完整")
        print("5. 大批量更新性能测试完成")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)