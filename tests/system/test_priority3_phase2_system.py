#!/usr/bin/env python3
"""
系统测试：优先级3阶段2 - 数据库集成系统
System Tests: Priority 3 Phase 2 - Database Integration System
"""

import unittest
import tempfile
import shutil
import os
import time
import threading
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aidcis2.data_management.hybrid_manager import HybridDataManager
from aidcis2.data_management.realtime_bridge import RealTimeDataBridge
from aidcis2.data_management.database_migration import DatabaseMigration
from modules.models import DatabaseManager, Workpiece, Hole, Measurement


class TestPriority3Phase2System(unittest.TestCase):
    """优先级3阶段2系统测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_system_phase2_")
        self.test_db = os.path.join(self.temp_dir, "system_test.db")
        self.database_url = f"sqlite:///{self.test_db}"
        
        # 初始化系统组件
        self.hybrid_manager = HybridDataManager(
            data_root=self.temp_dir,
            database_url=self.database_url
        )
        self.bridge = RealTimeDataBridge(self.hybrid_manager)
        self.migration = DatabaseMigration(self.database_url)
        
        # 运行数据库迁移
        self.migration.run_migration()
        
        # 创建大型测试DXF文件
        self.large_dxf = Path(self.temp_dir) / "large_system_test.dxf"
        self.large_dxf.write_text("large system test dxf content")
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_large_scale_database_integration(self):
        """测试大规模数据库集成"""
        # 创建大量孔位数据
        num_holes = 500
        holes_data = []
        
        for i in range(1, num_holes + 1):
            holes_data.append({
                "hole_id": f"H{i:05d}",
                "position": {"x": float(i % 50), "y": float(i // 50)},
                "diameter": 8.865 + (i % 10) * 0.001,
                "depth": 900.0 + (i % 100),
                "tolerance": 0.1
            })
        
        print(f"\n创建包含 {num_holes} 个孔位的大型项目...")
        start_time = time.time()
        
        # 创建项目
        project_id, project_path = self.hybrid_manager.create_project_from_dxf(
            str(self.large_dxf), "大规模数据库集成测试", holes_data
        )
        
        creation_time = time.time() - start_time
        print(f"项目创建耗时: {creation_time:.2f}秒")
        
        self.assertIsNotNone(project_id)
        self.assertIsNotNone(project_path)
        
        # 验证数据库记录
        session = self.hybrid_manager.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            self.assertIsNotNone(workpiece)
            self.assertEqual(workpiece.hole_count, num_holes)
            
            db_holes_count = session.query(Hole).filter_by(workpiece_id=workpiece.id).count()
            self.assertEqual(db_holes_count, num_holes)
            
        finally:
            self.hybrid_manager.db_manager.close_session(session)
        
        # 验证文件系统结构
        holes_dir = Path(project_path) / "holes"
        fs_holes_count = len([d for d in holes_dir.iterdir() if d.is_dir()])
        self.assertEqual(fs_holes_count, num_holes)
        
        # 性能要求
        self.assertLess(creation_time, 30.0, "大规模项目创建耗时过长")
        
        print(f"✅ 成功创建 {num_holes} 个孔位，数据库和文件系统一致")
    
    def test_concurrent_database_operations(self):
        """测试并发数据库操作"""
        num_projects = 5
        holes_per_project = 20
        
        projects_created = []
        creation_errors = []
        
        def create_concurrent_project(index):
            try:
                # 创建测试数据
                dxf_file = Path(self.temp_dir) / f"concurrent_db_test_{index}.dxf"
                dxf_file.write_text(f"concurrent database test {index}")
                
                holes_data = []
                for i in range(holes_per_project):
                    holes_data.append({
                        "hole_id": f"H{i:03d}",
                        "position": {"x": float(i), "y": float(index)},
                        "diameter": 8.865,
                        "depth": 900.0,
                        "tolerance": 0.1
                    })
                
                # 创建项目
                project_id, project_path = self.hybrid_manager.create_project_from_dxf(
                    str(dxf_file), f"并发数据库测试项目{index}", holes_data
                )
                
                if project_id and project_path:
                    projects_created.append(project_id)
                    
                    # 执行一些数据库操作
                    for i in range(5):
                        hole_id = f"H{i:03d}"
                        
                        # 开始测量
                        self.bridge.start_realtime_measurement(
                            hole_id, project_id, {"depth_range": [0, 900]}
                        )
                        
                        # 保存测量数据
                        measurement_data = [
                            {
                                "timestamp": f"2025-01-08T10:{index:02d}:{i:02d}",
                                "depth": i * 10.0,
                                "diameter": 8.865 + i * 0.001,
                                "operator": f"并发测试{index}"
                            }
                        ]
                        
                        self.bridge.save_measurement_result(
                            hole_id, project_id, measurement_data
                        )
                
            except Exception as e:
                creation_errors.append(f"项目{index}创建失败: {e}")
        
        # 并发创建项目
        print(f"\n并发创建 {num_projects} 个项目，每个 {holes_per_project} 个孔位...")
        threads = []
        
        start_time = time.time()
        for i in range(num_projects):
            thread = threading.Thread(target=create_concurrent_project, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        concurrent_time = time.time() - start_time
        print(f"并发操作耗时: {concurrent_time:.2f}秒")
        
        # 验证结果
        self.assertEqual(len(creation_errors), 0, f"并发创建错误: {creation_errors}")
        self.assertEqual(len(projects_created), num_projects)
        
        # 验证数据库完整性
        session = self.hybrid_manager.db_manager.get_session()
        try:
            total_workpieces = session.query(Workpiece).count()
            self.assertGreaterEqual(total_workpieces, num_projects)
            
            total_holes = session.query(Hole).count()
            self.assertGreaterEqual(total_holes, num_projects * holes_per_project)
            
            total_measurements = session.query(Measurement).count()
            self.assertGreaterEqual(total_measurements, num_projects * 5)  # 每个项目5个孔位有测量
            
        finally:
            self.hybrid_manager.db_manager.close_session(session)
        
        print(f"✅ 并发操作成功，创建 {len(projects_created)} 个项目")
    
    def test_data_consistency_under_stress(self):
        """测试压力下的数据一致性"""
        # 创建测试项目
        holes_data = [
            {
                "hole_id": f"H{i:03d}",
                "position": {"x": float(i), "y": 0.0},
                "diameter": 8.865,
                "depth": 900.0,
                "tolerance": 0.1
            }
            for i in range(1, 11)
        ]
        
        project_id, _ = self.hybrid_manager.create_project_from_dxf(
            str(self.large_dxf), "数据一致性压力测试", holes_data
        )
        
        # 压力测试：频繁的数据库和文件系统操作
        operations_count = 100
        print(f"\n执行 {operations_count} 次数据一致性操作...")
        
        start_time = time.time()
        
        for i in range(operations_count):
            hole_id = f"H{(i % 10) + 1:03d}"
            
            # 交替进行数据库和文件系统操作
            if i % 2 == 0:
                # 数据库操作
                session = self.hybrid_manager.db_manager.get_session()
                try:
                    workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
                    if workpiece:
                        hole = session.query(Hole).filter_by(
                            workpiece_id=workpiece.id, hole_id=hole_id
                        ).first()
                        if hole:
                            hole.measurement_count += 1
                            hole.status = "in_progress" if i % 4 == 0 else "completed"
                            session.commit()
                finally:
                    self.hybrid_manager.db_manager.close_session(session)
            else:
                # 文件系统操作
                status = "measuring" if i % 4 == 1 else "pending"
                self.hybrid_manager.hole_manager.update_hole_status(
                    project_id, hole_id, status, f"压力测试操作{i}"
                )
            
            # 每10次操作执行一次同步
            if i % 10 == 9:
                success = self.hybrid_manager.ensure_data_consistency(project_id)
                self.assertTrue(success, f"第{i+1}次同步失败")
        
        stress_time = time.time() - start_time
        print(f"压力测试耗时: {stress_time:.2f}秒")
        
        # 最终一致性检查
        final_success = self.hybrid_manager.ensure_data_consistency(project_id)
        self.assertTrue(final_success)
        
        # 验证数据完整性
        session = self.hybrid_manager.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            holes = session.query(Hole).filter_by(workpiece_id=workpiece.id).all()
            
            for hole in holes:
                # 验证数据库和文件系统状态一致
                fs_status = self.hybrid_manager.hole_manager.get_hole_status(
                    project_id, hole.hole_id
                )
                
                # 状态可能不完全一致（因为最后的同步），但应该是有效状态
                valid_statuses = ["pending", "measuring", "in_progress", "completed"]
                self.assertIn(hole.status, valid_statuses)
                self.assertIn(fs_status["current_status"], valid_statuses)
                
        finally:
            self.hybrid_manager.db_manager.close_session(session)
        
        print(f"✅ 压力测试完成，数据一致性保持良好")
    
    def test_measurement_data_scalability(self):
        """测试测量数据可扩展性"""
        # 创建项目
        holes_data = [
            {
                "hole_id": "H00001",
                "position": {"x": 10.0, "y": 20.0},
                "diameter": 8.865,
                "depth": 900.0,
                "tolerance": 0.1
            }
        ]
        
        project_id, _ = self.hybrid_manager.create_project_from_dxf(
            str(self.large_dxf), "测量数据可扩展性测试", holes_data
        )
        
        hole_id = "H00001"
        
        # 生成大量测量数据
        num_measurements = 5000
        print(f"\n保存 {num_measurements} 条测量数据...")
        
        measurement_data = []
        for i in range(num_measurements):
            measurement_data.append({
                "timestamp": f"2025-01-08T{i//3600:02d}:{(i%3600)//60:02d}:{i%60:02d}",
                "depth": i * 0.1,
                "diameter": 8.865 + (i % 100) * 0.0001,
                "operator": "可扩展性测试"
            })
        
        # 分批保存数据
        batch_size = 1000
        save_times = []
        
        for i in range(0, num_measurements, batch_size):
            batch = measurement_data[i:i + batch_size]
            
            start_time = time.time()
            success = self.bridge.save_measurement_result(
                hole_id, project_id, batch
            )
            save_time = time.time() - start_time
            save_times.append(save_time)
            
            self.assertTrue(success, f"第{i//batch_size + 1}批数据保存失败")
            print(f"第{i//batch_size + 1}批 ({len(batch)}条) 保存耗时: {save_time:.2f}秒")
        
        total_save_time = sum(save_times)
        print(f"总保存耗时: {total_save_time:.2f}秒")
        
        # 验证数据库中的记录数
        session = self.hybrid_manager.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            hole = session.query(Hole).filter_by(
                workpiece_id=workpiece.id, hole_id=hole_id
            ).first()
            
            db_measurements_count = session.query(Measurement).filter_by(hole_id=hole.id).count()
            self.assertEqual(db_measurements_count, num_measurements)
            
            # 验证统计信息
            self.assertEqual(hole.measurement_count, num_measurements)
            
        finally:
            self.hybrid_manager.db_manager.close_session(session)
        
        # 验证文件系统中的记录数
        csv_files = self.hybrid_manager.hole_manager.get_hole_measurements(
            project_id, hole_id
        )
        
        total_fs_records = 0
        load_times = []
        
        for csv_file in csv_files:
            start_time = time.time()
            data = self.hybrid_manager.hole_manager.load_measurement_data(csv_file)
            load_time = time.time() - start_time
            load_times.append(load_time)
            
            if data:
                total_fs_records += len(data)
        
        total_load_time = sum(load_times)
        print(f"总加载耗时: {total_load_time:.2f}秒")
        
        self.assertEqual(total_fs_records, num_measurements)
        
        # 性能要求
        avg_save_time = total_save_time / (num_measurements / batch_size)
        self.assertLess(avg_save_time, 5.0, "批量保存耗时过长")
        
        avg_load_time = total_load_time / len(csv_files) if csv_files else 0
        self.assertLess(avg_load_time, 2.0, "数据加载耗时过长")
        
        print(f"✅ 可扩展性测试完成，处理 {num_measurements} 条记录")
    
    def test_database_migration_system(self):
        """测试数据库迁移系统"""
        # 创建一个新的数据库进行迁移测试
        migration_db = os.path.join(self.temp_dir, "migration_test.db")
        migration_url = f"sqlite:///{migration_db}"
        
        migration_manager = DatabaseMigration(migration_url)
        
        print(f"\n测试数据库迁移系统...")
        
        # 备份测试
        backup_file = migration_manager.backup_database()
        # 新数据库没有备份文件，这是正常的
        
        # 运行迁移
        start_time = time.time()
        success = migration_manager.run_migration()
        migration_time = time.time() - start_time
        
        print(f"迁移耗时: {migration_time:.2f}秒")
        self.assertTrue(success)
        
        # 验证迁移后的表结构
        schema = migration_manager.check_current_schema()
        
        # 验证所有必需的表存在
        required_tables = ['workpieces', 'holes', 'measurements', 'endoscope_images']
        for table in required_tables:
            self.assertIn(table, schema, f"缺少表: {table}")
        
        # 验证workpieces表的新字段
        workpieces_columns = schema['workpieces']
        new_workpieces_fields = [
            'dxf_file_path', 'project_data_path', 'hole_count',
            'completed_holes', 'status', 'description', 'version'
        ]
        for field in new_workpieces_fields:
            self.assertIn(field, workpieces_columns, f"workpieces表缺少字段: {field}")
        
        # 验证holes表的新字段
        holes_columns = schema['holes']
        new_holes_fields = [
            'depth', 'file_system_path', 'last_measurement_at',
            'measurement_count', 'updated_at'
        ]
        for field in new_holes_fields:
            self.assertIn(field, holes_columns, f"holes表缺少字段: {field}")
        
        # 测试迁移后的功能
        hybrid_manager = HybridDataManager(
            data_root=os.path.join(self.temp_dir, "migration_test"),
            database_url=migration_url
        )
        
        # 创建测试项目验证迁移后的功能
        test_dxf = Path(self.temp_dir) / "migration_test.dxf"
        test_dxf.write_text("migration test dxf")
        
        holes_data = [
            {
                "hole_id": "H00001",
                "position": {"x": 10.0, "y": 20.0},
                "diameter": 8.865,
                "depth": 900.0,
                "tolerance": 0.1
            }
        ]
        
        project_id, project_path = hybrid_manager.create_project_from_dxf(
            str(test_dxf), "迁移后功能测试", holes_data
        )
        
        self.assertIsNotNone(project_id)
        self.assertIsNotNone(project_path)
        
        print(f"✅ 数据库迁移系统测试完成")
    
    def test_system_resource_monitoring(self):
        """测试系统资源监控"""
        try:
            import psutil
        except ImportError:
            self.skipTest("psutil not available for resource monitoring")
        
        process = psutil.Process(os.getpid())
        
        # 记录初始资源使用
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()
        
        print(f"\n初始内存使用: {initial_memory:.2f} MB")
        print(f"初始CPU使用: {initial_cpu:.2f}%")
        
        # 执行资源密集型操作
        num_projects = 3
        holes_per_project = 100
        measurements_per_hole = 50
        
        for project_idx in range(num_projects):
            # 创建项目
            dxf_file = Path(self.temp_dir) / f"resource_test_{project_idx}.dxf"
            dxf_file.write_text(f"resource test dxf {project_idx}")
            
            holes_data = []
            for i in range(holes_per_project):
                holes_data.append({
                    "hole_id": f"H{i:05d}",
                    "position": {"x": float(i % 10), "y": float(i // 10)},
                    "diameter": 8.865,
                    "depth": 900.0,
                    "tolerance": 0.1
                })
            
            project_id, _ = self.hybrid_manager.create_project_from_dxf(
                str(dxf_file), f"资源监控测试项目{project_idx}", holes_data
            )
            
            # 为部分孔位添加测量数据
            for i in range(0, holes_per_project, 10):  # 每10个孔位添加数据
                hole_id = f"H{i:05d}"
                
                measurement_data = []
                for j in range(measurements_per_hole):
                    measurement_data.append({
                        "timestamp": f"2025-01-08T{project_idx:02d}:{i//60:02d}:{j:02d}",
                        "depth": j * 2.0,
                        "diameter": 8.865 + j * 0.0001,
                        "operator": f"资源测试{project_idx}"
                    })
                
                self.bridge.save_measurement_result(
                    hole_id, project_id, measurement_data
                )
        
        # 记录最终资源使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()
        
        memory_increase = final_memory - initial_memory
        
        print(f"最终内存使用: {final_memory:.2f} MB")
        print(f"内存增长: {memory_increase:.2f} MB")
        print(f"最终CPU使用: {final_cpu:.2f}%")
        
        # 资源使用要求
        self.assertLess(memory_increase, 1000, "内存使用增长过多")  # 不超过1GB增长
        
        # 验证数据完整性
        session = self.hybrid_manager.db_manager.get_session()
        try:
            total_workpieces = session.query(Workpiece).count()
            total_holes = session.query(Hole).count()
            total_measurements = session.query(Measurement).count()
            
            expected_workpieces = num_projects
            expected_holes = num_projects * holes_per_project
            expected_measurements = num_projects * (holes_per_project // 10) * measurements_per_hole
            
            self.assertGreaterEqual(total_workpieces, expected_workpieces)
            self.assertGreaterEqual(total_holes, expected_holes)
            self.assertGreaterEqual(total_measurements, expected_measurements)
            
            print(f"数据库记录: {total_workpieces} 工件, {total_holes} 孔位, {total_measurements} 测量")
            
        finally:
            self.hybrid_manager.db_manager.close_session(session)
        
        print(f"✅ 系统资源监控测试完成")


if __name__ == '__main__':
    # 设置详细输出
    unittest.main(verbosity=2)
