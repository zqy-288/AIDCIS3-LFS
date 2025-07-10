#!/usr/bin/env python3
"""
单元测试：DataTemplates & DataValidator
Unit Tests: DataTemplates & DataValidator
"""

import unittest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aidcis2.data_management.data_templates import DataTemplates, DataValidator, DataExporter


class TestDataTemplates(unittest.TestCase):
    """DataTemplates单元测试类"""
    
    def test_create_project_metadata_template(self):
        """测试创建项目元数据模板"""
        project_id = "test_project_001"
        project_name = "测试项目"
        dxf_file = "test.dxf"
        total_holes = 100
        
        metadata = DataTemplates.create_project_metadata_template(
            project_id, project_name, dxf_file, total_holes
        )
        
        # 验证必需字段
        self.assertEqual(metadata["project_id"], project_id)
        self.assertEqual(metadata["project_name"], project_name)
        self.assertEqual(metadata["dxf_file"], dxf_file)
        self.assertEqual(metadata["total_holes"], total_holes)
        self.assertEqual(metadata["completed_holes"], 0)
        self.assertEqual(metadata["status"], "active")
        self.assertEqual(metadata["version"], "1.0")
        
        # 验证可选字段
        self.assertIn("created_at", metadata)
        self.assertIn("description", metadata)
        self.assertIn("tags", metadata)
        self.assertIn("settings", metadata)
        
        # 验证数据类型
        self.assertIsInstance(metadata["tags"], list)
        self.assertIsInstance(metadata["settings"], dict)
    
    def test_create_hole_info_template(self):
        """测试创建孔位信息模板"""
        hole_id = "H00001"
        position = {"x": 10.0, "y": 20.0}
        diameter = 8.865
        depth = 900.0
        
        hole_info = DataTemplates.create_hole_info_template(
            hole_id, position, diameter, depth
        )
        
        # 验证必需字段
        self.assertEqual(hole_info["hole_id"], hole_id)
        self.assertEqual(hole_info["position"], position)
        self.assertEqual(hole_info["diameter"], diameter)
        self.assertEqual(hole_info["depth"], depth)
        self.assertEqual(hole_info["status"], "pending")
        
        # 验证时间字段
        self.assertIn("created_at", hole_info)
        self.assertIn("last_updated", hole_info)
        
        # 验证扩展字段
        self.assertIn("properties", hole_info)
        self.assertIn("geometry", hole_info)
        
        # 验证数据类型
        self.assertIsInstance(hole_info["properties"], dict)
        self.assertIsInstance(hole_info["geometry"], dict)
    
    def test_create_hole_status_template(self):
        """测试创建孔位状态模板"""
        initial_status = "pending"
        reason = "初始化"
        
        status = DataTemplates.create_hole_status_template(initial_status, reason)
        
        # 验证状态字段
        self.assertEqual(status["current_status"], initial_status)
        self.assertIn("last_updated", status)
        
        # 验证状态历史
        self.assertIn("status_history", status)
        self.assertIsInstance(status["status_history"], list)
        self.assertEqual(len(status["status_history"]), 1)
        
        history_entry = status["status_history"][0]
        self.assertEqual(history_entry["status"], initial_status)
        self.assertEqual(history_entry["reason"], reason)
        self.assertIn("timestamp", history_entry)
        self.assertIn("operator", history_entry)
        
        # 验证统计字段
        self.assertIn("statistics", status)
        self.assertIsInstance(status["statistics"], dict)
    
    def test_create_measurement_data_template(self):
        """测试创建测量数据模板"""
        measurement_data = DataTemplates.create_measurement_data_template()
        
        # 验证数据类型
        self.assertIsInstance(measurement_data, list)
        self.assertEqual(len(measurement_data), 1)
        
        # 验证记录字段
        record = measurement_data[0]
        self.assertIn("timestamp", record)
        self.assertIn("depth", record)
        self.assertIn("diameter", record)
        self.assertIn("temperature", record)
        self.assertIn("pressure", record)
        self.assertIn("measurement_id", record)
        self.assertIn("quality", record)
        self.assertIn("operator", record)
        
        # 验证数据类型
        self.assertIsInstance(record["depth"], (int, float))
        self.assertIsInstance(record["diameter"], (int, float))
        self.assertIsInstance(record["temperature"], (int, float))
        self.assertIsInstance(record["pressure"], (int, float))


class TestDataValidator(unittest.TestCase):
    """DataValidator单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.validator = DataValidator()
    
    def test_validate_project_metadata_valid(self):
        """测试验证有效的项目元数据"""
        metadata = DataTemplates.create_project_metadata_template(
            "test_project", "测试项目", "test.dxf", 100
        )
        
        is_valid, errors = self.validator.validate_project_metadata(metadata)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_project_metadata_missing_fields(self):
        """测试验证缺少必需字段的项目元数据"""
        metadata = {
            "project_id": "test_project",
            # 缺少其他必需字段
        }
        
        is_valid, errors = self.validator.validate_project_metadata(metadata)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
        # 验证错误信息包含缺少的字段
        error_text = " ".join(errors)
        self.assertIn("project_name", error_text)
        self.assertIn("dxf_file", error_text)
        self.assertIn("created_at", error_text)
        self.assertIn("status", error_text)
    
    def test_validate_project_metadata_invalid_types(self):
        """测试验证数据类型错误的项目元数据"""
        metadata = DataTemplates.create_project_metadata_template(
            "test_project", "测试项目", "test.dxf", 100
        )
        
        # 修改为错误的数据类型
        metadata["total_holes"] = "not_a_number"
        metadata["completed_holes"] = "also_not_a_number"
        
        is_valid, errors = self.validator.validate_project_metadata(metadata)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
        error_text = " ".join(errors)
        self.assertIn("total_holes", error_text)
        self.assertIn("completed_holes", error_text)
    
    def test_validate_project_metadata_invalid_status(self):
        """测试验证无效状态值的项目元数据"""
        metadata = DataTemplates.create_project_metadata_template(
            "test_project", "测试项目", "test.dxf", 100
        )
        metadata["status"] = "invalid_status"
        
        is_valid, errors = self.validator.validate_project_metadata(metadata)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        
        error_text = " ".join(errors)
        self.assertIn("无效的状态值", error_text)
    
    def test_validate_hole_info_valid(self):
        """测试验证有效的孔位信息"""
        hole_info = DataTemplates.create_hole_info_template(
            "H00001", {"x": 10.0, "y": 20.0}
        )
        
        is_valid, errors = self.validator.validate_hole_info(hole_info)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_hole_info_missing_fields(self):
        """测试验证缺少必需字段的孔位信息"""
        hole_info = {
            "hole_id": "H00001",
            # 缺少其他必需字段
        }
        
        is_valid, errors = self.validator.validate_hole_info(hole_info)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_validate_hole_info_invalid_position(self):
        """测试验证无效位置信息的孔位信息"""
        hole_info = DataTemplates.create_hole_info_template(
            "H00001", {"x": 10.0, "y": 20.0}
        )
        
        # 测试无效的位置格式
        hole_info["position"] = "invalid_position"
        
        is_valid, errors = self.validator.validate_hole_info(hole_info)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_validate_hole_status_valid(self):
        """测试验证有效的孔位状态"""
        status = DataTemplates.create_hole_status_template()
        
        is_valid, errors = self.validator.validate_hole_status(status)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_measurement_data_valid(self):
        """测试验证有效的测量数据"""
        measurement_data = DataTemplates.create_measurement_data_template()
        
        is_valid, errors = self.validator.validate_measurement_data(measurement_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_measurement_data_invalid_type(self):
        """测试验证无效类型的测量数据"""
        measurement_data = "not_a_list"
        
        is_valid, errors = self.validator.validate_measurement_data(measurement_data)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestDataExporter(unittest.TestCase):
    """DataExporter单元测试类"""
    
    def test_export_project_summary(self):
        """测试导出项目摘要"""
        project_metadata = DataTemplates.create_project_metadata_template(
            "test_project", "测试项目", "test.dxf", 100
        )
        
        hole_statistics = {
            "total_holes": 100,
            "completed_holes": 50,
            "pending_holes": 30,
            "error_holes": 20,
            "completion_rate": 50.0
        }
        
        summary = DataExporter.export_project_summary(project_metadata, hole_statistics)
        
        # 验证摘要结构
        self.assertIn("project_info", summary)
        self.assertIn("statistics", summary)
        self.assertIn("export_timestamp", summary)
        self.assertIn("export_version", summary)
        
        # 验证项目信息
        project_info = summary["project_info"]
        self.assertEqual(project_info["id"], "test_project")
        self.assertEqual(project_info["name"], "测试项目")
        
        # 验证统计信息
        self.assertEqual(summary["statistics"], hole_statistics)
    
    def test_export_hole_report(self):
        """测试导出孔位报告"""
        hole_info = DataTemplates.create_hole_info_template(
            "H00001", {"x": 10.0, "y": 20.0}
        )
        
        hole_status = DataTemplates.create_hole_status_template()
        
        measurements = ["measurement_001.csv", "measurement_002.csv"]
        
        report = DataExporter.export_hole_report(hole_info, hole_status, measurements)
        
        # 验证报告结构
        self.assertIn("hole_info", report)
        self.assertIn("current_status", report)
        self.assertIn("status_history", report)
        self.assertIn("measurement_files", report)
        self.assertIn("total_measurements", report)
        self.assertIn("export_timestamp", report)
        
        # 验证内容
        self.assertEqual(report["hole_info"], hole_info)
        self.assertEqual(report["current_status"], "pending")
        self.assertEqual(report["measurement_files"], measurements)
        self.assertEqual(report["total_measurements"], 2)


if __name__ == '__main__':
    unittest.main()
