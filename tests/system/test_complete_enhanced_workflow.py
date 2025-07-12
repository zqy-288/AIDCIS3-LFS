"""
完整增强功能系统测试
端到端测试用户工作流程
"""

import pytest
import os
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

# 添加src目录到路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.product_model import ProductModelManager
from models.data_path_manager import DataPathManager
from models.inspection_batch_model import InspectionBatchManager


class TestCompleteEnhancedWorkflow:
    """完整增强功能系统测试"""
    
    @pytest.fixture
    def test_environment(self):
        """设置完整的测试环境"""
        # 创建临时目录
        temp_data_root = tempfile.mkdtemp()
        temp_db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db_file.close()
        
        # 创建管理器实例
        path_manager = DataPathManager(temp_data_root)
        product_manager = ProductModelManager(temp_db_file.name)
        batch_manager = InspectionBatchManager(temp_db_file.name, product_manager=product_manager, path_manager=path_manager)
        
        # 创建测试DXF文件
        test_dxf_path = os.path.join(temp_data_root, "test.dxf")
        with open(test_dxf_path, 'w') as f:
            f.write("TEST DXF CONTENT")
        
        yield {
            'data_root': temp_data_root,
            'db_path': temp_db_file.name,
            'dxf_path': test_dxf_path,
            'path_manager': path_manager,
            'product_manager': product_manager,
            'batch_manager': batch_manager
        }
        
        # 清理
        product_manager.close()
        batch_manager.close()
        shutil.rmtree(temp_data_root, ignore_errors=True)
        try:
            os.unlink(temp_db_file.name)
        except FileNotFoundError:
            pass
    
    def test_complete_product_lifecycle(self, test_environment):
        """测试完整的产品生命周期"""
        env = test_environment
        product_manager = env['product_manager']
        path_manager = env['path_manager']
        batch_manager = env['batch_manager']
        
        # ===== 第一阶段：产品创建 =====
        print("第一阶段：创建产品")
        
        # 1. 创建产品
        product = product_manager.create_product(
            model_name="TP-SystemTest-001",
            standard_diameter=16.0,
            tolerance_upper=0.12,
            tolerance_lower=-0.12,
            description="系统测试产品",
            dxf_file_path=env['dxf_path']
        )
        
        assert product.id is not None
        assert product.model_name == "TP-SystemTest-001"
        
        # 2. 创建产品目录结构
        product_paths = path_manager.create_product_structure(product.model_name)
        
        # 验证目录创建
        assert os.path.exists(product_paths['product_dir'])
        assert os.path.exists(product_paths['dxf_dir'])
        assert os.path.exists(product_paths['inspections_dir'])
        
        # 3. 复制DXF文件到产品目录
        product_dxf_path = path_manager.get_product_dxf_path(product.model_name)
        shutil.copy2(env['dxf_path'], product_dxf_path)
        assert os.path.exists(product_dxf_path)
        
        # 4. 创建产品信息文件
        product_info_path = path_manager.get_product_info_path(product.model_name)
        product_info = {
            "product_id": product.model_name,
            "product_name": product.model_name,
            "standard_diameter": product.standard_diameter,
            "tolerance_upper": product.tolerance_upper,
            "tolerance_lower": product.tolerance_lower,
            "created_at": datetime.now().isoformat(),
            "description": product.description
        }
        
        with open(product_info_path, 'w', encoding='utf-8') as f:
            json.dump(product_info, f, indent=2, ensure_ascii=False)
        
        assert os.path.exists(product_info_path)
        
        # ===== 第二阶段：检测批次管理 =====
        print("第二阶段：检测批次管理")
        
        # 1. 创建检测批次
        batch = batch_manager.create_batch(
            product_id=product.id,
            operator="system_test_operator",
            equipment_id="AIDCIS3_TEST_001",
            description="系统测试检测批次"
        )
        
        assert batch.batch_id is not None
        assert batch.status == "pending"
        
        # 2. 验证批次目录结构
        batch_path = path_manager.get_inspection_batch_path(product.model_name, batch.batch_id)
        assert os.path.exists(batch_path)
        
        # 3. 验证检测信息文件
        info_path = path_manager.get_inspection_info_path(product.model_name, batch.batch_id)
        assert os.path.exists(info_path)
        
        # ===== 第三阶段：检测过程模拟 =====
        print("第三阶段：检测过程模拟")
        
        # 1. 开始检测
        success = batch_manager.start_batch(batch.batch_id)
        assert success
        
        # 验证状态更新
        updated_batch = batch_manager.get_batch_by_id(batch.batch_id)
        assert updated_batch.status == "running"
        assert updated_batch.start_time is not None
        
        # 2. 创建孔位结构并模拟检测数据
        hole_ids = [f"H{i+1:05d}" for i in range(10)]  # 创建10个孔位\n        \n        for i, hole_id in enumerate(hole_ids):\n            # 创建孔位目录结构\n            hole_paths = path_manager.create_hole_structure(\n                product.model_name, batch.batch_id, hole_id\n            )\n            \n            # 模拟BISDM数据创建\n            panorama_path = path_manager.get_hole_panorama_path(\n                product.model_name, batch.batch_id, hole_id\n            )\n            Path(panorama_path).touch()\n            \n            # 创建结果图像\n            result_dir = path_manager.get_hole_bisdm_result_dir(\n                product.model_name, batch.batch_id, hole_id\n            )\n            for j in range(5):\n                result_file = Path(result_dir) / f\"2-{j+3}.0.png\"\n                result_file.touch()\n            \n            # 模拟CCIDM数据创建\n            measurement_path = path_manager.get_hole_measurement_path(\n                product.model_name, batch.batch_id, hole_id\n            )\n            measurement_data = f\"hole_id,diameter,status\\n{hole_id},{15.9 + i * 0.1},{'qualified' if i < 8 else 'defective'}\\n\"\n            Path(measurement_path).write_text(measurement_data)\n            \n            # 更新检测进度\n            batch_manager.update_batch_progress(\n                batch.batch_id,\n                total_holes=len(hole_ids),\n                completed_holes=i + 1,\n                qualified_holes=min(i + 1, 8),\n                defective_holes=max(0, i + 1 - 8)\n            )\n        \n        # 3. 完成检测\n        success = batch_manager.complete_batch(batch.batch_id)\n        assert success\n        \n        # 验证最终状态\n        final_batch = batch_manager.get_batch_by_id(batch.batch_id)\n        assert final_batch.status == \"completed\"\n        assert final_batch.end_time is not None\n        assert final_batch.overall_progress == 100.0\n        assert final_batch.qualification_rate == 80.0  # 8/10 = 80%\n        \n        # 4. 验证汇总文件\n        summary_path = path_manager.get_inspection_summary_path(product.model_name, batch.batch_id)\n        assert os.path.exists(summary_path)\n        \n        with open(summary_path, 'r', encoding='utf-8') as f:\n            summary_data = json.load(f)\n        \n        assert summary_data['total_holes'] == 10\n        assert summary_data['completed_holes'] == 10\n        assert summary_data['qualified_holes'] == 8\n        assert summary_data['defective_holes'] == 2\n        \n        # ===== 第四阶段：数据查询和验证 =====\n        print(\"第四阶段：数据查询和验证\")\n        \n        # 1. 验证产品查询\n        all_products = product_manager.get_all_products()\n        assert len(all_products) >= 1\n        assert any(p.model_name == \"TP-SystemTest-001\" for p in all_products)\n        \n        # 2. 验证批次查询\n        product_batches = batch_manager.get_batches_by_product(product.id)\n        assert len(product_batches) == 1\n        assert product_batches[0].batch_id == batch.batch_id\n        \n        # 3. 验证目录结构完整性\n        products = path_manager.list_products()\n        assert product.model_name in products\n        \n        batches = path_manager.list_inspection_batches(product.model_name)\n        assert batch.batch_id in batches\n        \n        holes = path_manager.list_holes(product.model_name, batch.batch_id)\n        assert set(holes) == set(hole_ids)\n        \n        # 4. 验证文件完整性\n        for hole_id in hole_ids:\n            # 验证BISDM文件\n            panorama_path = path_manager.get_hole_panorama_path(\n                product.model_name, batch.batch_id, hole_id\n            )\n            assert os.path.exists(panorama_path)\n            \n            # 验证CCIDM文件\n            measurement_path = path_manager.get_hole_measurement_path(\n                product.model_name, batch.batch_id, hole_id\n            )\n            assert os.path.exists(measurement_path)\n        \n        # ===== 第五阶段：产品删除测试 =====\n        print(\"第五阶段：产品删除测试\")\n        \n        # 1. 收集删除前的文件信息\n        product_path = path_manager.get_product_path(product.model_name)\n        files_before_delete = list(Path(product_path).rglob('*')) if os.path.exists(product_path) else []\n        \n        # 2. 删除产品（仅数据库）\n        product_manager.delete_product(product.id)\n        \n        # 验证数据库记录已删除\n        deleted_product = product_manager.get_product_by_id(product.id)\n        assert deleted_product is None\n        \n        # 验证文件仍然存在\n        assert os.path.exists(product_path)\n        \n        # 3. 模拟完整删除（包括文件）\n        if os.path.exists(product_path):\n            shutil.rmtree(product_path)\n        \n        assert not os.path.exists(product_path)\n        \n        print(\"系统测试完成：所有阶段验证通过\")\n    \n    def test_multiple_products_workflow(self, test_environment):\n        \"\"\"测试多产品工作流程\"\"\"\n        env = test_environment\n        product_manager = env['product_manager']\n        path_manager = env['path_manager']\n        batch_manager = env['batch_manager']\n        \n        # 创建多个产品\n        products = []\n        for i in range(3):\n            product = product_manager.create_product(\n                model_name=f\"TP-Multi-{i+1:03d}\",\n                standard_diameter=10.0 + i * 2,\n                tolerance_upper=0.05 + i * 0.02,\n                tolerance_lower=-(0.05 + i * 0.02),\n                description=f\"多产品测试 #{i+1}\"\n            )\n            products.append(product)\n            \n            # 创建目录结构\n            path_manager.create_product_structure(product.model_name)\n        \n        # 为每个产品创建检测批次\n        batches = []\n        with patch('models.inspection_batch_model.get_data_path_manager', return_value=path_manager):\n            for product in products:\n                batch = batch_manager.create_batch(\n                    product_id=product.id,\n                    operator=f\"operator_{product.model_name}\",\n                    description=f\"批次 for {product.model_name}\"\n                )\n                batches.append(batch)\n        \n        # 验证所有产品和批次\n        all_products = product_manager.get_all_products()\n        assert len(all_products) >= 3\n        \n        for product in products:\n            product_batches = batch_manager.get_batches_by_product(product.id)\n            assert len(product_batches) == 1\n        \n        # 验证目录结构\n        product_list = path_manager.list_products()\n        for product in products:\n            assert product.model_name in product_list\n        \n        print(\"多产品工作流程测试完成\")\n    \n    def test_data_migration_workflow(self, test_environment):\n        \"\"\"测试数据迁移工作流程\"\"\"\n        env = test_environment\n        path_manager = env['path_manager']\n        product_manager = env['product_manager']\n        batch_manager = env['batch_manager']\n        \n        # 1. 创建遗留数据结构\n        legacy_holes = [\"H00001\", \"H00002\", \"H00003\"]\n        \n        for hole_id in legacy_holes:\n            # 创建遗留目录\n            legacy_path = Path(env['data_root']) / hole_id\n            legacy_bisdm = legacy_path / \"BISDM\" / \"result\"\n            legacy_ccidm = legacy_path / \"CCIDM\"\n            \n            legacy_bisdm.mkdir(parents=True)\n            legacy_ccidm.mkdir(parents=True)\n            \n            # 创建遗留文件\n            (legacy_bisdm / \"panorama.png\").touch()\n            for i in range(3):\n                (legacy_bisdm / f\"2-{i+3}.0.png\").touch()\n            (legacy_ccidm / \"measurement_data_legacy.csv\").touch()\n        \n        # 2. 创建新的产品和批次\n        product = product_manager.create_product(\n            model_name=\"TP-Migration-001\",\n            standard_diameter=18.0,\n            tolerance_upper=0.15,\n            tolerance_lower=-0.15,\n            description=\"数据迁移测试产品\"\n        )\n        \n        path_manager.create_product_structure(product.model_name)\n        \n        with patch('models.inspection_batch_model.get_data_path_manager', return_value=path_manager):\n            batch = batch_manager.create_batch(\n                product_id=product.id,\n                description=\"数据迁移批次\"\n            )\n        \n        # 3. 执行数据迁移\n        migration_results = []\n        for hole_id in legacy_holes:\n            result = path_manager.migrate_legacy_data(\n                hole_id, product.model_name, batch.batch_id\n            )\n            migration_results.append(result)\n        \n        # 4. 验证迁移结果\n        assert all(migration_results), \"所有遗留数据应该迁移成功\"\n        \n        # 验证新结构中的数据\n        migrated_holes = path_manager.list_holes(product.model_name, batch.batch_id)\n        assert set(migrated_holes) == set(legacy_holes)\n        \n        for hole_id in legacy_holes:\n            # 验证迁移的BISDM数据\n            new_bisdm_dir = path_manager.get_hole_bisdm_dir(\n                product.model_name, batch.batch_id, hole_id\n            )\n            assert os.path.exists(os.path.join(new_bisdm_dir, \"legacy\"))\n            \n            # 验证迁移的CCIDM数据\n            new_ccidm_dir = path_manager.get_hole_ccidm_dir(\n                product.model_name, batch.batch_id, hole_id\n            )\n            assert os.path.exists(os.path.join(new_ccidm_dir, \"legacy\"))\n        \n        print(\"数据迁移工作流程测试完成\")\n    \n    @pytest.mark.slow\n    def test_performance_workflow(self, test_environment):\n        \"\"\"测试性能工作流程\"\"\"\n        env = test_environment\n        product_manager = env['product_manager']\n        path_manager = env['path_manager']\n        batch_manager = env['batch_manager']\n        \n        # 性能测试参数\n        num_products = 5\n        num_batches_per_product = 2\n        num_holes_per_batch = 50\n        \n        start_time = time.time()\n        \n        # 1. 批量创建产品\n        products = []\n        for i in range(num_products):\n            product = product_manager.create_product(\n                model_name=f\"TP-Perf-{i+1:03d}\",\n                standard_diameter=10.0 + i,\n                tolerance_upper=0.05,\n                tolerance_lower=-0.05,\n                description=f\"性能测试产品 #{i+1}\"\n            )\n            products.append(product)\n            path_manager.create_product_structure(product.model_name)\n        \n        product_creation_time = time.time() - start_time\n        print(f\"创建 {num_products} 个产品耗时: {product_creation_time:.2f}秒\")\n        \n        # 2. 批量创建检测批次\n        batch_creation_start = time.time()\n        \n        all_batches = []\n        with patch('models.inspection_batch_model.get_data_path_manager', return_value=path_manager):\n            for product in products:\n                for j in range(num_batches_per_product):\n                    batch = batch_manager.create_batch(\n                        product_id=product.id,\n                        operator=f\"perf_operator_{j+1}\",\n                        description=f\"性能测试批次 {j+1}\"\n                    )\n                    all_batches.append((product, batch))\n        \n        batch_creation_time = time.time() - batch_creation_start\n        total_batches = num_products * num_batches_per_product\n        print(f\"创建 {total_batches} 个批次耗时: {batch_creation_time:.2f}秒\")\n        \n        # 3. 批量创建孔位数据\n        hole_creation_start = time.time()\n        \n        total_holes_created = 0\n        for product, batch in all_batches:\n            for k in range(num_holes_per_batch):\n                hole_id = f\"H{k+1:05d}\"\n                path_manager.create_hole_structure(\n                    product.model_name, batch.batch_id, hole_id\n                )\n                total_holes_created += 1\n        \n        hole_creation_time = time.time() - hole_creation_start\n        print(f\"创建 {total_holes_created} 个孔位结构耗时: {hole_creation_time:.2f}秒\")\n        \n        # 4. 查询性能测试\n        query_start = time.time()\n        \n        # 查询所有产品\n        all_products = product_manager.get_all_products()\n        assert len(all_products) >= num_products\n        \n        # 查询所有批次\n        for product in products:\n            batches = batch_manager.get_batches_by_product(product.id)\n            assert len(batches) == num_batches_per_product\n        \n        # 查询目录结构\n        product_list = path_manager.list_products()\n        assert len(product_list) >= num_products\n        \n        query_time = time.time() - query_start\n        print(f\"查询操作耗时: {query_time:.2f}秒\")\n        \n        # 总耗时\n        total_time = time.time() - start_time\n        print(f\"性能测试总耗时: {total_time:.2f}秒\")\n        \n        # 性能断言\n        assert product_creation_time < 5.0, \"产品创建应在5秒内完成\"\n        assert batch_creation_time < 10.0, \"批次创建应在10秒内完成\"\n        assert hole_creation_time < 30.0, \"孔位创建应在30秒内完成\"\n        assert query_time < 2.0, \"查询操作应在2秒内完成\"\n        \n        print(\"性能工作流程测试完成\")\n    \n    def test_error_recovery_workflow(self, test_environment):\n        \"\"\"测试错误恢复工作流程\"\"\"\n        env = test_environment\n        product_manager = env['product_manager']\n        path_manager = env['path_manager']\n        batch_manager = env['batch_manager']\n        \n        # 1. 创建正常的产品和批次\n        product = product_manager.create_product(\n            model_name=\"TP-ErrorRecovery-001\",\n            standard_diameter=22.0,\n            tolerance_upper=0.18,\n            tolerance_lower=-0.18\n        )\n        \n        path_manager.create_product_structure(product.model_name)\n        \n        with patch('models.inspection_batch_model.get_data_path_manager', return_value=path_manager):\n            batch = batch_manager.create_batch(product_id=product.id)\n        \n        # 2. 模拟部分数据损坏\n        batch_path = path_manager.get_inspection_batch_path(product.model_name, batch.batch_id)\n        info_path = path_manager.get_inspection_info_path(product.model_name, batch.batch_id)\n        \n        # 删除检测信息文件（模拟文件损坏）\n        if os.path.exists(info_path):\n            os.remove(info_path)\n        \n        # 3. 尝试恢复：重新创建信息文件\n        batch_manager._update_inspection_info_file(batch)\n        \n        # 验证文件已恢复\n        assert os.path.exists(info_path)\n        \n        # 4. 模拟数据库连接错误\n        original_session = batch_manager.session\n        batch_manager.session = None\n        \n        # 尝试查询（应该失败）\n        with pytest.raises(AttributeError):\n            batch_manager.get_batch_by_id(batch.batch_id)\n        \n        # 恢复连接\n        batch_manager.session = original_session\n        \n        # 验证恢复后的操作\n        recovered_batch = batch_manager.get_batch_by_id(batch.batch_id)\n        assert recovered_batch is not None\n        assert recovered_batch.batch_id == batch.batch_id\n        \n        print(\"错误恢复工作流程测试完成\")\n\n\nclass TestSystemPerformanceMetrics:\n    \"\"\"系统性能指标测试\"\"\"\n    \n    @pytest.fixture\n    def performance_environment(self):\n        \"\"\"性能测试环境\"\"\"\n        temp_data_root = tempfile.mkdtemp()\n        temp_db_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)\n        temp_db_file.close()\n        \n        yield {\n            'data_root': temp_data_root,\n            'db_path': temp_db_file.name\n        }\n        \n        shutil.rmtree(temp_data_root, ignore_errors=True)\n        try:\n            os.unlink(temp_db_file.name)\n        except FileNotFoundError:\n            pass\n    \n    @pytest.mark.benchmark\n    def test_product_creation_benchmark(self, performance_environment, benchmark):\n        \"\"\"产品创建性能基准测试\"\"\"\n        env = performance_environment\n        product_manager = ProductModelManager(env['db_path'])\n        \n        def create_product():\n            return product_manager.create_product(\n                model_name=f\"TP-Bench-{time.time()}\",\n                standard_diameter=10.0,\n                tolerance_upper=0.05,\n                tolerance_lower=-0.05\n            )\n        \n        result = benchmark(create_product)\n        assert result.id is not None\n        \n        product_manager.close()\n    \n    @pytest.mark.benchmark\n    def test_directory_creation_benchmark(self, performance_environment, benchmark):\n        \"\"\"目录创建性能基准测试\"\"\"\n        env = performance_environment\n        path_manager = DataPathManager(env['data_root'])\n        \n        def create_directory_structure():\n            product_id = f\"TP-DirBench-{time.time()}\"\n            return path_manager.create_product_structure(product_id)\n        \n        result = benchmark(create_directory_structure)\n        assert 'product_dir' in result\n        assert os.path.exists(result['product_dir'])\n\n\nif __name__ == \"__main__\":\n    pytest.main([__file__, \"-v\", \"--tb=short\"])"