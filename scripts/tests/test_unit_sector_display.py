#!/usr/bin/env python3
"""
单元测试 - 扇形显示组件
测试扇形区域显示的各个独立功能
"""

import sys
import unittest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor

from aidcis2.graphics.sector_view import SectorGraphicsItem, SectorOverviewWidget
from aidcis2.graphics.sector_manager import SectorQuadrant, SectorProgress


class TestSectorGraphicsItem(unittest.TestCase):
    """测试扇形图形项"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """每个测试前的准备"""
        self.center = QPointF(0, 0)
        self.radius = 10  # 使用新的小半径
    
    def test_sector_creation(self):
        """测试扇形创建"""
        # 创建每个象限的扇形
        for sector in SectorQuadrant:
            item = SectorGraphicsItem(sector, self.center, self.radius)
            
            # 验证基本属性
            self.assertEqual(item.sector, sector)
            self.assertEqual(item.center, self.center)
            self.assertEqual(item.radius, self.radius)
            self.assertEqual(item.progress, 0.0)
            
            # 验证角度设置
            expected_angles = {
                SectorQuadrant.SECTOR_1: 0,
                SectorQuadrant.SECTOR_2: 90,
                SectorQuadrant.SECTOR_3: 180,
                SectorQuadrant.SECTOR_4: 270
            }
            self.assertEqual(item.start_angle, expected_angles[sector])
            self.assertEqual(item.span_angle, 90)
    
    def test_sector_names(self):
        """测试扇形名称"""
        expected_names = {
            SectorQuadrant.SECTOR_1: "区域1",
            SectorQuadrant.SECTOR_2: "区域2",
            SectorQuadrant.SECTOR_3: "区域3",
            SectorQuadrant.SECTOR_4: "区域4"
        }
        
        for sector in SectorQuadrant:
            item = SectorGraphicsItem(sector, self.center, self.radius)
            self.assertEqual(item._get_sector_name(), expected_names[sector])
    
    def test_progress_update(self):
        """测试进度更新"""
        item = SectorGraphicsItem(SectorQuadrant.SECTOR_1, self.center, self.radius)
        
        # 创建测试进度
        progress = SectorProgress(
            sector=SectorQuadrant.SECTOR_1,
            total_holes=100,
            completed_holes=75,
            qualified_holes=70,
            defective_holes=5,
            progress_percentage=75.0,
            status_color=QColor(0, 255, 0)
        )
        
        # 更新进度
        item.update_progress(progress)
        
        # 验证更新结果
        self.assertEqual(item.progress, 75.0)
        self.assertEqual(item.sector_color, QColor(0, 255, 0))
        self.assertIn("75.0%", item.text_item.toPlainText())
    
    def test_text_label_size(self):
        """测试文本标签大小"""
        item = SectorGraphicsItem(SectorQuadrant.SECTOR_1, self.center, self.radius)
        
        # 验证字体大小
        font = item.text_item.font()
        self.assertEqual(font.pointSize(), 3)  # 验证新的字体大小
        self.assertTrue(font.bold())


class TestSectorOverviewWidget(unittest.TestCase):
    """测试扇形概览组件"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """每个测试前的准备"""
        self.widget = SectorOverviewWidget()
    
    def test_widget_creation(self):
        """测试组件创建"""
        # 验证组件创建
        self.assertIsNotNone(self.widget)
        self.assertIsNotNone(self.widget.graphics_view)
        self.assertIsNotNone(self.widget.graphics_scene)
        
        # 验证扇形项创建
        self.assertEqual(len(self.widget.sector_items), 4)
        for sector in SectorQuadrant:
            self.assertIn(sector, self.widget.sector_items)
    
    def test_scene_setup(self):
        """测试场景设置"""
        # 验证场景大小和边距
        scene_rect = self.widget.graphics_scene.sceneRect()
        
        # 场景应该基于扇形大小（半径10）加上边距（3）
        # 预期场景大小应该较小
        self.assertLess(scene_rect.width(), 50)
        self.assertLess(scene_rect.height(), 50)
    
    def test_view_scaling(self):
        """测试视图缩放"""
        # 获取视图变换矩阵
        transform = self.widget.graphics_view.transform()
        
        # 验证缩放比例
        scale_x = transform.m11()
        scale_y = transform.m22()
        
        # 允许一定误差
        self.assertAlmostEqual(scale_x, 10.2, places=1)
        self.assertAlmostEqual(scale_y, 10.2, places=1)
    
    def test_overall_labels(self):
        """测试整体统计标签"""
        # 验证标签存在
        self.assertIsNotNone(self.widget.overall_progress_label)
        self.assertIsNotNone(self.widget.overall_qualified_label)
        
        # 验证初始文本
        self.assertIn("0%", self.widget.overall_progress_label.text())
        self.assertIn("0%", self.widget.overall_qualified_label.text())
    
    def test_update_overall_display(self):
        """测试整体显示更新"""
        # 模拟统计数据
        stats = {
            'total_holes': 100,
            'completed_holes': 80,
            'qualified_holes': 75
        }
        
        # 更新显示
        self.widget.update_overall_display(stats)
        
        # 验证更新结果
        self.assertIn("80.0%", self.widget.overall_progress_label.text())
        self.assertIn("93.8%", self.widget.overall_qualified_label.text())


class TestSectorIntegration(unittest.TestCase):
    """测试扇形组件集成"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def test_sector_manager_connection(self):
        """测试扇形管理器连接"""
        from aidcis2.graphics.sector_manager import SectorManager
        
        widget = SectorOverviewWidget()
        manager = SectorManager()
        
        # 设置管理器
        widget.set_sector_manager(manager)
        
        # 验证信号连接
        # 注意：实际信号连接需要在运行时验证
        self.assertEqual(widget.sector_manager, manager)
    
    def test_resize_behavior(self):
        """测试大小调整行为"""
        widget = SectorOverviewWidget()
        
        # 模拟大小调整事件
        widget.resize(200, 250)
        
        # 触发resize事件
        widget.resizeEvent(None)
        
        # 验证视图仍然适应场景
        scene_rect = widget.graphics_scene.sceneRect()
        view_rect = widget.graphics_view.viewport().rect()
        
        # 视图应该包含整个场景
        self.assertGreater(view_rect.width(), 0)
        self.assertGreater(view_rect.height(), 0)


if __name__ == "__main__":
    unittest.main()