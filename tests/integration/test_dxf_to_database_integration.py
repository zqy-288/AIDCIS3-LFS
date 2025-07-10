#!/usr/bin/env python3
"""
集成测试：DXF到数据库集成
Integration Tests: DXF to Database Integration
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aidcis2.integration.dxf_integration_manager import DXFIntegrationManager
from aidcis2.integration.ui_integration_adapter import UIIntegrationAdapter
from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader
from aidcis2.models.hole_data import HoleData, HoleCollection, Position, HoleStatus


class TestDXFToDatabaseIntegration(unittest.TestCase):
    """DXF到数据库集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_dxf_db_integration_")
        self.test_db = os.path.join(self.temp_dir, "test.db")
        self.database_url = f"sqlite:///{self.test_db}"
        
        # 创建测试DXF文件
        self.test_dxf = Path(self.temp_dir) / "integration_test.dxf"
        self.test_dxf.write_text("integration test dxf content")
        
        # 模拟孔位集合
        self.mock_hole_collection = self._create_mock_hole_collection()
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_mock_hole_collection(self) -> HoleCollection:
        """创建模拟孔位集合"""
        holes = {}
        for i in range(1, 6):  # 5个孔位
            hole_id = f"H{i:05d}"
            hole_data = HoleData(
                hole_id=hole_id,
                position=Position(x=float(i * 10), y=float(i * 20)),
                diameter=8.865 + i * 0.001,
                status=HoleStatus.PENDING
            )
            holes[hole_id] = hole_data
        
        return HoleCollection(
            holes=holes,
            metadata={
                'source_file': str(self.test_dxf),
                'total_entities': 20,
                'total_arcs': 5
            }
        )
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_dxf_integration_manager_full_workflow(self, mock_hybrid_manager_class, mock_dxf_parser_class):
        """测试DXF集成管理器完整工作流"""
        # 设置模拟对象
        mock_dxf_parser = Mock()
        mock_dxf_parser.parse_file.return_value = self.mock_hole_collection
        mock_dxf_parser_class.return_value = mock_dxf_parser
        
        mock_hybrid_manager = Mock()
        mock_hybrid_manager.create_project_from_dxf.return_value = ("test_project_001", "/path/to/project")
        mock_hybrid_manager.ensure_data_consistency.return_value = True
        mock_hybrid_manager.get_project_summary.return_value = {
            "project_name": "集成测试项目",
            "statistics": {"total_holes": 5, "completed_holes": 0}
        }
        mock_hybrid_manager_class.return_value = mock_hybrid_manager
        
        # 创建集成管理器
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        
        # 设置回调函数
        progress_calls = []
        completion_calls = []
        error_calls = []
        
        def progress_callback(message, current, total):
            progress_calls.append((message, current, total))
        
        def completion_callback(project_id, summary):
            completion_calls.append((project_id, summary))
        
        def error_callback(error_message):
            error_calls.append(error_message)
        
        manager.set_progress_callback(progress_callback)
        manager.set_completion_callback(completion_callback)
        manager.set_error_callback(error_callback)
        
        # 执行集成加载
        success, project_id, hole_collection = manager.load_dxf_file_integrated(
            str(self.test_dxf), "集成测试项目"
        )
        
        # 验证结果
        self.assertTrue(success)
        self.assertEqual(project_id, "test_project_001")
        self.assertEqual(hole_collection, self.mock_hole_collection)
        
        # 验证回调调用
        self.assertEqual(len(progress_calls), 5)  # 5个进度步骤
        self.assertEqual(len(completion_calls), 1)
        self.assertEqual(len(error_calls), 0)
        
        # 验证进度步骤
        expected_steps = ["解析DXF文件", "准备项目数据", "创建项目", "同步数据", "完成"]
        actual_steps = [call[0] for call in progress_calls]
        self.assertEqual(actual_steps, expected_steps)
        
        # 验证完成回调
        completion_project_id, completion_summary = completion_calls[0]
        self.assertEqual(completion_project_id, "test_project_001")
        self.assertIn("project_name", completion_summary)
        
        # 验证混合管理器调用
        mock_hybrid_manager.create_project_from_dxf.assert_called_once()
        mock_hybrid_manager.ensure_data_consistency.assert_called_once_with("test_project_001")
        mock_hybrid_manager.get_project_summary.assert_called_once_with("test_project_001")
        
        # 验证当前状态
        self.assertEqual(manager.current_project_id, "test_project_001")
        self.assertEqual(manager.current_hole_collection, self.mock_hole_collection)
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_ui_integration_adapter_workflow(self, mock_dxf_integration_class):
        """测试UI集成适配器工作流"""
        # 设置模拟对象
        mock_dxf_integration = Mock()
        mock_dxf_integration.load_dxf_file_integrated.return_value = (
            True, "test_project_002", self.mock_hole_collection
        )
        mock_dxf_integration.get_current_project_summary.return_value = {
            "project_name": "UI集成测试",
            "dxf_file_path": str(self.test_dxf),
            "status": "active"
        }
        mock_dxf_integration.get_hole_for_realtime.return_value = {
            "basic_info": {
                "position": {"x": 10.0, "y": 20.0},
                "diameter": 8.865,
                "depth": 900.0
            },
            "status_info": {"current_status": "pending"},
            "database_info": {"measurement_count": 0},
            "historical_data_available": False
        }
        mock_dxf_integration.navigate_to_realtime_monitoring.return_value = True
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        # 创建UI适配器
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 设置UI回调
        ui_callbacks = {
            "progress": [],
            "status": [],
            "error": [],
            "completion": []
        }
        
        def progress_callback(message, current, total):
            ui_callbacks["progress"].append((message, current, total))
        
        def status_callback(message):
            ui_callbacks["status"].append(message)
        
        def error_callback(error_message):
            ui_callbacks["error"].append(error_message)
        
        def completion_callback(project_id, summary):
            ui_callbacks["completion"].append((project_id, summary))
        
        adapter.set_ui_callbacks(
            progress_callback=progress_callback,
            status_callback=status_callback,
            error_callback=error_callback,
            completion_callback=completion_callback
        )
        
        # 1. 加载DXF文件
        load_result = adapter.load_dxf_file(str(self.test_dxf), "UI集成测试")
        
        self.assertTrue(load_result["success"])
        self.assertEqual(load_result["project_id"], "test_project_002")
        self.assertEqual(load_result["hole_count"], 5)
        self.assertIn("project_summary", load_result)
        
        # 2. 获取孔位信息
        hole_info = adapter.get_hole_for_selection("H00001")
        
        self.assertIsNotNone(hole_info)
        self.assertEqual(hole_info["hole_id"], "H00001")
        self.assertEqual(hole_info["position"]["x"], 10.0)
        self.assertEqual(hole_info["status"], "pending")
        
        # 3. 导航到实时监控
        nav_result = adapter.navigate_to_realtime("H00001")
        
        self.assertTrue(nav_result["success"])
        self.assertEqual(nav_result["hole_id"], "H00001")
        self.assertIn("hole_data", nav_result)
        
        # 验证集成管理器调用
        mock_dxf_integration.load_dxf_file_integrated.assert_called_once_with(
            str(self.test_dxf), "UI集成测试"
        )
        mock_dxf_integration.get_hole_for_realtime.assert_called_with("H00001")
        mock_dxf_integration.navigate_to_realtime_monitoring.assert_called_once_with("H00001")
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_legacy_dxf_loader_mode_switching(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试向后兼容加载器模式切换"""
        # 设置模拟对象
        mock_dxf_parser = Mock()
        mock_dxf_parser.parse_file.return_value = self.mock_hole_collection
        mock_dxf_parser_class.return_value = mock_dxf_parser
        
        mock_ui_adapter = Mock()
        mock_ui_adapter.load_dxf_file.return_value = {
            "success": True,
            "hole_collection": self.mock_hole_collection
        }
        mock_ui_adapter.get_project_info.return_value = {
            "has_project": True,
            "project_id": "test_project_003"
        }
        mock_ui_adapter.navigate_to_realtime.return_value = {
            "success": True,
            "hole_id": "H00001"
        }
        mock_ui_adapter_class.return_value = mock_ui_adapter
        
        # 创建向后兼容加载器
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        
        # 1. 测试传统模式
        loader.set_mode("legacy")
        
        # 加载DXF文件
        result = loader.load_dxf_file(str(self.test_dxf))
        self.assertEqual(result, self.mock_hole_collection)
        
        # 获取项目信息（传统模式）
        project_info = loader.get_project_info()
        self.assertFalse(project_info["has_project"])
        self.assertEqual(project_info["mode"], "legacy")
        
        # 导航到实时监控（传统模式不支持）
        nav_result = loader.navigate_to_realtime("H00001")
        self.assertFalse(nav_result["success"])
        self.assertIn("传统模式不支持", nav_result["error"])
        
        # 2. 切换到集成模式
        loader.set_mode("integrated")
        
        # 加载DXF文件
        result = loader.load_dxf_file(str(self.test_dxf), "集成模式测试")
        self.assertEqual(result, self.mock_hole_collection)
        
        # 获取项目信息（集成模式）
        project_info = loader.get_project_info()
        self.assertTrue(project_info["has_project"])
        self.assertEqual(project_info["project_id"], "test_project_003")
        
        # 导航到实时监控（集成模式支持）
        nav_result = loader.navigate_to_realtime("H00001")
        self.assertTrue(nav_result["success"])
        self.assertEqual(nav_result["hole_id"], "H00001")
        
        # 验证调用
        mock_dxf_parser.parse_file.assert_called_once()  # 传统模式调用
        mock_ui_adapter.load_dxf_file.assert_called_once()  # 集成模式调用
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_error_handling_integration(self, mock_hybrid_manager_class, mock_dxf_parser_class):
        """测试错误处理集成"""
        # 设置模拟对象抛出异常
        mock_dxf_parser = Mock()
        mock_dxf_parser.parse_file.side_effect = Exception("DXF解析错误")
        mock_dxf_parser_class.return_value = mock_dxf_parser
        
        mock_hybrid_manager = Mock()
        mock_hybrid_manager_class.return_value = mock_hybrid_manager
        
        # 创建集成管理器
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        
        # 设置错误回调
        error_calls = []
        
        def error_callback(error_message):
            error_calls.append(error_message)
        
        manager.set_error_callback(error_callback)
        
        # 执行加载（应该失败）
        success, project_id, hole_collection = manager.load_dxf_file_integrated(str(self.test_dxf))
        
        # 验证错误处理
        self.assertFalse(success)
        self.assertIsNone(project_id)
        self.assertIsNone(hole_collection)
        self.assertEqual(len(error_calls), 1)
        self.assertIn("DXF集成加载失败", error_calls[0])
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_hole_position_search_integration(self, mock_hybrid_manager_class, mock_dxf_parser_class):
        """测试孔位位置搜索集成"""
        # 设置模拟对象
        mock_dxf_parser = Mock()
        mock_dxf_parser.parse_file.return_value = self.mock_hole_collection
        mock_dxf_parser_class.return_value = mock_dxf_parser
        
        mock_hybrid_manager = Mock()
        mock_hybrid_manager.create_project_from_dxf.return_value = ("test_project_004", "/path")
        mock_hybrid_manager.ensure_data_consistency.return_value = True
        mock_hybrid_manager.get_project_summary.return_value = {}
        mock_hybrid_manager_class.return_value = mock_hybrid_manager
        
        # 创建集成管理器
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        
        # 加载DXF文件
        success, _, _ = manager.load_dxf_file_integrated(str(self.test_dxf))
        self.assertTrue(success)
        
        # 测试位置搜索
        test_cases = [
            # (x, y, tolerance, expected_hole_id)
            (10.0, 20.0, 0.1, "H00001"),  # 精确匹配
            (20.5, 40.5, 1.0, "H00002"),  # 容差内匹配
            (30.0, 60.0, 0.1, "H00003"),  # 精确匹配
            (100.0, 200.0, 1.0, None),    # 超出范围
            (15.0, 25.0, 1.0, None),      # 超出容差
        ]
        
        for x, y, tolerance, expected in test_cases:
            result = manager.get_hole_by_position(x, y, tolerance)
            self.assertEqual(result, expected, 
                           f"位置搜索失败: ({x}, {y}) 容差{tolerance} 期望{expected} 实际{result}")
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_project_statistics_integration(self, mock_dxf_integration_class):
        """测试项目统计集成"""
        # 设置模拟对象
        mock_dxf_integration = Mock()
        mock_dxf_integration.load_dxf_file_integrated.return_value = (
            True, "test_project_005", self.mock_hole_collection
        )
        mock_dxf_integration.get_current_project_summary.return_value = {
            "project_name": "统计测试项目"
        }
        mock_dxf_integration.get_project_statistics.return_value = {
            "total_holes": 5,
            "completed_holes": 2,
            "pending_holes": 2,
            "error_holes": 1,
            "completion_rate": 40.0
        }
        mock_dxf_integration.get_current_hole_collection.return_value = self.mock_hole_collection
        mock_dxf_integration.get_hole_for_realtime.side_effect = [
            {"status": "completed", "measurement_count": 10},
            {"status": "completed", "measurement_count": 8},
            {"status": "pending", "measurement_count": 0},
            {"status": "pending", "measurement_count": 0},
            {"status": "error", "measurement_count": 0}
        ]
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        # 创建UI适配器
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 加载DXF文件
        load_result = adapter.load_dxf_file(str(self.test_dxf))
        self.assertTrue(load_result["success"])
        
        # 获取项目信息
        project_info = adapter.get_project_info()
        self.assertTrue(project_info["has_project"])
        
        # 验证统计信息
        statistics = project_info["statistics"]
        self.assertEqual(statistics["total_holes"], 5)
        self.assertEqual(statistics["completed_holes"], 2)
        self.assertEqual(statistics["pending_holes"], 2)
        self.assertEqual(statistics["error_holes"], 1)
        self.assertEqual(statistics["completion_rate"], 40.0)
        
        # 获取孔位列表
        hole_list = adapter.get_hole_list()
        self.assertEqual(len(hole_list), 5)
        
        # 验证孔位状态分布
        status_counts = {}
        for hole in hole_list:
            status = hole["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        self.assertEqual(status_counts.get("completed", 0), 2)
        self.assertEqual(status_counts.get("pending", 0), 2)
        self.assertEqual(status_counts.get("error", 0), 1)


if __name__ == '__main__':
    unittest.main()
