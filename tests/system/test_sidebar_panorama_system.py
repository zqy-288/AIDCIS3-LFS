#!/usr/bin/env python3
"""
侧边栏全景图系统测试
测试完整的用户工作流程和系统级功能
"""

import unittest
import sys
from pathlib import Path
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt, QTimer, QEventLoop

from main_window import MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from aidcis2.graphics.sector_manager import SectorQuadrant


class TestSidebarPanoramaSystem(unittest.TestCase):
    """侧边栏全景图系统测试类"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """设置每个测试"""
        self.main_window = MainWindow()
        self.main_window.show()
        QTest.qWait(1000)  # 等待UI完全初始化
        
        # 创建完整的工作流程测试数据
        self.create_realistic_test_data()
    
    def tearDown(self):
        """清理每个测试"""
        if self.main_window:
            self.main_window.close()
        QTest.qWait(100)
    
    def create_realistic_test_data(self):
        """创建真实的测试数据集"""
        test_holes = {}
        
        # 模拟真实的管板孔位分布 - 5x5网格，每个象限有不同密度
        hole_id_counter = 1
        
        # 第一象限 (右上) - 密集分布
        for x in range(10, 100, 15):
            for y in range(10, 100, 15):
                hole = HoleData(
                    hole_id=f"H{hole_id_counter:03d}",
                    center_x=float(x),
                    center_y=float(y),
                    radius=2.5,
                    status=HoleStatus.PENDING
                )
                test_holes[hole.hole_id] = hole
                hole_id_counter += 1
        
        # 第二象限 (左上) - 中等密度
        for x in range(-90, -10, 20):
            for y in range(10, 90, 20):
                hole = HoleData(
                    hole_id=f"H{hole_id_counter:03d}",
                    center_x=float(x),
                    center_y=float(y),
                    radius=2.5,
                    status=HoleStatus.PENDING
                )
                test_holes[hole.hole_id] = hole
                hole_id_counter += 1
        
        # 第三象限 (左下) - 稀疏分布
        for x in range(-80, -20, 30):
            for y in range(-80, -20, 30):
                hole = HoleData(
                    hole_id=f"H{hole_id_counter:03d}",
                    center_x=float(x),
                    center_y=float(y),
                    radius=2.5,
                    status=HoleStatus.PENDING
                )
                test_holes[hole.hole_id] = hole
                hole_id_counter += 1
        
        # 第四象限 (右下) - 不规则分布
        positions = [(20, -30), (40, -50), (60, -20), (80, -70), (50, -40), (30, -60)]
        for x, y in positions:
            hole = HoleData(
                hole_id=f"H{hole_id_counter:03d}",
                center_x=float(x),
                center_y=float(y),
                radius=2.5,
                status=HoleStatus.PENDING
            )
            test_holes[hole.hole_id] = hole
            hole_id_counter += 1
        
        self.test_collection = HoleCollection(
            holes=test_holes,
            metadata={'source_file': 'system_test.dxf', 'total_holes': len(test_holes)}
        )
        
        # 加载数据到主窗口
        self.main_window.hole_collection = self.test_collection
        self.main_window.update_hole_display()
        QTest.qWait(500)
    
    def test_complete_user_workflow(self):
        """测试完整的用户工作流程"""
        print("\\n=== 测试完整用户工作流程 ===")
        
        # 1. 验证初始状态
        self.assertTrue(self.main_window.isVisible(), "主窗口应该可见")
        self.assertTrue(self.main_window.sidebar_panorama.isVisible(), "侧边栏全景图应该可见")
        
        total_holes = len(self.test_collection)
        print(f"✓ 加载了 {total_holes} 个孔位的测试数据")
        
        # 2. 测试扇形选择工作流程
        print("\\n--- 测试扇形选择工作流程 ---")
        for sector in SectorQuadrant:
            print(f"选择扇形: {sector.value}")
            
            # 选择扇形
            self.main_window.on_sector_selected(sector)
            QTest.qWait(200)
            
            # 验证视图切换
            current_sector = self.main_window.dynamic_sector_display.get_current_sector()
            self.assertEqual(current_sector, sector, f"应该切换到扇形 {sector}")
            
            # 验证统计信息更新
            stats_text = self.main_window.sector_stats_label.text()
            self.assertIn(sector.value.replace('_', ''), stats_text.replace(' ', '').replace('_', ''))
            
            print(f"✓ 扇形 {sector.value} 选择和显示正常")
        
        # 3. 测试扇形专注显示工作流程
        print("\\n--- 测试扇形专注显示功能 ---")
        
        # 验证初始状态显示第一个扇形
        current_sector = self.main_window.dynamic_sector_display.get_current_sector()
        self.assertEqual(current_sector, SectorQuadrant.SECTOR_1, "初始状态应显示第一个扇形")
        
        # 验证主视图只显示第一个扇形的孔位
        main_view = self.main_window.graphics_view
        if hasattr(main_view, 'hole_items'):
            displayed_holes = len(main_view.hole_items)
            sector_1_holes = self.main_window.sector_manager.get_sector_holes(SectorQuadrant.SECTOR_1)
            expected_holes = len(sector_1_holes)
            print(f"主视图显示: {displayed_holes} 个孔位，扇形1预期: {expected_holes} 个孔位")
            
            # 主视图应该只显示扇形1的孔位，不是全景
            total_holes = len(self.test_collection)
            self.assertLess(displayed_holes, total_holes, 
                           f"主视图应显示扇形专注内容({expected_holes})，而不是完整全景({total_holes})")
        
        # 测试扇形切换
        for i, sector in enumerate([SectorQuadrant.SECTOR_2, SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4]):
            print(f"切换到扇形: {sector.value}")
            self.main_window.dynamic_sector_display.switch_to_sector(sector)
            QTest.qWait(200)
            
            # 验证切换成功
            current_sector = self.main_window.dynamic_sector_display.get_current_sector()
            self.assertEqual(current_sector, sector, f"应该切换到{sector.value}")
            
            # 验证显示的孔位数量正确
            if hasattr(main_view, 'hole_items'):
                displayed_holes = len(main_view.hole_items)
                sector_holes = self.main_window.sector_manager.get_sector_holes(sector)
                expected_holes = len(sector_holes)
                print(f"  扇形{sector.value}: 显示{displayed_holes}个孔位，预期{expected_holes}个")
        
        print("✓ 扇形专注显示功能正常")
        
        # 4. 测试模拟工作流程
        print("\\n--- 测试模拟功能集成 ---")
        
        # 启用模拟按钮
        self.assertTrue(self.main_window.simulate_btn.isEnabled(), "模拟按钮应该启用")
        
        # 模拟一些检测结果
        test_holes = list(self.test_collection.holes.values())
        status_updates = [
            (HoleStatus.QUALIFIED, 5),
            (HoleStatus.DEFECTIVE, 3), 
            (HoleStatus.BLIND, 2)
        ]
        
        updated_count = 0
        for status, count in status_updates:
            for i in range(count):
                if updated_count < len(test_holes):
                    hole = test_holes[updated_count]
                    hole.status = status
                    self.main_window.sector_manager.update_hole_status(hole.hole_id, status)
                    updated_count += 1
        
        # 更新显示
        self.main_window.update_status_display()
        QTest.qWait(300)
        
        print(f"✓ 更新了 {updated_count} 个孔位的状态")
        
        # 4. 验证统计信息更新
        print("\\n--- 验证统计信息更新 ---")
        for sector in SectorQuadrant:
            progress = self.main_window.sector_manager.get_sector_progress(sector)
            if progress and progress.completed_holes > 0:
                print(f"✓ 扇形 {sector.value}: {progress.completed_holes} 已完成，{progress.qualified_holes} 合格")
    
    def test_performance_under_load(self):
        """测试系统负载性能"""
        print("\\n=== 测试系统负载性能 ===")
        
        # 快速切换扇形测试
        start_time = time.time()
        
        for _ in range(10):  # 快速切换10轮
            for sector in SectorQuadrant:
                self.main_window.on_sector_selected(sector)
                QTest.qWait(50)  # 短暂等待
        
        switch_time = time.time() - start_time
        print(f"✓ 40次扇形切换耗时: {switch_time:.2f}秒")
        self.assertLess(switch_time, 10.0, "扇形切换性能应该良好")
        
        # 批量状态更新测试
        start_time = time.time()
        
        test_holes = list(self.test_collection.holes.values())
        for i, hole in enumerate(test_holes[:20]):  # 更新前20个孔位
            status = HoleStatus.QUALIFIED if i % 2 == 0 else HoleStatus.DEFECTIVE
            hole.status = status
            self.main_window.sector_manager.update_hole_status(hole.hole_id, status)
        
        self.main_window.update_status_display()
        QTest.qWait(200)
        
        update_time = time.time() - start_time
        print(f"✓ 批量状态更新耗时: {update_time:.2f}秒")
        self.assertLess(update_time, 5.0, "批量更新性能应该良好")
    
    def test_layout_stability(self):
        """测试布局稳定性"""
        print("\\n=== 测试布局稳定性 ===")
        
        # 窗口大小变化测试
        original_size = self.main_window.size()
        
        # 调整窗口大小
        self.main_window.resize(1200, 800)
        QTest.qWait(200)
        
        self.main_window.resize(800, 600)
        QTest.qWait(200)
        
        self.main_window.resize(original_size)
        QTest.qWait(200)
        
        # 验证组件仍然可见和功能正常
        self.assertTrue(self.main_window.sidebar_panorama.isVisible())
        self.assertTrue(self.main_window.dynamic_sector_display.isVisible())
        self.assertTrue(self.main_window.sector_overview.isVisible())
        
        print("✓ 窗口大小变化后布局保持稳定")
        
        # 扇形选择功能性测试
        self.main_window.on_sector_selected(SectorQuadrant.SECTOR_2)
        QTest.qWait(100)
        
        current_sector = self.main_window.dynamic_sector_display.get_current_sector()
        self.assertEqual(current_sector, SectorQuadrant.SECTOR_2)
        
        print("✓ 布局变化后功能保持正常")
    
    def test_error_recovery(self):
        """测试错误恢复能力"""
        print("\\n=== 测试错误恢复能力 ===")
        
        # 模拟空数据情况
        empty_collection = HoleCollection(holes={}, metadata={'source_file': 'empty.dxf', 'total_holes': 0})
        
        try:
            self.main_window.hole_collection = empty_collection
            self.main_window.update_hole_display()
            QTest.qWait(200)
            
            # 应该不会崩溃，且UI仍然响应
            self.assertTrue(self.main_window.isVisible())
            print("✓ 空数据处理正常")
            
        except Exception as e:
            self.fail(f"空数据处理失败: {e}")
        
        # 恢复正常数据
        self.main_window.hole_collection = self.test_collection
        self.main_window.update_hole_display()
        QTest.qWait(200)
        
        # 验证恢复正常
        panorama_info = self.main_window.sidebar_panorama.info_label.text()
        self.assertNotIn("暂无数据", panorama_info)
        print("✓ 数据恢复正常")
    
    def test_memory_usage(self):
        """测试内存使用情况"""
        print("\\n=== 测试内存使用 ===")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 多次加载数据模拟内存使用
        for i in range(5):
            # 创建大量孔位数据
            large_holes = {}
            for j in range(500):
                hole = HoleData(
                    hole_id=f"MEM{i}_{j:03d}",
                    center_x=float(j % 50 * 10),
                    center_y=float(j // 50 * 10),
                    radius=2.5,
                    status=HoleStatus.PENDING
                )
                large_holes[hole.hole_id] = hole
            
            large_collection = HoleCollection(
                holes=large_holes,
                metadata={'source_file': f'memory_test_{i}.dxf', 'total_holes': len(large_holes)}
            )
            
            self.main_window.hole_collection = large_collection
            self.main_window.update_hole_display()
            QTest.qWait(300)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"✓ 内存使用: 初始 {initial_memory:.1f}MB, 最终 {final_memory:.1f}MB, 增长 {memory_increase:.1f}MB")
        
        # 内存增长应该合理（小于200MB）
        self.assertLess(memory_increase, 200, f"内存增长过大: {memory_increase:.1f}MB")
    
    def test_comprehensive_workflow(self):
        """测试综合工作流程"""
        print("\\n=== 测试综合工作流程 ===")
        
        workflow_steps = [
            "数据加载",
            "扇形选择", 
            "状态更新",
            "统计查看",
            "视图切换",
            "最终验证"
        ]
        
        for i, step in enumerate(workflow_steps):
            print(f"步骤 {i+1}: {step}")
            
            if step == "数据加载":
                # 验证数据已正确加载
                self.assertGreater(len(self.test_collection), 0)
                
            elif step == "扇形选择":
                # 选择每个扇形并验证
                for sector in SectorQuadrant:
                    self.main_window.on_sector_selected(sector)
                    QTest.qWait(100)
                    
            elif step == "状态更新":
                # 更新一些孔位状态
                test_holes = list(self.test_collection.holes.values())
                for i, hole in enumerate(test_holes[:10]):
                    status = [HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE, HoleStatus.BLIND][i % 3]
                    hole.status = status
                    self.main_window.sector_manager.update_hole_status(hole.hole_id, status)
                
            elif step == "统计查看":
                # 查看每个扇形的统计
                for sector in SectorQuadrant:
                    self.main_window.on_sector_selected(sector)
                    QTest.qWait(50)
                    progress = self.main_window.sector_manager.get_sector_progress(sector)
                    if progress:
                        self.assertGreaterEqual(progress.total_holes, 0)
                        
            elif step == "视图切换":
                # 快速切换视图
                for _ in range(3):
                    for sector in SectorQuadrant:
                        self.main_window.dynamic_sector_display.switch_to_sector(sector)
                        QTest.qWait(30)
                        
            elif step == "最终验证":
                # 最终状态验证
                self.assertTrue(self.main_window.isVisible())
                self.assertTrue(self.main_window.sidebar_panorama.isVisible())
                self.assertIsNotNone(self.main_window.hole_collection)
            
            print(f"  ✓ {step} 完成")
        
        print("✓ 综合工作流程测试通过")
    
    def test_sector_focused_simulation_workflow(self):
        """测试扇形专注模拟完整工作流程"""
        print("\\n=== 测试扇形专注模拟工作流程 ===")
        
        # 1. 验证初始扇形专注显示
        current_sector = self.main_window.dynamic_sector_display.get_current_sector()
        self.assertEqual(current_sector, SectorQuadrant.SECTOR_1)
        print("✓ 初始显示扇形1")
        
        # 2. 模拟扇形顺序检测流程
        sector_sequence = [SectorQuadrant.SECTOR_1, SectorQuadrant.SECTOR_2, 
                          SectorQuadrant.SECTOR_3, SectorQuadrant.SECTOR_4]
        
        for step, sector in enumerate(sector_sequence):
            print(f"\\n步骤 {step+1}: 模拟检测点移动到 {sector.value}")
            
            # 模拟检测点移动触发扇形切换
            self.main_window.dynamic_sector_display.switch_to_sector(sector)
            QTest.qWait(300)
            
            # 验证主视图切换到对应扇形
            current_sector = self.main_window.dynamic_sector_display.get_current_sector()
            self.assertEqual(current_sector, sector)
            
            # 验证主视图只显示该扇形孔位
            main_view = self.main_window.graphics_view
            if hasattr(main_view, 'hole_items'):
                displayed_holes = len(main_view.hole_items)
                sector_holes = self.main_window.sector_manager.get_sector_holes(sector)
                expected_holes = len(sector_holes)
                
                self.assertEqual(displayed_holes, expected_holes,
                               f"{sector.value}: 应显示{expected_holes}个孔位，实际{displayed_holes}个")
                print(f"  ✓ 主视图专注显示 {sector.value} 的 {displayed_holes} 个孔位")
            
            # 模拟在该扇形中检测几个孔位
            sector_holes = self.main_window.sector_manager.get_sector_holes(sector)
            for i, hole in enumerate(sector_holes[:2]):  # 每个扇形检测前2个孔位
                # 模拟检测过程：检测中 -> 结果
                hole.status = HoleStatus.PROCESSING
                QTest.qWait(50)
                
                # 设置最终结果
                result_status = HoleStatus.QUALIFIED if i % 2 == 0 else HoleStatus.DEFECTIVE
                hole.status = result_status
                self.main_window.sector_manager.update_hole_status(hole.hole_id, result_status)
                
                print(f"    ✓ 检测孔位 {hole.hole_id}: {result_status.value}")
        
        # 3. 验证侧边栏全景图始终显示完整数据
        panorama_info = self.main_window.sidebar_panorama.info_label.text()
        total_holes = len(self.test_collection)
        self.assertIn(str(total_holes), panorama_info)
        print(f"✓ 侧边栏全景图始终显示全部 {total_holes} 个孔位")
        
        # 4. 验证扇形统计信息正确更新
        for sector in SectorQuadrant:
            progress = self.main_window.sector_manager.get_sector_progress(sector)
            if progress and progress.completed_holes > 0:
                print(f"✓ {sector.value}: {progress.completed_holes} 已完成，{progress.qualified_holes} 合格")
        
        print("\\n✅ 扇形专注模拟工作流程测试完成")


def run_tests():
    """运行测试"""
    # 设置详细输出
    unittest.main(verbosity=2, buffer=False)


if __name__ == "__main__":
    run_tests()