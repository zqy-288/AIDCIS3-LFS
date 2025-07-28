#!/usr/bin/env python3
"""
示例名称: 基础检测流程演示

功能描述:
- 演示完整的检测工作流程
- 展示从文件加载到检测完成的全过程
- 监听检测进度和状态变化
- 演示检测结果的处理

使用方法:
python basic_detection.py

依赖要求:
- Python 3.8+
- PySide6 >= 6.0.0
- AIDCIS3-LFS项目源码

作者: AIDCIS3-LFS团队
创建时间: 2025-07-25
"""

import sys
import os
import time
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer, QObject
except ImportError as e:
    print(f"❌ PySide6导入失败: {e}")
    sys.exit(1)

try:
    from src.controllers.coordinators.main_window_coordinator import MainWindowCoordinator
except ImportError as e:
    print(f"❌ 项目模块导入失败: {e}")
    sys.exit(1)


class DetectionDemo(QObject):
    """检测演示类"""
    
    def __init__(self, coordinator: MainWindowCoordinator):
        super().__init__()
        self.coordinator = coordinator
        self.business_controller = coordinator.business_controller
        self.current_step = 0
        self.detection_started = False
        self.detection_completed = False
        
        # 演示步骤
        self.demo_steps = [
            "创建测试数据",
            "加载测试文件",
            "等待文件加载完成",
            "开始检测流程",
            "监听检测进度",
            "等待检测完成",
            "显示检测结果"
        ]
        
        # 设置信号连接
        self._setup_signal_connections()
        
        print("🔬 检测演示初始化完成")
    
    def _setup_signal_connections(self):
        """设置信号连接"""
        
        # 监听ViewModel变化
        self.business_controller.view_model_changed.connect(self._on_view_model_changed)
        
        # 监听消息事件
        self.business_controller.message_occurred.connect(self._on_message_occurred)
        
        print("🔗 检测监听器已设置")
    
    def start_demo(self):
        """开始演示"""
        print(f"\n🎬 开始检测演示 - 共{len(self.demo_steps)}个步骤")
        print("=" * 60)
        
        # 开始第一步
        self._execute_next_step()
    
    def _execute_next_step(self):
        """执行下一步"""
        if self.current_step >= len(self.demo_steps):
            self._demo_completed()
            return
        
        step_name = self.demo_steps[self.current_step]
        print(f"\n📋 步骤 {self.current_step + 1}/{len(self.demo_steps)}: {step_name}")
        print("-" * 40)
        
        if self.current_step == 0:
            self._create_test_data()
        elif self.current_step == 1:
            self._load_test_file()
        elif self.current_step == 2:
            self._wait_for_file_loading()
        elif self.current_step == 3:
            self._start_detection()
        elif self.current_step == 4:
            self._monitor_detection_progress()
        elif self.current_step == 5:
            self._wait_for_detection_completion()
        elif self.current_step == 6:
            self._show_detection_results()
        
        self.current_step += 1
    
    def _create_test_data(self):
        """步骤1: 创建测试数据"""
        print("📦 创建模拟的孔位数据...")
        
        # 创建测试用的孔位集合数据
        test_holes = []
        for i in range(20):  # 创建20个测试孔位
            hole_data = {
                'id': f'H{i:03d}',
                'x': i * 10,
                'y': 0,
                'diameter': 10.0,
                'status': 'pending'
            }
            test_holes.append(hole_data)
        
        self.test_data = {
            'holes': test_holes,
            'product_id': 'TEST_PRODUCT_001',
            'file_path': 'test_detection.dxf'
        }
        
        print(f"✅ 创建了{len(test_holes)}个测试孔位")
        
        # 延迟执行下一步
        QTimer.singleShot(1000, self._execute_next_step)
    
    def _load_test_file(self):
        """步骤2: 加载测试文件"""
        print("📁 模拟加载DXF文件...")
        
        try:
            # 直接更新ViewModel，模拟文件加载
            view_model = self.business_controller.view_model_manager.view_model
            view_model.loading = True
            
            # 模拟文件信息
            file_info = {
                'filename': self.test_data['file_path'],
                'hole_count': len(self.test_data['holes']),
                'file_size': '2.5KB',
                'created_time': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 更新文件信息
            self.business_controller.view_model_manager.update_file_info(
                self.test_data['file_path'], 
                file_info
            )
            
            print(f"✅ 文件加载请求已发送: {self.test_data['file_path']}")
            
        except Exception as e:
            print(f"❌ 文件加载失败: {e}")
        
        # 延迟执行下一步
        QTimer.singleShot(2000, self._execute_next_step)
    
    def _wait_for_file_loading(self):
        """步骤3: 等待文件加载完成"""
        print("⏳ 等待文件加载完成...")
        
        # 模拟文件加载完成
        view_model = self.business_controller.view_model_manager.view_model
        view_model.loading = False
        view_model.hole_collection = self.test_data['holes']  # 设置孔位数据
        
        # 发出更新信号
        self.business_controller.view_model_manager.view_model_changed.emit(view_model)
        
        print("✅ 文件加载完成")
        
        # 延迟执行下一步
        QTimer.singleShot(1000, self._execute_next_step)
    
    def _start_detection(self):
        """步骤4: 开始检测流程"""
        print("🚀 启动检测流程...")
        
        try:
            # 检查是否有可检测的数据
            view_model = self.business_controller.view_model_manager.view_model
            if not view_model.hole_collection:
                print("❌ 没有可检测的孔位数据")
                return
            
            # 启动检测
            detection_params = {
                'mode': 'auto',
                'confidence_threshold': 0.8,
                'batch_size': 5
            }
            
            self.business_controller.handle_user_action("start_detection", detection_params)
            self.detection_started = True
            
            print(f"✅ 检测已启动，参数: {detection_params}")
            
        except Exception as e:
            print(f"❌ 启动检测失败: {e}")
        
        # 延迟执行下一步
        QTimer.singleShot(1500, self._execute_next_step)
    
    def _monitor_detection_progress(self):
        """步骤5: 监听检测进度"""
        print("📊 开始监听检测进度...")
        
        # 这一步主要是设置监听，实际的进度更新会通过信号处理
        # 延迟执行下一步
        QTimer.singleShot(2000, self._execute_next_step)
    
    def _wait_for_detection_completion(self):
        """步骤6: 等待检测完成"""
        print("⏳ 等待检测完成...")
        
        # 检查检测是否完成
        def check_completion():
            if self.detection_completed:
                print("✅ 检测已完成")
                self._execute_next_step()
            else:
                print("🔄 检测进行中，继续等待...")
                QTimer.singleShot(1000, check_completion)
        
        # 开始检查
        QTimer.singleShot(1000, check_completion)
    
    def _show_detection_results(self):
        """步骤7: 显示检测结果"""
        print("📋 显示检测结果...")
        
        view_model = self.business_controller.view_model_manager.view_model
        
        if view_model.status_summary:
            print("🎯 检测结果摘要:")
            for status, count in view_model.status_summary.items():
                print(f"  - {status}: {count}个")
        else:
            print("📊 模拟检测结果:")
            print("  - 总孔位: 20个")
            print("  - 合格: 17个")
            print("  - 不合格: 2个")
            print("  - 警告: 1个")
        
        print("✅ 检测结果显示完成")
        
        # 完成演示
        QTimer.singleShot(2000, self._demo_completed)
    
    def _demo_completed(self):
        """演示完成"""
        print("\n🎉 检测演示完成！")
        print("=" * 60)
        print("📝 演示总结:")
        print("  ✅ 文件加载流程")
        print("  ✅ 检测启动流程")
        print("  ✅ 进度监听机制")
        print("  ✅ 结果处理流程")
        print("\n💡 这个演示展示了AIDCIS3-LFS的基本检测工作流程")
        
        # 延迟关闭应用
        QTimer.singleShot(3000, self._close_application)
    
    def _close_application(self):
        """关闭应用"""
        print("\n👋 演示结束，正在关闭应用...")
        QApplication.instance().quit()
    
    def _on_view_model_changed(self, view_model):
        """处理ViewModel变化"""
        # 检测状态变化
        if hasattr(view_model, 'detection_running'):
            if view_model.detection_running and not self.detection_started:
                print("🔬 检测状态: 已启动")
            elif not view_model.detection_running and self.detection_started and not self.detection_completed:
                print("🔬 检测状态: 已完成")
                self.detection_completed = True
        
        # 检测进度变化
        if hasattr(view_model, 'detection_progress') and view_model.detection_progress > 0:
            print(f"📈 检测进度: {view_model.detection_progress:.1f}%")
        
        # 孔位数据变化
        if hasattr(view_model, 'hole_collection') and view_model.hole_collection:
            hole_count = len(view_model.hole_collection) if hasattr(view_model.hole_collection, '__len__') else 'N/A'
            print(f"📍 孔位数据已加载: {hole_count}个孔位")
    
    def _on_message_occurred(self, message: str, level: str):
        """处理消息事件"""
        level_emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌'
        }
        
        emoji = level_emoji.get(level, '📝')
        print(f"{emoji} 系统消息: {message}")


def main():
    """主函数"""
    print("🔬 AIDCIS3-LFS 基础检测流程演示")
    print("=" * 60)
    print("💡 这个演示将展示：")
    print("  📁 文件加载流程")
    print("  🚀 检测启动过程")
    print("  📊 进度监听机制")
    print("  📋 结果处理流程")
    print()
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    app.setApplicationName("AIDCIS3-LFS Detection Demo")
    
    try:
        # 创建主窗口协调器
        coordinator = MainWindowCoordinator()
        print("✅ 主窗口协调器创建成功")
        
        # 显示主窗口
        coordinator.show()
        print("✅ 主窗口已显示")
        
        # 创建检测演示实例
        demo = DetectionDemo(coordinator)
        
        # 延迟开始演示
        QTimer.singleShot(2000, demo.start_demo)
        
        print("\n🎬 演示将在2秒后开始...")
        print("💡 请观察控制台输出了解检测流程")
        
        # 运行应用
        return app.exec()
        
    except Exception as e:
        print(f"❌ 演示运行失败: {e}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"\n👋 检测演示结束，退出代码: {exit_code}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断演示")
        sys.exit(0)
        
    except Exception as e:
        print(f"💥 演示异常: {e}")
        sys.exit(1)