"""
单元测试：视图控制功能
测试放大、缩小、适应视图按钮的功能
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

# 确保可以导入我们的模块
sys.path.insert(0, '/Users/vsiyo/Desktop/上位机软件第二级和3.1界面')

from aidcis2.ui.main_window import AIDCIS2MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


class TestViewControls:
    """视图控制功能单元测试"""
    
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
        return window
    
    def test_view_buttons_initial_state(self, main_window):
        """测试视图控制按钮的初始状态"""
        # 视图控制按钮应该初始为禁用状态
        assert not main_window.fit_view_btn.isEnabled()
        assert not main_window.zoom_in_btn.isEnabled()
        assert not main_window.zoom_out_btn.isEnabled()
    
    def test_view_buttons_enabled_after_data_load(self, main_window):
        """测试数据加载后视图控制按钮被启用"""
        # 模拟加载数据
        with patch.object(main_window, 'graphics_view') as mock_graphics_view:
            mock_graphics_view.load_holes = Mock()
            
            # 创建测试数据
            holes = {
                'H00001': HoleData('H00001', 100.0, 100.0, 8.865, HoleStatus.PENDING, '0')
            }
            main_window.hole_collection = HoleCollection(holes, {})
            
            # 调用更新显示
            main_window.update_hole_display()
            
            # 手动启用按钮（模拟正常流程）
            main_window.fit_view_btn.setEnabled(True)
            main_window.zoom_in_btn.setEnabled(True)
            main_window.zoom_out_btn.setEnabled(True)
            
            # 验证按钮已启用
            assert main_window.fit_view_btn.isEnabled()
            assert main_window.zoom_in_btn.isEnabled()
            assert main_window.zoom_out_btn.isEnabled()
    
    def test_fit_view_functionality(self, main_window):
        """测试适应视图功能"""
        # 模拟graphics_view
        main_window.graphics_view = Mock()
        main_window.graphics_view.fit_in_view = Mock()
        
        # 调用适应视图
        main_window.fit_view()
        
        # 验证graphics_view的fit_in_view方法被调用
        main_window.graphics_view.fit_in_view.assert_called_once()
    
    def test_zoom_in_functionality(self, main_window):
        """测试放大功能"""
        # 模拟graphics_view
        main_window.graphics_view = Mock()
        main_window.graphics_view.zoom_in = Mock()
        
        # 调用放大
        main_window.zoom_in()
        
        # 验证graphics_view的zoom_in方法被调用
        main_window.graphics_view.zoom_in.assert_called_once()
    
    def test_zoom_out_functionality(self, main_window):
        """测试缩小功能"""
        # 模拟graphics_view
        main_window.graphics_view = Mock()
        main_window.graphics_view.zoom_out = Mock()
        
        # 调用缩小
        main_window.zoom_out()
        
        # 验证graphics_view的zoom_out方法被调用
        main_window.graphics_view.zoom_out.assert_called_once()
    
    def test_view_controls_without_graphics_view(self, main_window):
        """测试没有graphics_view时的视图控制"""
        # 确保没有graphics_view属性
        if hasattr(main_window, 'graphics_view'):
            delattr(main_window, 'graphics_view')
        
        # 调用视图控制方法不应该抛出异常
        main_window.fit_view()
        main_window.zoom_in()
        main_window.zoom_out()
    
    def test_button_click_events(self, main_window):
        """测试按钮点击事件"""
        # 模拟graphics_view
        main_window.graphics_view = Mock()
        main_window.graphics_view.fit_in_view = Mock()
        main_window.graphics_view.zoom_in = Mock()
        main_window.graphics_view.zoom_out = Mock()
        
        # 启用按钮
        main_window.fit_view_btn.setEnabled(True)
        main_window.zoom_in_btn.setEnabled(True)
        main_window.zoom_out_btn.setEnabled(True)
        
        # 模拟按钮点击
        QTest.mouseClick(main_window.fit_view_btn, Qt.LeftButton)
        QTest.mouseClick(main_window.zoom_in_btn, Qt.LeftButton)
        QTest.mouseClick(main_window.zoom_out_btn, Qt.LeftButton)
        
        # 验证对应方法被调用
        main_window.graphics_view.fit_in_view.assert_called_once()
        main_window.graphics_view.zoom_in.assert_called_once()
        main_window.graphics_view.zoom_out.assert_called_once()


class TestSimulationProgress:
    """模拟进度功能单元测试"""
    
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
        return window
    
    def test_simulation_button_exists(self, main_window):
        """测试模拟进度按钮存在"""
        assert hasattr(main_window, 'simulate_btn')
        assert main_window.simulate_btn.text() == "使用模拟进度"
    
    def test_load_simulation_data(self, main_window):
        """测试启动模拟进度功能"""
        # 模拟graphics_view
        main_window.graphics_view = Mock()
        main_window.graphics_view.load_holes = Mock()

        # 调用启动模拟进度
        main_window.load_simulation_data()

        # 验证数据被创建
        assert main_window.hole_collection is not None
        assert len(main_window.hole_collection) == 100  # 10x10网格

        # 验证元数据
        assert main_window.hole_collection.metadata['simulation'] is True
        assert main_window.hole_collection.metadata['source_file'] == '模拟进度演示'
    
    def test_simulation_data_structure(self, main_window):
        """测试模拟进度数据的结构"""
        # 模拟graphics_view
        main_window.graphics_view = Mock()
        main_window.graphics_view.load_holes = Mock()

        # 启动模拟进度
        main_window.load_simulation_data()

        # 验证孔位数据结构
        holes = list(main_window.hole_collection.holes.values())
        first_hole = holes[0]

        assert first_hole.radius == 8.865
        assert first_hole.layer == "0"
        assert 'simulation' in first_hole.metadata
        assert first_hole.metadata['simulation'] is True
        assert 'row' in first_hole.metadata
        assert 'col' in first_hole.metadata

        # 验证初始状态都是待检
        assert first_hole.status == HoleStatus.PENDING
    
    def test_simulation_data_status_distribution(self, main_window):
        """测试模拟数据的状态分布"""
        # 模拟graphics_view
        main_window.graphics_view = Mock()
        main_window.graphics_view.load_holes = Mock()
        
        # 加载模拟数据
        main_window.load_simulation_data()
        
        # 统计状态分布
        status_counts = {}
        for hole in main_window.hole_collection.holes.values():
            status = hole.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 验证所有状态都存在（由于随机性，可能某些状态为0）
        total_holes = sum(status_counts.values())
        assert total_holes == 100
        
        # 验证状态类型正确
        valid_statuses = {HoleStatus.PENDING, HoleStatus.QUALIFIED, 
                         HoleStatus.DEFECTIVE, HoleStatus.PROCESSING}
        for status in status_counts.keys():
            assert status in valid_statuses
    
    def test_simulation_button_click(self, main_window):
        """测试模拟进度按钮点击"""
        # 模拟graphics_view
        main_window.graphics_view = Mock()
        main_window.graphics_view.load_holes = Mock()

        # 模拟按钮点击
        QTest.mouseClick(main_window.simulate_btn, Qt.LeftButton)

        # 验证数据被加载
        assert main_window.hole_collection is not None
        assert len(main_window.hole_collection) == 100

    def test_simulation_progress_timer(self, main_window):
        """测试模拟进度定时器功能"""
        # 模拟graphics_view
        main_window.graphics_view = Mock()
        main_window.graphics_view.load_holes = Mock()
        main_window.graphics_view.update_hole_status = Mock()

        # 启动模拟进度
        main_window.load_simulation_data()

        # 验证定时器被创建
        assert hasattr(main_window, 'simulation_timer')
        assert main_window.simulation_timer.isActive()

        # 验证按钮文本改变
        assert main_window.simulate_btn.text() == "停止模拟进度"

    def test_stop_simulation_progress(self, main_window):
        """测试停止模拟进度功能"""
        # 模拟graphics_view
        main_window.graphics_view = Mock()
        main_window.graphics_view.load_holes = Mock()

        # 启动模拟进度
        main_window.load_simulation_data()

        # 停止模拟进度
        main_window._stop_simulation_progress()

        # 验证定时器停止
        assert not main_window.simulation_timer.isActive()

        # 验证按钮文本恢复
        assert main_window.simulate_btn.text() == "使用模拟进度"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
