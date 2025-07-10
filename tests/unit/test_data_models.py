"""
UT-004, UT-005, UT-006: 数据模型单元测试
测试HoleData模型、StatusManager和数据转换适配器
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from aidcis2.models.status_manager import StatusManager
from aidcis2.data_adapter import DataAdapter
from modules.models import Hole, Workpiece


class TestHoleDataModel:
    """UT-004: HoleData模型测试"""
    
    def test_hole_data_creation(self):
        """测试HoleData对象创建"""
        hole = HoleData(
            hole_id="H00001",
            center_x=100.0,
            center_y=200.0,
            radius=8.865,
            status=HoleStatus.PENDING,
            layer="0"
        )
        
        # 验证基本属性
        assert hole.hole_id == "H00001"
        assert hole.center_x == 100.0
        assert hole.center_y == 200.0
        assert hole.radius == 8.865
        assert hole.status == HoleStatus.PENDING
        assert hole.layer == "0"
        assert hole.metadata == {}
        
        print("✅ HoleData对象创建成功")
    
    def test_hole_data_validation(self):
        """测试数据验证"""
        # 测试有效数据
        hole = HoleData(
            hole_id="H00001",
            center_x=100.0,
            center_y=200.0,
            radius=8.865
        )
        assert hole.hole_id == "H00001"
        
        # 测试默认ID生成
        hole_no_id = HoleData(
            hole_id="",
            center_x=100.0,
            center_y=200.0,
            radius=8.865
        )
        assert hole_no_id.hole_id == "hole_100.000_200.000"
        
        print("✅ 数据验证测试通过")
    
    def test_status_management(self):
        """测试状态管理"""
        hole = HoleData(
            hole_id="H00001",
            center_x=100.0,
            center_y=200.0,
            radius=8.865,
            status=HoleStatus.PENDING
        )
        
        # 测试状态更新
        hole.status = HoleStatus.QUALIFIED
        assert hole.status == HoleStatus.QUALIFIED
        
        # 测试状态枚举
        assert HoleStatus.PENDING.value == "pending"
        assert HoleStatus.QUALIFIED.value == "qualified"
        assert HoleStatus.DEFECTIVE.value == "defective"
        
        print("✅ 状态管理测试通过")
    
    def test_coordinate_calculations(self):
        """测试坐标计算"""
        hole1 = HoleData(
            hole_id="H00001",
            center_x=0.0,
            center_y=0.0,
            radius=8.865
        )
        
        hole2 = HoleData(
            hole_id="H00002",
            center_x=3.0,
            center_y=4.0,
            radius=8.865
        )
        
        # 测试位置属性
        assert hole1.position == (0.0, 0.0)
        assert hole2.position == (3.0, 4.0)
        
        # 测试距离计算
        distance = hole1.distance_to(hole2)
        assert abs(distance - 5.0) < 0.001  # 3-4-5三角形
        
        # 测试附近判断
        assert hole1.is_near(0.5, 0.5, 1.0)
        assert not hole1.is_near(2.0, 2.0, 1.0)
        
        print("✅ 坐标计算测试通过")
    
    def test_serialization(self):
        """测试序列化和反序列化"""
        original = HoleData(
            hole_id="H00001",
            center_x=100.0,
            center_y=200.0,
            radius=8.865,
            status=HoleStatus.QUALIFIED,
            layer="1",
            row=1,
            column=2,
            region="A",
            metadata={"test": "value"}
        )
        
        # 测试转换为字典
        data_dict = original.to_dict()
        assert data_dict['hole_id'] == "H00001"
        assert data_dict['center_x'] == 100.0
        assert data_dict['status'] == "qualified"
        assert data_dict['metadata']['test'] == "value"
        
        # 测试从字典创建
        restored = HoleData.from_dict(data_dict)
        assert restored.hole_id == original.hole_id
        assert restored.center_x == original.center_x
        assert restored.status == original.status
        assert restored.metadata == original.metadata
        
        print("✅ 序列化测试通过")


class TestStatusManager:
    """UT-005: StatusManager测试"""
    
    @pytest.fixture
    def status_manager(self):
        """创建StatusManager实例"""
        return StatusManager()
    
    @pytest.fixture
    def sample_holes(self):
        """创建测试孔位数据"""
        holes = [
            HoleData("H00001", 100.0, 100.0, 8.865, HoleStatus.PENDING),
            HoleData("H00002", 200.0, 100.0, 8.865, HoleStatus.QUALIFIED),
            HoleData("H00003", 300.0, 100.0, 8.865, HoleStatus.DEFECTIVE),
        ]
        return HoleCollection(holes={h.hole_id: h for h in holes})
    
    def test_status_update(self, status_manager, sample_holes):
        """测试状态更新"""
        hole = list(sample_holes.holes.values())[0]
        original_status = hole.status
        
        # 测试单个状态更新
        success = status_manager.update_hole_status(
            hole, HoleStatus.PROCESSING, "开始检测"
        )
        
        assert success
        assert hole.status == HoleStatus.PROCESSING
        
        # 验证历史记录
        history = status_manager.get_status_history(hole.hole_id)
        assert len(history) == 1
        assert history[0]['old_status'] == original_status
        assert history[0]['new_status'] == HoleStatus.PROCESSING
        assert history[0]['reason'] == "开始检测"
        
        print("✅ 状态更新测试通过")
    
    def test_status_statistics(self, status_manager, sample_holes):
        """测试状态统计"""
        # 测试状态统计
        stats = status_manager.get_status_statistics(sample_holes)
        assert stats[HoleStatus.PENDING] == 1
        assert stats[HoleStatus.QUALIFIED] == 1
        assert stats[HoleStatus.DEFECTIVE] == 1
        
        # 测试百分比计算
        percentages = status_manager.get_status_percentage(sample_holes)
        assert abs(percentages[HoleStatus.PENDING] - 33.33) < 0.1
        assert abs(percentages[HoleStatus.QUALIFIED] - 33.33) < 0.1
        assert abs(percentages[HoleStatus.DEFECTIVE] - 33.33) < 0.1
        
        print("✅ 状态统计测试通过")
    
    def test_batch_status_update(self, status_manager, sample_holes):
        """测试批量状态更新"""
        holes_list = list(sample_holes.holes.values())
        
        # 批量更新状态
        success_count = status_manager.batch_update_status(
            holes_list, HoleStatus.PROCESSING, "批量开始检测"
        )
        
        assert success_count == len(holes_list)
        
        # 验证所有孔位状态都已更新
        for hole in holes_list:
            assert hole.status == HoleStatus.PROCESSING
        
        print("✅ 批量状态更新测试通过")
    
    def test_completion_and_quality_rates(self, status_manager, sample_holes):
        """测试完成率和质量率计算"""
        # 测试完成率
        completion_rate = status_manager.get_completion_rate(sample_holes)
        # 有1个QUALIFIED和1个DEFECTIVE，共2个完成，总共3个
        assert abs(completion_rate - 66.67) < 0.1
        
        # 测试质量率
        quality_rate = status_manager.get_quality_rate(sample_holes)
        # 在2个已检测的孔位中，1个合格
        assert abs(quality_rate - 50.0) < 0.1
        
        print("✅ 完成率和质量率测试通过")
    
    def test_invalid_status_handling(self, status_manager):
        """测试无效状态处理"""
        hole = HoleData("H00001", 100.0, 100.0, 8.865, HoleStatus.PENDING)
        
        # 测试正常状态更新
        success = status_manager.update_hole_status(hole, HoleStatus.QUALIFIED)
        assert success
        assert hole.status == HoleStatus.QUALIFIED
        
        print("✅ 无效状态处理测试通过")


class TestDataAdapter:
    """UT-006: 数据转换适配器测试"""
    
    @pytest.fixture
    def adapter(self):
        """创建DataAdapter实例"""
        return DataAdapter()
    
    @pytest.fixture
    def sample_hole_data(self):
        """创建测试HoleData"""
        return HoleData(
            hole_id="H00001",
            center_x=100.0,
            center_y=200.0,
            radius=8.865,
            status=HoleStatus.QUALIFIED,
            layer="0",
            metadata={"tolerance": 0.1}
        )
    
    @pytest.fixture
    def sample_db_hole(self):
        """创建测试数据库Hole模型"""
        return Hole(
            id=1,
            hole_id="H00001",
            workpiece_id=1,
            position_x=100.0,
            position_y=200.0,
            target_diameter=17.73,  # radius * 2
            tolerance=0.1,
            status='qualified',
            created_at=datetime.now()
        )
    
    def test_hole_data_to_db_model(self, adapter, sample_hole_data):
        """测试HoleData转换为数据库模型"""
        workpiece_id = 1
        
        db_hole = adapter.hole_data_to_db_model(sample_hole_data, workpiece_id)
        
        # 验证转换结果
        assert db_hole.hole_id == sample_hole_data.hole_id
        assert db_hole.workpiece_id == workpiece_id
        assert db_hole.position_x == sample_hole_data.center_x
        assert db_hole.position_y == sample_hole_data.center_y
        assert abs(db_hole.target_diameter - sample_hole_data.radius * 2) < 0.001
        assert db_hole.tolerance == 0.1
        assert db_hole.status == 'qualified'
        
        print("✅ HoleData转换为数据库模型测试通过")
    
    def test_db_model_to_hole_data(self, adapter, sample_db_hole):
        """测试数据库模型转换为HoleData"""
        hole_data = adapter.db_model_to_hole_data(sample_db_hole)
        
        # 验证转换结果
        assert hole_data.hole_id == sample_db_hole.hole_id
        assert hole_data.center_x == sample_db_hole.position_x
        assert hole_data.center_y == sample_db_hole.position_y
        assert abs(hole_data.radius - sample_db_hole.target_diameter / 2) < 0.001
        assert hole_data.status == HoleStatus.QUALIFIED
        assert hole_data.metadata['db_id'] == sample_db_hole.id
        assert hole_data.metadata['tolerance'] == sample_db_hole.tolerance
        
        print("✅ 数据库模型转换为HoleData测试通过")
    
    def test_partial_data_conversion(self, adapter):
        """测试部分数据转换"""
        # 测试缺少某些字段的情况
        incomplete_hole_data = HoleData(
            hole_id="H00001",
            center_x=100.0,
            center_y=200.0,
            radius=8.865
            # 缺少metadata
        )
        
        db_hole = adapter.hole_data_to_db_model(incomplete_hole_data, 1)
        
        # 验证默认值处理
        assert db_hole.tolerance == 0.1  # 默认公差
        assert db_hole.status == 'not_detected'  # 默认状态
        
        print("✅ 部分数据转换测试通过")
    
    def test_conversion_error_handling(self, adapter):
        """测试转换错误处理"""
        # 测试无效数据
        invalid_hole_data = HoleData(
            hole_id="",  # 空ID
            center_x=100.0,
            center_y=200.0,
            radius=8.865
        )
        
        # 应该能够处理空ID（会生成默认ID）
        db_hole = adapter.hole_data_to_db_model(invalid_hole_data, 1)
        assert db_hole.hole_id == "hole_100.000_200.000"
        
        print("✅ 转换错误处理测试通过")
    
    def test_status_mapping(self, adapter):
        """测试状态映射"""
        # 测试所有状态的映射
        status_pairs = [
            (HoleStatus.PENDING, 'not_detected'),
            (HoleStatus.QUALIFIED, 'qualified'),
            (HoleStatus.DEFECTIVE, 'defective'),
            (HoleStatus.BLIND, 'blind'),
            (HoleStatus.TIE_ROD, 'tie_rod'),
            (HoleStatus.PROCESSING, 'processing')
        ]
        
        for aidcis2_status, db_status in status_pairs:
            # 正向映射
            assert adapter.status_mapping[aidcis2_status] == db_status
            # 反向映射
            assert adapter.reverse_status_mapping[db_status] == aidcis2_status
        
        print("✅ 状态映射测试通过")
    
    def test_validation(self, adapter, sample_hole_data):
        """测试转换验证"""
        workpiece_id = 1
        
        # 转换并验证
        db_hole = adapter.hole_data_to_db_model(sample_hole_data, workpiece_id)
        is_valid = adapter.validate_conversion(sample_hole_data, db_hole, workpiece_id)
        
        assert is_valid
        
        # 测试无效转换
        db_hole.hole_id = "WRONG_ID"
        is_valid = adapter.validate_conversion(sample_hole_data, db_hole, workpiece_id)
        
        assert not is_valid
        
        print("✅ 转换验证测试通过")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
