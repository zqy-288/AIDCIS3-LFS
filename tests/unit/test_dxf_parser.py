"""
UT-001, UT-002, UT-003: DXF解析器单元测试
测试DXF文件解析基础功能、孔位数据提取和HoleCollection生成
"""

import pytest
import tempfile
import os
from pathlib import Path
import ezdxf

from aidcis2.dxf_parser import DXFParser
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


# 全局fixture定义
@pytest.fixture
def parser():
    """创建DXF解析器实例"""
    return DXFParser()


@pytest.fixture
def sample_dxf_file():
    """创建测试用DXF文件"""
    # 创建临时DXF文件
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    # 添加测试孔位（两个半圆弧组成一个完整的孔）
    center = (100, 100)
    radius = 8.865

    # 添加第一个半圆弧 (0-180度)
    msp.add_arc(
        center=center,
        radius=radius,
        start_angle=0,
        end_angle=180,
        dxfattribs={'layer': '0'}
    )

    # 添加第二个半圆弧 (180-360度)
    msp.add_arc(
        center=center,
        radius=radius,
        start_angle=180,
        end_angle=360,
        dxfattribs={'layer': '0'}
    )

    # 添加第二个孔
    center2 = (200, 100)
    msp.add_arc(
        center=center2,
        radius=radius,
        start_angle=0,
        end_angle=180,
        dxfattribs={'layer': '0'}
    )
    msp.add_arc(
        center=center2,
        radius=radius,
        start_angle=180,
        end_angle=360,
        dxfattribs={'layer': '0'}
    )

    # 添加一个大圆（边界，应该被过滤）
    msp.add_arc(
        center=(0, 0),
        radius=2300,
        start_angle=0,
        end_angle=360,
        dxfattribs={'layer': '0'}
    )

    # 保存到临时文件
    with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as f:
        doc.saveas(f.name)
        yield f.name
        # 清理临时文件
        if os.path.exists(f.name):
            os.unlink(f.name)


@pytest.fixture
def empty_dxf_file():
    """创建空的DXF文件"""
    doc = ezdxf.new('R2010')
    with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as f:
        doc.saveas(f.name)
        yield f.name
        # 清理临时文件
        if os.path.exists(f.name):
            os.unlink(f.name)


@pytest.fixture
def invalid_dxf_file():
    """创建无效的DXF文件"""
    with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False, mode='w') as f:
        f.write("这不是一个有效的DXF文件")
        yield f.name
        # 清理临时文件
        if os.path.exists(f.name):
            os.unlink(f.name)


class TestDXFParserBasicFunctionality:
    """UT-001: DXF文件解析基础功能测试"""

    def test_parse_valid_dxf_file(self, parser, sample_dxf_file):
        """测试解析有效DXF文件"""
        result = parser.parse_file(sample_dxf_file)

        # 验证返回类型
        assert isinstance(result, HoleCollection)

        # 验证解析出了孔位
        assert len(result) > 0

        # 验证元数据
        assert 'source_file' in result.metadata
        assert 'dxf_version' in result.metadata
        assert result.metadata['source_file'] == sample_dxf_file

        print(f"✅ 成功解析DXF文件，识别到 {len(result)} 个孔位")
    
    def test_parse_empty_dxf_file(self, parser, empty_dxf_file):
        """测试解析空DXF文件"""
        result = parser.parse_file(empty_dxf_file)

        # 验证返回类型
        assert isinstance(result, HoleCollection)

        # 验证空文件结果
        assert len(result) == 0

        # 验证元数据存在
        assert 'source_file' in result.metadata

        print("✅ 空DXF文件解析正确")
    
    def test_parse_invalid_dxf_file(self, parser, invalid_dxf_file):
        """测试解析无效DXF文件"""
        with pytest.raises(Exception):  # 应该抛出异常
            parser.parse_file(invalid_dxf_file)

        print("✅ 无效DXF文件正确抛出异常")
    
    def test_parse_nonexistent_file(self, parser):
        """测试解析不存在的文件"""
        nonexistent_file = "/path/to/nonexistent/file.dxf"
        
        with pytest.raises(FileNotFoundError):
            parser.parse_file(nonexistent_file)
        
        print("✅ 不存在文件正确抛出FileNotFoundError")


class TestHoleDataExtraction:
    """UT-002: 孔位数据提取测试"""
    
    def test_extract_circle_entities(self, parser, sample_dxf_file):
        """测试提取圆形实体"""
        # 直接读取DXF文件测试弧形提取
        doc = ezdxf.readfile(sample_dxf_file)
        entities = list(doc.modelspace())

        arcs = parser._extract_arcs(entities)

        # 验证提取到弧形实体
        assert len(arcs) > 0

        # 验证所有提取的都是弧形
        for arc in arcs:
            assert arc.dxftype() == 'ARC'

        print(f"✅ 成功提取 {len(arcs)} 个弧形实体")
    
    def test_extract_hole_coordinates(self, parser, sample_dxf_file):
        """测试提取孔位坐标"""
        result = parser.parse_file(sample_dxf_file)

        # 验证孔位坐标
        holes = list(result.holes.values())
        assert len(holes) >= 2  # 应该有至少2个孔

        # 验证第一个孔的坐标
        hole1 = holes[0]
        assert isinstance(hole1.center_x, float)
        assert isinstance(hole1.center_y, float)
        assert hole1.center_x == 100.0
        assert hole1.center_y == 100.0

        print(f"✅ 孔位坐标提取正确: ({hole1.center_x}, {hole1.center_y})")

    def test_extract_hole_radius(self, parser, sample_dxf_file):
        """测试提取孔位半径"""
        result = parser.parse_file(sample_dxf_file)

        holes = list(result.holes.values())
        hole = holes[0]

        # 验证半径值
        assert isinstance(hole.radius, float)
        assert abs(hole.radius - 8.865) < 0.001  # 允许小误差

        print(f"✅ 孔位半径提取正确: {hole.radius}")
    
    def test_handle_malformed_entities(self, parser):
        """测试处理格式错误的实体"""
        # 创建包含格式错误实体的DXF文件
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        # 添加一个不完整的弧形（只有一个半圆）
        msp.add_arc(
            center=(100, 100),
            radius=8.865,
            start_angle=0,
            end_angle=90,  # 只有90度，不是完整的圆
            dxfattribs={'layer': '0'}
        )

        with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as f:
            doc.saveas(f.name)
            temp_file = f.name

        try:
            result = parser.parse_file(temp_file)

            # 不完整的弧形应该被过滤掉
            assert len(result) == 0

            print("✅ 格式错误的实体正确处理")

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestHoleCollectionGeneration:
    """UT-003: HoleCollection生成测试"""
    
    def test_create_hole_collection(self, parser, sample_dxf_file):
        """测试创建孔位集合"""
        result = parser.parse_file(sample_dxf_file)

        # 验证HoleCollection类型
        assert isinstance(result, HoleCollection)

        # 验证集合属性
        assert hasattr(result, 'holes')
        assert hasattr(result, 'total_count')
        assert hasattr(result, 'metadata')

        # 验证数据一致性
        assert result.total_count == len(result.holes)
        assert len(result) == result.total_count

        print(f"✅ HoleCollection创建成功，包含 {len(result)} 个孔位")

    def test_hole_id_generation(self, parser, sample_dxf_file):
        """测试孔位ID生成规则"""
        result = parser.parse_file(sample_dxf_file)

        holes = list(result.holes.values())

        # 验证ID格式
        for hole in holes:
            assert hole.hole_id.startswith('H')
            assert len(hole.hole_id) == 6  # H + 5位数字
            assert hole.hole_id[1:].isdigit()

        # 验证ID唯一性
        hole_ids = [hole.hole_id for hole in holes]
        assert len(hole_ids) == len(set(hole_ids))

        print(f"✅ 孔位ID生成正确: {hole_ids}")

    def test_empty_collection_handling(self, parser, empty_dxf_file):
        """测试空集合处理"""
        result = parser.parse_file(empty_dxf_file)

        # 验证空集合
        assert len(result) == 0
        assert result.total_count == 0
        assert len(result.holes) == 0

        # 验证空集合的方法
        assert result.get_bounds() == (0, 0, 0, 0)
        status_counts = result.get_status_counts()
        assert all(count == 0 for count in status_counts.values())

        print("✅ 空集合处理正确")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
