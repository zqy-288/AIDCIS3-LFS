#!/usr/bin/env python3
"""
示例名称: 文件加载演示

功能描述:
- 演示如何程序化加载DXF文件
- 展示业务控制器的文件处理能力
- 监听文件加载的各种状态和事件
- 演示错误处理和用户反馈

使用方法:
python file_loading.py [文件路径]

如果不提供文件路径，将使用示例测试文件

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
    from src.controllers.main_business_controller import MainBusinessController
except ImportError as e:
    print(f"❌ 项目模块导入失败: {e}")
    sys.exit(1)


class FileLoadingDemo(QObject):
    """文件加载演示类"""
    
    def __init__(self, coordinator: MainWindowCoordinator, file_path: str):
        super().__init__()
        self.coordinator = coordinator
        self.file_path = file_path
        self.business_controller = coordinator.business_controller
        
        # 连接信号以监听文件加载状态
        self._setup_signal_connections()
        
        print(f"📁 准备加载文件: {file_path}")
    
    def _setup_signal_connections(self):
        """设置信号连接以监听文件加载过程"""
        
        # 监听ViewModel变化
        self.business_controller.view_model_changed.connect(self._on_view_model_changed)
        
        # 监听消息事件
        self.business_controller.message_occurred.connect(self._on_message_occurred)
        
        print("🔗 文件加载监听器已设置")
    
    def start_loading(self):
        """开始加载文件"""
        print("🚀 开始加载文件...")
        
        # 检查文件是否存在
        if not os.path.exists(self.file_path):
            print(f"❌ 文件不存在: {self.file_path}")
            return False
        
        try:
            # 调用业务控制器的文件加载方法
            self.business_controller.handle_user_action(
                "load_dxf_file", 
                {"file_path": self.file_path}
            )
            return True
            
        except Exception as e:
            print(f"❌ 文件加载启动失败: {e}")
            return False
    
    def _on_view_model_changed(self, view_model):
        """监听ViewModel变化"""
        print("📊 ViewModel状态更新:")
        print(f"  - 当前文件: {view_model.current_file_path}")
        print(f"  - 加载状态: {'加载中' if view_model.loading else '已完成'}")
        
        if view_model.hole_collection:
            hole_count = len(view_model.hole_collection) if hasattr(view_model.hole_collection, '__len__') else 'N/A'
            print(f"  - 孔位数量: {hole_count}")
        
        if view_model.file_info:
            print(f"  - 文件信息: {view_model.file_info}")
    
    def _on_message_occurred(self, message: str, level: str):
        """监听消息事件"""
        level_emoji = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌'
        }
        
        emoji = level_emoji.get(level, '📝')
        print(f"{emoji} [{level.upper()}] {message}")


def create_test_file() -> str:
    """创建一个测试用的DXF文件内容"""
    test_file_path = "test_data.dxf"
    
    # 简单的DXF文件内容（用于演示）
    dxf_content = """0
SECTION
2
HEADER
9
$ACADVER
1
AC1015
0
ENDSEC
0
SECTION
2
ENTITIES
0
CIRCLE
8
0
10
0.0
20
0.0
30
0.0
40
10.0
0
CIRCLE
8
0
10
20.0
20
0.0
30
0.0
40
10.0
0
ENDSEC
0
EOF
"""
    
    try:
        with open(test_file_path, 'w') as f:
            f.write(dxf_content)
        print(f"✅ 创建测试文件: {test_file_path}")
        return test_file_path
    except Exception as e:
        print(f"❌ 创建测试文件失败: {e}")
        return None


def main():
    """主函数"""
    print("📁 AIDCIS3-LFS 文件加载演示")
    print("=" * 50)
    
    # 获取文件路径
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"📂 使用指定文件: {file_path}")
    else:
        # 创建测试文件
        file_path = create_test_file()
        if not file_path:
            print("❌ 无法创建测试文件")
            return 1
        print(f"📂 使用测试文件: {file_path}")
    
    # 创建Qt应用
    app = QApplication(sys.argv)
    app.setApplicationName("AIDCIS3-LFS File Loading Demo")
    
    try:
        # 创建主窗口协调器
        coordinator = MainWindowCoordinator()
        print("✅ 主窗口协调器创建成功")
        
        # 创建文件加载演示实例
        demo = FileLoadingDemo(coordinator, file_path)
        
        # 显示主窗口（可选，主要用于演示）
        coordinator.show()
        print("✅ 主窗口已显示")
        
        # 延迟开始文件加载（让UI有时间初始化）
        def start_demo():
            print("\n🎬 开始文件加载演示...")
            if demo.start_loading():
                print("✅ 文件加载已启动")
            else:
                print("❌ 文件加载启动失败")
                app.quit()
        
        # 使用定时器延迟执行
        QTimer.singleShot(1000, start_demo)  # 1秒后开始
        
        # 设置自动退出定时器（演示用）
        def auto_exit():
            print("\n⏰ 演示时间结束，自动退出...")
            coordinator.close()
            app.quit()
        
        QTimer.singleShot(10000, auto_exit)  # 10秒后自动退出
        
        print("\n💡 提示：")
        print("  - 观察控制台输出了解文件加载过程")
        print("  - 10秒后将自动退出演示")
        print("  - 也可手动关闭窗口退出")
        
        # 运行应用
        return app.exec()
        
    except Exception as e:
        print(f"❌ 演示运行失败: {e}")
        return 1
    
    finally:
        # 清理测试文件
        if len(sys.argv) <= 1 and os.path.exists("test_data.dxf"):
            try:
                os.remove("test_data.dxf")
                print("🧹 测试文件已清理")
            except:
                pass


if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"\n👋 文件加载演示结束，退出代码: {exit_code}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断演示")
        sys.exit(0)
        
    except Exception as e:
        print(f"💥 演示异常: {e}")
        sys.exit(1)