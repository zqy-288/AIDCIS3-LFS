"""
系统测试：全景图同步系统端到端测试
测试完整的数据库驱动全景图更新系统，包括实际的UI组件和数据持久化
"""

import unittest
import sys
import os
import tempfile
import time
import threading
from datetime import datetime
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from aidcis2.data_management.panorama_sync_manager import PanoramaSyncManager, StatusUpdateBuffer
from aidcis2.models.hole_data import HoleStatus
from modules.models import DatabaseManager, HoleStatusUpdate, Hole, Workpiece


class TestPanoramaSyncSystem(unittest.TestCase):
    """全景图同步系统测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # 创建数据库管理器
        self.db_manager = DatabaseManager(f"sqlite:///{self.temp_db.name}")
        self.db_manager.create_tables()
        
        # 创建模拟全景图组件系统
        self.panorama_system = PanoramaSystemMock()
        
        # 创建同步管理器
        self.sync_manager = PanoramaSyncManager(self.db_manager, self.panorama_system)
        
        # 创建状态缓冲区
        self.status_buffer = StatusUpdateBuffer(self.db_manager, buffer_size=10, flush_interval=0.5)
        
        # 创建完整的测试数据集
        self._create_complete_test_dataset()
        
        print(f"\\n=== 系统测试环境初始化完成 ===")
        print(f"数据库: {self.temp_db.name}")
        print(f"工件数: {len(self.test_workpieces)}")
        print(f"孔位数: {sum(len(holes) for holes in self.test_holes.values())}")
    
    def tearDown(self):
        """测试后清理"""
        self.sync_manager.stop_sync()
        self.status_buffer.flush()  # 确保数据被保存
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def _create_complete_test_dataset(self):
        """创建完整的测试数据集"""
        session = self.db_manager.get_session()
        try:
            self.test_workpieces = []
            self.test_holes = {}
            
            # 创建3个不同类型的工件
            workpiece_configs = [
                ("TUBE-PLATE-001", "管板工件A", "tube_plate", 50),
                ("HEAT-EXCHANGER-001", "换热器工件B", "heat_exchanger", 75),
                ("PRESSURE-VESSEL-001", "压力容器工件C", "pressure_vessel", 100)
            ]
            
            for wp_id, name, wp_type, hole_count in workpiece_configs:
                # 创建工件
                workpiece = Workpiece(
                    workpiece_id=wp_id,
                    name=name,
                    type=wp_type,
                    hole_count=hole_count,
                    status='active'
                )
                session.add(workpiece)
                session.flush()
                self.test_workpieces.append(workpiece)
                
                # 创建孔位
                holes = []
                for i in range(hole_count):
                    hole = Hole(
                        hole_id=f"{wp_id}-H{i+1:03d}",
                        workpiece_id=workpiece.id,
                        position_x=(i % 10) * 20.0,
                        position_y=(i // 10) * 20.0,
                        target_diameter=25.0 + (i % 5) * 2.0,  # 变化直径
                        tolerance=0.1 + (i % 3) * 0.05,        # 变化公差
                        status='pending'
                    )
                    holes.append(hole)
                    session.add(hole)
                
                self.test_holes[wp_id] = holes
            
            session.commit()
            
        finally:
            self.db_manager.close_session(session)
    
    def test_complete_detection_workflow(self):
        """测试完整的检测工作流程"""
        print("\\n=== 测试完整检测工作流程 ===")
        
        # 模拟检测系统开始工作
        print("1. 模拟检测系统开始工作...")
        self.sync_manager.start_sync(200)  # 200ms同步间隔
        
        # 模拟检测过程：依次检测每个工件的孔位
        detection_results = []
        
        for workpiece in self.test_workpieces:
            wp_id = workpiece.workpiece_id
            holes = self.test_holes[wp_id]
            
            print(f"2. 开始检测工件: {wp_id} ({len(holes)} 个孔位)")
            
            # 模拟随机检测结果
            import random
            random.seed(42)  # 固定种子确保可重复性
            
            for i, hole in enumerate(holes[:10]):  # 只检测前10个孔位
                # 模拟检测延迟
                time.sleep(0.01)
                
                # 随机生成检测结果
                statuses = ['qualified', 'defective', 'blind', 'processing']
                weights = [0.7, 0.2, 0.05, 0.05]  # 大部分合格
                status = random.choices(statuses, weights=weights)[0]
                
                # 更新状态到数据库
                success = self.db_manager.update_hole_status(
                    hole.hole_id, status, "automated_detection", 
                    operator_id="system", batch_id=f"batch_{workpiece.id}"
                )
                
                if success:
                    detection_results.append((hole.hole_id, status))
                    
                    # 每5个孔位打印一次进度
                    if (i + 1) % 5 == 0:
                        print(f"   已检测 {i+1}/{min(10, len(holes))} 个孔位")
        
        print(f"3. 检测完成，总计 {len(detection_results)} 个结果")
        
        # 等待同步完成（最多5秒）
        print("4. 等待同步完成...")
        start_wait = time.time()
        while time.time() - start_wait < 5.0:
            pending = self.db_manager.get_pending_status_updates()
            if len(pending) == 0:
                break
            time.sleep(0.1)
        
        # 验证同步结果
        final_pending = self.db_manager.get_pending_status_updates()
        self.assertEqual(len(final_pending), 0, f"仍有 {len(final_pending)} 个未同步更新")
        
        # 验证全景图系统收到了所有更新
        total_updates = self.panorama_system.get_total_updates()
        self.assertEqual(total_updates, len(detection_results), 
                        f"全景图更新数 ({total_updates}) 与检测结果数 ({len(detection_results)}) 不匹配")
        
        print(f"5. 系统验证完成:")
        print(f"   - 检测结果: {len(detection_results)}")
        print(f"   - 全景图更新: {total_updates}")
        print(f"   - 同步率: {100.0}%")
        
        # 停止同步
        self.sync_manager.stop_sync()
    
    def test_high_frequency_updates(self):
        """测试高频率更新场景"""
        print("\\n=== 测试高频率更新场景 ===")
        
        # 启动快速同步
        self.sync_manager.start_sync(50)  # 50ms超快同步
        print("1. 启动高频同步模式 (50ms间隔)")
        
        # 快速连续更新（模拟实时检测）
        print("2. 模拟高频实时检测...")
        start_time = time.time()
        update_count = 0
        
        # 对第一个工件的所有孔位进行快速更新
        first_workpiece = self.test_workpieces[0]
        holes = self.test_holes[first_workpiece.workpiece_id]
        
        for hole in holes:
            # 快速连续更新状态
            statuses = ['processing', 'qualified', 'defective']
            for status in statuses:
                self.db_manager.update_hole_status(
                    hole.hole_id, status, "high_freq_test", 
                    batch_id=f"high_freq_{int(time.time()*1000)}"
                )
                update_count += 1
                time.sleep(0.001)  # 1ms间隔，非常快
        
        update_time = time.time() - start_time
        print(f"3. 完成 {update_count} 个快速更新，耗时 {update_time:.3f}秒")
        print(f"   更新频率: {update_count/update_time:.0f} 更新/秒")
        
        # 等待所有更新被同步
        print("4. 等待高频更新同步...")
        max_wait = 10.0  # 最多等待10秒
        start_wait = time.time()
        
        while time.time() - start_wait < max_wait:
            pending = self.db_manager.get_pending_status_updates()
            if len(pending) == 0:
                break
            time.sleep(0.05)
        
        # 验证结果
        remaining_pending = self.db_manager.get_pending_status_updates()
        sync_time = time.time() - start_wait
        
        print(f"5. 高频同步结果:")
        print(f"   - 同步耗时: {sync_time:.3f}秒")
        print(f"   - 剩余未同步: {len(remaining_pending)}")
        print(f"   - 全景图总更新数: {self.panorama_system.get_total_updates()}")
        
        # 性能断言
        self.assertEqual(len(remaining_pending), 0, "高频更新同步不完整")
        self.assertLess(sync_time, 5.0, "高频同步耗时过长")
        
        self.sync_manager.stop_sync()
    
    def test_system_reliability_under_stress(self):
        """测试系统压力下的可靠性"""
        print("\\n=== 测试系统压力可靠性 ===")
        
        # 创建多线程更新场景
        print("1. 创建多线程压力测试环境...")
        
        self.sync_manager.start_sync(100)  # 100ms同步间隔
        
        # 压力测试参数
        num_threads = 3
        updates_per_thread = 50
        total_expected_updates = num_threads * updates_per_thread
        
        # 线程同步对象
        thread_results = []
        thread_exceptions = []
        
        def stress_test_worker(thread_id, start_hole_index):
            """压力测试工作线程"""
            try:
                worker_updates = []
                workpiece = self.test_workpieces[thread_id % len(self.test_workpieces)]
                holes = self.test_holes[workpiece.workpiece_id]
                
                for i in range(updates_per_thread):
                    hole_index = (start_hole_index + i) % len(holes)
                    hole = holes[hole_index]
                    
                    # 随机状态和延迟
                    import random
                    status = random.choice(['qualified', 'defective', 'processing'])
                    
                    success = self.db_manager.update_hole_status(
                        hole.hole_id, status, f"stress_test_t{thread_id}",
                        operator_id=f"thread_{thread_id}",
                        batch_id=f"stress_batch_{thread_id}_{i}"
                    )
                    
                    if success:
                        worker_updates.append((hole.hole_id, status))
                    
                    # 随机短延迟
                    time.sleep(random.uniform(0.001, 0.01))
                
                thread_results.append((thread_id, worker_updates))
                
            except Exception as e:
                thread_exceptions.append((thread_id, e))
        
        # 启动压力测试线程
        print(f"2. 启动 {num_threads} 个并发测试线程...")
        threads = []
        
        for i in range(num_threads):
            thread = threading.Thread(
                target=stress_test_worker, 
                args=(i, i * 20)  # 每个线程从不同孔位开始
            )
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        print("3. 所有压力测试线程完成")
        
        # 检查线程异常
        if thread_exceptions:
            print(f"❌ 发现线程异常: {thread_exceptions}")
            self.fail(f"压力测试中发生异常: {thread_exceptions}")
        
        # 统计结果
        total_thread_updates = sum(len(results[1]) for results in thread_results)
        print(f"4. 线程更新统计: {total_thread_updates}/{total_expected_updates}")
        
        # 等待同步完成
        print("5. 等待压力测试同步完成...")
        max_wait = 15.0
        start_wait = time.time()
        
        while time.time() - start_wait < max_wait:
            pending = self.db_manager.get_pending_status_updates()
            if len(pending) == 0:
                break
            time.sleep(0.1)
        
        # 最终验证
        final_pending = self.db_manager.get_pending_status_updates()
        sync_stats = self.db_manager.get_status_update_stats()
        panorama_updates = self.panorama_system.get_total_updates()
        
        print("6. 压力测试结果:")
        print(f"   - 预期更新数: {total_expected_updates}")
        print(f"   - 线程完成数: {total_thread_updates}")
        print(f"   - 数据库总更新: {sync_stats.get('total_updates', 0)}")
        print(f"   - 剩余未同步: {len(final_pending)}")
        print(f"   - 全景图更新数: {panorama_updates}")
        print(f"   - 同步率: {sync_stats.get('sync_rate', 0):.1f}%")
        
        # 可靠性断言
        self.assertEqual(len(thread_exceptions), 0, "压力测试中发生异常")
        self.assertEqual(len(final_pending), 0, "压力测试后仍有未同步更新")
        self.assertGreaterEqual(sync_stats.get('sync_rate', 0), 99.0, "同步率过低")
        
        self.sync_manager.stop_sync()
    
    def test_data_persistence_and_recovery(self):
        """测试数据持久化和恢复"""
        print("\\n=== 测试数据持久化和恢复 ===")
        
        # 第一阶段：创建数据并部分同步
        print("1. 第一阶段：创建数据...")
        workpiece = self.test_workpieces[0]
        holes = self.test_holes[workpiece.workpiece_id][:20]  # 使用前20个孔位
        
        # 添加多个状态更新
        phase1_updates = []
        for i, hole in enumerate(holes):
            status = 'qualified' if i % 2 == 0 else 'defective'
            success = self.db_manager.update_hole_status(
                hole.hole_id, status, "persistence_test_p1",
                batch_id="persistence_batch_1"
            )
            if success:
                phase1_updates.append((hole.hole_id, status))
        
        print(f"   添加了 {len(phase1_updates)} 个状态更新")
        
        # 部分同步（模拟系统中断前的状态）
        pending_updates = self.db_manager.get_pending_status_updates(limit=10)
        if pending_updates:
            update_ids = [update['id'] for update in pending_updates[:5]]  # 只同步前5个
            self.db_manager.mark_status_updates_synced(update_ids)
            print(f"   部分同步了 {len(update_ids)} 个更新")
        
        # 检查持久化状态
        remaining_pending = self.db_manager.get_pending_status_updates()
        initial_stats = self.db_manager.get_status_update_stats()
        
        print("2. 第一阶段状态:")
        print(f"   - 总更新数: {initial_stats['total_updates']}")
        print(f"   - 待同步数: {initial_stats['pending_updates']}")
        print(f"   - 已同步数: {initial_stats['synced_updates']}")
        
        # 第二阶段：模拟系统重启和恢复
        print("3. 第二阶段：模拟系统重启...")
        
        # 创建新的同步管理器（模拟重启）
        recovery_panorama = PanoramaSystemMock()
        recovery_sync_manager = PanoramaSyncManager(self.db_manager, recovery_panorama)
        
        print("4. 恢复后验证数据完整性...")
        
        # 验证数据仍然存在
        recovery_stats = self.db_manager.get_status_update_stats()
        self.assertEqual(recovery_stats['total_updates'], initial_stats['total_updates'],
                        "重启后总更新数丢失")
        self.assertEqual(recovery_stats['pending_updates'], initial_stats['pending_updates'],
                        "重启后待同步数不一致")
        
        print("5. 执行恢复同步...")
        
        # 启动恢复同步
        recovery_sync_manager.start_sync(100)
        
        # 等待恢复同步完成
        start_recovery = time.time()
        while time.time() - start_recovery < 5.0:
            pending = self.db_manager.get_pending_status_updates()
            if len(pending) == 0:
                break
            time.sleep(0.1)
        
        # 验证恢复结果
        final_stats = self.db_manager.get_status_update_stats()
        recovery_panorama_updates = recovery_panorama.get_total_updates()
        
        print("6. 恢复验证结果:")
        print(f"   - 恢复前待同步: {initial_stats['pending_updates']}")
        print(f"   - 恢复后待同步: {final_stats['pending_updates']}")
        print(f"   - 恢复期间全景图更新: {recovery_panorama_updates}")
        print(f"   - 最终同步率: {final_stats['sync_rate']:.1f}%")
        
        # 持久化断言
        self.assertEqual(final_stats['pending_updates'], 0, "恢复后仍有待同步更新")
        self.assertEqual(final_stats['sync_rate'], 100.0, "恢复后同步率不完整")
        self.assertGreater(recovery_panorama_updates, 0, "恢复期间无全景图更新")
        
        recovery_sync_manager.stop_sync()
        
        # 第三阶段：添加新数据验证正常运行
        print("7. 第三阶段：验证恢复后正常运行...")
        
        # 添加新的更新
        new_updates = []
        for hole in holes[10:15]:  # 使用不同的孔位
            success = self.db_manager.update_hole_status(
                hole.hole_id, "processing", "persistence_test_p3",
                batch_id="persistence_batch_3"
            )
            if success:
                new_updates.append(hole.hole_id)
        
        recovery_sync_manager.start_sync(100)
        
        # 等待新数据同步
        start_new = time.time()
        while time.time() - start_new < 3.0:
            pending = self.db_manager.get_pending_status_updates()
            if len(pending) == 0:
                break
            time.sleep(0.1)
        
        # 最终验证
        final_pending = self.db_manager.get_pending_status_updates()
        total_panorama_updates = recovery_panorama.get_total_updates()
        
        print("8. 最终验证:")
        print(f"   - 新增更新数: {len(new_updates)}")
        print(f"   - 最终待同步: {len(final_pending)}")
        print(f"   - 总全景图更新: {total_panorama_updates}")
        
        self.assertEqual(len(final_pending), 0, "新数据同步不完整")
        self.assertGreaterEqual(total_panorama_updates, len(new_updates), "新数据全景图更新不足")
        
        recovery_sync_manager.stop_sync()


class PanoramaSystemMock:
    """模拟完整的全景图系统"""
    
    def __init__(self):
        self.update_history = []
        self.batch_calls = 0
        self.error_count = 0
        self.last_update_time = None
        
    def batch_update_hole_status(self, status_updates):
        """模拟批量更新孔位状态"""
        try:
            self.batch_calls += 1
            current_time = datetime.now()
            
            batch_record = {
                'timestamp': current_time,
                'batch_id': self.batch_calls,
                'updates': dict(status_updates),
                'count': len(status_updates)
            }
            
            self.update_history.append(batch_record)
            self.last_update_time = current_time
            
            # 模拟一些处理时间
            time.sleep(0.001)
            
            print(f"   [全景图系统] 批次 #{self.batch_calls}: 更新 {len(status_updates)} 个孔位")
            
        except Exception as e:
            self.error_count += 1
            print(f"   [全景图系统] 错误: {e}")
            raise
    
    def get_total_updates(self):
        """获取总更新数"""
        return sum(record['count'] for record in self.update_history)
    
    def get_batch_count(self):
        """获取批次数"""
        return self.batch_calls
    
    def get_error_count(self):
        """获取错误数"""
        return self.error_count
    
    def get_last_update_time(self):
        """获取最后更新时间"""
        return self.last_update_time
    
    def get_update_statistics(self):
        """获取更新统计信息"""
        if not self.update_history:
            return {}
        
        total_updates = self.get_total_updates()
        avg_batch_size = total_updates / len(self.update_history) if self.update_history else 0
        
        time_spans = []
        for i in range(1, len(self.update_history)):
            span = (self.update_history[i]['timestamp'] - 
                   self.update_history[i-1]['timestamp']).total_seconds()
            time_spans.append(span)
        
        avg_interval = sum(time_spans) / len(time_spans) if time_spans else 0
        
        return {
            'total_updates': total_updates,
            'batch_count': self.batch_calls,
            'avg_batch_size': avg_batch_size,
            'avg_interval_seconds': avg_interval,
            'error_count': self.error_count,
            'last_update': self.last_update_time
        }


if __name__ == '__main__':
    # 运行系统测试
    unittest.main(verbosity=2)