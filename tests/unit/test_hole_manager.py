#!/usr/bin/env python3
"""
单元测试：HoleDataManager
Unit Tests: HoleDataManager
"""

import unittest
import tempfile
import shutil
import json
import csv
from pathlib import Path
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aidcis2.data_management.project_manager import ProjectDataManager
from aidcis2.data_management.hole_manager import HoleDataManager


class TestHoleDataManager(unittest.TestCase):
    """HoleDataManager单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_hole_manager_")
        self.project_manager = ProjectDataManager(self.temp_dir)
        self.hole_manager = HoleDataManager(self.project_manager)
        
        # 创建测试项目
        test_dxf = Path(self.temp_dir) / "test.dxf"
        test_dxf.write_text("dummy dxf content")
        
        self.project_id, self.project_path = self.project_manager.create_project(
            str(test_dxf), "测试项目"
        )
        
        # 测试孔位数据
        self.test_hole_id = "H00001"
        self.test_hole_info = {
            "hole_id": self.test_hole_id,
            "position": {"x": 10.0, "y": 20.0},
            "diameter": 8.865,
            "depth": 900.0
        }
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_create_hole_directory_success(self):
        """测试成功创建孔位目录"""
        success = self.hole_manager.create_hole_directory(
            self.project_id, self.test_hole_id, self.test_hole_info
        )
        self.assertTrue(success)
        
        # 验证目录结构
        hole_path = self.hole_manager.get_hole_path(self.project_id, self.test_hole_id)
        self.assertIsNotNone(hole_path)
        
        hole_dir = Path(hole_path)
        self.assertTrue(hole_dir.exists())
        self.assertTrue((hole_dir / "BISDM").exists())
        self.assertTrue((hole_dir / "CCIDM").exists())
        self.assertTrue((hole_dir / "BISDM" / "info.json").exists())
        self.assertTrue((hole_dir / "BISDM" / "status.json").exists())
    
    def test_create_hole_directory_invalid_project(self):
        """测试在无效项目中创建孔位目录"""
        success = self.hole_manager.create_hole_directory(
            "invalid_project", self.test_hole_id, self.test_hole_info
        )
        self.assertFalse(success)
    
    def test_save_and_get_hole_info(self):
        """测试保存和获取孔位信息"""
        # 创建孔位目录
        self.hole_manager.create_hole_directory(
            self.project_id, self.test_hole_id, self.test_hole_info
        )
        
        # 获取孔位信息
        retrieved_info = self.hole_manager.get_hole_info(self.project_id, self.test_hole_id)
        
        self.assertIsNotNone(retrieved_info)
        self.assertEqual(retrieved_info["hole_id"], self.test_hole_id)
        self.assertEqual(retrieved_info["position"]["x"], 10.0)
        self.assertEqual(retrieved_info["position"]["y"], 20.0)
        self.assertEqual(retrieved_info["diameter"], 8.865)
        self.assertEqual(retrieved_info["depth"], 900.0)
        self.assertIn("created_at", retrieved_info)
        self.assertIn("last_updated", retrieved_info)
    
    def test_get_hole_info_not_exists(self):
        """测试获取不存在的孔位信息"""
        result = self.hole_manager.get_hole_info(self.project_id, "nonexistent_hole")
        self.assertIsNone(result)
    
    def test_save_and_get_hole_status(self):
        """测试保存和获取孔位状态"""
        # 创建孔位目录
        self.hole_manager.create_hole_directory(
            self.project_id, self.test_hole_id, self.test_hole_info
        )
        
        # 获取初始状态
        status = self.hole_manager.get_hole_status(self.project_id, self.test_hole_id)
        
        self.assertIsNotNone(status)
        self.assertEqual(status["current_status"], "pending")
        self.assertEqual(len(status["status_history"]), 1)
        self.assertEqual(status["status_history"][0]["status"], "pending")
        self.assertEqual(status["status_history"][0]["reason"], "初始化")
        self.assertIn("last_updated", status)
    
    def test_update_hole_status(self):
        """测试更新孔位状态"""
        # 创建孔位目录
        self.hole_manager.create_hole_directory(
            self.project_id, self.test_hole_id, self.test_hole_info
        )
        
        # 更新状态
        success = self.hole_manager.update_hole_status(
            self.project_id, self.test_hole_id, "in_progress", "开始测量"
        )
        self.assertTrue(success)
        
        # 验证更新结果
        status = self.hole_manager.get_hole_status(self.project_id, self.test_hole_id)
        self.assertEqual(status["current_status"], "in_progress")
        self.assertEqual(len(status["status_history"]), 2)
        self.assertEqual(status["status_history"][1]["status"], "in_progress")
        self.assertEqual(status["status_history"][1]["reason"], "开始测量")
    
    def test_save_measurement_data(self):
        """测试保存测量数据"""
        # 创建孔位目录
        self.hole_manager.create_hole_directory(
            self.project_id, self.test_hole_id, self.test_hole_info
        )
        
        # 测试数据
        measurement_data = [
            {"timestamp": "2025-01-08T10:00:00", "depth": 0.0, "diameter": 8.865},
            {"timestamp": "2025-01-08T10:00:01", "depth": 1.0, "diameter": 8.870},
            {"timestamp": "2025-01-08T10:00:02", "depth": 2.0, "diameter": 8.860}
        ]
        
        # 保存数据
        success = self.hole_manager.save_measurement_data(
            self.project_id, self.test_hole_id, measurement_data, "test_measurement.csv"
        )
        self.assertTrue(success)
        
        # 验证文件存在
        hole_path = self.hole_manager.get_hole_path(self.project_id, self.test_hole_id)
        csv_file = Path(hole_path) / "CCIDM" / "test_measurement.csv"
        self.assertTrue(csv_file.exists())
        
        # 验证文件内容
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0]["depth"], "0.0")
            self.assertEqual(rows[0]["diameter"], "8.865")
    
    def test_get_hole_measurements(self):
        """测试获取孔位测量文件列表"""
        # 创建孔位目录
        self.hole_manager.create_hole_directory(
            self.project_id, self.test_hole_id, self.test_hole_info
        )
        
        # 保存多个测量文件
        measurement_data = [{"timestamp": "2025-01-08T10:00:00", "depth": 0.0, "diameter": 8.865}]
        
        self.hole_manager.save_measurement_data(
            self.project_id, self.test_hole_id, measurement_data, "measurement_001.csv"
        )
        self.hole_manager.save_measurement_data(
            self.project_id, self.test_hole_id, measurement_data, "measurement_002.csv"
        )
        
        # 获取文件列表
        csv_files = self.hole_manager.get_hole_measurements(self.project_id, self.test_hole_id)
        
        self.assertEqual(len(csv_files), 2)
        self.assertTrue(any("measurement_001.csv" in f for f in csv_files))
        self.assertTrue(any("measurement_002.csv" in f for f in csv_files))
    
    def test_load_measurement_data(self):
        """测试加载测量数据"""
        # 创建孔位目录
        self.hole_manager.create_hole_directory(
            self.project_id, self.test_hole_id, self.test_hole_info
        )
        
        # 保存测试数据
        measurement_data = [
            {"timestamp": "2025-01-08T10:00:00", "depth": 0.0, "diameter": 8.865},
            {"timestamp": "2025-01-08T10:00:01", "depth": 1.0, "diameter": 8.870}
        ]
        
        self.hole_manager.save_measurement_data(
            self.project_id, self.test_hole_id, measurement_data, "load_test.csv"
        )
        
        # 获取文件路径
        csv_files = self.hole_manager.get_hole_measurements(self.project_id, self.test_hole_id)
        csv_file = csv_files[0]
        
        # 加载数据
        loaded_data = self.hole_manager.load_measurement_data(csv_file)
        
        self.assertIsNotNone(loaded_data)
        self.assertEqual(len(loaded_data), 2)
        self.assertEqual(loaded_data[0]["depth"], "0.0")
        self.assertEqual(loaded_data[0]["diameter"], "8.865")
        self.assertEqual(loaded_data[1]["depth"], "1.0")
        self.assertEqual(float(loaded_data[1]["diameter"]), 8.870)
    
    def test_load_measurement_data_not_exists(self):
        """测试加载不存在的测量数据文件"""
        result = self.hole_manager.load_measurement_data("nonexistent_file.csv")
        self.assertIsNone(result)
    
    def test_get_hole_path_exists(self):
        """测试获取存在的孔位路径"""
        # 创建孔位目录
        self.hole_manager.create_hole_directory(
            self.project_id, self.test_hole_id, self.test_hole_info
        )
        
        hole_path = self.hole_manager.get_hole_path(self.project_id, self.test_hole_id)
        self.assertIsNotNone(hole_path)
        self.assertTrue(Path(hole_path).exists())
    
    def test_get_hole_path_not_exists(self):
        """测试获取不存在的孔位路径"""
        result = self.hole_manager.get_hole_path(self.project_id, "nonexistent_hole")
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
