#!/usr/bin/env python3
"""
集成测试：优先级3阶段2数据库集成
Integration Tests: Priority 3 Phase 2 Database Integration
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aidcis2.data_management.hybrid_manager import HybridDataManager
from aidcis2.data_management.realtime_bridge import RealTimeDataBridge
from aidcis2.data_management.database_migration import DatabaseMigration
from modules.models import DatabaseManager, Workpiece, Hole, Measurement


class TestDatabaseIntegrationPhase2(unittest.TestCase):
    """优先级3阶段2数据库集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_db_integration_phase2_")
        self.test_db = os.path.join(self.temp_dir, "test.db")
        self.database_url = f"sqlite:///{self.test_db}"
        
        # 初始化组件
        self.hybrid_manager = HybridDataManager(
            data_root=self.temp_dir,
            database_url=self.database_url
        )
        self.bridge = RealTimeDataBridge(self.hybrid_manager)
        self.migration = DatabaseMigration(self.database_url)
        
        # 创建测试数据
        self.test_dxf = Path(self.temp_dir) / "integration_test.dxf"
        self.test_dxf.write_text("integration test dxf content")
        
        self.test_holes_data = [
            {
                "hole_id": "H00001",
                "position": {"x": 10.0, "y": 20.0},
                "diameter": 8.865,
                "depth": 900.0,
                "tolerance": 0.1
            },
            {
                "hole_id": "H00002",
                "position": {"x": 30.0, "y": 40.0},
                "diameter": 8.870,
                "depth": 950.0,
                "tolerance": 0.1
            },
            {
                "hole_id": "H00003",
                "position": {"x": 50.0, "y": 60.0},
                "diameter": 8.860,
                "depth": 920.0,
                "tolerance": 0.1
            }
        ]
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_database_migration_integration(self):
        """测试数据库迁移集成"""
        # 运行迁移
        success = self.migration.run_migration()
        self.assertTrue(success)
        
        # 验证迁移后的表结构
        schema = self.migration.check_current_schema()
        
        # 验证workpieces表字段
        workpieces_columns = schema.get('workpieces', [])
        expected_workpieces_columns = [
            'id', 'workpiece_id', 'name', 'type', 'material',
            'dxf_file_path', 'project_data_path', 'hole_count',
            'completed_holes', 'status', 'description', 'version',
            'created_at', 'updated_at'
        ]
        
        for column in expected_workpieces_columns:
            self.assertIn(column, workpieces_columns, f"workpieces表缺少字段: {column}")
        
        # 验证holes表字段
        holes_columns = schema.get('holes', [])
        expected_holes_columns = [
            'id', 'hole_id', 'workpiece_id', 'position_x', 'position_y',
            'target_diameter', 'tolerance', 'depth', 'file_system_path',
            'status', 'last_measurement_at', 'measurement_count',
            'created_at', 'updated_at'
        ]
        
        for column in expected_holes_columns:
            self.assertIn(column, holes_columns, f"holes表缺少字段: {column}")
    
    def test_hybrid_manager_database_integration(self):
        """测试混合管理器数据库集成"""
        # 创建项目
        project_id, project_path = self.hybrid_manager.create_project_from_dxf(
            str(self.test_dxf), "数据库集成测试项目", self.test_holes_data
        )
        
        self.assertIsNotNone(project_id)
        self.assertIsNotNone(project_path)
        
        # 验证数据库记录
        session = self.hybrid_manager.db_manager.get_session()
        try:
            # 验证工件记录
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            self.assertIsNotNone(workpiece)
            self.assertEqual(workpiece.name, "数据库集成测试项目")
            self.assertEqual(workpiece.hole_count, len(self.test_holes_data))
            self.assertEqual(workpiece.status, "active")
            self.assertIsNotNone(workpiece.project_data_path)
            self.assertIsNotNone(workpiece.dxf_file_path)
            
            # 验证孔位记录
            holes = session.query(Hole).filter_by(workpiece_id=workpiece.id).all()
            self.assertEqual(len(holes), len(self.test_holes_data))
            
            for hole in holes:
                # 查找对应的测试数据
                test_hole = next(h for h in self.test_holes_data if h["hole_id"] == hole.hole_id)
                
                self.assertEqual(hole.position_x, test_hole["position"]["x"])
                self.assertEqual(hole.position_y, test_hole["position"]["y"])
                self.assertEqual(hole.target_diameter, test_hole["diameter"])
                self.assertEqual(hole.tolerance, test_hole["tolerance"])
                self.assertEqual(hole.depth, test_hole["depth"])
                self.assertEqual(hole.status, "pending")
                self.assertIsNotNone(hole.file_system_path)
                self.assertTrue(Path(hole.file_system_path).exists())
                
        finally:
            self.hybrid_manager.db_manager.close_session(session)
        
        # 验证文件系统结构
        self.assertTrue(Path(project_path).exists())
        holes_dir = Path(project_path) / "holes"
        self.assertTrue(holes_dir.exists())
        
        for hole_data in self.test_holes_data:
            hole_dir = holes_dir / hole_data["hole_id"]
            self.assertTrue(hole_dir.exists())
            self.assertTrue((hole_dir / "BISDM").exists())
            self.assertTrue((hole_dir / "CCIDM").exists())
    
    def test_realtime_bridge_database_integration(self):
        """测试实时桥梁数据库集成"""
        # 创建项目
        project_id, _ = self.hybrid_manager.create_project_from_dxf(
            str(self.test_dxf), "实时桥梁集成测试", self.test_holes_data
        )
        
        hole_id = self.test_holes_data[0]["hole_id"]
        
        # 测试开始实时测量
        success = self.bridge.start_realtime_measurement(
            hole_id, project_id, {"depth_range": [0, 900]}
        )
        self.assertTrue(success)
        
        # 验证数据库状态更新
        session = self.bridge.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            hole = session.query(Hole).filter_by(
                workpiece_id=workpiece.id, hole_id=hole_id
            ).first()
            
            self.assertEqual(hole.status, "measuring")
            self.assertIsNotNone(hole.last_measurement_at)
            
        finally:
            self.bridge.db_manager.close_session(session)
        
        # 测试保存测量结果
        measurement_data = [
            {
                "timestamp": "2025-01-08T10:00:00",
                "depth": 0.0,
                "diameter": 8.865,
                "operator": "集成测试"
            },
            {
                "timestamp": "2025-01-08T10:00:01",
                "depth": 10.0,
                "diameter": 8.870,
                "operator": "集成测试"
            },
            {
                "timestamp": "2025-01-08T10:00:02",
                "depth": 20.0,
                "diameter": 8.860,
                "operator": "集成测试"
            }
        ]
        
        success = self.bridge.save_measurement_result(
            hole_id, project_id, measurement_data
        )
        self.assertTrue(success)
        
        # 验证数据库测量记录
        session = self.bridge.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            hole = session.query(Hole).filter_by(
                workpiece_id=workpiece.id, hole_id=hole_id
            ).first()
            
            measurements = session.query(Measurement).filter_by(hole_id=hole.id).all()
            self.assertEqual(len(measurements), len(measurement_data))
            
            # 验证测量数据内容
            for i, measurement in enumerate(measurements):
                expected = measurement_data[i]
                self.assertEqual(measurement.depth, expected["depth"])
                self.assertEqual(measurement.diameter, expected["diameter"])
                self.assertEqual(measurement.operator, expected["operator"])
                self.assertIsNotNone(measurement.is_qualified)
                self.assertIsNotNone(measurement.deviation)
            
            # 验证孔位状态和统计
            self.assertEqual(hole.status, "completed")
            self.assertEqual(hole.measurement_count, len(measurement_data))
            
        finally:
            self.bridge.db_manager.close_session(session)
        
        # 验证文件系统保存
        csv_files = self.hybrid_manager.hole_manager.get_hole_measurements(
            project_id, hole_id
        )
        self.assertGreater(len(csv_files), 0)
        
        loaded_data = self.hybrid_manager.hole_manager.load_measurement_data(csv_files[0])
        self.assertEqual(len(loaded_data), len(measurement_data))
    
    def test_data_synchronization_integration(self):
        """测试数据同步集成"""
        # 创建项目
        project_id, _ = self.hybrid_manager.create_project_from_dxf(
            str(self.test_dxf), "数据同步集成测试", self.test_holes_data
        )
        
        # 修改数据库数据
        session = self.hybrid_manager.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            workpiece.completed_holes = 2
            workpiece.description = "数据库修改的描述"
            
            hole = session.query(Hole).filter_by(workpiece_id=workpiece.id).first()
            hole.status = "completed"
            hole.measurement_count = 15
            
            session.commit()
        finally:
            self.hybrid_manager.db_manager.close_session(session)
        
        # 修改文件系统数据
        fs_updates = {"status": "paused", "custom_field": "文件系统添加"}
        self.hybrid_manager.project_manager.update_project_metadata(project_id, fs_updates)
        
        hole_id = self.test_holes_data[0]["hole_id"]
        self.hybrid_manager.hole_manager.update_hole_status(
            project_id, hole_id, "error", "文件系统错误状态"
        )
        
        # 执行双向同步
        success = self.hybrid_manager.ensure_data_consistency(project_id)
        self.assertTrue(success)
        
        # 验证同步结果
        # 检查数据库
        session = self.hybrid_manager.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            # 文件系统的修改应该同步到数据库
            self.assertEqual(workpiece.status, "paused")
            # 数据库的修改应该保留
            self.assertEqual(workpiece.completed_holes, 2)
            self.assertEqual(workpiece.description, "数据库修改的描述")
            
            hole = session.query(Hole).filter_by(workpiece_id=workpiece.id, hole_id=hole_id).first()
            # 文件系统的状态修改应该同步到数据库
            self.assertEqual(hole.status, "error")
            # 数据库的统计修改应该保留
            self.assertEqual(hole.measurement_count, 15)
            
        finally:
            self.hybrid_manager.db_manager.close_session(session)
        
        # 检查文件系统
        metadata = self.hybrid_manager.project_manager.get_project_metadata(project_id)
        # 数据库的修改应该同步到文件系统
        self.assertEqual(metadata["completed_holes"], 2)
        self.assertEqual(metadata["description"], "数据库修改的描述")
        # 文件系统的修改应该保留
        self.assertEqual(metadata["status"], "paused")
        self.assertEqual(metadata["custom_field"], "文件系统添加")
        
        hole_status = self.hybrid_manager.hole_manager.get_hole_status(project_id, hole_id)
        self.assertEqual(hole_status["current_status"], "error")
    
    def test_historical_data_integration(self):
        """测试历史数据集成"""
        # 创建项目
        project_id, _ = self.hybrid_manager.create_project_from_dxf(
            str(self.test_dxf), "历史数据集成测试", self.test_holes_data
        )
        
        hole_id = self.test_holes_data[0]["hole_id"]
        
        # 添加数据库测量数据
        db_measurement_data = [
            {
                "timestamp": "2025-01-08T09:00:00",
                "depth": 0.0,
                "diameter": 8.865,
                "operator": "数据库测试"
            },
            {
                "timestamp": "2025-01-08T09:00:01",
                "depth": 5.0,
                "diameter": 8.870,
                "operator": "数据库测试"
            }
        ]
        
        self.bridge.save_measurements_to_database(hole_id, project_id, db_measurement_data)
        
        # 添加文件系统测量数据
        fs_measurement_data = [
            {
                "timestamp": "2025-01-08T10:00:00",
                "depth": 10.0,
                "diameter": 8.860
            },
            {
                "timestamp": "2025-01-08T10:00:01",
                "depth": 15.0,
                "diameter": 8.875
            }
        ]
        
        self.hybrid_manager.hole_manager.save_measurement_data(
            project_id, hole_id, fs_measurement_data
        )
        
        # 加载历史数据
        historical_data = self.bridge.load_historical_data(hole_id, project_id)
        
        # 验证历史数据整合
        self.assertEqual(len(historical_data), 4)  # 2个数据库 + 2个文件系统
        
        # 验证数据来源标识
        db_sources = [d for d in historical_data if d.get("source") == "database"]
        fs_sources = [d for d in historical_data if d.get("source") == "filesystem"]
        
        self.assertEqual(len(db_sources), 2)
        self.assertEqual(len(fs_sources), 2)
        
        # 验证数据排序（按时间戳）
        timestamps = [d["timestamp"] for d in historical_data]
        self.assertEqual(timestamps, sorted(timestamps))
        
        # 验证数据内容
        self.assertEqual(historical_data[0]["depth"], 0.0)  # 最早的数据库记录
        self.assertEqual(historical_data[-1]["depth"], 15.0)  # 最晚的文件系统记录
    
    def test_complete_workflow_integration(self):
        """测试完整工作流集成"""
        # 1. 创建项目
        project_id, _ = self.hybrid_manager.create_project_from_dxf(
            str(self.test_dxf), "完整工作流集成测试", self.test_holes_data
        )
        
        # 2. 获取项目摘要
        summary = self.hybrid_manager.get_project_summary(project_id)
        self.assertIsNotNone(summary)
        self.assertTrue(summary["data_sources"]["database"])
        self.assertTrue(summary["data_sources"]["filesystem"])
        
        # 3. 对每个孔位执行测量流程
        for i, hole_data in enumerate(self.test_holes_data):
            hole_id = hole_data["hole_id"]
            
            # 获取孔位完整数据
            complete_data = self.bridge.get_hole_complete_data(hole_id, project_id)
            self.assertIsNotNone(complete_data)
            
            # 开始测量
            success = self.bridge.start_realtime_measurement(
                hole_id, project_id, {"depth_range": [0, hole_data["depth"]]}
            )
            self.assertTrue(success)
            
            # 生成测量数据
            measurement_data = [
                {
                    "timestamp": f"2025-01-08T10:{i:02d}:{j:02d}",
                    "depth": j * 10.0,
                    "diameter": hole_data["diameter"] + j * 0.001,
                    "operator": f"工作流测试{i+1}"
                }
                for j in range(5)
            ]
            
            # 保存测量结果
            success = self.bridge.save_measurement_result(
                hole_id, project_id, measurement_data
            )
            self.assertTrue(success)
        
        # 4. 验证最终状态
        final_summary = self.hybrid_manager.get_project_summary(project_id)
        self.assertEqual(final_summary["statistics"]["total_holes"], len(self.test_holes_data))
        self.assertEqual(final_summary["statistics"]["completed_holes"], len(self.test_holes_data))
        self.assertEqual(final_summary["statistics"]["completion_rate"], 100.0)
        
        # 5. 验证数据库完整性
        session = self.hybrid_manager.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=project_id).first()
            self.assertEqual(workpiece.hole_count, len(self.test_holes_data))
            
            total_measurements = session.query(Measurement).join(Hole).filter(
                Hole.workpiece_id == workpiece.id
            ).count()
            self.assertEqual(total_measurements, len(self.test_holes_data) * 5)  # 每个孔5条测量
            
        finally:
            self.hybrid_manager.db_manager.close_session(session)
        
        # 6. 验证文件系统完整性
        for hole_data in self.test_holes_data:
            hole_id = hole_data["hole_id"]
            csv_files = self.hybrid_manager.hole_manager.get_hole_measurements(
                project_id, hole_id
            )
            self.assertGreater(len(csv_files), 0)
            
            loaded_data = self.hybrid_manager.hole_manager.load_measurement_data(csv_files[0])
            self.assertEqual(len(loaded_data), 5)


if __name__ == '__main__':
    unittest.main()
