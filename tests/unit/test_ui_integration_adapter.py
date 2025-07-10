#!/usr/bin/env python3
"""
单元测试：UI集成适配器
Unit Tests: UI Integration Adapter
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aidcis2.integration.ui_integration_adapter import UIIntegrationAdapter
from aidcis2.models.hole_data import HoleData, HoleCollection, Position, HoleStatus


class TestUIIntegrationAdapter(unittest.TestCase):
    """UI集成适配器单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_ui_adapter_")
        self.test_db = os.path.join(self.temp_dir, "test.db")
        self.database_url = f"sqlite:///{self.test_db}"
        
        # 创建测试DXF文件
        self.test_dxf = Path(self.temp_dir) / "test.dxf"
        self.test_dxf.write_text("dummy dxf content")
        
        # 模拟孔位集合
        self.mock_hole_collection = self._create_mock_hole_collection()
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def _create_mock_hole_collection(self) -> HoleCollection:
        """创建模拟孔位集合"""
        holes = {}
        for i in range(1, 4):
            hole_id = f"H{i:05d}"
            hole_data = HoleData(
                hole_id=hole_id,
                position=Position(x=float(i * 10), y=float(i * 20)),
                diameter=8.865,
                status=HoleStatus.PENDING
            )
            holes[hole_id] = hole_data
        
        return HoleCollection(
            holes=holes,
            metadata={
                'source_file': str(self.test_dxf),
                'total_entities': 10,
                'total_arcs': 3
            }
        )
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_init(self, mock_dxf_integration_class):
        """测试初始化"""
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        self.assertIsNotNone(adapter.dxf_integration)
        self.assertIsNone(adapter.ui_progress_callback)
        self.assertIsNone(adapter.ui_status_callback)
        self.assertIsNone(adapter.ui_error_callback)
        self.assertIsNone(adapter.ui_completion_callback)
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_set_ui_callbacks(self, mock_dxf_integration_class):
        """测试设置UI回调函数"""
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        progress_callback = Mock()
        status_callback = Mock()
        error_callback = Mock()
        completion_callback = Mock()
        
        adapter.set_ui_callbacks(
            progress_callback=progress_callback,
            status_callback=status_callback,
            error_callback=error_callback,
            completion_callback=completion_callback
        )
        
        self.assertEqual(adapter.ui_progress_callback, progress_callback)
        self.assertEqual(adapter.ui_status_callback, status_callback)
        self.assertEqual(adapter.ui_error_callback, error_callback)
        self.assertEqual(adapter.ui_completion_callback, completion_callback)
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_load_dxf_file_success(self, mock_dxf_integration_class):
        """测试成功加载DXF文件"""
        # 设置模拟对象
        mock_dxf_integration = Mock()
        mock_dxf_integration.load_dxf_file_integrated.return_value = (
            True, "test_project_001", self.mock_hole_collection
        )
        mock_dxf_integration.get_current_project_summary.return_value = {
            "project_name": "测试项目",
            "status": "active"
        }
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 执行加载
        result = adapter.load_dxf_file(str(self.test_dxf), "测试项目")
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["project_id"], "test_project_001")
        self.assertEqual(result["hole_collection"], self.mock_hole_collection)
        self.assertEqual(result["hole_count"], 3)
        self.assertEqual(result["file_name"], "test.dxf")
        self.assertIn("project_summary", result)
        self.assertIn("message", result)
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_load_dxf_file_failure(self, mock_dxf_integration_class):
        """测试DXF文件加载失败"""
        # 设置模拟对象返回失败
        mock_dxf_integration = Mock()
        mock_dxf_integration.load_dxf_file_integrated.return_value = (False, None, None)
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 执行加载
        result = adapter.load_dxf_file(str(self.test_dxf))
        
        # 验证结果
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("message", result)
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_load_dxf_file_exception(self, mock_dxf_integration_class):
        """测试DXF文件加载异常"""
        # 设置模拟对象抛出异常
        mock_dxf_integration = Mock()
        mock_dxf_integration.load_dxf_file_integrated.side_effect = Exception("测试异常")
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 执行加载
        result = adapter.load_dxf_file(str(self.test_dxf))
        
        # 验证结果
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("测试异常", result["error"])
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_get_hole_for_selection_success(self, mock_dxf_integration_class):
        """测试成功获取孔位选择信息"""
        # 设置模拟对象
        mock_dxf_integration = Mock()
        mock_dxf_integration.get_hole_for_realtime.return_value = {
            "basic_info": {
                "position": {"x": 10.0, "y": 20.0},
                "diameter": 8.865,
                "depth": 900.0
            },
            "status_info": {
                "current_status": "pending"
            },
            "database_info": {
                "measurement_count": 5
            },
            "historical_data_available": True
        }
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 执行获取
        result = adapter.get_hole_for_selection("H00001")
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result["hole_id"], "H00001")
        self.assertEqual(result["position"]["x"], 10.0)
        self.assertEqual(result["diameter"], 8.865)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["measurement_count"], 5)
        self.assertTrue(result["has_historical_data"])
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_get_hole_for_selection_not_found(self, mock_dxf_integration_class):
        """测试获取不存在的孔位"""
        # 设置模拟对象返回None
        mock_dxf_integration = Mock()
        mock_dxf_integration.get_hole_for_realtime.return_value = None
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 执行获取
        result = adapter.get_hole_for_selection("INVALID_HOLE")
        
        # 验证结果
        self.assertIsNone(result)
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_navigate_to_realtime_success(self, mock_dxf_integration_class):
        """测试成功导航到实时监控"""
        # 设置模拟对象
        mock_dxf_integration = Mock()
        mock_dxf_integration.navigate_to_realtime_monitoring.return_value = True
        mock_dxf_integration.get_hole_for_realtime.return_value = {
            "basic_info": {"position": {"x": 10.0, "y": 20.0}}
        }
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 执行导航
        result = adapter.navigate_to_realtime("H00001")
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["hole_id"], "H00001")
        self.assertIn("hole_data", result)
        self.assertIn("message", result)
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_navigate_to_realtime_failure(self, mock_dxf_integration_class):
        """测试导航到实时监控失败"""
        # 设置模拟对象返回失败
        mock_dxf_integration = Mock()
        mock_dxf_integration.navigate_to_realtime_monitoring.return_value = False
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 执行导航
        result = adapter.navigate_to_realtime("H00001")
        
        # 验证结果
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("message", result)
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_get_project_info_with_project(self, mock_dxf_integration_class):
        """测试获取项目信息（有项目）"""
        # 设置模拟对象
        mock_dxf_integration = Mock()
        mock_dxf_integration.get_current_project_id.return_value = "test_project_001"
        mock_dxf_integration.get_current_project_summary.return_value = {
            "project_name": "测试项目",
            "dxf_file_path": "/path/to/test.dxf",
            "created_at": "2025-01-08T10:00:00",
            "status": "active"
        }
        mock_dxf_integration.get_project_statistics.return_value = {
            "total_holes": 10,
            "completed_holes": 5
        }
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 执行获取
        result = adapter.get_project_info()
        
        # 验证结果
        self.assertTrue(result["has_project"])
        self.assertEqual(result["project_id"], "test_project_001")
        self.assertEqual(result["project_name"], "测试项目")
        self.assertIn("statistics", result)
        self.assertIn("created_at", result)
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_get_project_info_no_project(self, mock_dxf_integration_class):
        """测试获取项目信息（无项目）"""
        # 设置模拟对象返回None
        mock_dxf_integration = Mock()
        mock_dxf_integration.get_current_project_id.return_value = None
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 执行获取
        result = adapter.get_project_info()
        
        # 验证结果
        self.assertFalse(result["has_project"])
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_find_hole_by_position(self, mock_dxf_integration_class):
        """测试根据位置查找孔位"""
        # 设置模拟对象
        mock_dxf_integration = Mock()
        mock_dxf_integration.get_hole_by_position.return_value = "H00001"
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 执行查找
        result = adapter.find_hole_by_position(10.0, 20.0, 1.0)
        
        # 验证结果
        self.assertEqual(result, "H00001")
        mock_dxf_integration.get_hole_by_position.assert_called_once_with(10.0, 20.0, 1.0)
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_update_hole_status_ui_success(self, mock_dxf_integration_class):
        """测试成功更新孔位状态"""
        # 设置模拟对象
        mock_dxf_integration = Mock()
        mock_dxf_integration.update_hole_status.return_value = True
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 设置状态回调
        status_callback = Mock()
        adapter.set_ui_callbacks(status_callback=status_callback)
        
        # 执行更新
        result = adapter.update_hole_status_ui("H00001", "completed", "测试完成")
        
        # 验证结果
        self.assertTrue(result)
        mock_dxf_integration.update_hole_status.assert_called_once_with("H00001", "completed", "测试完成")
        status_callback.assert_called_once()
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_get_hole_list(self, mock_dxf_integration_class):
        """测试获取孔位列表"""
        # 设置模拟对象
        mock_dxf_integration = Mock()
        mock_dxf_integration.get_current_hole_collection.return_value = self.mock_hole_collection
        mock_dxf_integration.get_hole_for_realtime.side_effect = [
            {"status": "pending", "measurement_count": 0},
            {"status": "in_progress", "measurement_count": 3},
            {"status": "completed", "measurement_count": 10}
        ]
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 执行获取
        result = adapter.get_hole_list()
        
        # 验证结果
        self.assertEqual(len(result), 3)
        
        # 验证排序（按hole_id）
        hole_ids = [hole["hole_id"] for hole in result]
        self.assertEqual(hole_ids, sorted(hole_ids))
        
        # 验证第一个孔位信息
        first_hole = result[0]
        self.assertEqual(first_hole["hole_id"], "H00001")
        self.assertEqual(first_hole["position"]["x"], 10.0)
        self.assertEqual(first_hole["diameter"], 8.865)
        self.assertEqual(first_hole["status"], "pending")
        self.assertEqual(first_hole["measurement_count"], 0)
    
    @patch('aidcis2.integration.ui_integration_adapter.DXFIntegrationManager')
    def test_cleanup(self, mock_dxf_integration_class):
        """测试清理功能"""
        # 设置模拟对象
        mock_dxf_integration = Mock()
        mock_dxf_integration_class.return_value = mock_dxf_integration
        
        adapter = UIIntegrationAdapter(self.temp_dir, self.database_url)
        
        # 执行清理
        adapter.cleanup()
        
        # 验证调用
        mock_dxf_integration.cleanup.assert_called_once()


if __name__ == '__main__':
    unittest.main()
