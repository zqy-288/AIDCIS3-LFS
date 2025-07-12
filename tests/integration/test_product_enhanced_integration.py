"""
产品管理增强功能集成测试
测试产品管理、路径管理、检测批次的集成工作流
"""

import pytest
import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# 添加src目录到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.product_model import ProductModelManager, ProductModel
from models.data_path_manager import DataPathManager
from models.inspection_batch_model import InspectionBatchManager


class TestProductEnhancedIntegration:
    """产品管理增强功能集成测试"""
    
    @pytest.fixture
    def temp_data_root(self):
        """创建临时数据根目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def temp_db_path(self):
        """创建临时数据库路径"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_file.close()
        yield temp_file.name
        try:
            os.unlink(temp_file.name)
        except FileNotFoundError:
            pass
    
    @pytest.fixture
    def managers(self, temp_data_root, temp_db_path):
        """创建管理器实例"""
        path_manager = DataPathManager(temp_data_root)
        product_manager = ProductModelManager(temp_db_path)
        batch_manager = InspectionBatchManager(temp_db_path, product_manager=product_manager, path_manager=path_manager)
        
        yield {
            'path': path_manager,
            'product': product_manager,
            'batch': batch_manager
        }
        
        # 清理
        product_manager.close()
        batch_manager.close()
    
    def test_product_creation_with_path_integration(self, managers):
        """测试产品创建与路径管理集成"""
        product_manager = managers['product']
        path_manager = managers['path']
        
        # 创建产品
        product = product_manager.create_product(
            model_name="TP-Integration-001",
            standard_diameter=10.0,
            tolerance_upper=0.05,
            tolerance_lower=-0.05,
            description="集成测试产品"
        )
        
        # 创建对应的目录结构
        paths = path_manager.create_product_structure(product.model_name)
        
        # 验证产品数据库记录
        assert product.id is not None
        assert product.model_name == "TP-Integration-001"
        
        # 验证目录结构创建
        assert os.path.exists(paths['product_dir'])
        assert os.path.exists(paths['dxf_dir'])
        assert os.path.exists(paths['inspections_dir'])
        
        # 验证路径查询
        products = path_manager.list_products()
        assert product.model_name in products
    
    def test_inspection_batch_creation_workflow(self, managers):
        """测试检测批次创建完整工作流"""
        product_manager = managers['product']
        path_manager = managers['path']
        batch_manager = managers['batch']
        
        # 1. 创建产品
        product = product_manager.create_product(
            model_name="TP-Batch-001",
            standard_diameter=12.0,
            tolerance_upper=0.08,
            tolerance_lower=-0.08
        )
        
        # 2. 创建产品目录结构
        path_manager.create_product_structure(product.model_name)
        
        # 3. 创建检测批次
        batch = batch_manager.create_batch(
            product_id=product.id,
            operator="test_operator",
            equipment_id="AIDCIS3_001",
            description="集成测试批次"
        )
        
        # 4. 验证批次数据
        assert batch.batch_id is not None
        assert batch.product_id == product.id
        assert batch.operator == "test_operator"
        assert batch.status == "pending"
        
        # 5. 验证目录结构
        batch_path = path_manager.get_inspection_batch_path(product.model_name, batch.batch_id)
        assert os.path.exists(batch_path)
        
        holes_dir = path_manager.get_holes_dir(product.model_name, batch.batch_id)
        assert os.path.exists(holes_dir)
        
        # 6. 验证检测信息文件
        info_path = path_manager.get_inspection_info_path(product.model_name, batch.batch_id)
        assert os.path.exists(info_path)
        
        with open(info_path, 'r', encoding='utf-8') as f:
            info_data = json.load(f)
        
        assert info_data['batch_id'] == batch.batch_id
        assert info_data['product_name'] == product.model_name
        assert info_data['operator'] == "test_operator"
    
    def test_batch_progress_update_integration(self, managers):
        """测试批次进度更新集成"""
        product_manager = managers['product']
        path_manager = managers['path']
        batch_manager = managers['batch']
        
        # 创建产品和批次
        product = product_manager.create_product(
            model_name="TP-Progress-001",
            standard_diameter=15.0,
            tolerance_upper=0.1,
            tolerance_lower=-0.1
        )
        
        path_manager.create_product_structure(product.model_name)
        
        batch = batch_manager.create_batch(product_id=product.id)
        
        # 开始批次
        batch_manager.start_batch(batch.batch_id)
        
        # 更新进度
        batch_manager.update_batch_progress(
            batch.batch_id,
            total_holes=100,
            completed_holes=50,
            qualified_holes=48,
            defective_holes=2
        )
        
        # 验证数据库中的进度
        updated_batch = batch_manager.get_batch_by_id(batch.batch_id)
        assert updated_batch.total_holes == 100
        assert updated_batch.completed_holes == 50
        assert updated_batch.qualified_holes == 48
        assert updated_batch.defective_holes == 2
        assert updated_batch.overall_progress == 50.0
        assert updated_batch.qualification_rate == 96.0
        
        # 验证汇总文件更新
        summary_path = path_manager.get_inspection_summary_path(product.model_name, batch.batch_id)
        assert os.path.exists(summary_path)
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        assert summary_data['total_holes'] == 100
        assert summary_data['completed_holes'] == 50
        assert summary_data['qualification_rate'] == 96.0
    
    def test_hole_structure_creation_integration(self, managers):
        """测试孔位结构创建集成"""
        product_manager = managers['product']
        path_manager = managers['path']
        batch_manager = managers['batch']
        
        # 创建基础结构
        product = product_manager.create_product(
            model_name="TP-Hole-001",
            standard_diameter=8.0,
            tolerance_upper=0.03,
            tolerance_lower=-0.03
        )
        
        path_manager.create_product_structure(product.model_name)
        
        batch = batch_manager.create_batch(product_id=product.id)
        
        # 创建多个孔位结构
        hole_ids = ["H00001", "H00002", "H00003", "H00004", "H00005"]
        
        for hole_id in hole_ids:
            hole_paths = path_manager.create_hole_structure(
                product.model_name, batch.batch_id, hole_id
            )
            
            # 验证每个孔位的目录结构
            assert os.path.exists(hole_paths['hole_dir'])
            assert os.path.exists(hole_paths['bisdm_dir'])
            assert os.path.exists(hole_paths['bisdm_result_dir'])
            assert os.path.exists(hole_paths['ccidm_dir'])
        
        # 验证孔位列表查询
        holes = path_manager.list_holes(product.model_name, batch.batch_id)
        assert set(holes) == set(hole_ids)
        
        # 模拟创建一些测试文件
        for hole_id in hole_ids[:3]:  # 前3个孔位有数据
            # 创建BISDM全景图
            panorama_path = path_manager.get_hole_panorama_path(
                product.model_name, batch.batch_id, hole_id
            )
            Path(panorama_path).touch()
            
            # 创建BISDM结果图像
            result_dir = path_manager.get_hole_bisdm_result_dir(
                product.model_name, batch.batch_id, hole_id
            )
            for i in range(3):
                result_file = Path(result_dir) / f"2-{i+3}.0.png"
                result_file.touch()
            
            # 创建CCIDM测量数据
            measurement_path = path_manager.get_hole_measurement_path(
                product.model_name, batch.batch_id, hole_id
            )
            Path(measurement_path).touch()
        
        # 验证文件创建
        for hole_id in hole_ids[:3]:
            panorama_path = path_manager.get_hole_panorama_path(
                product.model_name, batch.batch_id, hole_id
            )
            assert os.path.exists(panorama_path)
    
    def test_product_deletion_with_file_cleanup(self, managers):
        """测试产品删除与文件清理集成"""
        product_manager = managers['product']
        path_manager = managers['path']
        batch_manager = managers['batch']
        
        # 创建完整的产品数据结构
        product = product_manager.create_product(
            model_name="TP-Delete-001",
            standard_diameter=20.0,
            tolerance_upper=0.15,
            tolerance_lower=-0.15,
            dxf_file_path="/tmp/test.dxf"
        )
        
        # 创建目录结构和文件
        path_manager.create_product_structure(product.model_name)
        
        # 创建DXF文件
        dxf_path = path_manager.get_product_dxf_path(product.model_name)
        Path(dxf_path).parent.mkdir(parents=True, exist_ok=True)
        Path(dxf_path).touch()
        
        # 创建检测批次和数据
        batch = batch_manager.create_batch(product_id=product.id)
        
        # 创建一些孔位数据
        for i in range(3):
            hole_id = f"H{i+1:05d}"
            path_manager.create_hole_structure(product.model_name, batch.batch_id, hole_id)
            
            # 创建测试文件
            panorama_path = path_manager.get_hole_panorama_path(
                product.model_name, batch.batch_id, hole_id
            )
            Path(panorama_path).touch()
        
        # 验证文件和目录存在
        product_path = path_manager.get_product_path(product.model_name)
        assert os.path.exists(product_path)
        assert os.path.exists(dxf_path)
        
        # 删除产品（数据库记录）
        product_manager.delete_product(product.id)
        
        # 验证数据库记录已删除
        deleted_product = product_manager.get_product_by_id(product.id)
        assert deleted_product is None
        
        # 验证文件仍然存在（仅删除数据库记录）
        assert os.path.exists(product_path)
        assert os.path.exists(dxf_path)
        
        # 手动清理文件（模拟完整删除）
        if os.path.exists(product_path):
            shutil.rmtree(product_path)
        
        assert not os.path.exists(product_path)
    
    def test_legacy_data_migration_integration(self, managers):
        """测试遗留数据迁移集成"""
        product_manager = managers['product']
        path_manager = managers['path']
        batch_manager = managers['batch']
        
        # 创建遗留数据结构
        legacy_holes = ["H00001", "H00002"]
        
        for hole_id in legacy_holes:
            # 创建遗留目录结构
            legacy_path = Path(path_manager.data_root) / hole_id
            legacy_bisdm = legacy_path / "BISDM" / "result"
            legacy_ccidm = legacy_path / "CCIDM"
            
            legacy_bisdm.mkdir(parents=True)
            legacy_ccidm.mkdir(parents=True)
            
            # 创建一些遗留文件
            (legacy_bisdm / "2-3.0.png").touch()
            (legacy_bisdm / "2-4.0.png").touch()
            (legacy_ccidm / "measurement_data.csv").touch()
        
        # 创建新的产品和批次
        product = product_manager.create_product(
            model_name="TP-Migration-001",
            standard_diameter=25.0,
            tolerance_upper=0.2,
            tolerance_lower=-0.2
        )
        
        path_manager.create_product_structure(product.model_name)
        
        batch = batch_manager.create_batch(product_id=product.id)
        
        # 执行数据迁移
        migration_results = []
        for hole_id in legacy_holes:
            result = path_manager.migrate_legacy_data(
                hole_id, product.model_name, batch.batch_id
            )
            migration_results.append(result)
        
        # 验证迁移结果
        assert all(migration_results), "所有数据迁移应该成功"
        
        # 验证新结构中的数据
        for hole_id in legacy_holes:
            new_bisdm_dir = path_manager.get_hole_bisdm_dir(
                product.model_name, batch.batch_id, hole_id
            )
            new_ccidm_dir = path_manager.get_hole_ccidm_dir(
                product.model_name, batch.batch_id, hole_id
            )
            
            # 验证迁移的数据存在
            assert os.path.exists(os.path.join(new_bisdm_dir, "legacy"))
            assert os.path.exists(os.path.join(new_ccidm_dir, "legacy"))
    
    def test_concurrent_batch_operations(self, managers):
        """测试并发批次操作"""
        product_manager = managers['product']
        path_manager = managers['path']
        batch_manager = managers['batch']
        
        # 创建产品
        product = product_manager.create_product(
            model_name="TP-Concurrent-001",
            standard_diameter=30.0,
            tolerance_upper=0.25,
            tolerance_lower=-0.25
        )
        
        path_manager.create_product_structure(product.model_name)
        
        # 创建多个并发批次
        batches = []
        for i in range(3):
            batch = batch_manager.create_batch(
                product_id=product.id,
                operator=f"operator_{i+1}",
                description=f"并发测试批次 {i+1}"
            )
            batches.append(batch)
        
        # 验证所有批次都创建成功
        assert len(batches) == 3
        
        # 验证批次ID的唯一性
        batch_ids = [batch.batch_id for batch in batches]
        assert len(set(batch_ids)) == 3, "批次ID应该唯一"
        
        # 验证对应的目录结构
        for batch in batches:
            batch_path = path_manager.get_inspection_batch_path(
                product.model_name, batch.batch_id
            )
            assert os.path.exists(batch_path)
        
        # 测试批次状态更新
        for i, batch in enumerate(batches):
            batch_manager.start_batch(batch.batch_id)
            batch_manager.update_batch_progress(
                batch.batch_id,
                total_holes=100,
                completed_holes=i * 30,
                qualified_holes=i * 28
            )
        
        # 验证所有批次的状态
        updated_batches = batch_manager.get_batches_by_product(product.id)
        assert len(updated_batches) == 3
        
        for batch in updated_batches:
            assert batch.status == "running"
            assert batch.total_holes == 100


class TestErrorHandlingIntegration:
    """错误处理集成测试"""
    
    @pytest.fixture
    def temp_data_root(self):
        """创建临时数据根目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def temp_db_path(self):
        """创建临时数据库路径"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_file.close()
        yield temp_file.name
        try:
            os.unlink(temp_file.name)
        except FileNotFoundError:
            pass
    
    def test_database_error_handling(self, temp_data_root, temp_db_path):
        """测试数据库错误处理"""
        # 创建正常的管理器
        path_manager = DataPathManager(temp_data_root)
        product_manager = ProductModelManager(temp_db_path)
        
        # 创建产品
        product = product_manager.create_product(
            model_name="TP-Error-001",
            standard_diameter=5.0,
            tolerance_upper=0.02,
            tolerance_lower=-0.02
        )
        
        # 关闭数据库连接（模拟数据库错误）
        product_manager.close()
        
        # 尝试查询产品（应该失败）
        with pytest.raises(Exception):
            product_manager.get_product_by_id(product.id)
    
    def test_file_system_error_handling(self, temp_data_root, temp_db_path):
        """测试文件系统错误处理"""
        path_manager = DataPathManager(temp_data_root)
        
        # 创建只读目录（模拟权限错误）
        readonly_dir = Path(temp_data_root) / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # 只读权限
        
        try:
            # 尝试在只读目录中创建子目录（应该失败）
            with pytest.raises(PermissionError):
                (readonly_dir / "subdir").mkdir()
        finally:
            # 恢复权限以便清理
            readonly_dir.chmod(0o755)
    
    def test_invalid_data_handling(self, temp_data_root, temp_db_path):
        """测试无效数据处理"""
        product_manager = ProductModelManager(temp_db_path)
        
        # 测试无效的产品数据
        with pytest.raises(ValueError):
            product_manager.create_product(
                model_name="",  # 空名称
                standard_diameter=10.0,
                tolerance_upper=0.05,
                tolerance_lower=-0.05
            )
        
        with pytest.raises(ValueError):
            product_manager.create_product(
                model_name="Valid-Name",
                standard_diameter=-1.0,  # 负数直径
                tolerance_upper=0.05,
                tolerance_lower=-0.05
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])