"""
数据路径管理器单元测试
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# 添加src目录到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.data_path_manager import DataPathManager, PathInfo


class TestDataPathManager:
    """数据路径管理器测试类"""
    
    @pytest.fixture
    def temp_data_root(self):
        """创建临时数据根目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def path_manager(self, temp_data_root):
        """创建路径管理器实例"""
        return DataPathManager(temp_data_root)
    
    def test_initialization(self, temp_data_root):
        """测试路径管理器初始化"""
        manager = DataPathManager(temp_data_root)
        
        # 验证数据根目录设置正确
        assert str(manager.data_root) == temp_data_root
        
        # 验证基本目录已创建
        assert os.path.exists(temp_data_root)
        assert os.path.exists(os.path.join(temp_data_root, "Products"))
    
    def test_get_product_paths(self, path_manager):
        """测试产品路径生成"""
        product_id = "TP-001"
        
        # 测试基本路径
        product_path = path_manager.get_product_path(product_id)
        expected_path = str(path_manager.data_root / "Products" / product_id)
        assert product_path == expected_path
        
        # 测试DXF目录路径
        dxf_dir = path_manager.get_product_dxf_dir(product_id)
        expected_dxf_dir = str(path_manager.data_root / "Products" / product_id / "dxf")
        assert dxf_dir == expected_dxf_dir
        
        # 测试产品信息文件路径
        info_path = path_manager.get_product_info_path(product_id)
        expected_info_path = str(path_manager.data_root / "Products" / product_id / "product_info.json")
        assert info_path == expected_info_path
    
    def test_get_inspection_paths(self, path_manager):
        """测试检测批次路径生成"""
        product_id = "TP-001"
        batch_id = "20250113_142530_123456"
        
        # 测试检测目录路径
        inspections_dir = path_manager.get_inspections_dir(product_id)
        expected_dir = str(path_manager.data_root / "Products" / product_id / "Inspections")
        assert inspections_dir == expected_dir
        
        # 测试批次路径
        batch_path = path_manager.get_inspection_batch_path(product_id, batch_id)
        expected_batch_path = str(path_manager.data_root / "Products" / product_id / "Inspections" / batch_id)
        assert batch_path == expected_batch_path
        
        # 测试检测信息文件路径
        info_path = path_manager.get_inspection_info_path(product_id, batch_id)
        expected_info_path = str(path_manager.data_root / "Products" / product_id / "Inspections" / batch_id / "inspection_info.json")
        assert info_path == expected_info_path
    
    def test_get_hole_paths(self, path_manager):
        """测试孔位路径生成"""
        product_id = "TP-001"
        batch_id = "20250113_142530_123456"
        hole_id = "H00001"
        
        # 测试孔位目录路径
        hole_path = path_manager.get_hole_path(product_id, batch_id, hole_id)
        expected_path = str(path_manager.data_root / "Products" / product_id / "Inspections" / batch_id / "Holes" / hole_id)
        assert hole_path == expected_path
        
        # 测试BISDM目录路径
        bisdm_path = path_manager.get_hole_bisdm_dir(product_id, batch_id, hole_id)
        expected_bisdm = str(path_manager.data_root / "Products" / product_id / "Inspections" / batch_id / "Holes" / hole_id / "BISDM")
        assert bisdm_path == expected_bisdm
        
        # 测试CCIDM目录路径
        ccidm_path = path_manager.get_hole_ccidm_dir(product_id, batch_id, hole_id)
        expected_ccidm = str(path_manager.data_root / "Products" / product_id / "Inspections" / batch_id / "Holes" / hole_id / "CCIDM")
        assert ccidm_path == expected_ccidm
        
        # 测试全景图路径
        panorama_path = path_manager.get_hole_panorama_path(product_id, batch_id, hole_id)
        expected_panorama = str(path_manager.data_root / "Products" / product_id / "Inspections" / batch_id / "Holes" / hole_id / "BISDM" / "panorama.png")
        assert panorama_path == expected_panorama
    
    def test_create_product_structure(self, path_manager):
        """测试产品目录结构创建"""
        product_id = "TP-001"
        
        # 创建目录结构
        paths = path_manager.create_product_structure(product_id)
        
        # 验证返回的路径
        assert "product_dir" in paths
        assert "dxf_dir" in paths
        assert "inspections_dir" in paths
        
        # 验证目录已创建
        assert os.path.exists(paths["product_dir"])
        assert os.path.exists(paths["dxf_dir"])
        assert os.path.exists(paths["inspections_dir"])
        
        # 验证目录结构正确
        expected_product_path = path_manager.get_product_path(product_id)
        assert paths["product_dir"] == expected_product_path
    
    def test_create_inspection_structure(self, path_manager):
        """测试检测批次目录结构创建"""
        product_id = "TP-001"
        batch_id = "20250113_142530_123456"
        
        # 先创建产品结构
        path_manager.create_product_structure(product_id)
        
        # 创建检测结构
        paths = path_manager.create_inspection_structure(product_id, batch_id)
        
        # 验证返回的路径
        assert "batch_dir" in paths
        assert "holes_dir" in paths
        
        # 验证目录已创建
        assert os.path.exists(paths["batch_dir"])
        assert os.path.exists(paths["holes_dir"])
    
    def test_create_hole_structure(self, path_manager):
        """测试孔位目录结构创建"""
        product_id = "TP-001"
        batch_id = "20250113_142530_123456"
        hole_id = "H00001"
        
        # 先创建上级结构
        path_manager.create_product_structure(product_id)
        path_manager.create_inspection_structure(product_id, batch_id)
        
        # 创建孔位结构
        paths = path_manager.create_hole_structure(product_id, batch_id, hole_id)
        
        # 验证返回的路径
        assert "hole_dir" in paths
        assert "bisdm_dir" in paths
        assert "bisdm_result_dir" in paths
        assert "ccidm_dir" in paths
        
        # 验证目录已创建
        for path in paths.values():
            assert os.path.exists(path)
    
    def test_get_path_info(self, path_manager):
        """测试路径信息查询"""
        product_id = "TP-001"
        
        # 测试不存在的路径
        nonexistent_path = path_manager.get_product_path(product_id)
        info = path_manager.get_path_info(nonexistent_path)
        
        assert isinstance(info, PathInfo)
        assert info.path == nonexistent_path
        assert not info.exists
        assert info.size == 0
        assert info.created_at is None
        
        # 创建目录并测试
        path_manager.create_product_structure(product_id)
        info = path_manager.get_path_info(nonexistent_path)
        
        assert info.exists
        assert info.size >= 0
        assert info.created_at is not None
    
    def test_list_products(self, path_manager):
        """测试产品列表查询"""
        # 初始应该为空
        products = path_manager.list_products()
        assert products == []
        
        # 创建几个产品
        product_ids = ["TP-001", "TP-002", "TP-003"]
        for product_id in product_ids:
            path_manager.create_product_structure(product_id)
        
        # 验证产品列表
        products = path_manager.list_products()
        assert set(products) == set(product_ids)
    
    def test_list_inspection_batches(self, path_manager):
        """测试检测批次列表查询"""
        product_id = "TP-001"
        
        # 产品不存在时应返回空列表
        batches = path_manager.list_inspection_batches(product_id)
        assert batches == []
        
        # 创建产品和批次
        path_manager.create_product_structure(product_id)
        batch_ids = ["20250113_142530", "20250113_143000", "20250113_143500"]
        for batch_id in batch_ids:
            path_manager.create_inspection_structure(product_id, batch_id)
        
        # 验证批次列表
        batches = path_manager.list_inspection_batches(product_id)
        assert set(batches) == set(batch_ids)
    
    def test_list_holes(self, path_manager):
        """测试孔位列表查询"""
        product_id = "TP-001"
        batch_id = "20250113_142530_123456"
        
        # 批次不存在时应返回空列表
        holes = path_manager.list_holes(product_id, batch_id)
        assert holes == []
        
        # 创建结构和孔位
        path_manager.create_product_structure(product_id)
        path_manager.create_inspection_structure(product_id, batch_id)
        
        hole_ids = ["H00001", "H00002", "H00003"]
        for hole_id in hole_ids:
            path_manager.create_hole_structure(product_id, batch_id, hole_id)
        
        # 验证孔位列表
        holes = path_manager.list_holes(product_id, batch_id)
        assert set(holes) == set(hole_ids)
    
    def test_legacy_path_compatibility(self, path_manager):
        """测试遗留路径兼容性"""
        hole_id = "H00001"
        
        # 测试遗留路径生成
        legacy_path = path_manager.get_legacy_hole_path(hole_id)
        expected_legacy = str(path_manager.data_root / hole_id)
        assert legacy_path == expected_legacy
        
        # 测试遗留BISDM路径
        legacy_bisdm = path_manager.get_legacy_bisdm_path(hole_id)
        expected_bisdm = str(path_manager.data_root / hole_id / "BISDM")
        assert legacy_bisdm == expected_bisdm
        
        # 测试遗留CCIDM路径
        legacy_ccidm = path_manager.get_legacy_ccidm_path(hole_id)
        expected_ccidm = str(path_manager.data_root / hole_id / "CCIDM")
        assert legacy_ccidm == expected_ccidm
    
    def test_generate_batch_id(self, path_manager):
        """测试批次ID生成"""
        batch_id = path_manager.generate_batch_id()
        
        # 验证格式: YYYYMMDD_HHMMSS_microsecond_random
        import re
        pattern = r'^\d{8}_\d{6}_\d{3}\d{3}$'
        assert re.match(pattern, batch_id), f"批次ID格式不正确: {batch_id}"
        
        # 测试连续生成的ID不重复
        batch_id2 = path_manager.generate_batch_id()
        assert batch_id != batch_id2, "连续生成的批次ID应该不同"
    
    def test_is_valid_product_id(self, path_manager):
        """测试产品ID验证"""
        # 有效的产品ID
        valid_ids = ["TP-001", "Product_123", "test-product"]
        for product_id in valid_ids:
            assert path_manager.is_valid_product_id(product_id)
        
        # 无效的产品ID
        invalid_ids = ["", "TP/001", "TP\\001", "TP:001", "TP*001", "TP?001", 'TP"001', "TP<001", "TP>001", "TP|001"]
        for product_id in invalid_ids:
            assert not path_manager.is_valid_product_id(product_id)
    
    def test_cleanup_empty_directories(self, path_manager):
        """测试空目录清理"""
        # 创建一些嵌套的空目录
        test_dirs = [
            path_manager.data_root / "empty1",
            path_manager.data_root / "empty2" / "nested",
            path_manager.data_root / "nonempty"
        ]
        
        for test_dir in test_dirs:
            test_dir.mkdir(parents=True, exist_ok=True)
        
        # 在非空目录中创建文件
        (test_dirs[2] / "file.txt").touch()
        
        # 执行清理
        path_manager.cleanup_empty_directories()
        
        # 验证空目录被删除，非空目录保留
        assert not test_dirs[0].exists()
        assert not test_dirs[1].exists()
        assert not test_dirs[1].parent.exists()  # empty2目录也应该被删除
        assert test_dirs[2].exists()  # 非空目录保留
    
    @patch('shutil.copytree')
    def test_migrate_legacy_data_success(self, mock_copytree, path_manager, temp_data_root):
        """测试遗留数据迁移成功情况"""
        hole_id = "H00001"
        product_id = "TP-001"
        batch_id = "20250113_142530_123456"
        
        # 创建遗留数据目录
        legacy_path = Path(temp_data_root) / hole_id
        legacy_bisdm = legacy_path / "BISDM"
        legacy_ccidm = legacy_path / "CCIDM"
        
        legacy_path.mkdir()
        legacy_bisdm.mkdir()
        legacy_ccidm.mkdir()
        
        # 执行迁移
        result = path_manager.migrate_legacy_data(hole_id, product_id, batch_id)
        
        # 验证结果
        assert result is True
        assert mock_copytree.call_count == 2  # BISDM和CCIDM各调用一次
    
    def test_migrate_legacy_data_no_source(self, path_manager):
        """测试遗留数据迁移 - 源不存在"""
        hole_id = "H00001"
        product_id = "TP-001"
        batch_id = "20250113_142530_123456"
        
        # 不创建遗留数据，直接迁移
        result = path_manager.migrate_legacy_data(hole_id, product_id, batch_id)
        
        # 验证结果
        assert result is False


class TestDataPathManagerIntegration:
    """数据路径管理器集成测试"""
    
    @pytest.fixture
    def temp_data_root(self):
        """创建临时数据根目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_complete_workflow(self, temp_data_root):
        """测试完整的数据管理工作流"""
        manager = DataPathManager(temp_data_root)
        
        # 1. 创建产品
        product_id = "TP-001"
        product_paths = manager.create_product_structure(product_id)
        
        # 2. 创建检测批次
        batch_id = "20250113_142530_123456"
        batch_paths = manager.create_inspection_structure(product_id, batch_id)
        
        # 3. 创建孔位
        hole_ids = ["H00001", "H00002", "H00003"]
        for hole_id in hole_ids:
            manager.create_hole_structure(product_id, batch_id, hole_id)
        
        # 4. 验证完整的目录结构
        expected_structure = [
            f"Products/{product_id}",
            f"Products/{product_id}/dxf",
            f"Products/{product_id}/Inspections",
            f"Products/{product_id}/Inspections/{batch_id}",
            f"Products/{product_id}/Inspections/{batch_id}/Holes",
        ]
        
        for hole_id in hole_ids:
            expected_structure.extend([
                f"Products/{product_id}/Inspections/{batch_id}/Holes/{hole_id}",
                f"Products/{product_id}/Inspections/{batch_id}/Holes/{hole_id}/BISDM",
                f"Products/{product_id}/Inspections/{batch_id}/Holes/{hole_id}/BISDM/result",
                f"Products/{product_id}/Inspections/{batch_id}/Holes/{hole_id}/CCIDM",
            ])
        
        # 验证所有目录都存在
        for path_suffix in expected_structure:
            full_path = os.path.join(temp_data_root, path_suffix)
            assert os.path.exists(full_path), f"目录不存在: {full_path}"
        
        # 5. 验证查询功能
        assert manager.list_products() == [product_id]
        assert manager.list_inspection_batches(product_id) == [batch_id]
        assert set(manager.list_holes(product_id, batch_id)) == set(hole_ids)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])