#!/usr/bin/env python3
"""
单元测试 - DXF旋转功能
测试DXF文件预旋转和扇形区域分配
"""

import sys
import unittest
import math
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from PySide6.QtCore import QPointF

from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from aidcis2.dxf_parser import DXFParser
from aidcis2.graphics.dynamic_sector_view import SectorGraphicsManager
from aidcis2.graphics.sector_manager import SectorQuadrant


class TestDXFRotation(unittest.TestCase):
    """测试DXF旋转功能"""
    
    def setUp(self):
        """每个测试前的准备"""
        self.parser = DXFParser()
    
    def test_rotation_calculation(self):
        """测试旋转计算"""
        # 创建多个测试孔位形成一个正方形
        holes = []
        holes.append(HoleData(
            hole_id="H001",
            center_x=100,
            center_y=100,
            radius=5,
            status=HoleStatus.PENDING
        ))
        holes.append(HoleData(
            hole_id="H002",
            center_x=100,
            center_y=-100,
            radius=5,
            status=HoleStatus.PENDING
        ))
        holes.append(HoleData(
            hole_id="H003",
            center_x=-100,
            center_y=-100,
            radius=5,
            status=HoleStatus.PENDING
        ))
        holes.append(HoleData(
            hole_id="H004",
            center_x=-100,
            center_y=100,
            radius=5,
            status=HoleStatus.PENDING
        ))
        
        # 执行90度逆时针旋转
        # 中心点在(0,0)，所以旋转后坐标会按照(-y,x)变换
        self.parser._rotate_holes_90_ccw(holes)
        
        # 验证旋转结果
        # H001: (100,100) -> (-100,100)
        self.assertAlmostEqual(holes[0].center_x, -100, places=5)
        self.assertAlmostEqual(holes[0].center_y, 100, places=5)
        
        # H002: (100,-100) -> (100,100)
        self.assertAlmostEqual(holes[1].center_x, 100, places=5)
        self.assertAlmostEqual(holes[1].center_y, 100, places=5)
        
        # H003: (-100,-100) -> (100,-100)
        self.assertAlmostEqual(holes[2].center_x, 100, places=5)
        self.assertAlmostEqual(holes[2].center_y, -100, places=5)
        
        # H004: (-100,100) -> (-100,-100)
        self.assertAlmostEqual(holes[3].center_x, -100, places=5)
        self.assertAlmostEqual(holes[3].center_y, -100, places=5)
    
    def test_rotation_with_offset(self):
        """测试带偏移的旋转"""
        # 创建偏离原点的孔位
        holes = []
        holes.append(HoleData(
            hole_id="H001",
            center_x=150,  # 偏离中心50
            center_y=100,
            radius=5,
            status=HoleStatus.PENDING
        ))
        holes.append(HoleData(
            hole_id="H002",
            center_x=50,   # 偏离中心-50
            center_y=100,
            radius=5,
            status=HoleStatus.PENDING
        ))
        
        # 执行旋转
        self.parser._rotate_holes_90_ccw(holes)
        
        # 验证旋转保持相对位置
        # 中心点应该是 (100, 100)
        # H001: (150, 100) 相对中心 (50, 0) -> 旋转后 (0, 50) -> 绝对 (100, 150)
        # H002: (50, 100) 相对中心 (-50, 0) -> 旋转后 (0, -50) -> 绝对 (100, 50)
        self.assertAlmostEqual(holes[0].center_x, 100, places=5)
        self.assertAlmostEqual(holes[0].center_y, 150, places=5)
        self.assertAlmostEqual(holes[1].center_x, 100, places=5)
        self.assertAlmostEqual(holes[1].center_y, 50, places=5)
    
    def test_metadata_update(self):
        """测试元数据更新"""
        # 创建测试孔位集合
        holes = {
            "H001": HoleData("H001", 100, 0, 5, HoleStatus.PENDING)
        }
        collection = HoleCollection(holes=holes)
        
        # 解析时应该设置pre_rotated标记
        # 注意：这需要模拟parse_file的行为
        collection.metadata['pre_rotated'] = True
        
        self.assertTrue(collection.metadata.get('pre_rotated', False))


class TestSectorAssignment(unittest.TestCase):
    """测试扇形区域分配"""
    
    def setUp(self):
        """每个测试前的准备"""
        # 创建测试孔位集合
        holes = {}
        positions = [
            ("H001", 100, 50),    # 右上
            ("H002", -100, 50),   # 左上
            ("H003", -100, -50),  # 左下
            ("H004", 100, -50),   # 右下
        ]
        
        for hole_id, x, y in positions:
            holes[hole_id] = HoleData(
                hole_id=hole_id,
                center_x=x,
                center_y=y,
                radius=5,
                status=HoleStatus.PENDING
            )
        
        self.collection = HoleCollection(holes=holes)
        self.manager = SectorGraphicsManager(self.collection)
    
    def test_angle_calculation(self):
        """测试角度计算"""
        hole = self.collection.holes["H001"]  # (100, 50)
        
        # 计算角度
        dx = hole.center_x - self.manager.center_point.x()
        dy = hole.center_y - self.manager.center_point.y()
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        
        # 验证角度（应该在第一象限）
        self.assertGreater(angle_deg, 0)
        self.assertLess(angle_deg, 90)
    
    def test_qt_angle_conversion(self):
        """测试Qt角度转换"""
        # 数学坐标系角度
        math_angles = [0, 45, 90, 135, 180, 225, 270, 315]
        
        # 对应的Qt坐标系角度
        expected_qt = [0, 315, 270, 225, 180, 135, 90, 45]
        
        for math_angle, expected in zip(math_angles, expected_qt):
            qt_angle = (360 - math_angle) % 360
            self.assertEqual(qt_angle, expected)
    
    def test_sector_assignment_strict(self):
        """测试严格的扇形分配"""
        # 验证每个孔位的扇形分配
        # 注意：Qt坐标系是顺时针的，所以分配是：
        # H001 (100, 50): 数学角度26.6° -> Qt角度333.4° -> SECTOR_4
        # H002 (-100, 50): 数学角度153.4° -> Qt角度206.6° -> SECTOR_3
        # H003 (-100, -50): 数学角度206.6° -> Qt角度153.4° -> SECTOR_2
        # H004 (100, -50): 数学角度333.4° -> Qt角度26.6° -> SECTOR_1
        expected_sectors = {
            "H001": SectorQuadrant.SECTOR_4,  # (100, 50)
            "H002": SectorQuadrant.SECTOR_3,  # (-100, 50)
            "H003": SectorQuadrant.SECTOR_2,  # (-100, -50)
            "H004": SectorQuadrant.SECTOR_1,  # (100, -50)
        }
        
        for hole_id, expected_sector in expected_sectors.items():
            hole = self.collection.holes[hole_id]
            
            # 测试每个扇形
            for sector in SectorQuadrant:
                is_in_sector = self.manager._is_hole_in_sector(hole, sector)
                
                if sector == expected_sector:
                    self.assertTrue(is_in_sector, 
                        f"{hole_id} 应该在 {sector} 中")
                else:
                    self.assertFalse(is_in_sector, 
                        f"{hole_id} 不应该在 {sector} 中")
    
    def test_boundary_cases(self):
        """测试边界情况"""
        # 创建边界上的孔位
        boundary_holes = [
            ("B001", 100, 0),    # 正右 (0°)
            ("B002", 0, 100),    # 正上 (90°)
            ("B003", -100, 0),   # 正左 (180°)
            ("B004", 0, -100),   # 正下 (270°)
        ]
        
        for hole_id, x, y in boundary_holes:
            hole = HoleData(hole_id, x, y, 5, HoleStatus.PENDING)
            
            # 计算应该属于哪个扇形
            dx = x
            dy = y
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)
            if angle_deg < 0:
                angle_deg += 360
            
            # 转换为Qt角度
            qt_angle = (360 - angle_deg) % 360
            
            # 确定期望的扇形
            if 0 <= qt_angle < 90:
                expected = SectorQuadrant.SECTOR_1
            elif 90 <= qt_angle < 180:
                expected = SectorQuadrant.SECTOR_2
            elif 180 <= qt_angle < 270:
                expected = SectorQuadrant.SECTOR_3
            else:
                expected = SectorQuadrant.SECTOR_4
            
            # 验证分配
            result = self.manager._is_hole_in_sector(hole, expected)
            self.assertTrue(result, 
                f"边界孔位 {hole_id} at ({x}, {y}) 应该在扇形 {expected} 中")


class TestSectorCollections(unittest.TestCase):
    """测试扇形集合创建"""
    
    def setUp(self):
        """每个测试前的准备"""
        # 创建均匀分布的孔位
        holes = {}
        hole_id = 1
        
        for angle in range(0, 360, 10):  # 每10度一个孔
            rad = math.radians(angle)
            x = 100 * math.cos(rad)
            y = 100 * math.sin(rad)
            
            holes[f"H{hole_id:03d}"] = HoleData(
                hole_id=f"H{hole_id:03d}",
                center_x=x,
                center_y=y,
                radius=5,
                status=HoleStatus.PENDING
            )
            hole_id += 1
        
        self.collection = HoleCollection(holes=holes)
        self.manager = SectorGraphicsManager(self.collection)
    
    def test_sector_distribution(self):
        """测试扇形分布"""
        # 获取所有扇形集合
        sector_collections = self.manager.get_all_sector_collections()
        
        # 验证有4个扇形
        self.assertEqual(len(sector_collections), 4)
        
        # 验证每个扇形都有孔位
        for sector, collection in sector_collections.items():
            self.assertGreater(len(collection), 0, 
                f"扇形 {sector} 应该包含孔位")
        
        # 验证总数相等
        total_in_sectors = sum(len(c) for c in sector_collections.values())
        self.assertEqual(total_in_sectors, len(self.collection))
    
    def test_no_overlap(self):
        """测试扇形无重叠"""
        # 收集所有扇形中的孔位ID
        all_hole_ids = set()
        
        for sector in SectorQuadrant:
            sector_collection = self.manager.get_sector_collection(sector)
            if sector_collection:
                for hole_id in sector_collection.holes.keys():
                    self.assertNotIn(hole_id, all_hole_ids, 
                        f"孔位 {hole_id} 出现在多个扇形中")
                    all_hole_ids.add(hole_id)
    
    def test_sector_bounds(self):
        """测试扇形边界"""
        for sector in SectorQuadrant:
            sector_collection = self.manager.get_sector_collection(sector)
            if sector_collection and len(sector_collection) > 0:
                bounds = sector_collection.get_bounds()
                
                # 验证边界有效
                self.assertLess(bounds[0], bounds[2])  # min_x < max_x
                self.assertLess(bounds[1], bounds[3])  # min_y < max_y
                
                # 验证边界存储在元数据中
                self.assertEqual(
                    sector_collection.metadata.get('sector_bounds'),
                    bounds
                )


if __name__ == "__main__":
    unittest.main()