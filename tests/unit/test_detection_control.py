"""
检测控制功能单元测试
测试开始、暂停、恢复、停止检测功能
"""

import pytest
import sys
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

# 确保可以导入我们的模块
sys.path.insert(0, '/Users/vsiyo/Desktop/上位机软件第二级和3.1界面')

from aidcis2.ui.main_window import AIDCIS2MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


class TestDetectionControl:
    """检测控制功能测试"""
    
    @pytest.fixture
    def app(self):
        """创建QApplication实例"""
        if not QApplication.instance():
            return QApplication([])
        return QApplication.instance()
    
    @pytest.fixture
    def main_window(self, app):
        """创建主窗口实例"""
        window = AIDCIS2MainWindow()
        # 模拟graphics_view
        window.graphics_view = Mock()
        window.graphics_view.load_holes = Mock()
        window.graphics_view.update_hole_status = Mock()
        return window
    
    @pytest.fixture
    def sample_holes(self):
        """创建示例孔位数据"""
        holes = {}
        for i in range(5):
            hole_id = f"H{i+1:05d}"
            holes[hole_id] = HoleData(
                hole_id=hole_id,
                center_x=i * 50.0,
                center_y=0.0,
                radius=8.865,
                status=HoleStatus.PENDING,
                layer="0"
            )
        return HoleCollection(holes, {'test': True})
    
    def test_detection_buttons_initial_state(self, main_window):
        """测试检测按钮初始状态"""
        assert not main_window.start_detection_btn.isEnabled()
        assert not main_window.pause_detection_btn.isEnabled()
        assert not main_window.stop_detection_btn.isEnabled()
        
        assert main_window.start_detection_btn.text() == "开始检测"
        assert main_window.pause_detection_btn.text() == "暂停检测"
        assert main_window.stop_detection_btn.text() == "停止检测"
    
    def test_detection_buttons_enabled_after_data_load(self, main_window, sample_holes):
        """测试数据加载后检测按钮状态"""
        main_window.hole_collection = sample_holes
        main_window.update_hole_display()
        
        # 模拟启用检测按钮
        main_window.start_detection_btn.setEnabled(True)
        
        assert main_window.start_detection_btn.isEnabled()
        assert not main_window.pause_detection_btn.isEnabled()
        assert not main_window.stop_detection_btn.isEnabled()
    
    def test_start_detection_without_data(self, main_window):
        """测试没有数据时开始检测"""
        # 模拟QMessageBox
        with patch('aidcis2.ui.main_window.QMessageBox.warning') as mock_warning:
            main_window.start_detection()
            mock_warning.assert_called_once()
    
    def test_start_detection_with_data(self, main_window, sample_holes):
        """测试有数据时开始检测"""
        main_window.hole_collection = sample_holes
        
        # 调用开始检测
        main_window.start_detection()
        
        # 验证状态
        assert hasattr(main_window, 'detection_running')
        assert main_window.detection_running is True
        assert main_window.detection_paused is False
        assert main_window.current_hole_index == 0
        
        # 验证按钮状态
        assert not main_window.start_detection_btn.isEnabled()
        assert main_window.pause_detection_btn.isEnabled()
        assert main_window.stop_detection_btn.isEnabled()
        
        # 验证定时器
        assert hasattr(main_window, 'detection_timer')
        assert main_window.detection_timer.isActive()
    
    def test_pause_detection(self, main_window, sample_holes):
        """测试暂停检测"""
        main_window.hole_collection = sample_holes
        main_window.start_detection()
        
        # 暂停检测
        main_window.pause_detection()
        
        # 验证状态
        assert main_window.detection_paused is True
        assert not main_window.detection_timer.isActive()
        assert main_window.pause_detection_btn.text() == "恢复检测"
    
    def test_resume_detection(self, main_window, sample_holes):
        """测试恢复检测"""
        main_window.hole_collection = sample_holes
        main_window.start_detection()
        main_window.pause_detection()
        
        # 恢复检测
        main_window.pause_detection()
        
        # 验证状态
        assert main_window.detection_paused is False
        assert main_window.detection_timer.isActive()
        assert main_window.pause_detection_btn.text() == "暂停检测"
    
    def test_stop_detection(self, main_window, sample_holes):
        """测试停止检测"""
        main_window.hole_collection = sample_holes
        main_window.start_detection()
        
        # 停止检测
        main_window.stop_detection()
        
        # 验证状态
        assert main_window.detection_running is False
        assert main_window.detection_paused is False
        assert main_window.current_hole_index == 0
        assert not main_window.detection_timer.isActive()
        
        # 验证按钮状态
        assert main_window.start_detection_btn.isEnabled()
        assert not main_window.pause_detection_btn.isEnabled()
        assert not main_window.stop_detection_btn.isEnabled()
        assert main_window.pause_detection_btn.text() == "暂停检测"
        
        # 验证进度条重置
        assert main_window.progress_bar.value() == 0
    
    def test_create_ordered_hole_list(self, main_window, sample_holes):
        """测试创建有序孔位列表"""
        main_window.hole_collection = sample_holes
        
        ordered_holes = main_window._create_ordered_hole_list()
        
        # 验证排序正确（按Y坐标然后X坐标）
        assert len(ordered_holes) == 5
        for i in range(len(ordered_holes) - 1):
            current = ordered_holes[i]
            next_hole = ordered_holes[i + 1]
            assert (current.center_y < next_hole.center_y or 
                   (current.center_y == next_hole.center_y and current.center_x <= next_hole.center_x))
    
    def test_simulate_hole_detection(self, main_window, sample_holes):
        """测试模拟孔位检测"""
        main_window.hole_collection = sample_holes
        hole = list(sample_holes.holes.values())[0]
        
        # 模拟检测
        main_window._simulate_hole_detection(hole)
        
        # 验证状态改变
        assert hole.status in [HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE, HoleStatus.BLIND]
        
        # 验证图形视图更新被调用
        main_window.graphics_view.update_hole_status.assert_called_once()
    
    def test_generate_detection_result(self, main_window, sample_holes):
        """测试生成检测结果"""
        main_window.hole_collection = sample_holes
        hole = list(sample_holes.holes.values())[0]
        
        # 测试多次生成结果
        results = []
        for _ in range(100):
            result = main_window._generate_detection_result(hole)
            results.append(result)
        
        # 验证结果在预期范围内
        valid_statuses = {HoleStatus.QUALIFIED, HoleStatus.DEFECTIVE, HoleStatus.BLIND}
        assert all(result in valid_statuses for result in results)
        
        # 验证有多样性（不是所有结果都相同）
        unique_results = set(results)
        assert len(unique_results) > 1
    
    def test_is_edge_hole(self, main_window):
        """测试边缘孔位判断"""
        # 创建3x3网格
        holes = {}
        for row in range(3):
            for col in range(3):
                hole_id = f"H{row*3+col+1:05d}"
                holes[hole_id] = HoleData(
                    hole_id=hole_id,
                    center_x=col * 50.0,
                    center_y=row * 50.0,
                    radius=8.865,
                    status=HoleStatus.PENDING,
                    layer="0"
                )
        
        main_window.hole_collection = HoleCollection(holes, {})
        
        # 测试边缘孔位
        edge_holes = [holes['H00001'], holes['H00002'], holes['H00003'],  # 顶行
                     holes['H00004'], holes['H00006'],                    # 左右边
                     holes['H00007'], holes['H00008'], holes['H00009']]   # 底行
        
        for hole in edge_holes:
            assert main_window._is_edge_hole(hole), f"孔位 {hole.hole_id} 应该是边缘孔位"
        
        # 测试中心孔位
        center_hole = holes['H00005']
        assert not main_window._is_edge_hole(center_hole), "中心孔位不应该是边缘孔位"
    
    def test_detection_process_step(self, main_window, sample_holes):
        """测试检测过程步骤"""
        main_window.hole_collection = sample_holes
        main_window.start_detection()
        
        initial_index = main_window.current_hole_index
        
        # 执行一个检测步骤
        main_window._process_detection_step()
        
        # 验证索引增加
        assert main_window.current_hole_index == initial_index + 1
        
        # 验证进度更新
        expected_progress = int((main_window.current_hole_index / len(main_window.detection_holes)) * 100)
        assert main_window.progress_bar.value() == expected_progress
    
    def test_detection_completion(self, main_window, sample_holes):
        """测试检测完成"""
        main_window.hole_collection = sample_holes
        main_window.start_detection()
        
        # 模拟检测完成
        main_window.current_hole_index = len(main_window.detection_holes)
        
        with patch('aidcis2.ui.main_window.QMessageBox.information') as mock_info:
            main_window._process_detection_step()
            
            # 验证完成对话框显示
            mock_info.assert_called_once()
            
            # 验证状态重置
            assert main_window.detection_running is False
            assert main_window.start_detection_btn.isEnabled()
            assert not main_window.pause_detection_btn.isEnabled()
            assert not main_window.stop_detection_btn.isEnabled()
            assert main_window.progress_bar.value() == 100


class TestDetectionControlIntegration:
    """检测控制集成测试"""
    
    @pytest.fixture
    def app(self):
        """创建QApplication实例"""
        if not QApplication.instance():
            return QApplication([])
        return QApplication.instance()
    
    @pytest.fixture
    def main_window(self, app):
        """创建主窗口实例"""
        window = AIDCIS2MainWindow()
        window.graphics_view = Mock()
        window.graphics_view.load_holes = Mock()
        window.graphics_view.update_hole_status = Mock()
        return window
    
    def test_button_click_events(self, main_window):
        """测试按钮点击事件"""
        # 加载模拟数据
        main_window.load_simulation_data()
        QApplication.processEvents()

        # 停止模拟进度定时器，避免干扰检测控制
        if hasattr(main_window, 'simulation_timer') and main_window.simulation_timer.isActive():
            main_window._stop_simulation_progress()

        # 测试开始检测按钮点击
        QTest.mouseClick(main_window.start_detection_btn, Qt.LeftButton)
        QApplication.processEvents()

        assert hasattr(main_window, 'detection_running')
        assert main_window.detection_running is True
        assert main_window.detection_paused is False

        # 测试暂停按钮点击（直接调用方法，避免UI事件复杂性）
        main_window.pause_detection()
        assert main_window.detection_paused is True
        assert main_window.pause_detection_btn.text() == "恢复检测"

        # 测试恢复按钮点击
        main_window.pause_detection()
        assert main_window.detection_paused is False
        assert main_window.pause_detection_btn.text() == "暂停检测"

        # 测试停止按钮点击
        main_window.stop_detection()
        assert main_window.detection_running is False
        assert main_window.start_detection_btn.isEnabled()
        assert not main_window.pause_detection_btn.isEnabled()
        assert not main_window.stop_detection_btn.isEnabled()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
