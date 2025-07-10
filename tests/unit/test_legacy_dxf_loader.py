#!/usr/bin/env python3
"""
单元测试：向后兼容DXF加载器
Unit Tests: Legacy DXF Loader
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from aidcis2.integration.legacy_dxf_loader import LegacyDXFLoader
from aidcis2.models.hole_data import HoleData, HoleCollection, Position, HoleStatus


class TestLegacyDXFLoader(unittest.TestCase):
    """向后兼容DXF加载器单元测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp(prefix="test_legacy_loader_")
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
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_init(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试初始化"""
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        
        self.assertIsNotNone(loader.dxf_parser)
        self.assertIsNotNone(loader.ui_adapter)
        self.assertEqual(loader.mode, "integrated")  # 默认集成模式
        self.assertIsNone(loader.current_hole_collection)
        self.assertIsNone(loader.current_file_path)
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_set_mode(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试设置模式"""
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        
        # 测试设置为传统模式
        loader.set_mode("legacy")
        self.assertEqual(loader.mode, "legacy")
        
        # 测试设置为集成模式
        loader.set_mode("integrated")
        self.assertEqual(loader.mode, "integrated")
        
        # 测试无效模式
        loader.set_mode("invalid")
        self.assertEqual(loader.mode, "integrated")  # 应该保持不变
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_load_dxf_file_not_exists(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试加载不存在的文件"""
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        
        with self.assertRaises(FileNotFoundError):
            loader.load_dxf_file("nonexistent.dxf")
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_load_dxf_file_empty(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试加载空文件"""
        # 创建空文件
        empty_file = Path(self.temp_dir) / "empty.dxf"
        empty_file.touch()
        
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        
        with self.assertRaises(ValueError):
            loader.load_dxf_file(str(empty_file))
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_load_legacy_mode_success(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试传统模式成功加载"""
        # 设置模拟对象
        mock_dxf_parser = Mock()
        mock_dxf_parser.parse_file.return_value = self.mock_hole_collection
        mock_dxf_parser_class.return_value = mock_dxf_parser
        
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        loader.set_mode("legacy")
        
        # 执行加载
        result = loader.load_dxf_file(str(self.test_dxf))
        
        # 验证结果
        self.assertEqual(result, self.mock_hole_collection)
        self.assertEqual(loader.current_hole_collection, self.mock_hole_collection)
        self.assertEqual(loader.current_file_path, str(self.test_dxf))
        
        # 验证调用
        mock_dxf_parser.parse_file.assert_called_once_with(str(self.test_dxf))
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_load_legacy_mode_no_holes(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试传统模式加载无孔位文件"""
        # 设置模拟对象返回空集合
        empty_collection = HoleCollection(holes={}, metadata={})
        mock_dxf_parser = Mock()
        mock_dxf_parser.parse_file.return_value = empty_collection
        mock_dxf_parser_class.return_value = mock_dxf_parser
        
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        loader.set_mode("legacy")
        
        # 执行加载（应该成功，但有警告）
        result = loader.load_dxf_file(str(self.test_dxf))
        
        # 验证结果
        self.assertEqual(result, empty_collection)
        self.assertEqual(len(result), 0)
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_load_legacy_mode_parse_failure(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试传统模式解析失败"""
        # 设置模拟对象返回None
        mock_dxf_parser = Mock()
        mock_dxf_parser.parse_file.return_value = None
        mock_dxf_parser_class.return_value = mock_dxf_parser
        
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        loader.set_mode("legacy")
        
        # 执行加载
        with self.assertRaises(ValueError):
            loader.load_dxf_file(str(self.test_dxf))
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_load_integrated_mode_success(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试集成模式成功加载"""
        # 设置模拟对象
        mock_ui_adapter = Mock()
        mock_ui_adapter.load_dxf_file.return_value = {
            "success": True,
            "hole_collection": self.mock_hole_collection
        }
        mock_ui_adapter_class.return_value = mock_ui_adapter
        
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        loader.set_mode("integrated")
        
        # 执行加载
        result = loader.load_dxf_file(str(self.test_dxf), "测试项目")
        
        # 验证结果
        self.assertEqual(result, self.mock_hole_collection)
        self.assertEqual(loader.current_hole_collection, self.mock_hole_collection)
        self.assertEqual(loader.current_file_path, str(self.test_dxf))
        
        # 验证调用
        mock_ui_adapter.load_dxf_file.assert_called_once_with(str(self.test_dxf), "测试项目")
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_load_integrated_mode_failure(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试集成模式加载失败"""
        # 设置模拟对象返回失败
        mock_ui_adapter = Mock()
        mock_ui_adapter.load_dxf_file.return_value = {
            "success": False,
            "error": "加载失败"
        }
        mock_ui_adapter_class.return_value = mock_ui_adapter
        
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        loader.set_mode("integrated")
        
        # 执行加载
        with self.assertRaises(ValueError):
            loader.load_dxf_file(str(self.test_dxf))
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_get_project_info_legacy_mode(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试传统模式获取项目信息"""
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        loader.set_mode("legacy")
        loader.current_file_path = str(self.test_dxf)
        loader.current_hole_collection = self.mock_hole_collection
        
        # 执行获取
        result = loader.get_project_info()
        
        # 验证结果
        self.assertFalse(result["has_project"])
        self.assertEqual(result["mode"], "legacy")
        self.assertEqual(result["file_path"], str(self.test_dxf))
        self.assertEqual(result["hole_count"], 3)
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_get_project_info_integrated_mode(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试集成模式获取项目信息"""
        # 设置模拟对象
        mock_ui_adapter = Mock()
        mock_ui_adapter.get_project_info.return_value = {
            "has_project": True,
            "project_id": "test_project_001"
        }
        mock_ui_adapter_class.return_value = mock_ui_adapter
        
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        loader.set_mode("integrated")
        
        # 执行获取
        result = loader.get_project_info()
        
        # 验证结果
        self.assertTrue(result["has_project"])
        self.assertEqual(result["project_id"], "test_project_001")
        
        # 验证调用
        mock_ui_adapter.get_project_info.assert_called_once()
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_navigate_to_realtime_legacy_mode(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试传统模式导航到实时监控"""
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        loader.set_mode("legacy")
        
        # 执行导航
        result = loader.navigate_to_realtime("H00001")
        
        # 验证结果
        self.assertFalse(result["success"])
        self.assertIn("传统模式不支持", result["error"])
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_navigate_to_realtime_integrated_mode(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试集成模式导航到实时监控"""
        # 设置模拟对象
        mock_ui_adapter = Mock()
        mock_ui_adapter.navigate_to_realtime.return_value = {
            "success": True,
            "hole_id": "H00001"
        }
        mock_ui_adapter_class.return_value = mock_ui_adapter
        
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        loader.set_mode("integrated")
        
        # 执行导航
        result = loader.navigate_to_realtime("H00001")
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["hole_id"], "H00001")
        
        # 验证调用
        mock_ui_adapter.navigate_to_realtime.assert_called_once_with("H00001")
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_find_hole_by_position_legacy_mode(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试传统模式根据位置查找孔位"""
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        loader.set_mode("legacy")
        loader.current_hole_collection = self.mock_hole_collection
        
        # 执行查找
        result = loader.find_hole_by_position(10.0, 20.0, 1.0)
        
        # 验证结果
        self.assertEqual(result, "H00001")
        
        # 测试超出容差
        result = loader.find_hole_by_position(15.0, 25.0, 1.0)
        self.assertIsNone(result)
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_get_hole_info_legacy_mode(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试传统模式获取孔位信息"""
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        loader.set_mode("legacy")
        loader.current_hole_collection = self.mock_hole_collection
        
        # 执行获取
        result = loader.get_hole_info("H00001")
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result["hole_id"], "H00001")
        self.assertEqual(result["position"]["x"], 10.0)
        self.assertEqual(result["diameter"], 8.865)
        self.assertEqual(result["mode"], "legacy")
        
        # 测试不存在的孔位
        result = loader.get_hole_info("INVALID")
        self.assertIsNone(result)
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_get_hole_list_legacy_mode(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试传统模式获取孔位列表"""
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        loader.set_mode("legacy")
        loader.current_hole_collection = self.mock_hole_collection
        
        # 执行获取
        result = loader.get_hole_list()
        
        # 验证结果
        self.assertEqual(len(result), 3)
        
        # 验证排序
        hole_ids = [hole["hole_id"] for hole in result]
        self.assertEqual(hole_ids, sorted(hole_ids))
        
        # 验证第一个孔位
        first_hole = result[0]
        self.assertEqual(first_hole["hole_id"], "H00001")
        self.assertEqual(first_hole["measurement_count"], 0)  # 传统模式无测量数据
    
    @patch('aidcis2.integration.legacy_dxf_loader.DXFParser')
    @patch('aidcis2.integration.legacy_dxf_loader.UIIntegrationAdapter')
    def test_cleanup(self, mock_ui_adapter_class, mock_dxf_parser_class):
        """测试清理功能"""
        # 设置模拟对象
        mock_ui_adapter = Mock()
        mock_ui_adapter_class.return_value = mock_ui_adapter
        
        loader = LegacyDXFLoader(self.temp_dir, self.database_url)
        loader.current_hole_collection = self.mock_hole_collection
        loader.current_file_path = str(self.test_dxf)
        
        # 执行清理
        loader.cleanup()
        
        # 验证清理结果
        self.assertIsNone(loader.current_hole_collection)
        self.assertIsNone(loader.current_file_path)
        
        # 验证集成模式下的清理调用
        loader.set_mode("integrated")
        loader.cleanup()
        mock_ui_adapter.cleanup.assert_called_once()


if __name__ == '__main__':
    unittest.main()
