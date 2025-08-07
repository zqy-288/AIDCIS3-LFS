#!/usr/bin/env python3
"""
扇形分隔线修复验证脚本
快速测试修复后的扇形分隔线是否正确显示
"""

import sys
import os
from pathlib import Path

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, current_dir)
sys.path.insert(0, src_dir)

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt, QTimer

def main():
    """测试修复后的扇形分隔线"""
    print("🚀 验证扇形分隔线修复效果")
    print("=" * 50)
    
    app = QApplication([])
    
    try:
        # 导入修复后的组件
        from src.pages.main_detection_p1.components.graphics.complete_panorama_widget import CompletePanoramaWidget
        print("✅ 全景图组件导入成功")
        
        # 创建测试窗口
        window = QMainWindow()
        window.setWindowTitle("扇形分隔线验证")
        window.setGeometry(200, 200, 800, 800)
        
        central_widget = QWidget()
        window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 状态标签
        status_label = QLabel("正在创建全景图组件...")
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)
        
        # 创建全景图组件
        panorama_widget = CompletePanoramaWidget()
        panorama_widget.setFixedSize(600, 600)
        layout.addWidget(panorama_widget)
        
        # 模拟数据加载（使用CAP1000数据）
        print("🔍 正在加载CAP1000数据...")
        
        # 导入数据管理器
        from src.core.shared_data_manager import SharedDataManager
        data_manager = SharedDataManager()
        
        # 获取CAP1000数据
        if hasattr(data_manager, 'hole_collection') and data_manager.hole_collection:
            hole_data = data_manager.hole_collection
            print(f"✅ 找到CAP1000数据: {len(hole_data.holes)} 个孔位")
            
            # 加载数据到全景图
            panorama_widget.load_hole_data(hole_data)
            status_label.setText(
                "✅ 验证完成!\n"
                "请检查全景图中是否显示:\n"
                "• 深灰色十字分隔线\n"
                "• 灰色虚线扇形边界\n"
                "• 四个清晰的扇形区域"
            )
            print("✅ 数据已加载到全景图组件")
            print("🔍 请观察窗口中的扇形分隔线效果")
            
        else:
            status_label.setText("⚠️ 未找到CAP1000数据\n但组件创建成功")
            print("⚠️ 未找到CAP1000数据，但组件创建成功")
        
        # 显示窗口
        window.show()
        
        # 5秒后自动关闭
        QTimer.singleShot(8000, window.close)
        
        print("📋 验证窗口已打开，将在8秒后自动关闭")
        
        # 运行应用
        app.exec()
        
        print("✅ 验证完成")
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n🔚 验证结果: {'成功' if success else '失败'}")
    sys.exit(0 if success else 1)