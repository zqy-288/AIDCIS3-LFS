"""
系统测试：完整工作流程测试
测试从启动应用到使用视图控制和模拟数据的完整流程
"""

import pytest
import sys
import time
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

# 确保可以导入我们的模块
sys.path.insert(0, '/Users/vsiyo/Desktop/上位机软件第二级和3.1界面')

from aidcis2.ui.main_window import AIDCIS2MainWindow
from aidcis2.models.hole_data import HoleStatus


class TestCompleteWorkflow:
    """完整工作流程系统测试"""
    
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
        window.show()  # 显示窗口进行系统测试
        return window
    
    def test_application_startup(self, main_window):
        """测试应用程序启动"""
        # 验证窗口正确创建和显示
        assert main_window.isVisible()
        assert main_window.windowTitle() == "AIDCIS2 - 管孔检测系统"
        
        # 验证初始状态
        assert not main_window.start_detection_btn.isEnabled()
        assert not main_window.fit_view_btn.isEnabled()
        assert not main_window.zoom_in_btn.isEnabled()
        assert not main_window.zoom_out_btn.isEnabled()
        
        # 验证模拟数据按钮可用
        assert main_window.simulate_btn.isEnabled()
    
    def test_simulation_data_workflow(self, main_window):
        """测试模拟数据完整工作流程"""
        # 步骤1: 点击模拟数据按钮
        QTest.mouseClick(main_window.simulate_btn, Qt.LeftButton)
        
        # 等待数据加载
        QApplication.processEvents()
        
        # 验证数据加载成功
        assert main_window.hole_collection is not None
        assert len(main_window.hole_collection) == 100
        
        # 验证UI更新
        assert "模拟进度演示" in main_window.file_name_label.text()
        assert "100" in main_window.hole_count_label.text()
        
        # 验证按钮状态更新
        assert main_window.start_detection_btn.isEnabled()
        assert main_window.fit_view_btn.isEnabled()
        assert main_window.zoom_in_btn.isEnabled()
        assert main_window.zoom_out_btn.isEnabled()
        
        # 验证图形视图加载数据
        assert main_window.graphics_view.hole_collection is not None
        assert len(main_window.graphics_view.hole_items) == 100
    
    def test_view_controls_workflow(self, main_window):
        """测试视图控制完整工作流程"""
        # 先加载模拟数据
        main_window.load_simulation_data()
        QApplication.processEvents()
        
        # 获取初始变换
        initial_transform = main_window.graphics_view.transform()
        
        # 步骤1: 测试适应视图
        QTest.mouseClick(main_window.fit_view_btn, Qt.LeftButton)
        QApplication.processEvents()
        
        # 步骤2: 测试放大
        for _ in range(3):  # 连续放大3次
            QTest.mouseClick(main_window.zoom_in_btn, Qt.LeftButton)
            QApplication.processEvents()
        
        zoom_in_transform = main_window.graphics_view.transform()
        
        # 步骤3: 测试缩小
        for _ in range(2):  # 缩小2次
            QTest.mouseClick(main_window.zoom_out_btn, Qt.LeftButton)
            QApplication.processEvents()
        
        zoom_out_transform = main_window.graphics_view.transform()
        
        # 验证变换确实发生
        assert initial_transform != zoom_in_transform
        assert zoom_in_transform != zoom_out_transform
    
    def test_hole_interaction_workflow(self, main_window):
        """测试孔位交互完整工作流程"""
        # 加载模拟数据
        main_window.load_simulation_data()
        QApplication.processEvents()
        
        # 获取第一个孔位
        first_hole = list(main_window.hole_collection.holes.values())[0]
        
        # 模拟孔位选择
        main_window.on_hole_selected(first_hole)
        QApplication.processEvents()
        
        # 验证选择状态
        assert main_window.selected_hole == first_hole
        assert main_window.goto_realtime_btn.isEnabled()
        assert main_window.goto_history_btn.isEnabled()
        assert main_window.mark_defective_btn.isEnabled()
        
        # 验证详细信息更新
        assert first_hole.hole_id in main_window.selected_hole_id_label.text()
    
    def test_status_distribution_workflow(self, main_window):
        """测试状态分布显示工作流程"""
        # 加载模拟数据
        main_window.load_simulation_data()
        QApplication.processEvents()
        
        # 验证状态统计显示
        pending_text = main_window.pending_count_label.text()
        qualified_text = main_window.qualified_count_label.text()
        defective_text = main_window.defective_count_label.text()
        processing_text = main_window.processing_count_label.text()
        
        # 提取数字
        import re
        pending_count = int(re.search(r'\d+', pending_text).group())
        qualified_count = int(re.search(r'\d+', qualified_text).group())
        defective_count = int(re.search(r'\d+', defective_text).group())
        processing_count = int(re.search(r'\d+', processing_text).group())
        
        # 验证总数正确
        total_count = pending_count + qualified_count + defective_count + processing_count
        assert total_count == 100
        
        # 验证进度条更新
        progress_value = main_window.progress_bar.value()
        assert 0 <= progress_value <= 100
    
    def test_multiple_data_loads_workflow(self, main_window):
        """测试多次数据加载工作流程"""
        # 第一次加载模拟数据
        main_window.load_simulation_data()
        QApplication.processEvents()

        assert main_window.hole_collection is not None
        assert len(main_window.hole_collection) == 100

        # 第二次加载模拟数据
        main_window.load_simulation_data()
        QApplication.processEvents()

        # 验证数据仍然正确
        assert main_window.hole_collection is not None
        assert len(main_window.hole_collection) == 100
    
    def test_ui_responsiveness_workflow(self, main_window):
        """测试UI响应性工作流程"""
        # 加载大量数据
        main_window.load_simulation_data()
        
        # 快速连续操作
        operations = [
            lambda: QTest.mouseClick(main_window.fit_view_btn, Qt.LeftButton),
            lambda: QTest.mouseClick(main_window.zoom_in_btn, Qt.LeftButton),
            lambda: QTest.mouseClick(main_window.zoom_out_btn, Qt.LeftButton),
            lambda: QTest.mouseClick(main_window.zoom_in_btn, Qt.LeftButton),
            lambda: QTest.mouseClick(main_window.fit_view_btn, Qt.LeftButton),
        ]
        
        # 执行快速操作序列
        for operation in operations:
            operation()
            QApplication.processEvents()
        
        # 验证应用程序仍然响应
        assert main_window.isVisible()
        assert main_window.graphics_view.hole_collection is not None
    
    def test_memory_usage_workflow(self, main_window):
        """测试内存使用工作流程"""
        import gc

        # 多次加载数据
        for _ in range(5):
            main_window.load_simulation_data()
            QApplication.processEvents()
            gc.collect()

        # 验证最终状态正确
        assert main_window.hole_collection is not None
        assert len(main_window.hole_collection) == 100
    
    def test_error_recovery_workflow(self, main_window):
        """测试错误恢复工作流程"""
        # 模拟错误情况
        with patch.object(main_window.graphics_view, 'load_holes', side_effect=Exception("Test error")):
            # 尝试加载数据
            main_window.load_simulation_data()
            QApplication.processEvents()
        
        # 恢复正常操作
        main_window.load_simulation_data()
        QApplication.processEvents()
        
        # 验证应用程序恢复正常
        assert main_window.hole_collection is not None
        assert len(main_window.hole_collection) == 100
    
    def test_performance_workflow(self, main_window):
        """测试性能工作流程"""
        import time
        
        # 测试数据加载性能
        start_time = time.time()
        main_window.load_simulation_data()
        QApplication.processEvents()
        load_time = time.time() - start_time
        
        # 验证加载时间合理（应该在几秒内完成）
        assert load_time < 5.0  # 5秒内完成
        
        # 测试视图操作性能
        start_time = time.time()
        for _ in range(10):
            main_window.zoom_in()
            main_window.zoom_out()
            QApplication.processEvents()
        operation_time = time.time() - start_time
        
        # 验证操作时间合理
        assert operation_time < 2.0  # 2秒内完成


class TestUserScenarios:
    """用户场景系统测试"""
    
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
        window.show()
        return window
    
    def test_new_user_scenario(self, main_window):
        """测试新用户使用场景"""
        # 场景：新用户首次使用软件
        
        # 1. 用户启动软件
        assert main_window.isVisible()
        
        # 2. 用户看到界面，尝试使用模拟数据
        QTest.mouseClick(main_window.simulate_btn, Qt.LeftButton)
        QApplication.processEvents()
        
        # 3. 用户看到数据加载，尝试视图操作
        QTest.mouseClick(main_window.fit_view_btn, Qt.LeftButton)
        QApplication.processEvents()
        
        # 4. 用户尝试放大查看细节
        QTest.mouseClick(main_window.zoom_in_btn, Qt.LeftButton)
        QApplication.processEvents()
        
        # 验证用户操作成功
        assert main_window.hole_collection is not None
        assert main_window.fit_view_btn.isEnabled()
    
    def test_expert_user_scenario(self, main_window):
        """测试专家用户使用场景"""
        # 场景：专家用户快速操作
        
        # 1. 快速加载数据
        main_window.load_simulation_data()
        QApplication.processEvents()
        
        # 2. 快速浏览不同区域
        for _ in range(5):
            main_window.zoom_in()
            main_window.zoom_out()
            main_window.fit_view()
            QApplication.processEvents()
        
        # 3. 选择特定孔位进行分析
        first_hole = list(main_window.hole_collection.holes.values())[0]
        main_window.on_hole_selected(first_hole)
        QApplication.processEvents()
        
        # 验证专家操作流畅
        assert main_window.selected_hole is not None
        assert main_window.goto_realtime_btn.isEnabled()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
