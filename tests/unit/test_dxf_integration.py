#!/usr/bin/env python3
"""
单元测试：DXF集成
Unit Tests: DXF Integration
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aidcis2.integration.dxf_integration_manager import DXFIntegrationManager
from aidcis2.models.hole_data import HoleData, HoleCollection, Position, HoleStatus


class TestDXFIntegrationManager(unittest.TestCase):
    """DXF集成管理器单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_dxf_integration_")
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
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_init(self, mock_hybrid_manager, mock_dxf_parser):
        """测试初始化"""
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        
        self.assertIsNotNone(manager.dxf_parser)
        self.assertIsNotNone(manager.hybrid_manager)
        self.assertIsNotNone(manager.realtime_bridge)
        self.assertIsNone(manager.current_project_id)
        self.assertIsNone(manager.current_hole_collection)
    
    def test_set_callbacks(self):
        """测试设置回调函数"""
        with patch('aidcis2.integration.dxf_integration_manager.DXFParser'), \
             patch('aidcis2.integration.dxf_integration_manager.HybridDataManager'):
            
            manager = DXFIntegrationManager(self.temp_dir, self.database_url)
            
            progress_callback = Mock()
            completion_callback = Mock()
            error_callback = Mock()
            
            manager.set_progress_callback(progress_callback)
            manager.set_completion_callback(completion_callback)
            manager.set_error_callback(error_callback)
            
            self.assertEqual(manager.progress_callback, progress_callback)
            self.assertEqual(manager.completion_callback, completion_callback)
            self.assertEqual(manager.error_callback, error_callback)
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_validate_file_success(self, mock_hybrid_manager, mock_dxf_parser):
        """测试文件验证成功"""
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        
        # 测试有效文件
        result = manager._validate_file(str(self.test_dxf))
        self.assertTrue(result)
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_validate_file_not_exists(self, mock_hybrid_manager, mock_dxf_parser):
        """测试文件不存在"""
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        
        error_callback = Mock()
        manager.set_error_callback(error_callback)
        
        # 测试不存在的文件
        result = manager._validate_file("nonexistent.dxf")
        self.assertFalse(result)
        error_callback.assert_called_once()
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_validate_file_empty(self, mock_hybrid_manager, mock_dxf_parser):
        """测试空文件"""
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        
        # 创建空文件
        empty_file = Path(self.temp_dir) / "empty.dxf"
        empty_file.touch()
        
        error_callback = Mock()
        manager.set_error_callback(error_callback)
        
        result = manager._validate_file(str(empty_file))
        self.assertFalse(result)
        error_callback.assert_called_once()
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_validate_file_wrong_extension(self, mock_hybrid_manager, mock_dxf_parser):
        """测试错误的文件扩展名"""
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        
        # 创建非DXF文件
        wrong_file = Path(self.temp_dir) / "test.txt"
        wrong_file.write_text("not a dxf file")
        
        error_callback = Mock()
        manager.set_error_callback(error_callback)
        
        result = manager._validate_file(str(wrong_file))
        self.assertFalse(result)
        error_callback.assert_called_once()
    
    def test_convert_hole_collection_to_data(self):
        """测试孔位集合转换"""
        with patch('aidcis2.integration.dxf_integration_manager.DXFParser'), \
             patch('aidcis2.integration.dxf_integration_manager.HybridDataManager'):
            
            manager = DXFIntegrationManager(self.temp_dir, self.database_url)
            
            holes_data = manager._convert_hole_collection_to_data(self.mock_hole_collection)
            
            self.assertEqual(len(holes_data), 3)
            
            for i, hole_dict in enumerate(holes_data):
                expected_hole_id = f"H{i+1:05d}"
                self.assertEqual(hole_dict["hole_id"], expected_hole_id)
                self.assertEqual(hole_dict["position"]["x"], float((i+1) * 10))
                self.assertEqual(hole_dict["position"]["y"], float((i+1) * 20))
                self.assertEqual(hole_dict["diameter"], 8.865)
                self.assertEqual(hole_dict["depth"], 900.0)
                self.assertEqual(hole_dict["tolerance"], 0.1)
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_load_dxf_file_integrated_success(self, mock_hybrid_manager_class, mock_dxf_parser_class):
        """测试成功的集成DXF加载"""
        # 设置模拟对象
        mock_dxf_parser = Mock()
        mock_dxf_parser.parse_file.return_value = self.mock_hole_collection
        mock_dxf_parser_class.return_value = mock_dxf_parser
        
        mock_hybrid_manager = Mock()
        mock_hybrid_manager.create_project_from_dxf.return_value = ("test_project_001", "/path/to/project")
        mock_hybrid_manager.ensure_data_consistency.return_value = True
        mock_hybrid_manager.get_project_summary.return_value = {"project_name": "测试项目"}
        mock_hybrid_manager_class.return_value = mock_hybrid_manager
        
        # 创建管理器
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        
        # 设置回调
        progress_callback = Mock()
        completion_callback = Mock()
        manager.set_progress_callback(progress_callback)
        manager.set_completion_callback(completion_callback)
        
        # 执行加载
        success, project_id, hole_collection = manager.load_dxf_file_integrated(str(self.test_dxf))
        
        # 验证结果
        self.assertTrue(success)
        self.assertEqual(project_id, "test_project_001")
        self.assertEqual(hole_collection, self.mock_hole_collection)
        self.assertEqual(manager.current_project_id, "test_project_001")
        self.assertEqual(manager.current_hole_collection, self.mock_hole_collection)
        
        # 验证回调调用
        self.assertEqual(progress_callback.call_count, 5)  # 5个进度步骤
        completion_callback.assert_called_once()
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_load_dxf_file_integrated_no_holes(self, mock_hybrid_manager_class, mock_dxf_parser_class):
        """测试DXF文件无孔位的情况"""
        # 设置模拟对象返回空孔位集合
        empty_collection = HoleCollection(holes={}, metadata={})
        
        mock_dxf_parser = Mock()
        mock_dxf_parser.parse_file.return_value = empty_collection
        mock_dxf_parser_class.return_value = mock_dxf_parser
        
        mock_hybrid_manager = Mock()
        mock_hybrid_manager_class.return_value = mock_hybrid_manager
        
        # 创建管理器
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        
        error_callback = Mock()
        manager.set_error_callback(error_callback)
        
        # 执行加载
        success, project_id, hole_collection = manager.load_dxf_file_integrated(str(self.test_dxf))
        
        # 验证结果
        self.assertFalse(success)
        self.assertIsNone(project_id)
        self.assertIsNone(hole_collection)
        error_callback.assert_called_once()
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_load_dxf_file_integrated_project_creation_failed(self, mock_hybrid_manager_class, mock_dxf_parser_class):
        """测试项目创建失败的情况"""
        # 设置模拟对象
        mock_dxf_parser = Mock()
        mock_dxf_parser.parse_file.return_value = self.mock_hole_collection
        mock_dxf_parser_class.return_value = mock_dxf_parser
        
        mock_hybrid_manager = Mock()
        mock_hybrid_manager.create_project_from_dxf.return_value = (None, None)  # 创建失败
        mock_hybrid_manager_class.return_value = mock_hybrid_manager
        
        # 创建管理器
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        
        error_callback = Mock()
        manager.set_error_callback(error_callback)
        
        # 执行加载
        success, project_id, hole_collection = manager.load_dxf_file_integrated(str(self.test_dxf))
        
        # 验证结果
        self.assertFalse(success)
        self.assertIsNone(project_id)
        self.assertIsNone(hole_collection)
        error_callback.assert_called_once()
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_get_hole_by_position(self, mock_hybrid_manager_class, mock_dxf_parser_class):
        """测试根据位置查找孔位"""
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        manager.current_hole_collection = self.mock_hole_collection
        
        # 测试精确匹配
        hole_id = manager.get_hole_by_position(10.0, 20.0, 0.1)
        self.assertEqual(hole_id, "H00001")
        
        # 测试容差内匹配
        hole_id = manager.get_hole_by_position(10.5, 20.5, 1.0)
        self.assertEqual(hole_id, "H00001")
        
        # 测试超出容差
        hole_id = manager.get_hole_by_position(15.0, 25.0, 1.0)
        self.assertIsNone(hole_id)
        
        # 测试无孔位集合
        manager.current_hole_collection = None
        hole_id = manager.get_hole_by_position(10.0, 20.0, 1.0)
        self.assertIsNone(hole_id)
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_get_project_statistics_no_project(self, mock_hybrid_manager_class, mock_dxf_parser_class):
        """测试无项目时的统计信息"""
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        
        stats = manager.get_project_statistics()
        
        expected_stats = {
            "total_holes": 0,
            "completed_holes": 0,
            "pending_holes": 0,
            "error_holes": 0,
            "completion_rate": 0.0
        }
        
        self.assertEqual(stats, expected_stats)
    
    @patch('aidcis2.integration.dxf_integration_manager.DXFParser')
    @patch('aidcis2.integration.dxf_integration_manager.HybridDataManager')
    def test_cleanup(self, mock_hybrid_manager_class, mock_dxf_parser_class):
        """测试清理功能"""
        manager = DXFIntegrationManager(self.temp_dir, self.database_url)
        manager.current_project_id = "test_project"
        manager.current_hole_collection = self.mock_hole_collection
        
        manager.cleanup()
        
        self.assertIsNone(manager.current_project_id)
        self.assertIsNone(manager.current_hole_collection)


if __name__ == '__main__':
    unittest.main()
