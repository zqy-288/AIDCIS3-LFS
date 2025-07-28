#!/usr/bin/env python3
"""
业务控制器集成测试
验证MainBusinessController及其服务的集成正确性
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject

from src.controllers import MainBusinessController, UserAction
from src.ui.view_models.view_model_manager import MainViewModelManager
from src.ui.view_models.main_view_model import MainViewModel
from src.core_business.models.hole_data import HoleData, HoleCollection, HoleStatus


class TestSignalReceiver(QObject):
    """测试信号接收器"""
    
    def __init__(self):
        super().__init__()
        self.received_signals = []
        
    def on_view_model_changed(self, view_model):
        """接收视图模型变化信号"""
        self.received_signals.append(("view_model_changed", view_model))
        print(f"✓ 接收到视图模型变化信号")
        
    def on_message_occurred(self, message_type, message_content):
        """接收消息信号"""
        self.received_signals.append(("message_occurred", message_type, message_content))
        print(f"✓ 接收到消息信号: [{message_type}] {message_content}")


def create_test_hole_collection() -> HoleCollection:
    """创建测试用的孔位集合"""
    holes = {}
    
    # 创建一些测试孔位
    for i in range(1, 6):
        hole_id = f"H{i:03d}"
        hole = HoleData(
            hole_id=hole_id,
            center_x=i * 100.0,
            center_y=50.0,
            radius=5.0,
            status=HoleStatus.PENDING
        )
        holes[hole_id] = hole
    
    collection = HoleCollection()
    collection.holes = holes
    
    # 添加get_bounds方法（如果没有的话）
    if not hasattr(collection, 'get_bounds'):
        collection.get_bounds = lambda: (0, 0, 500, 100)
    
    return collection


def test_main_business_controller():
    """测试MainBusinessController"""
    print("=== 测试MainBusinessController ===")
    
    # 创建Qt应用
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    try:
        # 创建视图模型管理器
        view_model_manager = MainViewModelManager()
        
        # 创建业务控制器
        controller = MainBusinessController(view_model_manager)
        
        # 创建信号接收器
        receiver = TestSignalReceiver()
        
        # 连接信号
        controller.view_model_changed.connect(receiver.on_view_model_changed)
        controller.message_occurred.connect(receiver.on_message_occurred)
        
        print("✓ MainBusinessController创建成功")
        
        # 测试基本功能
        view_model = controller.get_view_model()
        assert view_model is not None
        print("✓ 获取视图模型成功")
        
        # 测试日志添加
        controller.add_log_message("测试日志消息")
        assert len(view_model.log_messages) > 0
        print("✓ 添加日志消息成功")
        
        return controller, receiver
        
    except Exception as e:
        print(f"❌ MainBusinessController测试失败: {e}")
        raise


def test_detection_workflow(controller, receiver):
    """测试检测工作流程"""
    print("\n=== 测试检测工作流程 ===")
    
    try:
        # 创建测试数据
        hole_collection = create_test_hole_collection()
        
        # 设置孔位集合
        controller.view_model_manager.update_hole_collection(hole_collection)
        print("✓ 设置孔位集合成功")
        
        # 开始检测
        result = controller.handle_user_action(UserAction.START_DETECTION)
        assert result.get("success") == True
        print("✓ 开始检测成功")
        
        # 暂停检测
        result = controller.handle_user_action(UserAction.PAUSE_DETECTION)
        assert result.get("success") == True
        print("✓ 暂停检测成功")
        
        # 恢复检测
        result = controller.handle_user_action(UserAction.PAUSE_DETECTION)
        assert result.get("success") == True
        print("✓ 恢复检测成功")
        
        # 停止检测
        result = controller.handle_user_action(UserAction.STOP_DETECTION)
        assert result.get("success") == True
        print("✓ 停止检测成功")
        
        print("检测工作流程测试完成!")
        
    except Exception as e:
        print(f"❌ 检测工作流程测试失败: {e}")
        raise


def test_search_functionality(controller, receiver):
    """测试搜索功能"""
    print("\n=== 测试搜索功能 ===")
    
    try:
        # 创建测试数据
        hole_collection = create_test_hole_collection()
        controller.view_model_manager.update_hole_collection(hole_collection)
        
        # 执行搜索
        result = controller.handle_user_action(UserAction.PERFORM_SEARCH, search_query="AAAC001R001")
        assert result.get("success") == True
        print("✓ 搜索孔位AAAC001R001成功")
        
        # 测试特殊命令
        result = controller.handle_user_action(UserAction.PERFORM_SEARCH, search_query="SNAKE_DEMO")
        assert result.get("success") == True
        print("✓ 执行SNAKE_DEMO命令成功")
        
        # 清空搜索
        result = controller.handle_user_action(UserAction.CLEAR_SEARCH)
        assert result.get("success") == True
        print("✓ 清空搜索成功")
        
        print("搜索功能测试完成!")
        
    except Exception as e:
        print(f"❌ 搜索功能测试失败: {e}")
        raise


def test_file_operations(controller, receiver):
    """测试文件操作"""
    print("\n=== 测试文件操作 ===")
    
    try:
        # 测试加载DXF文件（使用不存在的文件，应该失败）
        result = controller.handle_user_action(UserAction.LOAD_DXF_FILE, file_path="/nonexistent/file.dxf")
        assert result.get("success") == False
        print("✓ 加载不存在文件正确失败")
        
        # 测试产品选择
        class MockProduct:
            def __init__(self):
                self.model_name = "测试产品"
                self.dxf_file_path = None
        
        mock_product = MockProduct()
        result = controller.handle_user_action(UserAction.SELECT_PRODUCT, product=mock_product)
        assert result.get("success") == True
        print("✓ 选择产品成功")
        
        print("文件操作测试完成!")
        
    except Exception as e:
        print(f"❌ 文件操作测试失败: {e}")
        raise


def test_hole_operations(controller, receiver):
    """测试孔位操作"""
    print("\n=== 测试孔位操作 ===")
    
    try:
        # 创建测试数据
        hole_collection = create_test_hole_collection()
        controller.view_model_manager.update_hole_collection(hole_collection)
        
        # 选择孔位
        test_hole = list(hole_collection.holes.values())[0]
        result = controller.handle_user_action(UserAction.SELECT_HOLE, hole=test_hole)
        assert result.get("success") == True
        print("✓ 选择孔位成功")
        
        # 标记异常
        result = controller.handle_user_action(UserAction.MARK_DEFECTIVE, hole_id=test_hole.hole_id)
        assert result.get("success") == True
        print("✓ 标记孔位异常成功")
        
        print("孔位操作测试完成!")
        
    except Exception as e:
        print(f"❌ 孔位操作测试失败: {e}")
        raise


def test_simulation_workflow(controller, receiver):
    """测试模拟工作流程"""
    print("\n=== 测试模拟工作流程 ===")
    
    try:
        # 创建测试数据
        hole_collection = create_test_hole_collection()
        controller.view_model_manager.update_hole_collection(hole_collection)
        
        # 开始模拟
        result = controller.handle_user_action(UserAction.START_SIMULATION)
        assert result.get("success") == True
        print("✓ 开始模拟成功")
        
        # 停止模拟
        result = controller.handle_user_action(UserAction.STOP_SIMULATION)
        assert result.get("success") == True
        print("✓ 停止模拟成功")
        
        print("模拟工作流程测试完成!")
        
    except Exception as e:
        print(f"❌ 模拟工作流程测试失败: {e}")
        raise


def test_signal_integration(receiver):
    """测试信号集成"""
    print("\n=== 测试信号集成 ===")
    
    try:
        # 检查接收到的信号
        signal_types = set()
        for signal_data in receiver.received_signals:
            signal_types.add(signal_data[0])
        
        print(f"✓ 共接收到 {len(receiver.received_signals)} 个信号")
        print(f"✓ 信号类型: {list(signal_types)}")
        
        # 验证关键信号
        assert "message_occurred" in signal_types
        print("✓ 消息信号集成正常")
        
        print("信号集成测试完成!")
        
    except Exception as e:
        print(f"❌ 信号集成测试失败: {e}")
        raise


def main():
    """主测试函数"""
    print("开始业务控制器集成测试...\n")
    
    try:
        # 基础功能测试
        controller, receiver = test_main_business_controller()
        
        # 功能测试
        test_detection_workflow(controller, receiver)
        test_search_functionality(controller, receiver)
        test_file_operations(controller, receiver)
        test_hole_operations(controller, receiver)
        test_simulation_workflow(controller, receiver)
        
        # 信号集成测试
        test_signal_integration(receiver)
        
        # 清理资源
        controller.cleanup()
        
        print("\n🎉 所有测试通过!")
        return 0
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)