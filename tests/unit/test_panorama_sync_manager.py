"""
单元测试：全景图同步管理器
测试PanoramaSyncManager和StatusUpdateBuffer类的功能
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
from aidcis2.models.hole_data import HoleStatus
from modules.models import DatabaseManager, HoleStatusUpdate, Hole, Workpiece


class TestPanoramaSyncManager(unittest.TestCase):
    """测试PanoramaSyncManager类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # 创建数据库管理器
        self.db_manager = DatabaseManager(f"sqlite:///{self.temp_db.name}")
        self.db_manager.create_tables()
        
        # 创建模拟全景图组件
        self.mock_panorama_widget = Mock()
        
        # 创建同步管理器
        self.sync_manager = PanoramaSyncManager(self.db_manager, self.mock_panorama_widget)
        
        # 创建测试数据
        self._create_test_data()
    
    def tearDown(self):
        """测试后清理"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def _create_test_data(self):
        """创建测试数据"""
        session = self.db_manager.get_session()
        try:
            # 创建工件
            workpiece = Workpiece(
                workpiece_id="TEST-001",
                name="测试工件",
                type="test",
                hole_count=5
            )
            session.add(workpiece)
            session.flush()
            
            # 创建孔位
            holes = []
            for i in range(5):
                hole = Hole(
                    hole_id=f"H{i+1:03d}",
                    workpiece_id=workpiece.id,
                    position_x=i * 10.0,
                    position_y=i * 10.0,
                    target_diameter=25.0,
                    tolerance=0.1,
                    status='pending'
                )
                holes.append(hole)
                session.add(hole)
            
            session.commit()
            self.test_workpiece_id = workpiece.id
            self.test_holes = holes
            
        finally:
            self.db_manager.close_session(session)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.sync_manager.db_manager)
        self.assertEqual(self.sync_manager.panorama_widget, self.mock_panorama_widget)
        self.assertEqual(self.sync_manager.sync_interval, 1000)
        self.assertEqual(self.sync_manager.batch_size, 50)
        self.assertTrue(self.sync_manager.auto_sync_enabled)
    
    def test_status_mapping(self):
        """测试状态映射"""
        expected_mapping = {
            'pending': HoleStatus.PENDING,
            'qualified': HoleStatus.QUALIFIED,
            'defective': HoleStatus.DEFECTIVE,
            'blind': HoleStatus.BLIND,
            'tie_rod': HoleStatus.TIE_ROD,
            'processing': HoleStatus.PROCESSING
        }
        self.assertEqual(self.sync_manager.status_mapping, expected_mapping)
    
    def test_start_stop_sync(self):
        """测试启动和停止同步"""
        # 测试启动
        self.sync_manager.start_sync(500)
        self.assertTrue(self.sync_manager.sync_timer.isActive())
        self.assertEqual(self.sync_manager.sync_interval, 500)
        
        # 测试停止
        self.sync_manager.stop_sync()
        self.assertFalse(self.sync_manager.sync_timer.isActive())
        self.assertFalse(self.sync_manager.auto_sync_enabled)
    
    def test_sync_updates_no_pending(self):
        """测试没有待更新数据时的同步"""
        with patch.object(self.db_manager, 'get_pending_status_updates', return_value=[]):
            self.sync_manager.sync_updates()
            
        # 应该没有调用全景图更新方法
        self.mock_panorama_widget.batch_update_hole_status.assert_not_called()
    
    def test_sync_updates_with_data(self):
        """测试有数据时的同步"""
        # 创建状态更新记录
        self.db_manager.update_hole_status("H001", "qualified", "test")
        self.db_manager.update_hole_status("H002", "defective", "test")
        
        # 模拟全景图组件的方法
        self.mock_panorama_widget.batch_update_hole_status = Mock()
        
        # 执行同步
        self.sync_manager.sync_updates()
        
        # 验证调用了全景图更新
        self.mock_panorama_widget.batch_update_hole_status.assert_called_once()
        
        # 验证状态被标记为已同步
        pending_updates = self.db_manager.get_pending_status_updates()
        self.assertEqual(len(pending_updates), 0)
    
    def test_update_panorama_widget(self):
        """测试更新全景图组件"""
        updates = [
            {
                'id': 1,
                'hole_id': 'H001',
                'new_status': 'qualified',
                'update_timestamp': datetime.now()
            },
            {
                'id': 2,
                'hole_id': 'H002',
                'new_status': 'defective',
                'update_timestamp': datetime.now()
            }
        ]
        
        # 模拟全景图组件有batch_update_hole_status方法
        self.mock_panorama_widget.batch_update_hole_status = Mock()
        
        success_count = self.sync_manager._update_panorama_widget(updates)
        
        self.assertEqual(success_count, 2)
        self.mock_panorama_widget.batch_update_hole_status.assert_called_once()
        
        # 验证调用参数
        call_args = self.mock_panorama_widget.batch_update_hole_status.call_args[0][0]
        self.assertEqual(call_args['H001'], HoleStatus.QUALIFIED)
        self.assertEqual(call_args['H002'], HoleStatus.DEFECTIVE)
    
    def test_update_panorama_widget_fallback(self):
        """测试全景图组件回退方法"""
        updates = [
            {
                'id': 1,
                'hole_id': 'H001',
                'new_status': 'qualified',
                'update_timestamp': datetime.now()
            }
        ]
        
        # 模拟全景图组件只有update_hole_status方法
        self.mock_panorama_widget.batch_update_hole_status = None
        self.mock_panorama_widget.update_hole_status = Mock()
        
        success_count = self.sync_manager._update_panorama_widget(updates)
        
        self.assertEqual(success_count, 1)
        self.mock_panorama_widget.update_hole_status.assert_called_once_with('H001', HoleStatus.QUALIFIED)
    
    def test_force_sync(self):
        """测试强制同步"""
        with patch.object(self.sync_manager, 'sync_updates') as mock_sync:
            self.sync_manager.force_sync()
            mock_sync.assert_called_once()
    
    def test_set_panorama_widget(self):
        """测试设置全景图组件"""
        new_widget = Mock()
        self.sync_manager.set_panorama_widget(new_widget)
        self.assertEqual(self.sync_manager.panorama_widget, new_widget)
    
    def test_get_sync_stats(self):
        """测试获取同步统计信息"""
        stats = self.sync_manager.get_sync_stats()
        
        self.assertIn('auto_sync_enabled', stats)
        self.assertIn('sync_interval', stats)
        self.assertIn('total_synced', stats)
        self.assertIn('sync_errors', stats)
        self.assertIn('db_stats', stats)
    
    def test_unknown_status_handling(self):
        """测试未知状态处理"""
        updates = [
            {
                'id': 1,
                'hole_id': 'H001',
                'new_status': 'unknown_status',
                'update_timestamp': datetime.now()
            }
        ]
        
        self.mock_panorama_widget.batch_update_hole_status = Mock()
        
        success_count = self.sync_manager._update_panorama_widget(updates)
        
        # 未知状态应该被跳过
        self.assertEqual(success_count, 0)
        # 仍应调用批量更新方法，但参数为空
        self.mock_panorama_widget.batch_update_hole_status.assert_called_once_with({})


class TestStatusUpdateBuffer(unittest.TestCase):
    """测试StatusUpdateBuffer类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # 创建数据库管理器
        self.db_manager = DatabaseManager(f"sqlite:///{self.temp_db.name}")
        self.db_manager.create_tables()
        
        # 创建缓冲区
        self.buffer = StatusUpdateBuffer(self.db_manager, buffer_size=3, flush_interval=1.0)
    
    def tearDown(self):
        """测试后清理"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.buffer.buffer_size, 3)
        self.assertEqual(self.buffer.flush_interval, 1.0)
        self.assertEqual(len(self.buffer.buffer), 0)
    
    def test_add_update_no_flush(self):
        """测试添加更新但未达到刷新条件"""
        self.buffer.add_update("H001", "qualified", "test")
        self.assertEqual(len(self.buffer.buffer), 1)
        
        # 验证更新内容
        update = self.buffer.buffer[0]
        self.assertEqual(update['hole_id'], "H001")
        self.assertEqual(update['new_status'], "qualified")
        self.assertEqual(update['update_source'], "test")
    
    def test_add_update_with_buffer_size_flush(self):
        """测试缓冲区大小触发刷新"""
        with patch.object(self.buffer, 'flush') as mock_flush:
            # 添加足够的更新触发刷新
            for i in range(3):
                self.buffer.add_update(f"H{i+1:03d}", "qualified", "test")
            
            mock_flush.assert_called_once()
    
    def test_add_update_with_time_flush(self):
        """测试时间间隔触发刷新"""
        with patch.object(self.buffer, 'flush') as mock_flush:
            # 模拟时间过去
            self.buffer.last_flush_time = time.time() - 2.0  # 2秒前
            
            self.buffer.add_update("H001", "qualified", "test")
            
            mock_flush.assert_called_once()
    
    def test_flush_empty_buffer(self):
        """测试刷新空缓冲区"""
        with patch.object(self.db_manager, 'update_hole_status') as mock_update:
            self.buffer.flush()
            mock_update.assert_not_called()
    
    def test_flush_with_data(self):
        """测试刷新有数据的缓冲区"""
        # 添加测试数据
        self.buffer.add_update("H001", "qualified", "test", "operator1", "batch1")
        self.buffer.add_update("H002", "defective", "test", "operator2", "batch2")
        
        # 防止自动刷新
        original_flush = self.buffer.flush
        self.buffer.flush = Mock()
        
        # 手动调用原始flush方法
        with patch.object(self.db_manager, 'update_hole_status') as mock_update:
            original_flush()
            
            # 验证调用了正确的次数
            self.assertEqual(mock_update.call_count, 2)
            
            # 验证调用参数
            calls = mock_update.call_args_list
            self.assertEqual(calls[0][1]['hole_id'], "H001")
            self.assertEqual(calls[0][1]['new_status'], "qualified")
            self.assertEqual(calls[1][1]['hole_id'], "H002")
            self.assertEqual(calls[1][1]['new_status'], "defective")
        
        # 验证缓冲区被清空
        self.assertEqual(len(self.buffer.buffer), 0)


class TestDatabaseManager(unittest.TestCase):
    """测试DatabaseManager的状态更新相关方法"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # 创建数据库管理器
        self.db_manager = DatabaseManager(f"sqlite:///{self.temp_db.name}")
        self.db_manager.create_tables()
        
        # 创建测试数据
        self._create_test_data()
    
    def tearDown(self):
        """测试后清理"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def _create_test_data(self):
        """创建测试数据"""
        session = self.db_manager.get_session()
        try:
            # 创建工件
            workpiece = Workpiece(
                workpiece_id="TEST-001",
                name="测试工件",
                type="test"
            )
            session.add(workpiece)
            session.flush()
            
            # 创建孔位
            hole = Hole(
                hole_id="H001",
                workpiece_id=workpiece.id,
                position_x=0.0,
                position_y=0.0,
                target_diameter=25.0,
                tolerance=0.1,
                status='pending'
            )
            session.add(hole)
            session.commit()
            
            self.test_hole_id = "H001"
            
        finally:
            self.db_manager.close_session(session)
    
    def test_update_hole_status(self):
        """测试更新孔位状态"""
        result = self.db_manager.update_hole_status(
            "H001", "qualified", "test", "operator1", "batch1"
        )
        
        self.assertTrue(result)
        
        # 验证状态更新记录
        pending_updates = self.db_manager.get_pending_status_updates()
        self.assertEqual(len(pending_updates), 1)
        
        update = pending_updates[0]
        self.assertEqual(update['hole_id'], "H001")
        self.assertEqual(update['new_status'], "qualified")
        self.assertEqual(update['update_source'], "test")
    
    def test_update_nonexistent_hole(self):
        """测试更新不存在的孔位"""
        result = self.db_manager.update_hole_status("NONEXISTENT", "qualified")
        self.assertFalse(result)
    
    def test_get_pending_status_updates(self):
        """测试获取待同步状态更新"""
        # 添加几个状态更新
        self.db_manager.update_hole_status("H001", "qualified", "test1")
        self.db_manager.update_hole_status("H001", "defective", "test2")
        
        pending_updates = self.db_manager.get_pending_status_updates()
        
        self.assertEqual(len(pending_updates), 2)
        self.assertEqual(pending_updates[0]['new_status'], "qualified")
        self.assertEqual(pending_updates[1]['new_status'], "defective")
    
    def test_mark_status_updates_synced(self):
        """测试标记状态更新为已同步"""
        # 添加状态更新
        self.db_manager.update_hole_status("H001", "qualified", "test")
        
        # 获取更新ID
        pending_updates = self.db_manager.get_pending_status_updates()
        update_ids = [update['id'] for update in pending_updates]
        
        # 标记为已同步
        result = self.db_manager.mark_status_updates_synced(update_ids)
        self.assertTrue(result)
        
        # 验证没有待同步的更新了
        pending_updates = self.db_manager.get_pending_status_updates()
        self.assertEqual(len(pending_updates), 0)
    
    def test_get_status_update_stats(self):
        """测试获取状态更新统计信息"""
        # 添加一些状态更新
        self.db_manager.update_hole_status("H001", "qualified", "test1")
        self.db_manager.update_hole_status("H001", "defective", "test2")
        
        # 标记一个为已同步
        pending_updates = self.db_manager.get_pending_status_updates()
        self.db_manager.mark_status_updates_synced([pending_updates[0]['id']])
        
        # 获取统计信息
        stats = self.db_manager.get_status_update_stats()
        
        self.assertEqual(stats['total_updates'], 2)
        self.assertEqual(stats['pending_updates'], 1)
        self.assertEqual(stats['synced_updates'], 1)
        self.assertEqual(stats['sync_rate'], 50.0)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)