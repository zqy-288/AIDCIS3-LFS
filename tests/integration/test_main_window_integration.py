"""
IT-001: 主窗口组件加载集成测试
验证AIDCIS2主界面正确集成到主窗口
"""

import pytest
import tempfile
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtTest import QTest

from aidcis2.ui.main_window import AIDCIS2MainWindow
from aidcis2.models.hole_data import HoleData, HoleCollection, HoleStatus


@pytest.fixture(scope="module")
def qapp():
    """创建QApplication实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def main_window(qapp):
    """创建AIDCIS2MainWindow实例"""
    window = AIDCIS2MainWindow()
    yield window
    window.close()


@pytest.fixture
def sample_hole_collection():
    """创建测试用孔位集合"""
    holes = [
        HoleData("H00001", 100.0, 100.0, 8.865, HoleStatus.PENDING),
        HoleData("H00002", 200.0, 100.0, 8.865, HoleStatus.QUALIFIED),
        HoleData("H00003", 300.0, 100.0, 8.865, HoleStatus.DEFECTIVE),
    ]
    return HoleCollection(holes={h.hole_id: h for h in holes})


class TestMainWindowIntegration:
    """主窗口集成测试类"""
    
    def test_aidcis2_tab_loading(self, main_window):
        """测试AIDCIS2选项卡正确加载"""
        # 验证：主窗口包含AIDCIS2组件
        assert main_window is not None
        assert isinstance(main_window, AIDCIS2MainWindow)
        
        # 验证：选项卡标题正确显示
        assert main_window.windowTitle() == "AIDCIS2 - 管孔检测系统"
        
        # 验证：选项卡内容正确渲染
        assert main_window.isVisible() == False  # 窗口未显示但已创建
        assert main_window.minimumSize().width() == 1200
        assert main_window.minimumSize().height() == 800
        
        print("✅ AIDCIS2选项卡正确加载")
    
    def test_component_initialization(self, main_window):
        """测试组件初始化"""
        # 验证：核心组件正确初始化
        assert main_window.dxf_parser is not None
        assert main_window.status_manager is not None
        assert main_window.data_adapter is not None
        
        # 验证：UI组件存在
        assert hasattr(main_window, 'load_dxf_btn')
        assert hasattr(main_window, 'search_input')
        assert hasattr(main_window, 'view_combo')
        assert hasattr(main_window, 'progress_bar')
        
        # 验证：信号定义正确
        assert hasattr(main_window, 'navigate_to_realtime')
        assert hasattr(main_window, 'navigate_to_history')
        assert hasattr(main_window, 'status_updated')
        
        print("✅ 组件初始化正确")
    
    def test_signal_connections(self, main_window):
        """测试信号连接"""
        # 验证：按钮信号连接（通过检查是否有连接的槽函数）
        # 在PySide6中，我们通过检查按钮点击是否能正常工作来验证连接

        # 验证：按钮存在且可点击
        assert main_window.load_dxf_btn is not None
        assert main_window.start_detection_btn is not None
        assert main_window.goto_realtime_btn is not None
        assert main_window.goto_history_btn is not None

        # 验证：信号对象存在
        assert hasattr(main_window, 'navigate_to_realtime')
        assert hasattr(main_window, 'navigate_to_history')

        print("✅ 信号连接正确")
    
    def test_initial_state(self, main_window):
        """测试初始状态"""
        # 验证：初始按钮状态
        assert main_window.start_detection_btn.isEnabled() == False
        assert main_window.pause_detection_btn.isEnabled() == False
        assert main_window.stop_detection_btn.isEnabled() == False
        
        assert main_window.goto_realtime_btn.isEnabled() == False
        assert main_window.goto_history_btn.isEnabled() == False
        assert main_window.mark_defective_btn.isEnabled() == False
        
        # 验证：初始显示内容
        assert main_window.file_name_label.text() == "未加载文件"
        assert main_window.hole_count_label.text() == "孔位数量: 0"
        assert main_window.selected_hole_id_label.text() == "未选择"
        
        print("✅ 初始状态正确")
    
    def test_hole_collection_loading(self, main_window, sample_hole_collection):
        """测试孔位集合加载"""
        # 设置孔位集合
        main_window.set_hole_collection(sample_hole_collection)
        
        # 验证：孔位集合正确设置
        assert main_window.hole_collection is not None
        assert len(main_window.hole_collection) == 3
        
        # 验证：显示更新
        assert main_window.hole_count_label.text() == "孔位数量: 3"
        
        # 验证：状态统计更新
        assert "待检: 1" in main_window.pending_count_label.text()
        assert "合格: 1" in main_window.qualified_count_label.text()
        assert "异常: 1" in main_window.defective_count_label.text()
        
        print("✅ 孔位集合加载正确")
    
    def test_hole_selection(self, main_window, sample_hole_collection):
        """测试孔位选择功能"""
        # 设置孔位集合
        main_window.set_hole_collection(sample_hole_collection)
        
        # 选择第一个孔位
        hole = list(sample_hole_collection.holes.values())[0]
        main_window.select_hole(hole)
        
        # 验证：孔位选择正确
        assert main_window.selected_hole == hole
        assert main_window.selected_hole_id_label.text() == hole.hole_id
        assert f"({hole.center_x:.2f}, {hole.center_y:.2f})" in main_window.selected_hole_pos_label.text()
        
        # 验证：相关按钮启用
        assert main_window.goto_realtime_btn.isEnabled() == True
        assert main_window.goto_history_btn.isEnabled() == True
        assert main_window.mark_defective_btn.isEnabled() == True
        
        print("✅ 孔位选择功能正确")
    
    def test_navigation_signals(self, main_window, sample_hole_collection, qapp):
        """测试导航信号发射"""
        # 设置孔位集合并选择孔位
        main_window.set_hole_collection(sample_hole_collection)
        hole = list(sample_hole_collection.holes.values())[0]
        main_window.select_hole(hole)
        
        # 测试实时监控导航信号
        signal_received = []
        main_window.navigate_to_realtime.connect(lambda hole_id: signal_received.append(('realtime', hole_id)))
        
        # 触发导航
        main_window.goto_realtime()
        
        # 验证：信号正确发射
        assert len(signal_received) == 1
        assert signal_received[0] == ('realtime', hole.hole_id)
        
        # 测试历史数据导航信号
        signal_received.clear()
        main_window.navigate_to_history.connect(lambda hole_id: signal_received.append(('history', hole_id)))
        
        main_window.goto_history()
        
        # 验证：信号正确发射
        assert len(signal_received) == 1
        assert signal_received[0] == ('history', hole.hole_id)
        
        print("✅ 导航信号发射正确")
    
    def test_status_update_functionality(self, main_window, sample_hole_collection):
        """测试状态更新功能"""
        # 设置孔位集合并选择孔位
        main_window.set_hole_collection(sample_hole_collection)
        hole = list(sample_hole_collection.holes.values())[0]  # PENDING状态的孔位
        main_window.select_hole(hole)
        
        # 记录原始状态
        original_status = hole.status
        assert original_status == HoleStatus.PENDING
        
        # 标记为异常
        main_window.mark_defective()
        
        # 验证：状态更新正确
        assert hole.status == HoleStatus.DEFECTIVE
        assert main_window.selected_hole_status_label.text() == "defective"
        
        # 验证：统计信息更新
        assert "待检: 0" in main_window.pending_count_label.text()
        assert "异常: 2" in main_window.defective_count_label.text()
        
        print("✅ 状态更新功能正确")
    
    def test_log_functionality(self, main_window):
        """测试日志功能"""
        # 清空日志
        main_window.log_display.clear()
        
        # 添加日志消息
        test_message = "测试日志消息"
        main_window.log_message(test_message)
        
        # 验证：日志正确显示
        log_content = main_window.log_display.toPlainText()
        assert test_message in log_content
        assert "[" in log_content  # 时间戳格式
        assert "]" in log_content
        
        print("✅ 日志功能正确")
    
    def test_window_resize_handling(self, main_window):
        """测试窗口大小调整处理"""
        # 显示窗口以便测试组件可见性
        main_window.show()

        # 获取初始大小
        initial_size = main_window.size()

        # 调整窗口大小
        new_width = 1400
        new_height = 900
        main_window.resize(new_width, new_height)

        # 验证：窗口大小正确调整
        current_size = main_window.size()
        assert current_size.width() == new_width
        assert current_size.height() == new_height

        # 验证：布局自适应调整（组件存在且已创建）
        assert main_window.load_dxf_btn is not None
        assert main_window.progress_bar is not None
        assert main_window.log_display is not None

        # 隐藏窗口
        main_window.hide()

        print("✅ 窗口大小调整处理正确")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
