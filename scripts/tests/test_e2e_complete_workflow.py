#!/usr/bin/env python3
"""
端到端测试 - 完整工作流程
测试从DXF加载到模拟进度的完整流程
"""

import sys
import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, Qt
from PySide6.QtTest import QTest

from main_window import MainWindow
from aidcis2.dxf_parser import DXFParser
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from aidcis2.graphics.sector_manager import SectorQuadrant


class TestE2ECompleteWorkflow(unittest.TestCase):
    """端到端完整工作流程测试"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """每个测试前的准备"""
        self.window = MainWindow()
        self.window.show()
        QTest.qWaitForWindowExposed(self.window)
    
    def tearDown(self):
        """每个测试后的清理"""
        if hasattr(self.window, 'simulation_timer_v2') and self.window.simulation_timer_v2:
            self.window.simulation_timer_v2.stop()
        self.window.close()
    
    def create_test_dxf_file(self):
        """创建测试DXF文件"""
        content = """0
SECTION
2
ENTITIES
0
CIRCLE
8
0
10
100.0
20
50.0
40
5.0
0
CIRCLE
8
0
10
-100.0
20
50.0
40
5.0
0
CIRCLE
8
0
10
-100.0
20
-50.0
40
5.0
0
CIRCLE
8
0
10
100.0
20
-50.0
40
5.0
0
ENDSEC
0
EOF"""
        
        # 创建临时文件
        fd, path = tempfile.mkstemp(suffix='.dxf')
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        
        return path
    
    def test_complete_workflow(self):
        """测试完整工作流程"""
        # Step 1: 创建并加载DXF文件
        dxf_path = self.create_test_dxf_file()
        
        try:
            # 模拟选择产品型号
            with patch.object(QMessageBox, 'information'):
                self.window.hole_collection = self.window.dxf_parser.parse_file(dxf_path)
                self.window.current_dxf_file = dxf_path
                self.window.load_dxf_to_views()
            
            # 验证DXF加载
            self.assertIsNotNone(self.window.hole_collection)
            self.assertEqual(len(self.window.hole_collection), 4)
            
            # Step 2: 验证DXF旋转
            # 检查元数据
            self.assertTrue(self.window.hole_collection.metadata.get('pre_rotated', False))
            
            # Step 3: 验证扇形管理器初始化
            self.assertIsNotNone(self.window.sector_manager)
            
            # 验证扇形分配
            for sector in SectorQuadrant:
                holes = self.window.sector_manager.get_sector_holes(sector)
                self.assertEqual(len(holes), 1, f"每个扇形应该有1个孔位")
            
            # Step 4: 验证UI组件初始化
            # 验证按钮启用
            self.assertTrue(self.window.simulate_btn.isEnabled())
            self.assertTrue(self.window.start_detection_btn.isEnabled())
            
            # 验证状态显示
            self.assertIn("0/4", self.window.progress_label.text())
            
            # Step 5: 测试扇形点击
            # 模拟点击扇形1
            if hasattr(self.window, 'sector_overview') and self.window.sector_overview:
                # 发射扇形选择信号
                self.window.sector_overview.sector_selected.emit(SectorQuadrant.SECTOR_1)
                
                # 验证动态扇形显示更新
                if hasattr(self.window, 'dynamic_sector_display'):
                    current = self.window.dynamic_sector_display.get_current_sector()
                    self.assertEqual(current, SectorQuadrant.SECTOR_1)
            
            # Step 6: 开始模拟进度
            self.window._start_simulation_progress_v2()
            
            # 验证模拟开始
            self.assertTrue(self.window.simulation_running_v2)
            self.assertEqual(self.window.simulate_btn.text(), "停止模拟")
            
            # Step 7: 执行几步模拟
            processed_count = 0
            for i in range(2):  # 处理2个孔位
                if self.window.simulation_index_v2 < len(self.window.holes_list_v2):
                    # 创建模拟图形项
                    hole = self.window.holes_list_v2[self.window.simulation_index_v2]
                    mock_item = MagicMock()
                    self.window.graphics_view.hole_items[hole.hole_id] = mock_item
                    
                    # 执行更新
                    self.window._update_simulation_v2()
                    processed_count += 1
                    
                    # 等待异步更新
                    QTest.qWait(150)
            
            # 验证处理
            self.assertGreater(processed_count, 0)
            
            # Step 8: 验证状态更新
            # 检查统计数据
            total_stats = sum(self.window.v2_stats.values())
            self.assertEqual(total_stats, processed_count)
            
            # Step 9: 停止模拟
            self.window._start_simulation_progress_v2()
            
            # 验证停止
            self.assertFalse(self.window.simulation_running_v2)
            self.assertEqual(self.window.simulate_btn.text(), "使用模拟进度")
            
        finally:
            # 清理临时文件
            os.unlink(dxf_path)
    
    def test_ui_responsiveness(self):
        """测试UI响应性"""
        # 创建测试数据
        dxf_path = self.create_test_dxf_file()
        
        try:
            # 加载数据
            with patch.object(QMessageBox, 'information'):
                self.window.hole_collection = self.window.dxf_parser.parse_file(dxf_path)
                self.window.load_dxf_to_views()
            
            # 测试缩放功能
            initial_transform = self.window.graphics_view.transform()
            
            # 放大
            self.window.zoom_in()
            zoom_in_transform = self.window.graphics_view.transform()
            self.assertNotEqual(initial_transform.m11(), zoom_in_transform.m11())
            
            # 缩小
            self.window.zoom_out()
            zoom_out_transform = self.window.graphics_view.transform()
            self.assertLess(zoom_out_transform.m11(), zoom_in_transform.m11())
            
            # 适应窗口
            self.window.fit_view()
            
            # 重置视图
            self.window.reset_view()
            
        finally:
            os.unlink(dxf_path)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试没有加载DXF时的操作
        with patch.object(QMessageBox, 'warning') as mock_warning:
            # 尝试开始检测
            self.window.start_detection()
            mock_warning.assert_called_once()
            
            # 重置mock
            mock_warning.reset_mock()
            
            # 尝试开始模拟
            self.window._start_simulation_progress_v2()
            mock_warning.assert_called_once()
    
    def test_data_persistence(self):
        """测试数据持久性"""
        dxf_path = self.create_test_dxf_file()
        
        try:
            # 加载数据
            with patch.object(QMessageBox, 'information'):
                self.window.hole_collection = self.window.dxf_parser.parse_file(dxf_path)
                self.window.load_dxf_to_views()
            
            # 修改一些孔位状态
            hole_ids = list(self.window.hole_collection.holes.keys())
            if len(hole_ids) >= 2:
                self.window.hole_collection.holes[hole_ids[0]].status = HoleStatus.QUALIFIED
                self.window.hole_collection.holes[hole_ids[1]].status = HoleStatus.DEFECTIVE
            
            # 更新显示
            self.window.update_status_display()
            
            # 验证状态保持
            self.assertEqual(
                self.window.hole_collection.holes[hole_ids[0]].status,
                HoleStatus.QUALIFIED
            )
            self.assertEqual(
                self.window.hole_collection.holes[hole_ids[1]].status,
                HoleStatus.DEFECTIVE
            )
            
            # 验证统计更新
            self.assertIn("2/4", self.window.progress_label.text())
            
        finally:
            os.unlink(dxf_path)


class TestE2EUserInteractions(unittest.TestCase):
    """端到端用户交互测试"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """每个测试前的准备"""
        self.window = MainWindow()
        
        # 创建测试数据
        holes = {}
        for i in range(8):
            angle = i * 45  # 每45度一个孔
            import math
            x = 100 * math.cos(math.radians(angle))
            y = 100 * math.sin(math.radians(angle))
            
            holes[f"H{i+1:03d}"] = HoleData(
                hole_id=f"H{i+1:03d}",
                center_x=x,
                center_y=y,
                radius=5,
                status=HoleStatus.NOT_DETECTED
            )
        
        self.hole_collection = HoleCollection(holes=holes)
    
    def tearDown(self):
        """每个测试后的清理"""
        self.window.close()
    
    def test_search_functionality(self):
        """测试搜索功能"""
        # 加载数据
        self.window.hole_collection = self.hole_collection
        self.window.graphics_view.load_holes(self.hole_collection)
        self.window.update_completer_data()
        
        # 测试搜索
        self.window.search_input.setText("H003")
        self.window.perform_search()
        
        # 验证搜索结果
        # 注意：实际搜索功能可能需要进一步实现
        log_text = self.window.log_text.toPlainText()
        self.assertIn("搜索", log_text)
    
    def test_view_filtering(self):
        """测试视图过滤"""
        # 加载数据
        self.window.hole_collection = self.hole_collection
        
        # 更新一些状态
        holes_list = list(self.hole_collection.holes.values())
        holes_list[0].status = HoleStatus.QUALIFIED
        holes_list[1].status = HoleStatus.DEFECTIVE
        
        # 测试不同的过滤选项
        filter_options = ["待检", "合格", "异常", "盲孔", "拉杆孔", "检测中"]
        
        for option in filter_options:
            self.window.view_combo.setCurrentText(option)
            self.window.filter_holes(option)
            
            # 验证日志
            log_text = self.window.log_text.toPlainText()
            self.assertIn(f"过滤视图: {option}", log_text)
    
    def test_hole_selection_operations(self):
        """测试孔位选择操作"""
        # 加载数据
        self.window.hole_collection = self.hole_collection
        self.window.graphics_view.load_holes(self.hole_collection)
        
        # 模拟选择孔位
        test_hole = list(self.hole_collection.holes.values())[0]
        self.window.selected_hole = test_hole
        
        # 测试跳转到实时监控（应该显示警告）
        with patch.object(QMessageBox, 'warning') as mock_warning:
            self.window.goto_realtime()
            mock_warning.assert_called_once()
            
            # 验证警告消息
            args = mock_warning.call_args[0]
            self.assertIn("没有实时监控数据", args[2])
        
        # 测试跳转到历史数据（应该显示警告）
        with patch.object(QMessageBox, 'warning') as mock_warning:
            self.window.goto_history()
            mock_warning.assert_called_once()
            
            # 验证警告消息
            args = mock_warning.call_args[0]
            self.assertIn("没有历史数据", args[2])
    
    def test_detection_control_flow(self):
        """测试检测控制流程"""
        # 加载数据
        self.window.hole_collection = self.hole_collection
        
        # 开始检测
        self.window.start_detection()
        
        # 验证检测状态
        self.assertTrue(self.window.detection_running)
        self.assertFalse(self.window.start_detection_btn.isEnabled())
        self.assertTrue(self.window.pause_detection_btn.isEnabled())
        self.assertTrue(self.window.stop_detection_btn.isEnabled())
        
        # 暂停检测
        self.window.pause_detection()
        self.assertTrue(self.window.detection_paused)
        self.assertEqual(self.window.pause_detection_btn.text(), "恢复检测")
        
        # 恢复检测
        self.window.pause_detection()
        self.assertFalse(self.window.detection_paused)
        self.assertEqual(self.window.pause_detection_btn.text(), "暂停检测")
        
        # 停止检测
        self.window.stop_detection()
        self.assertFalse(self.window.detection_running)
        self.assertTrue(self.window.start_detection_btn.isEnabled())
        self.assertFalse(self.window.pause_detection_btn.isEnabled())


if __name__ == "__main__":
    unittest.main()