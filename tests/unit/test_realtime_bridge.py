#!/usr/bin/env python3
"""
单元测试：RealTimeDataBridge
Unit Tests: RealTimeDataBridge
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
from modules.models import DatabaseManager, Workpiece, Hole, Measurement


class TestRealTimeDataBridge(unittest.TestCase):
    """RealTimeDataBridge单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_realtime_bridge_")
        self.test_db = os.path.join(self.temp_dir, "test.db")
        self.database_url = f"sqlite:///{self.test_db}"
        
        # 初始化混合数据管理器和实时数据桥梁
        self.hybrid_manager = HybridDataManager(
            data_root=self.temp_dir,
            database_url=self.database_url
        )
        self.bridge = RealTimeDataBridge(self.hybrid_manager)
        
        # 创建测试项目
        self.test_dxf = Path(self.temp_dir) / "test.dxf"
        self.test_dxf.write_text("dummy dxf content")
        
        self.test_holes_data = [
            {
                "hole_id": "H00001",
                "position": {"x": 10.0, "y": 20.0},
                "diameter": 8.865,
                "depth": 900.0,
                "tolerance": 0.1
            }
        ]
        
        self.project_id, self.project_path = self.hybrid_manager.create_project_from_dxf(
            str(self.test_dxf), "实时桥梁测试项目", self.test_holes_data
        )
        self.hole_id = self.test_holes_data[0]["hole_id"]
        
        # 回调函数测试变量
        self.navigation_called = False
        self.navigation_data = None
        self.data_update_called = False
        self.data_update_data = None
        self.status_update_called = False
        self.status_update_data = None
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def navigation_callback(self, hole_id, hole_data):
        """导航回调函数"""
        self.navigation_called = True
        self.navigation_data = (hole_id, hole_data)
    
    def data_update_callback(self, hole_id, measurement_data):
        """数据更新回调函数"""
        self.data_update_called = True
        self.data_update_data = (hole_id, measurement_data)
    
    def status_update_callback(self, hole_id, status):
        """状态更新回调函数"""
        self.status_update_called = True
        self.status_update_data = (hole_id, status)
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.bridge.hybrid_manager)
        self.assertIsNotNone(self.bridge.db_manager)
        self.assertIsNone(self.bridge.navigation_callback)
        self.assertIsNone(self.bridge.data_update_callback)
        self.assertIsNone(self.bridge.status_update_callback)
    
    def test_set_callbacks(self):
        """测试设置回调函数"""
        self.bridge.set_navigation_callback(self.navigation_callback)
        self.bridge.set_data_update_callback(self.data_update_callback)
        self.bridge.set_status_update_callback(self.status_update_callback)
        
        self.assertIsNotNone(self.bridge.navigation_callback)
        self.assertIsNotNone(self.bridge.data_update_callback)
        self.assertIsNotNone(self.bridge.status_update_callback)
    
    def test_navigate_to_realtime_success(self):
        """测试成功导航到实时监控"""
        # 设置回调函数
        self.bridge.set_navigation_callback(self.navigation_callback)
        
        # 执行导航
        success = self.bridge.navigate_to_realtime(self.hole_id, self.project_id)
        
        self.assertTrue(success)
        self.assertTrue(self.navigation_called)
        self.assertIsNotNone(self.navigation_data)
        
        # 验证回调数据
        callback_hole_id, callback_hole_data = self.navigation_data
        self.assertEqual(callback_hole_id, self.hole_id)
        self.assertIn("hole_id", callback_hole_data)
        self.assertIn("project_id", callback_hole_data)
        self.assertIn("basic_info", callback_hole_data)
        self.assertIn("status_info", callback_hole_data)
    
    def test_navigate_to_realtime_no_callback(self):
        """测试没有设置回调函数的导航"""
        success = self.bridge.navigate_to_realtime(self.hole_id, self.project_id)
        self.assertFalse(success)
    
    def test_navigate_to_realtime_invalid_hole(self):
        """测试导航到无效孔位"""
        self.bridge.set_navigation_callback(self.navigation_callback)
        
        success = self.bridge.navigate_to_realtime("INVALID_HOLE", self.project_id)
        self.assertFalse(success)
        self.assertFalse(self.navigation_called)
    
    def test_load_historical_data_empty(self):
        """测试加载空的历史数据"""
        historical_data = self.bridge.load_historical_data(self.hole_id, self.project_id)
        
        self.assertIsInstance(historical_data, list)
        self.assertEqual(len(historical_data), 0)
    
    def test_start_realtime_measurement(self):
        """测试开始实时测量"""
        # 设置状态更新回调
        self.bridge.set_status_update_callback(self.status_update_callback)
        
        measurement_params = {"depth_range": [0, 900], "step": 10}
        
        success = self.bridge.start_realtime_measurement(
            self.hole_id, self.project_id, measurement_params
        )
        
        self.assertTrue(success)
        self.assertTrue(self.status_update_called)
        
        # 验证状态更新
        callback_hole_id, callback_status = self.status_update_data
        self.assertEqual(callback_hole_id, self.hole_id)
        self.assertEqual(callback_status, "measuring")
        
        # 验证数据库状态更新
        session = self.bridge.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=self.project_id).first()
            hole = session.query(Hole).filter_by(
                workpiece_id=workpiece.id, hole_id=self.hole_id
            ).first()
            
            self.assertIsNotNone(hole.last_measurement_at)
            
        finally:
            self.bridge.db_manager.close_session(session)
    
    def test_save_measurement_result(self):
        """测试保存测量结果"""
        # 设置数据更新回调
        self.bridge.set_data_update_callback(self.data_update_callback)
        
        # 测试测量数据
        measurement_data = [
            {
                "timestamp": "2025-01-08T10:00:00",
                "depth": 0.0,
                "diameter": 8.865,
                "operator": "测试"
            },
            {
                "timestamp": "2025-01-08T10:00:01",
                "depth": 10.0,
                "diameter": 8.870,
                "operator": "测试"
            }
        ]
        
        success = self.bridge.save_measurement_result(
            self.hole_id, self.project_id, measurement_data
        )
        
        self.assertTrue(success)
        self.assertTrue(self.data_update_called)
        
        # 验证回调数据
        callback_hole_id, callback_data = self.data_update_data
        self.assertEqual(callback_hole_id, self.hole_id)
        self.assertEqual(len(callback_data), 2)
        
        # 验证文件系统保存
        csv_files = self.hybrid_manager.hole_manager.get_hole_measurements(
            self.project_id, self.hole_id
        )
        self.assertGreater(len(csv_files), 0)
        
        # 验证数据库保存
        session = self.bridge.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=self.project_id).first()
            hole = session.query(Hole).filter_by(
                workpiece_id=workpiece.id, hole_id=self.hole_id
            ).first()
            
            measurements = session.query(Measurement).filter_by(hole_id=hole.id).all()
            self.assertEqual(len(measurements), 2)
            
            # 验证测量数据内容
            for i, measurement in enumerate(measurements):
                self.assertEqual(measurement.depth, measurement_data[i]["depth"])
                self.assertEqual(measurement.diameter, measurement_data[i]["diameter"])
                self.assertEqual(measurement.operator, measurement_data[i]["operator"])
                self.assertIsNotNone(measurement.is_qualified)
                self.assertIsNotNone(measurement.deviation)
            
        finally:
            self.bridge.db_manager.close_session(session)
    
    def test_get_hole_complete_data(self):
        """测试获取孔位完整数据"""
        complete_data = self.bridge.get_hole_complete_data(self.hole_id, self.project_id)
        
        self.assertIsNotNone(complete_data)
        self.assertEqual(complete_data["hole_id"], self.hole_id)
        self.assertEqual(complete_data["project_id"], self.project_id)
        self.assertIn("basic_info", complete_data)
        self.assertIn("status_info", complete_data)
        self.assertIn("database_info", complete_data)
        self.assertIn("file_system_path", complete_data)
        self.assertIn("historical_data_available", complete_data)
        
        # 验证基础信息
        basic_info = complete_data["basic_info"]
        self.assertEqual(basic_info["hole_id"], self.hole_id)
        self.assertEqual(basic_info["diameter"], 8.865)
        
        # 验证数据库信息
        db_info = complete_data["database_info"]
        self.assertEqual(db_info["target_diameter"], 8.865)
        self.assertEqual(db_info["tolerance"], 0.1)
        self.assertEqual(db_info["depth"], 900.0)
    
    def test_load_database_measurements(self):
        """测试从数据库加载测量数据"""
        # 先添加一些测量数据
        measurement_data = [
            {
                "timestamp": "2025-01-08T10:00:00",
                "depth": 0.0,
                "diameter": 8.865,
                "operator": "测试"
            }
        ]
        
        self.bridge.save_measurement_result(
            self.hole_id, self.project_id, measurement_data
        )
        
        # 加载数据库测量数据
        db_data = self.bridge.load_database_measurements(self.hole_id, self.project_id)
        
        self.assertEqual(len(db_data), 1)
        self.assertEqual(db_data[0]["depth"], 0.0)
        self.assertEqual(db_data[0]["diameter"], 8.865)
        self.assertEqual(db_data[0]["operator"], "测试")
        self.assertEqual(db_data[0]["source"], "database")
        self.assertIn("is_qualified", db_data[0])
        self.assertIn("deviation", db_data[0])
    
    def test_load_filesystem_measurements(self):
        """测试从文件系统加载测量数据"""
        # 先保存一些测量数据到文件系统
        measurement_data = [
            {
                "timestamp": "2025-01-08T10:00:00",
                "depth": 5.0,
                "diameter": 8.870
            }
        ]
        
        self.hybrid_manager.hole_manager.save_measurement_data(
            self.project_id, self.hole_id, measurement_data
        )
        
        # 加载文件系统测量数据
        fs_data = self.bridge.load_filesystem_measurements(self.hole_id, self.project_id)
        
        self.assertEqual(len(fs_data), 1)
        self.assertEqual(float(fs_data[0]["depth"]), 5.0)
        self.assertEqual(float(fs_data[0]["diameter"]), 8.870)
        self.assertEqual(fs_data[0]["source"], "filesystem")
        self.assertIn("file", fs_data[0])
    
    def test_deduplicate_measurements(self):
        """测试去重测量数据"""
        measurements = [
            {"timestamp": "2025-01-08T10:00:00", "depth": 0.0, "diameter": 8.865},
            {"timestamp": "2025-01-08T10:00:00", "depth": 0.0, "diameter": 8.865},  # 重复
            {"timestamp": "2025-01-08T10:00:01", "depth": 1.0, "diameter": 8.870},
            {"timestamp": "2025-01-08T10:00:00", "depth": 0.0, "diameter": 8.860},  # 重复时间戳和深度，但直径不同
        ]
        
        unique_measurements = self.bridge.deduplicate_measurements(measurements)
        
        # 应该保留3条记录（第2条被去重）
        self.assertEqual(len(unique_measurements), 3)
        
        # 验证去重逻辑
        timestamps_depths = [(m["timestamp"], m["depth"]) for m in unique_measurements]
        self.assertEqual(len(set(timestamps_depths)), 3)
    
    def test_update_hole_status(self):
        """测试更新孔位状态"""
        success = self.bridge.update_hole_status(
            self.hole_id, self.project_id, "in_progress", "测试状态更新"
        )
        
        self.assertTrue(success)
        
        # 验证文件系统状态更新
        hole_status = self.hybrid_manager.hole_manager.get_hole_status(
            self.project_id, self.hole_id
        )
        self.assertEqual(hole_status["current_status"], "in_progress")
        
        # 验证数据库状态更新
        session = self.bridge.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=self.project_id).first()
            hole = session.query(Hole).filter_by(
                workpiece_id=workpiece.id, hole_id=self.hole_id
            ).first()
            
            self.assertEqual(hole.status, "in_progress")
            
        finally:
            self.bridge.db_manager.close_session(session)
    
    def test_update_measurement_statistics(self):
        """测试更新测量统计"""
        success = self.bridge.update_measurement_statistics(
            self.hole_id, self.project_id, 5
        )
        
        self.assertTrue(success)
        
        # 验证数据库统计更新
        session = self.bridge.db_manager.get_session()
        try:
            workpiece = session.query(Workpiece).filter_by(workpiece_id=self.project_id).first()
            hole = session.query(Hole).filter_by(
                workpiece_id=workpiece.id, hole_id=self.hole_id
            ).first()
            
            self.assertEqual(hole.measurement_count, 5)
            
        finally:
            self.bridge.db_manager.close_session(session)


if __name__ == '__main__':
    unittest.main()
