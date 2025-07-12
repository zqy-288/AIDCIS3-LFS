#!/usr/bin/env python3
"""
动态扇形功能单元测试
"""

import unittest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from aidcis2.graphics.dynamic_sector_manager import DynamicSectorManager, DynamicSectorQuadrant
from aidcis2.graphics.sector_manager_adapter import SectorManagerAdapter
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


class TestDynamicSector(unittest.TestCase):
    """测试动态扇形功能"""
    
    def test_dynamic_sector_manager_creation(self):
        """测试动态扇形管理器创建"""
        # 测试不同扇形数量
        for sector_count in [2, 3, 4, 6, 8, 12]:
            manager = DynamicSectorManager(sector_count)
            self.assertEqual(manager.sector_count, sector_count)
            self.assertEqual(len(manager.sectors), sector_count)
            
            # 验证扇形角度
            angle_per_sector = 360 / sector_count
            for i, sector in enumerate(manager.sectors):
                expected_start = i * angle_per_sector
                expected_end = (i + 1) * angle_per_sector
                self.assertAlmostEqual(sector.start_angle, expected_start, places=2)
                self.assertAlmostEqual(sector.end_angle, expected_end, places=2)
    
    def test_sector_manager_adapter(self):
        """测试扇形管理器适配器"""
        adapter = SectorManagerAdapter()
        
        # 默认应该是4扇形固定模式
        self.assertEqual(adapter.get_sector_count(), 4)
        
        # 切换到动态模式
        adapter.set_dynamic_mode(True, 6)
        self.assertEqual(adapter.get_sector_count(), 6)
        
        # 切换回固定模式
        adapter.set_dynamic_mode(False)
        self.assertEqual(adapter.get_sector_count(), 4)
    
    def test_hole_assignment_to_sectors(self):
        """测试孔位分配到扇形"""
        manager = DynamicSectorManager(4)
        
        # 创建测试孔位
        holes = []
        # 在每个象限创建一个孔
        positions = [(100, 0), (0, 100), (-100, 0), (0, -100)]
        for i, (x, y) in enumerate(positions):
            hole = HoleData(
                hole_id=f"H{i+1:03d}",
                center_x=x,
                center_y=y,
                radius=5.0,
                status=HoleStatus.PENDING
            )
            holes.append(hole)
        
        # 创建孔位集合
        holes_dict = {hole.hole_id: hole for hole in holes}
        hole_collection = HoleCollection(holes=holes_dict)
        
        # 加载到管理器
        manager.load_hole_collection(hole_collection)
        
        # 验证每个扇形有一个孔
        for i in range(4):
            sector = manager.sectors[i]
            progress = manager.get_sector_progress(sector)
            self.assertEqual(progress.total_holes, 1)
    
    def test_invalid_sector_count(self):
        """测试无效的扇形数量"""
        with self.assertRaises(ValueError):
            DynamicSectorManager(1)  # 太少
        
        with self.assertRaises(ValueError):
            DynamicSectorManager(13)  # 太多
        
        with self.assertRaises(ValueError):
            adapter = SectorManagerAdapter()
            adapter.set_dynamic_mode(True, 20)


if __name__ == "__main__":
    unittest.main()