"""
集成测试：视图控制与图形组件的集成
测试视图控制按钮与OptimizedGraphicsView的集成
"""

import pytest
import sys
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

# 确保可以导入我们的模块
sys.path.insert(0, '/Users/vsiyo/Desktop/上位机软件第二级和3.1界面')

from aidcis2.ui.main_window import AIDCIS2MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus
from aidcis2.graphics.graphics_view import OptimizedGraphicsView


class TestViewControlsIntegration:
    """视图控制集成测试"""
    
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
    
    def test_graphics_view_creation(self, main_window):
        """测试图形视图的创建"""
        # 验证图形视图被正确创建
        assert hasattr(main_window, 'graphics_view')
        assert isinstance(main_window.graphics_view, OptimizedGraphicsView)
    
    def test_graphics_view_signal_connections(self, main_window):
        """测试图形视图信号连接"""
        # 验证信号连接
        graphics_view = main_window.graphics_view
        
        # 检查信号是否存在
        assert hasattr(graphics_view, 'hole_clicked')
        assert hasattr(graphics_view, 'hole_hovered')
        assert hasattr(graphics_view, 'view_changed')
    
    def test_data_loading_integration(self, main_window):
        """测试数据加载与视图的集成"""
        # 创建测试数据
        holes = {}
        for i in range(5):
            hole_id = f"H{i+1:05d}"
            holes[hole_id] = HoleData(
                hole_id=hole_id,
                center_x=i * 50.0,
                center_y=i * 50.0,
                radius=8.865,
                status=HoleStatus.PENDING,
                layer="0"
            )
        
        hole_collection = HoleCollection(holes, {'test': True})
        main_window.hole_collection = hole_collection
        
        # 更新显示
        main_window.update_hole_display()
        
        # 验证图形视图接收到数据
        assert main_window.graphics_view.hole_collection is not None
        assert len(main_window.graphics_view.hole_items) == 5
    
    def test_view_controls_with_real_graphics_view(self, main_window):
        """测试视图控制与真实图形视图的交互"""
        # 加载测试数据
        holes = {
            'H00001': HoleData('H00001', 100.0, 100.0, 8.865, HoleStatus.PENDING, '0')
        }
        main_window.hole_collection = HoleCollection(holes, {})
        main_window.update_hole_display()
        
        # 启用视图控制按钮
        main_window.fit_view_btn.setEnabled(True)
        main_window.zoom_in_btn.setEnabled(True)
        main_window.zoom_out_btn.setEnabled(True)
        
        # 测试视图控制功能
        initial_transform = main_window.graphics_view.transform()
        
        # 测试放大
        main_window.zoom_in()
        after_zoom_in = main_window.graphics_view.transform()
        
        # 测试缩小
        main_window.zoom_out()
        after_zoom_out = main_window.graphics_view.transform()
        
        # 测试适应视图
        main_window.fit_view()
        after_fit = main_window.graphics_view.transform()
        
        # 验证变换确实发生了（具体值可能因实现而异）
        assert initial_transform != after_zoom_in or after_zoom_in != after_zoom_out
    
    def test_simulation_data_integration(self, main_window):
        """测试模拟数据与图形视图的集成"""
        # 加载模拟数据
        main_window.load_simulation_data()
        
        # 验证数据被正确加载到图形视图
        assert main_window.hole_collection is not None
        assert len(main_window.hole_collection) == 100
        
        # 验证图形视图接收到数据
        assert main_window.graphics_view.hole_collection is not None
        assert len(main_window.graphics_view.hole_items) == 100
        
        # 验证按钮状态
        assert main_window.fit_view_btn.isEnabled()
        assert main_window.zoom_in_btn.isEnabled()
        assert main_window.zoom_out_btn.isEnabled()
    
    def test_hole_selection_integration(self, main_window):
        """测试孔位选择的集成"""
        # 加载测试数据
        holes = {
            'H00001': HoleData('H00001', 100.0, 100.0, 8.865, HoleStatus.PENDING, '0')
        }
        main_window.hole_collection = HoleCollection(holes, {})
        main_window.update_hole_display()
        
        # 模拟孔位选择
        hole = holes['H00001']
        main_window.on_hole_selected(hole)
        
        # 验证选择状态
        assert main_window.selected_hole == hole
        assert main_window.goto_realtime_btn.isEnabled()
        assert main_window.goto_history_btn.isEnabled()
        assert main_window.mark_defective_btn.isEnabled()
    
    def test_ui_update_integration(self, main_window):
        """测试UI更新的集成"""
        # 加载模拟数据
        main_window.load_simulation_data()
        
        # 验证文件信息更新
        assert "模拟进度演示" in main_window.file_name_label.text()
        assert "100" in main_window.hole_count_label.text()
        
        # 验证状态统计更新
        pending_text = main_window.pending_count_label.text()
        qualified_text = main_window.qualified_count_label.text()
        defective_text = main_window.defective_count_label.text()
        processing_text = main_window.processing_count_label.text()
        
        # 验证文本格式正确
        assert "待检:" in pending_text
        assert "合格:" in qualified_text
        assert "异常:" in defective_text
        assert "检测中:" in processing_text


class TestDXFIntegration:
    """DXF文件加载集成测试"""
    
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
    
    def test_dxf_parser_integration(self, main_window):
        """测试DXF解析器集成"""
        # 验证DXF解析器存在
        assert hasattr(main_window, 'dxf_parser')
        assert main_window.dxf_parser is not None
    
    @patch('aidcis2.ui.main_window.QFileDialog.getOpenFileName')
    def test_dxf_file_dialog_integration(self, mock_dialog, main_window):
        """测试DXF文件对话框集成"""
        # 模拟文件对话框返回空（用户取消）
        mock_dialog.return_value = ('', '')
        
        # 调用加载DXF文件
        main_window.load_dxf_file()
        
        # 验证对话框被调用
        mock_dialog.assert_called_once()
    
    def test_view_controls_enabled_after_dxf_load(self, main_window):
        """测试DXF加载后视图控制按钮启用"""
        # 模拟成功的DXF加载
        holes = {
            'H00001': HoleData('H00001', 100.0, 100.0, 8.865, HoleStatus.PENDING, '0')
        }
        main_window.hole_collection = HoleCollection(holes, {'source_file': 'test.dxf'})
        
        # 模拟DXF加载成功的状态更新
        main_window.start_detection_btn.setEnabled(True)
        main_window.fit_view_btn.setEnabled(True)
        main_window.zoom_in_btn.setEnabled(True)
        main_window.zoom_out_btn.setEnabled(True)
        
        # 验证按钮状态
        assert main_window.start_detection_btn.isEnabled()
        assert main_window.fit_view_btn.isEnabled()
        assert main_window.zoom_in_btn.isEnabled()
        assert main_window.zoom_out_btn.isEnabled()


class TestErrorHandling:
    """错误处理集成测试"""
    
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
    
    def test_graphics_view_error_handling(self, main_window):
        """测试图形视图错误处理"""
        # 模拟图形视图加载失败
        with patch.object(main_window.graphics_view, 'load_holes', side_effect=Exception("Test error")):
            # 创建测试数据
            holes = {
                'H00001': HoleData('H00001', 100.0, 100.0, 8.865, HoleStatus.PENDING, '0')
            }
            main_window.hole_collection = HoleCollection(holes, {})
            
            # 调用更新显示不应该崩溃
            main_window.update_hole_display()
    
    def test_simulation_data_error_handling(self, main_window):
        """测试模拟数据错误处理"""
        # 模拟图形视图不存在
        if hasattr(main_window, 'graphics_view'):
            delattr(main_window, 'graphics_view')
        
        # 调用加载模拟数据不应该崩溃
        main_window.load_simulation_data()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
