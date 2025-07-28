#!/usr/bin/env python3
"""
快速UI测试脚本
验证修复后的内窥镜组件显示
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from src.main_window import MainWindowEnhanced

def main():
    app = QApplication(sys.argv)
    
    print("🚀 启动修复后的主程序...")
    
    # 创建主窗口
    window = MainWindowEnhanced()
    window.setWindowTitle("AIDCIS3-LFS - 修复验证")
    
    # 自动切换到实时监控标签页
    if hasattr(window, 'tab_widget'):
        for i in range(window.tab_widget.count()):
            if "实时监控" in window.tab_widget.tabText(i):
                window.tab_widget.setCurrentIndex(i)
                print(f"✅ 已自动切换到实时监控标签页")
                break
    
    # 检查内窥镜组件
    if hasattr(window, 'realtime_tab') and hasattr(window.realtime_tab, 'endoscope_view'):
        endoscope = window.realtime_tab.endoscope_view
        print(f"✅ 内窥镜组件已加载")
        print(f"   类型: {type(endoscope)}")
        print(f"   最小尺寸: {endoscope.minimumSize()}")
        
        # 检查分割器
        if hasattr(window.realtime_tab, 'main_splitter'):
            splitter = window.realtime_tab.main_splitter
            print(f"✅ 分割器已创建，包含 {splitter.count()} 个组件")
    
    window.show()
    
    print("\n🎯 现在应该能看到:")
    print("   1. 上半部分: 管孔直径实时监控图表")
    print("   2. 下半部分: 内窥镜图像显示区域")
    print("   3. 内窥镜区域显示占位符文本")
    
    return app.exec()

if __name__ == "__main__":
    main()