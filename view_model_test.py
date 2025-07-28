#!/usr/bin/env python3
"""
视图模型测试文件
验证MainViewModel和MainViewModelManager的正确性
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject

from src.ui.view_models.main_view_model import (
    MainViewModel, DetectionState, SimulationState, ViewMode,
    DetectionStats, TimeStats, FileInfo, SelectedHoleInfo,
    SnakePathConfig, SectorViewConfig, SystemStatus
)
from src.ui.view_models.view_model_manager import MainViewModelManager
from src.core_business.models.hole_data import HoleData, HoleStatus


class SignalReceiver(QObject):
    """信号接收器，用于测试信号发射"""
    
    def __init__(self):
        super().__init__()
        self.received_signals = []
        
    def on_signal_received(self, signal_name, *args):
        """接收信号"""
        self.received_signals.append((signal_name, args))
        print(f"接收到信号: {signal_name}, 参数: {args}")


def test_main_view_model():
    """测试MainViewModel数据模型"""
    print("=== 测试MainViewModel ===")
    
    # 创建默认视图模型
    view_model = MainViewModel()
    
    # 验证默认值
    assert view_model.detection_state == DetectionState.IDLE
    assert view_model.simulation_state == SimulationState.IDLE
    assert view_model.file_info.file_name == "未加载"
    assert view_model.selected_hole_info.hole_id == "未选择"
    assert len(view_model.detection_holes) == 0
    print("✓ 默认值验证通过")
    
    # 测试重置方法
    view_model.detection_state = DetectionState.RUNNING
    view_model.simulation_state = SimulationState.RUNNING
    view_model.time_stats.detection_elapsed_seconds = 100
    
    view_model.reset_detection_state()
    assert view_model.detection_state == DetectionState.IDLE
    assert view_model.time_stats.detection_elapsed_seconds == 0
    print("✓ 重置检测状态方法验证通过")
    
    view_model.reset_simulation_state()
    assert view_model.simulation_state == SimulationState.IDLE
    assert view_model.simulation_index_v2 == 0
    print("✓ 重置模拟状态方法验证通过")
    
    # 测试文件信息更新
    view_model.update_file_info("/test/path/file.dxf", "test_file.dxf", "1.2MB", 100)
    assert view_model.file_info.current_file_path == "/test/path/file.dxf"
    assert view_model.file_info.file_name == "test_file.dxf"
    assert view_model.file_info.file_size == "1.2MB"
    assert view_model.file_info.hole_count == 100
    print("✓ 文件信息更新方法验证通过")
    
    # 测试选中孔位信息更新
    test_hole = HoleData(
        hole_id="H001",
        center_x=100.0,
        center_y=200.0,
        radius=5.0,
        status=HoleStatus.PENDING
    )
    view_model.update_selected_hole_info(test_hole)
    assert view_model.selected_hole == test_hole
    assert view_model.selected_hole_info.hole_id == "H001"
    assert "100.0" in view_model.selected_hole_info.position
    print("✓ 选中孔位信息更新方法验证通过")
    
    # 测试日志消息
    view_model.add_log_message("测试日志消息")
    assert len(view_model.log_messages) == 1
    assert "测试日志消息" in view_model.log_messages[0]
    print("✓ 日志消息方法验证通过")
    
    print("MainViewModel测试完成!\n")


def test_main_view_model_manager():
    """测试MainViewModelManager"""
    print("=== 测试MainViewModelManager ===")
    
    # 创建Qt应用（信号需要事件循环）
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # 创建管理器
    manager = MainViewModelManager()
    
    # 创建信号接收器
    receiver = SignalReceiver()
    
    # 连接信号
    manager.detection_state_changed.connect(
        lambda state: receiver.on_signal_received("detection_state_changed", state)
    )
    manager.file_info_changed.connect(
        lambda info: receiver.on_signal_received("file_info_changed", info)
    )
    manager.selected_hole_changed.connect(
        lambda hole: receiver.on_signal_received("selected_hole_changed", hole)
    )
    manager.log_message_added.connect(
        lambda msg: receiver.on_signal_received("log_message_added", msg)
    )
    manager.progress_changed.connect(
        lambda val, max_val: receiver.on_signal_received("progress_changed", val, max_val)
    )
    
    # 测试检测状态更新
    manager.set_detection_state(DetectionState.RUNNING)
    assert manager.view_model.detection_state == DetectionState.RUNNING
    print("✓ 检测状态更新验证通过")
    
    # 测试文件信息更新
    manager.update_file_info("/test/file.dxf", "test.dxf", "2.5MB", 150)
    assert manager.view_model.file_info.current_file_path == "/test/file.dxf"
    print("✓ 文件信息更新验证通过")
    
    # 测试孔位选择
    test_hole = HoleData(
        hole_id="H002",
        center_x=150.0,
        center_y=250.0,
        radius=6.0,
        status=HoleStatus.QUALIFIED
    )
    manager.set_selected_hole(test_hole)
    assert manager.view_model.selected_hole == test_hole
    print("✓ 孔位选择验证通过")
    
    # 测试进度更新
    manager.update_progress(50, 200)
    assert manager.view_model.progress_value == 50
    assert manager.view_model.progress_maximum == 200
    print("✓ 进度更新验证通过")
    
    # 测试日志添加
    manager.add_log_message("测试管理器日志")
    assert len(manager.view_model.log_messages) == 1
    print("✓ 日志添加验证通过")
    
    # 测试时间统计更新
    now = datetime.now()
    manager.update_time_stats(elapsed_seconds=300, estimated_seconds=600, start_time=now)
    assert manager.view_model.time_stats.detection_elapsed_seconds == 300
    assert manager.view_model.time_stats.estimated_seconds == 600
    assert manager.view_model.time_stats.start_time == now
    print("✓ 时间统计更新验证通过")
    
    # 测试蛇形路径配置更新
    holes = [test_hole]
    analysis = {"total_distance": 1000.0}
    stats = {"efficiency": 0.85}
    manager.update_snake_path_config(
        enabled=True,
        debug_mode=True,
        sorted_holes=holes,
        analysis=analysis,
        stats=stats,
        simulation_index=5
    )
    config = manager.view_model.snake_path_config
    assert config.enabled == True
    assert config.debug_mode == True
    assert len(config.sorted_holes) == 1
    assert config.analysis["total_distance"] == 1000.0
    assert config.stats["efficiency"] == 0.85
    assert config.simulation_index == 5
    print("✓ 蛇形路径配置更新验证通过")
    
    # 测试系统状态更新
    manager.update_system_status(
        status_message="检测中",
        connection_status="设备已连接",
        last_aidcis2_status="RUNNING"
    )
    status = manager.view_model.system_status
    assert status.status_message == "检测中"
    assert status.connection_status == "设备已连接"
    assert status.last_aidcis2_status == "RUNNING"
    print("✓ 系统状态更新验证通过")
    
    # 测试重置方法
    manager.reset_detection()
    assert manager.view_model.detection_state == DetectionState.IDLE
    print("✓ 重置检测验证通过")
    
    manager.reset_simulation()
    assert manager.view_model.simulation_state == SimulationState.IDLE
    print("✓ 重置模拟验证通过")
    
    # 检查信号是否被发射
    print(f"✓ 共接收到 {len(receiver.received_signals)} 个信号")
    
    print("MainViewModelManager测试完成!\n")


def test_integration():
    """集成测试"""
    print("=== 集成测试 ===")
    
    # 创建管理器
    manager = MainViewModelManager()
    
    # 模拟完整的检测流程
    print("模拟检测流程...")
    
    # 1. 加载文件
    manager.update_file_info("/data/workpiece.dxf", "workpiece.dxf", "5.2MB", 500)
    
    # 2. 开始检测
    manager.set_detection_state(DetectionState.RUNNING)
    manager.update_time_stats(start_time=datetime.now())
    
    # 3. 模拟检测进展
    for i in range(5):
        progress = (i + 1) * 20  # 20%, 40%, 60%, 80%, 100%
        manager.update_progress(progress, 100)
        
        # 更新统计
        stats = DetectionStats(
            completed_count=progress,
            pending_count=100 - progress,
            qualified_count=int(progress * 0.9),
            defective_count=int(progress * 0.1),
            completion_rate=progress,
            qualification_rate=90.0
        )
        manager.update_detection_stats(stats)
        
        # 更新时间
        manager.update_time_stats(elapsed_seconds=(i + 1) * 60)
        
        manager.add_log_message(f"检测进度: {progress}%")
    
    # 4. 完成检测
    manager.set_detection_state(DetectionState.IDLE)
    manager.add_log_message("检测完成")
    
    # 验证最终状态
    assert manager.view_model.progress_value == 100
    assert manager.view_model.detection_stats.completion_rate == 100
    assert len(manager.view_model.log_messages) == 6  # 5个进度 + 1个完成
    
    print("✓ 集成测试通过")


def main():
    """主测试函数"""
    print("开始视图模型测试...\n")
    
    try:
        test_main_view_model()
        test_main_view_model_manager()
        test_integration()
        
        print("🎉 所有测试通过!")
        return 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)