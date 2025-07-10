#!/usr/bin/env python3
"""
集成测试：数据管理系统集成
Integration Tests: Data Management System Integration
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aidcis2.data_management.project_manager import ProjectDataManager
from aidcis2.data_management.hole_manager import HoleDataManager
from aidcis2.data_management.data_templates import DataTemplates, DataValidator


class TestDataManagementIntegration(unittest.TestCase):
    """数据管理系统集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_data_integration_")
        self.project_manager = ProjectDataManager(self.temp_dir)
        self.hole_manager = HoleDataManager(self.project_manager)
        self.validator = DataValidator()
        
        # 创建测试DXF文件
        self.test_dxf = Path(self.temp_dir) / "integration_test.dxf"
        self.test_dxf.write_text("dummy dxf content for integration test")
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_complete_project_workflow(self):
        """测试完整的项目工作流"""
        # 1. 创建项目
        project_name = "集成测试项目"
        project_id, project_path = self.project_manager.create_project(
            str(self.test_dxf), project_name
        )
        
        self.assertIsNotNone(project_id)
        self.assertTrue(Path(project_path).exists())
        
        # 2. 验证项目元数据
        metadata = self.project_manager.get_project_metadata(project_id)
        is_valid, errors = self.validator.validate_project_metadata(metadata)
        self.assertTrue(is_valid, f"项目元数据验证失败: {errors}")
        
        # 3. 创建多个孔位
        holes_data = [
            {"hole_id": "H00001", "position": {"x": 10.0, "y": 20.0}},
            {"hole_id": "H00002", "position": {"x": 30.0, "y": 40.0}},
            {"hole_id": "H00003", "position": {"x": 50.0, "y": 60.0}},
            {"hole_id": "H00004", "position": {"x": 70.0, "y": 80.0}},
            {"hole_id": "H00005", "position": {"x": 90.0, "y": 100.0}}
        ]
        
        created_holes = []
        for hole_data in holes_data:
            hole_info = DataTemplates.create_hole_info_template(
                hole_data["hole_id"], hole_data["position"]
            )
            
            # 验证孔位信息
            is_valid, errors = self.validator.validate_hole_info(hole_info)
            self.assertTrue(is_valid, f"孔位信息验证失败: {errors}")
            
            # 创建孔位
            success = self.hole_manager.create_hole_directory(
                project_id, hole_data["hole_id"], hole_info
            )
            self.assertTrue(success, f"孔位创建失败: {hole_data['hole_id']}")
            created_holes.append(hole_data["hole_id"])
        
        # 4. 更新项目统计
        self.project_manager.update_project_metadata(
            project_id, {"total_holes": len(holes_data)}
        )
        
        # 5. 模拟测量流程
        measurement_results = []
        for i, hole_id in enumerate(created_holes[:3]):  # 只测量前3个孔位
            # 开始测量
            success = self.hole_manager.update_hole_status(
                project_id, hole_id, "in_progress", f"开始测量孔位 {hole_id}"
            )
            self.assertTrue(success)
            
            # 生成测量数据
            measurement_data = [
                {
                    "timestamp": f"2025-01-08T10:{i:02d}:{j:02d}",
                    "depth": j * 10.0,
                    "diameter": 8.865 + j * 0.001,
                    "temperature": 25.0 + j * 0.1,
                    "pressure": 1013.25
                }
                for j in range(10)
            ]
            
            # 验证测量数据
            is_valid, errors = self.validator.validate_measurement_data(measurement_data)
            self.assertTrue(is_valid, f"测量数据验证失败: {errors}")
            
            # 保存测量数据
            success = self.hole_manager.save_measurement_data(
                project_id, hole_id, measurement_data
            )
            self.assertTrue(success)
            
            # 完成测量
            success = self.hole_manager.update_hole_status(
                project_id, hole_id, "completed", f"孔位 {hole_id} 测量完成"
            )
            self.assertTrue(success)
            
            measurement_results.append({
                "hole_id": hole_id,
                "data_points": len(measurement_data)
            })
        
        # 6. 验证最终状态
        final_stats = self.project_manager.get_project_statistics(project_id)
        self.assertEqual(final_stats["total_holes"], 5)
        self.assertEqual(final_stats["completed_holes"], 3)
        self.assertEqual(final_stats["pending_holes"], 2)
        self.assertEqual(final_stats["error_holes"], 0)
        self.assertAlmostEqual(final_stats["completion_rate"], 60.0, places=1)
        
        # 7. 验证数据完整性
        for hole_id in created_holes:
            # 验证孔位信息存在
            hole_info = self.hole_manager.get_hole_info(project_id, hole_id)
            self.assertIsNotNone(hole_info)
            
            # 验证孔位状态存在
            hole_status = self.hole_manager.get_hole_status(project_id, hole_id)
            self.assertIsNotNone(hole_status)
            
            # 验证状态历史
            self.assertGreaterEqual(len(hole_status["status_history"]), 1)
            
            # 验证测量数据（前3个孔位）
            if hole_id in [h["hole_id"] for h in measurement_results]:
                csv_files = self.hole_manager.get_hole_measurements(project_id, hole_id)
                self.assertGreater(len(csv_files), 0)
                
                # 验证可以加载测量数据
                loaded_data = self.hole_manager.load_measurement_data(csv_files[0])
                self.assertIsNotNone(loaded_data)
                self.assertEqual(len(loaded_data), 10)
    
    def test_project_and_hole_manager_integration(self):
        """测试项目管理器和孔位管理器集成"""
        # 创建项目
        project_id, _ = self.project_manager.create_project(
            str(self.test_dxf), "集成测试项目2"
        )
        
        # 测试孔位管理器与项目管理器的交互
        hole_id = "H00001"
        hole_info = DataTemplates.create_hole_info_template(
            hole_id, {"x": 10.0, "y": 20.0}
        )
        
        # 创建孔位
        success = self.hole_manager.create_hole_directory(project_id, hole_id, hole_info)
        self.assertTrue(success)
        
        # 验证孔位路径通过项目管理器可以访问
        holes_dir = self.project_manager.get_holes_directory(project_id)
        self.assertIsNotNone(holes_dir)
        
        hole_path = self.hole_manager.get_hole_path(project_id, hole_id)
        self.assertIsNotNone(hole_path)
        self.assertTrue(hole_path.startswith(holes_dir))
        
        # 验证项目统计反映孔位状态
        initial_stats = self.project_manager.get_project_statistics(project_id)
        self.assertEqual(initial_stats["total_holes"], 1)
        self.assertEqual(initial_stats["pending_holes"], 1)
        
        # 更新孔位状态
        self.hole_manager.update_hole_status(project_id, hole_id, "completed", "测试完成")
        
        # 验证统计更新
        updated_stats = self.project_manager.get_project_statistics(project_id)
        self.assertEqual(updated_stats["completed_holes"], 1)
        self.assertEqual(updated_stats["pending_holes"], 0)
    
    def test_data_validation_integration(self):
        """测试数据验证集成"""
        # 创建项目
        project_id, _ = self.project_manager.create_project(
            str(self.test_dxf), "验证集成测试项目"
        )
        
        # 测试有效数据流程
        hole_id = "H00001"
        hole_info = DataTemplates.create_hole_info_template(
            hole_id, {"x": 10.0, "y": 20.0}
        )
        
        # 验证模板生成的数据
        is_valid, errors = self.validator.validate_hole_info(hole_info)
        self.assertTrue(is_valid)
        
        # 创建孔位
        success = self.hole_manager.create_hole_directory(project_id, hole_id, hole_info)
        self.assertTrue(success)
        
        # 验证保存的数据
        saved_info = self.hole_manager.get_hole_info(project_id, hole_id)
        is_valid, errors = self.validator.validate_hole_info(saved_info)
        self.assertTrue(is_valid)
        
        saved_status = self.hole_manager.get_hole_status(project_id, hole_id)
        is_valid, errors = self.validator.validate_hole_status(saved_status)
        self.assertTrue(is_valid)
        
        # 测试测量数据验证
        measurement_data = DataTemplates.create_measurement_data_template()
        is_valid, errors = self.validator.validate_measurement_data(measurement_data)
        self.assertTrue(is_valid)
        
        # 保存并验证测量数据
        success = self.hole_manager.save_measurement_data(
            project_id, hole_id, measurement_data
        )
        self.assertTrue(success)
        
        # 加载并验证数据完整性
        csv_files = self.hole_manager.get_hole_measurements(project_id, hole_id)
        self.assertGreater(len(csv_files), 0)
        
        loaded_data = self.hole_manager.load_measurement_data(csv_files[0])
        self.assertIsNotNone(loaded_data)
        self.assertEqual(len(loaded_data), 1)
    
    def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 测试无效项目ID
        invalid_project_id = "nonexistent_project"
        
        # 孔位管理器应该正确处理无效项目
        success = self.hole_manager.create_hole_directory(
            invalid_project_id, "H00001", {}
        )
        self.assertFalse(success)
        
        hole_info = self.hole_manager.get_hole_info(invalid_project_id, "H00001")
        self.assertIsNone(hole_info)
        
        # 测试项目管理器错误处理
        metadata = self.project_manager.get_project_metadata(invalid_project_id)
        self.assertIsNone(metadata)
        
        project_path = self.project_manager.get_project_path(invalid_project_id)
        self.assertIsNone(project_path)
        
        # 测试数据验证错误处理
        invalid_metadata = {"invalid": "data"}
        is_valid, errors = self.validator.validate_project_metadata(invalid_metadata)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_concurrent_operations(self):
        """测试并发操作"""
        # 创建项目
        project_id, _ = self.project_manager.create_project(
            str(self.test_dxf), "并发测试项目"
        )
        
        # 同时创建多个孔位
        hole_ids = [f"H{i:05d}" for i in range(1, 11)]
        
        for hole_id in hole_ids:
            hole_info = DataTemplates.create_hole_info_template(
                hole_id, {"x": float(hole_id[1:3]), "y": float(hole_id[3:5])}
            )
            
            success = self.hole_manager.create_hole_directory(
                project_id, hole_id, hole_info
            )
            self.assertTrue(success, f"孔位创建失败: {hole_id}")
        
        # 验证所有孔位都创建成功
        for hole_id in hole_ids:
            hole_path = self.hole_manager.get_hole_path(project_id, hole_id)
            self.assertIsNotNone(hole_path)
            
            hole_info = self.hole_manager.get_hole_info(project_id, hole_id)
            self.assertIsNotNone(hole_info)
        
        # 验证项目统计
        stats = self.project_manager.get_project_statistics(project_id)
        self.assertEqual(stats["total_holes"], len(hole_ids))


if __name__ == '__main__':
    unittest.main()
